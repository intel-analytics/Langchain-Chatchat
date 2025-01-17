import streamlit as st
from webui_pages.utils import *
from st_aggrid import AgGrid, JsCode
from st_aggrid.grid_options_builder import GridOptionsBuilder
import pandas as pd
from server.knowledge_base.utils import get_file_path, LOADER_DICT
from server.knowledge_base.kb_service.base import get_kb_details, get_kb_file_details
from typing import Literal, Dict, Tuple
from configs import (kbs_config,
                     EMBEDDING_MODEL, DEFAULT_VS_TYPE,
                     CHUNK_SIZE, OVERLAP_SIZE, ZH_TITLE_ENHANCE)
from server.utils import list_embed_models, list_online_embed_models
import os
import time

cell_renderer = JsCode("""function(params) {if(params.value==true){return '✓'}else{return '×'}}""")


def config_aggrid(
        df: pd.DataFrame,
        columns: Dict[Tuple[str, str], Dict] = {},
        selection_mode: Literal["single", "multiple", "disabled"] = "single",
        use_checkbox: bool = False,
) -> GridOptionsBuilder:
    gb = GridOptionsBuilder.from_dataframe(df)
    gb.configure_column("No", width=40)
    for (col, header), kw in columns.items():
        gb.configure_column(col, header, wrapHeaderText=True, **kw)
    gb.configure_selection(
        selection_mode=selection_mode,
        use_checkbox=use_checkbox,
        pre_selected_rows=st.session_state.get("selected_rows", [0]),
    )
    gb.configure_pagination(
        enabled=True,
        paginationAutoPageSize=False,
        paginationPageSize=10
    )
    return gb


def file_exists(kb: str, selected_rows: List) -> Tuple[str, str]:
    """
    check whether a doc file exists in local knowledge base folder.
    return the file's name and path if it exists.
    """
    if selected_rows:
        file_name = selected_rows[0]["file_name"]
        file_path = get_file_path(kb, file_name)
        if os.path.isfile(file_path):
            return file_name, file_path
    return "", ""


def knowledge_base_page(api: ApiRequest, is_lite: bool = None):
    language = st.session_state.get('language', '简体中文')

    error_text = {
        "English": "Error occurred when getting knowledge base details, please check if you have initialized or migrated the knowledge base according to `README.md` or if there is a database connection error.",
        "简体中文": "获取知识库信息错误，请检查是否已按照 `README.md` 中 `4 知识库初始化与迁移` 步骤完成初始化或迁移，或是否为数据库连接错误。"
    }
    try:
        kb_list = {x["kb_name"]: x for x in get_kb_details()}
    except Exception as e:
        st.error(error_text[language])
        st.stop()
    kb_names = list(kb_list.keys())

    if "selected_kb_name" in st.session_state and st.session_state["selected_kb_name"] in kb_names:
        selected_kb_index = kb_names.index(st.session_state["selected_kb_name"])
    else:
        selected_kb_index = 0

    if "selected_kb_info" not in st.session_state:
        st.session_state["selected_kb_info"] = ""

    def format_selected_kb(kb_name: str) -> str:
        if kb := kb_list.get(kb_name):
            return f"{kb_name} ({kb['vs_type']} @ {kb['embed_model']})"
        else:
            return kb_name

    select_kb_text = {
        "English": "New Knowledge Base",
        "简体中文": "新建知识库"
    }
    selected_kb = st.selectbox(
        {
            'English': 'Please select or create a knowledge base:',
            '简体中文': '请选择或新建知识库：'
        }[language],
        kb_names + [select_kb_text[language]],
        format_func=format_selected_kb,
        index=selected_kb_index
    )

    
    if selected_kb == select_kb_text["English"] or selected_kb == select_kb_text["简体中文"]:
        with st.form(select_kb_text[language]):

            kb_name = st.text_input(
                {
                    "English": "New Knowledge Base Name",
                    "简体中文": "新建知识库名称"
                }[language],
                placeholder={
                    "简体中文":"新知识库名称，不支持中文命名",
                    "English":"New knowledge base name, no Chinese characters supported"
                }[language],
                key="kb_name",
            )
            kb_info = st.text_input(
                {
                    "简体中文":"知识库简介",
                    "English":"Knowledge Base Introduction"
                }[language],
                placeholder={
                    "简体中文":"知识库简介，方便Agent查找",
                    "English":"Write a Knowledge Base introduction for Agent to find matches efficiently"
                }[language],
                key="kb_info",
            )

            cols = st.columns(2)

            vs_types = list(kbs_config.keys())
            vs_type = cols[0].selectbox(
                {
                    "简体中文":"向量库类型",
                    "English":"Vector Store Type"
                }[language],
                vs_types,
                index=vs_types.index(DEFAULT_VS_TYPE),
                key="vs_type",
            )

            if is_lite:
                embed_models = list_online_embed_models()
            else:
                embed_models = list_embed_models() + list_online_embed_models()

            embed_model = cols[1].selectbox(
                {
                    "简体中文":"Embedding 模型",
                    "English":"Embedding Model"
                }[language],
                embed_models,
                index=embed_models.index(EMBEDDING_MODEL),
                key="embed_model",
            )

            submit_create_kb = st.form_submit_button(
                {
                    "简体中文":"新建",
                    "English":"Create"
                }[language],
                # disabled=not bool(kb_name),
                use_container_width=True,
            )

        if submit_create_kb:
            if not kb_name or not kb_name.strip():
                st.error({
                    "简体中文":"知识库名称不能为空!",
                    "English":"Knowledge Base Name cannot be empty!"
                }[language])
            elif kb_name in kb_list:
                st.error(
                    {
                        "简体中文": "知识库名称已存在，请重新输入",
                        "English": "Knowledge Base Name already exists, please input another name"
                    }[language]
                )
            else:
                ret = api.create_knowledge_base(
                    knowledge_base_name=kb_name,
                    vector_store_type=vs_type,
                    embed_model=embed_model,
                )
                st.toast(ret.get("msg", " "))
                st.session_state["selected_kb_name"] = kb_name
                st.session_state["selected_kb_info"] = kb_info
                st.rerun()

    elif selected_kb:
        kb = selected_kb
        kb_name = kb_list[kb]['kb_name']
        kb_info_text = {
            "简体中文": f"关于数据库{kb_name}的介绍",
            "English": f"Introduction of Knowledge Base {kb_name}"
        }
        st.session_state["selected_kb_info"] = kb_info_text[language]
        # 上传文件
        files = st.file_uploader({
                                    '简体中文':"上传知识文件：",
                                    "English":"Upload Knowledge Files:"
                                }[language],
                                 [i for ls in LOADER_DICT.values() for i in ls],
                                 accept_multiple_files=True,
                                 )
        kb_info = st.text_area({
                                    '简体中文':"请输入知识库介绍:",
                                    "English":"Please input knowledge base introduction:"
                                }[language], value=st.session_state["selected_kb_info"], max_chars=None,
                               key=None, help=None, on_change=None, args=None, kwargs=None)

        if kb_info != st.session_state["selected_kb_info"]:
            st.session_state["selected_kb_info"] = kb_info
            api.update_kb_info(kb, kb_info)

        # with st.sidebar:
        with st.expander(
                {
                    "简体中文": "文件处理配置",
                    "English": "File Processing Configuration"
                }[language],
                expanded=True,
        ):
            cols = st.columns(3)
            chunk_size = cols[0].number_input({
                '简体中文':"单段文本最大长度: ",
                "English":"Max Length of Each Text: "
            }[language], 1, 1000, CHUNK_SIZE)

            chunk_overlap = cols[1].number_input({
                "简体中文": "相邻文本重合长度：",
                "English": "Overlap Length of adjacent texts: "
            }[language], 0, chunk_size, OVERLAP_SIZE)

            cols[2].write("")
            cols[2].write("")

            zh_title_enhance = cols[2].checkbox({
                "简体中文": "开启中文标题加强",
                "English": "Enable Chinese Title Enhancement"
            }[language], ZH_TITLE_ENHANCE)

        if st.button(
                {
                    '简体中文':"添加文件到知识库",
                    "English":"Add Files to Knowledge Base"
                }[language],
                # use_container_width=True,
                disabled=len(files) == 0,
        ):
            ret = api.upload_kb_docs(files,
                                     knowledge_base_name=kb,
                                     override=True,
                                     chunk_size=chunk_size,
                                     chunk_overlap=chunk_overlap,
                                     zh_title_enhance=zh_title_enhance)
            if msg := check_success_msg(ret):
                st.toast(msg, icon="✔")
            elif msg := check_error_msg(ret):
                st.toast(msg, icon="✖")

        st.divider()

        # 知识库详情
        # st.info("请选择文件，点击按钮进行操作。")
        doc_details = pd.DataFrame(get_kb_file_details(kb))
        selected_rows = []
        if not len(doc_details):
            st.info({
                "简体中文": f"知识库 `{kb}` 中暂无文件",
                "English": f"No files in knowledge base `{kb}`"
            }[language])
        else:
            st.write({
                "简体中文": f"知识库 `{kb}` 中已有文件",
                "English": f"Files in knowledge base `{kb}`"
            }[language])
            st.info({
                '简体中文':"知识库中包含源文件与向量库，请从下表中选择文件后操作",
                "English":"The knowledge base contains source files and vector stores, please select a file from the table below to proceed"
            }[language])
            doc_details.drop(columns=["kb_name"], inplace=True)
            doc_details = doc_details[[
                "No", "file_name", "document_loader", "text_splitter", "docs_count", "in_folder", "in_db",
            ]]
            doc_details["in_folder"] = doc_details["in_folder"].replace(True, "✓").replace(False, "×")
            doc_details["in_db"] = doc_details["in_db"].replace(True, "✓").replace(False, "×")

            doc_details_text = {
                "No":{
                    "简体中文":"序号",
                    "English": "No."
                },
                "file_name":{
                    "简体中文":"文档名称",
                    "English":"Document Name"
                },
                "document_loader":{
                    "简体中文":"文档加载器",
                    "English":"Document Loader"
                },
                "docs_count":{
                    "简体中文":"文档数量",
                    "English":"Document Count"
                },
                "text_splitter":{
                    "简体中文":"分词器",
                    "English":"Text Splitter"
                },
                "in_folder":{
                    "简体中文":"源文件",
                    "English":"Source File"
                },
                "in_db":{
                    "简体中文":"向量库",
                    "English":"Vector Store"
                }
            }
            gb = config_aggrid(
                doc_details,
                {
                    ("No", doc_details_text["No"][language]): {},
                    ("file_name", doc_details_text["file_name"][language]): {},
                    # ("file_ext", "文档类型"): {},
                    # ("file_version", "文档版本"): {},
                    ("document_loader", doc_details_text["document_loader"][language]): {},
                    ("docs_count", doc_details_text["docs_count"][language]): {},
                    ("text_splitter", doc_details_text["text_splitter"][language]): {},
                    # ("create_time", "创建时间"): {},
                    ("in_folder", doc_details_text["in_folder"][language]): {"cellRenderer": cell_renderer},
                    ("in_db", doc_details_text["in_db"][language]): {"cellRenderer": cell_renderer},
                },
                "multiple",
            )

            doc_grid = AgGrid(
                doc_details,
                gb.build(),
                columns_auto_size_mode="FIT_CONTENTS",
                theme="alpine",
                custom_css={
                    "#gridToolBar": {"display": "none"},
                },
                allow_unsafe_jscode=True,
                enable_enterprise_modules=False
            )

            selected_rows = doc_grid.get("selected_rows", [])

            cols = st.columns(4)
            file_name, file_path = file_exists(kb, selected_rows)
            if file_path:
                with open(file_path, "rb") as fp:
                    cols[0].download_button(
                        {
                            "简体中文": "下载选中文档",
                            "English": "Download Selected Files"
                        }[language],
                        fp,
                        file_name=file_name,
                        use_container_width=True, )
            else:
                cols[0].download_button(
                    {
                        "简体中文": "下载选中文档",
                        "English": "Download Selected Files"
                    }[language],
                    "",
                    disabled=True,
                    use_container_width=True, )

            st.write()
            # 将文件分词并加载到向量库中
            if cols[1].button(
                    {"简体中文":"重新添加至向量库", "English": "Re-add to Vector Store"}[language] 
                    if selected_rows and (
                            pd.DataFrame(selected_rows)["in_db"]).any() else {"简体中文":"添加至向量库",
                                                                              "English":"Add to Vector Store"}[language],
                    disabled=not file_exists(kb, selected_rows)[0],
                    use_container_width=True,
            ):
                file_names = [row["file_name"] for row in selected_rows]
                api.update_kb_docs(kb,
                                   file_names=file_names,
                                   chunk_size=chunk_size,
                                   chunk_overlap=chunk_overlap,
                                   zh_title_enhance=zh_title_enhance)
                st.rerun()

            # 将文件从向量库中删除，但不删除文件本身。
            if cols[2].button(
                    {"简体中文":"从向量库删除","English":"Delete from Vector Store"}[language],
                    disabled=not (selected_rows and selected_rows[0]["in_db"]),
                    use_container_width=True,
            ):
                file_names = [row["file_name"] for row in selected_rows]
                api.delete_kb_docs(kb, file_names=file_names)
                st.rerun()

            if cols[3].button(
                    {"简体中文":"从知识库中删除", "English":"Delete from Knowledge Base"}[language],
                    type="primary",
                    use_container_width=True,
            ):
                file_names = [row["file_name"] for row in selected_rows]
                api.delete_kb_docs(kb, file_names=file_names, delete_content=True)
                st.rerun()

        st.divider()

        cols = st.columns(3)

        if cols[0].button(
                {"简体中文":"依据源文件重建向量库",
                "English":"Recreate Vector Store based on Source Files"}[language],
                help={
                    "简体中文":"无需上传文件，通过其它方式将文档拷贝到对应知识库content目录下，点击本按钮即可重建知识库。",
                    "English":"No need to upload files. Please copy the documents to the corresponding knowledge base content directory by other means, and click this button to rebuild the knowledge base."
                }[language],
                use_container_width=True,
                type="primary",
        ):
            with st.spinner({
                "简体中文":"向量库重构中，请耐心等待，勿刷新或关闭页面。",
                "English":"Reconstructing Vector Store, please wait patiently, and do not refresh or close the page."
            }[language]):
                empty = st.empty()
                empty.progress(0.0, "")
                for d in api.recreate_vector_store(kb,
                                                   chunk_size=chunk_size,
                                                   chunk_overlap=chunk_overlap,
                                                   zh_title_enhance=zh_title_enhance):
                    if msg := check_error_msg(d):
                        st.toast(msg)
                    else:
                        empty.progress(d["finished"] / d["total"], d["msg"])
                st.rerun()

        if cols[2].button(
                {"简体中文":"删除知识库", "English":"Delete Knowledge Base"}[language],
                use_container_width=True,
        ):
            ret = api.delete_knowledge_base(kb)
            st.toast(ret.get("msg", " "))
            time.sleep(1)
            st.rerun()

        with st.sidebar:
            keyword = st.text_input({"简体中文":"查询关键字", "English":"Search Keyword"}[language])
            top_k = st.slider({"简体中文":"匹配条数", "English":"Match Entries"}[language], 1, 100, 3)

        st.write({"简体中文":"文件内文档列表。双击进行修改，在删除列填入 Y 可删除对应行。",
                "English":"Document list in the file. Double-click to modify, fill in Y in the delete column to delete the corresponding row."}[language])
        docs = []
        df = pd.DataFrame([], columns=["seq", "id", "content", "source"])
        if selected_rows:
            file_name = selected_rows[0]["file_name"]
            docs = api.search_kb_docs(knowledge_base_name=selected_kb, file_name=file_name)
            data = [
                {"seq": i + 1, "id": x["id"], "page_content": x["page_content"], "source": x["metadata"].get("source"),
                 "type": x["type"],
                 "metadata": json.dumps(x["metadata"], ensure_ascii=False),
                 "to_del": "",
                 } for i, x in enumerate(docs)]
            df = pd.DataFrame(data)

            gb = GridOptionsBuilder.from_dataframe(df)
            gb.configure_columns(["id", "source", "type", "metadata"], hide=True)
            gb.configure_column("seq", "No.", width=50)
            gb.configure_column("page_content", {"简体中文":"内容","English":"Content"}[language], editable=True, autoHeight=True, wrapText=True, flex=1,
                                cellEditor="agLargeTextCellEditor", cellEditorPopup=True)
            gb.configure_column("to_del", {"简体中文":"删除", "English":"Delete"}[language], editable=True, width=50, wrapHeaderText=True,
                                cellEditor="agCheckboxCellEditor", cellRender="agCheckboxCellRenderer")
            gb.configure_selection()
            edit_docs = AgGrid(df, gb.build())

            if st.button({"简体中文":"保存更改", "English":"Save Changes"}[language]):
                origin_docs = {
                    x["id"]: {"page_content": x["page_content"], "type": x["type"], "metadata": x["metadata"]} for x in
                    docs}
                changed_docs = []
                for index, row in edit_docs.data.iterrows():
                    origin_doc = origin_docs[row["id"]]
                    if row["page_content"] != origin_doc["page_content"]:
                        if row["to_del"] not in ["Y", "y", 1]:
                            changed_docs.append({
                                "page_content": row["page_content"],
                                "type": row["type"],
                                "metadata": json.loads(row["metadata"]),
                            })

                if changed_docs:
                    if api.update_kb_docs(knowledge_base_name=selected_kb,
                                          file_names=[file_name],
                                          docs={file_name: changed_docs}):
                        st.toast({
                            "简体中文":"更新文档成功",
                            "English":"Update Document Successfully"
                        }[language])
                    else:
                        st.toast({
                            "简体中文":"更新文档失败",
                            "English":"Failed to Update Document"
                        }[language])
