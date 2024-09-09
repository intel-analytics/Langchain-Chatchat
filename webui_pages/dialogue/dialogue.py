import streamlit as st
from webui_pages.utils import *
from streamlit_chatbox import *
from streamlit_modal import Modal
from datetime import datetime
import os
import re
import time
from configs import (TEMPERATURE, HISTORY_LEN, PROMPT_TEMPLATES, LLM_MODELS,
                     DEFAULT_KNOWLEDGE_BASE, DEFAULT_SEARCH_ENGINE, SUPPORT_AGENT_MODEL)
from server.knowledge_base.utils import LOADER_DICT
import uuid
from typing import List, Dict

chat_box = ChatBox(
    assistant_avatar=os.path.join(
        "img",
        "chatchat_icon_blue_square_v2.png"
    )
)

def get_messages_history(history_len: int, content_in_expander: bool = False) -> List[Dict]:
    '''
    返回消息历史。
    content_in_expander控制是否返回expander元素中的内容，一般导出的时候可以选上，传入LLM的history不需要
    '''

    def filter(msg):
        content = [x for x in msg["elements"] if x._output_method in ["markdown", "text"]]
        if not content_in_expander:
            content = [x for x in content if not x._in_expander]
        content = [x.content for x in content]

        return {
            "role": msg["role"],
            "content": "\n\n".join(content),
        }

    return chat_box.filter_history(history_len=history_len, filter=filter)


@st.cache_data
def upload_temp_docs(files, _api: ApiRequest) -> str:
    '''
    将文件上传到临时目录，用于文件对话
    返回临时向量库ID
    '''
    return _api.upload_temp_docs(files).get("data", {}).get("id")


def parse_command(text: str, modal: Modal) -> bool:
    '''
    检查用户是否输入了自定义命令，当前支持：
    /new {session_name}。如果未提供名称，默认为“会话X”
    /del {session_name}。如果未提供名称，在会话数量>1的情况下，删除当前会话。
    /clear {session_name}。如果未提供名称，默认清除当前会话
    /help。查看命令帮助
    返回值：输入的是命令返回True，否则返回False
    '''
    if 'language' not in st.session_state:
        st.session_state['language'] = "简体中文"
    language = st.session_state['language']
    
    if m := re.match(r"/([^\s]+)\s*(.*)", text):
        cmd, name = m.groups()
        name = name.strip()
        conv_names = chat_box.get_chat_names()
        if cmd == "help":
            modal.open()
        elif cmd == "new":
            if not name:
                i = 1
                while True:
                    if language=="简体中文":
                        name = f"会话{i}"
                    elif language=="English":
                        name = f"Session{i}"
                    if name not in conv_names:
                        break
                    i += 1
            if name in st.session_state["conversation_ids"]:
                st.error(f"该会话名称 “{name}” 已存在")
                time.sleep(1)
            else:
                st.session_state["conversation_ids"][name] = uuid.uuid4().hex
                st.session_state["cur_conv_name"] = name
        elif cmd == "del":
            name = name or st.session_state.get("cur_conv_name")
            if len(conv_names) == 1:
                st.error("这是最后一个会话，无法删除")
                time.sleep(1)
            elif not name or name not in st.session_state["conversation_ids"]:
                st.error(f"无效的会话名称：“{name}”")
                time.sleep(1)
            else:
                st.session_state["conversation_ids"].pop(name, None)
                chat_box.del_chat_name(name)
                st.session_state["cur_conv_name"] = ""
        elif cmd == "clear":
            chat_box.reset_history(name=name or None)
        return True
    return False


def dialogue_page(api: ApiRequest, is_lite: bool = False):
    if 'language' not in st.session_state:
        st.session_state['language'] = "简体中文"
    language = st.session_state['language']

    st.session_state.setdefault("conversation_ids", {})
    st.session_state["conversation_ids"].setdefault(chat_box.cur_chat_name, uuid.uuid4().hex)
    st.session_state.setdefault("file_chat_id", None)
    default_model = api.get_default_llm_model()[0]

    if not chat_box.chat_inited:
        if language == "简体中文":
            st.toast(
                f"欢迎使用 [`Langchain-Chatchat`](https://github.com/intel-analytics/Langchain-Chatchat/) ! \n\n"
                f"当前运行的模型`{default_model}`, 您可以开始提问了."
            )
        elif language == "English":
            st.toast(
                f"Welcome to [`Langchain-Chatchat`](https://github.com/intel-analytics/Langchain-Chatchat/) ! \n\n"
                f"The current model running is {default_model}. Now you can start asking questions"
            )
        chat_box.init_session()

    # 弹出自定义命令帮助信息
    modal = Modal("自定义命令", key="cmd_help", max_width="500")
    if modal.is_open():
        with modal.container():
            cmds = [x for x in parse_command.__doc__.split("\n") if x.strip().startswith("/")]
            st.write("\n\n".join(cmds))

    with st.sidebar:
        # 多会话
        conv_names = list(st.session_state["conversation_ids"].keys())
        index = 0
        if st.session_state.get("cur_conv_name") in conv_names:
            index = conv_names.index(st.session_state.get("cur_conv_name"))
        indicator = {"简体中文":"当前会话：", "English":"Current Session:"}
        conversation_name = st.selectbox(indicator[language], conv_names, index=index)
        chat_box.use_chat_name(conversation_name)
        conversation_id = st.session_state["conversation_ids"][conversation_name]

        def on_mode_change():
            mode = st.session_state.dialogue_mode
            text_dict = {"简体中文": f"已切换到 {mode} 模式。","English":f"Switched to {mode} mode"}
            text = text_dict[language]
            if language == "简体中文":
                if mode == "知识库问答":
                    cur_kb = st.session_state.get("selected_kb")
                    if cur_kb:
                        text = f"{text} 当前知识库： `{cur_kb}`。"
            elif language == "English":
                if mode == "Knowledge Base QA":
                    cur_kb = st.session_state.get("selected_kb")
                    if cur_kb:
                        text = f"{text} current knowledge base: `{cur_kb}`。"
            st.toast(text)

        if language == "简体中文":
            dialogue_modes = ["LLM 对话",
                            "知识库问答",
                            "文件对话",
                            "搜索引擎问答",
                            "自定义Agent问答",
                            ]
        elif language == "English":
            dialogue_modes = ["LLM Chat",
                            "Knowledge Base QA",
                            "File Chat",
                            "Search Engine QA",
                            "Custom Agent QA",
                            ]
        indicator = {"简体中文":"请选择对话模式：", "English":"Select conversation mode:"}
        dialogue_mode = st.selectbox(indicator[language],
                                     dialogue_modes,
                                     index=1,
                                     on_change=on_mode_change,
                                     key="dialogue_mode",
                                     )

        def on_llm_change():
            if llm_model:
                config = api.get_model_config(llm_model)
                if not config.get("online_api"):  # 只有本地model_worker可以切换模型
                    st.session_state["prev_llm_model"] = llm_model
                st.session_state["cur_llm_model"] = st.session_state.llm_model

        def llm_model_format_func(x):
            if x in running_models:
                return f"{x} (Running)"
            return x

        running_models = list(api.list_running_models())
        available_models = []
        config_models = api.list_config_models()
        if not is_lite:
            for k, v in config_models.get("local", {}).items():
                if (v.get("model_path_exists")
                        and k not in running_models):
                    available_models.append(k)
        for k, v in config_models.get("online", {}).items():
            if not v.get("provider") and k not in running_models and k in LLM_MODELS:
                available_models.append(k)
        llm_models = running_models + available_models
        cur_llm_model = st.session_state.get("cur_llm_model", default_model)
        if cur_llm_model in llm_models:
            index = llm_models.index(cur_llm_model)
        else:
            index = 0
        indicator = {"简体中文":"选择LLM模型：","English":"Choose LLM Model:"}
        llm_model = st.selectbox(indicator[language],
                                 llm_models,
                                 index,
                                 format_func=llm_model_format_func,
                                 on_change=on_llm_change,
                                 key="llm_model",
                                 )
        if (st.session_state.get("prev_llm_model") != llm_model
                and not is_lite
                and not llm_model in config_models.get("online", {})
                and not llm_model in config_models.get("langchain", {})
                and llm_model not in running_models):
            indicator = {
                "简体中文":f"正在加载模型： {llm_model}，请勿进行操作或刷新页面",
                "English":f"Loading model: {llm_model}. Do not perform any operations or refresh the page."
            }
            with st.spinner(indicator[language]):
                prev_model = st.session_state.get("prev_llm_model")
                r = api.change_llm_model(prev_model, llm_model, language)
                if msg := check_error_msg(r):
                    st.error(msg)
                elif msg := check_success_msg(r):
                    st.success(msg)
                    st.session_state["prev_llm_model"] = llm_model
        if language == "简体中文":
            index_prompt = {
                "LLM 对话": "llm_chat",
                "自定义Agent问答": "agent_chat",
                "搜索引擎问答": "search_engine_chat",
                "知识库问答": "knowledge_base_chat",
                "文件对话": "knowledge_base_chat",
            }
        elif language == "English":
            index_prompt = {
                "LLM Chat": "llm_chat",
                "Custom Agent QA": "agent_chat",
                "Search Engine QA": "search_engine_chat",
                "Knowledge Base QA": "knowledge_base_chat",
                "File Chat": "knowledge_base_chat",
            }
        prompt_templates_kb_list = list(PROMPT_TEMPLATES[index_prompt[dialogue_mode]].keys())
        prompt_template_name = prompt_templates_kb_list[0]
        if "prompt_template_select" not in st.session_state:
            st.session_state.prompt_template_select = prompt_templates_kb_list[0]

        def prompt_change():
            indicator = {
                "简体中文":f"已切换为 {st.session_state.prompt_template_select} 模板。",
                "English":f"Switched to {st.session_state.prompt_template_select} template. "
            }
            text = indicator[language]
            st.toast(text)

        indicator = {
            "简体中文":"请选择Prompt模板：",
            "English":"Please choose prompt template:"
        }
        prompt_template_select = st.selectbox(
            indicator[language],
            prompt_templates_kb_list,
            index=0,
            on_change=prompt_change,
            key="prompt_template_select",
        )
        prompt_template_name = st.session_state.prompt_template_select
        indicator = {
            "简体中文":"历史对话轮数：",
            "English":"Dialogue Rounds: "
        }
        temperature = st.slider("Temperature：", 0.0, 2.0, TEMPERATURE, 0.05)
        history_len = st.number_input(indicator[language], 0, 20, HISTORY_LEN)

        def on_kb_change():
            indicator = {
                "简体中文":f"已加载知识库： {st.session_state.selected_kb}",
                "English":f"Loaded knowledge base: {st.session_state.selected_kb}"
            }
            st.toast(indicator[language])

        indicators = [{
            "简体中文":"知识库问答",
            "English":"Knowledge Base QA"
        },
        {
            "简体中文":"文件对话",
            "English":"File Chat"
        },
        {
            "简体中文":"搜索引擎问答",
            "English":"Search Engine QA"
        },
        ]
        if dialogue_mode == indicators[0][language]:
            indicator = {
                "简体中文":"知识库配置",
                "English":"Knowledge base settings"
            }
            with st.expander(indicator[language], True):
                kb_list = api.list_knowledge_bases()
                index = 0
                if DEFAULT_KNOWLEDGE_BASE in kb_list:
                    index = kb_list.index(DEFAULT_KNOWLEDGE_BASE)
                indicator = {
                    "简体中文":"请选择知识库：",
                    "English":"Choose knowledge base:"
                }
                selected_kb = st.selectbox(
                    indicator[language],
                    kb_list,
                    index=index,
                    on_change=on_kb_change,
                    key="selected_kb",
                )
                indicator = {
                    "简体中文":"匹配知识条数：",
                    "English":"Matched entries:"
                }
                kb_top_k = st.number_input(indicator[language], 1, 20, VECTOR_SEARCH_TOP_K)

                ## Bge 模型会超过1
                indicator = {
                    "简体中文":"知识匹配分数阈值：",
                    "English":"Knowledge matching score threshold"
                }
                score_threshold = st.slider(indicator[language], 0.0, 2.0, float(SCORE_THRESHOLD), 0.01)
        elif dialogue_mode == indicators[1][language]:
            indicator = {
                "简体中文":"文件对话配置",
                "English":"File Chat Settings"
            }
            with st.expander(indicator[language], True):
                indicator = {
                    "简体中文":"上传知识文件：",
                    "English":"Upload knowledge file"
                }
                files = st.file_uploader(indicator[language],
                                         [i for ls in LOADER_DICT.values() for i in ls],
                                         accept_multiple_files=True,
                                         )
                indicator = {
                    "简体中文":"匹配知识条数：",
                    "English":"Matched entries:"
                }
                kb_top_k = st.number_input(indicator[language], 1, 20, VECTOR_SEARCH_TOP_K)

                ## Bge 模型会超过1
                indicator = {
                    "简体中文":"知识匹配分数阈值：",
                    "English":"Knowledge matching score threshold"
                }
                score_threshold = st.slider(indicator[language], 0.0, 2.0, float(SCORE_THRESHOLD), 0.01)
                indicator = {
                    "简体中文":"开始上传",
                    "English":"Start upload"
                }
                if st.button(indicator[language], disabled=len(files) == 0):
                    st.session_state["file_chat_id"] = upload_temp_docs(files, api)
        elif dialogue_mode == indicators[2][language]:
            search_engine_list = api.list_search_engines()
            if DEFAULT_SEARCH_ENGINE in search_engine_list:
                index = search_engine_list.index(DEFAULT_SEARCH_ENGINE)
            else:
                index = search_engine_list.index("duckduckgo") if "duckduckgo" in search_engine_list else 0
            indicator = {
                "简体中文":"搜索引擎配置",
                "English":"Search Engine Settings"
            }
            with st.expander(indicator[language], True):
                indicator = {
                    "简体中文":"请选择搜索引擎",
                    "English":"Choose Search Engine",
                }
                search_engine = st.selectbox(
                    label=indicator[language],
                    options=search_engine_list,
                    index=index,
                )
                indicator = {
                    "简体中文":"匹配搜索结果条数：",
                    "English":"Matched entries:"
                }
                se_top_k = st.number_input(indicator[language], 1, 20, SEARCH_ENGINE_TOP_K)

    # Display chat messages from history on app rerun
    chat_box.output_messages()
    indicator = {
        "简体中文":"请输入对话内容，换行请使用Shift+Enter。输入/help查看自定义命令 ",
        "English":"Type your message here. Use Shift+Enter for new lines. Type /help for custom commands."
    }
    chat_input_placeholder = indicator[language]

    def on_feedback(
            feedback,
            message_id: str = "",
            history_index: int = -1,
    ):
        reason = feedback["text"]
        score_int = chat_box.set_feedback(feedback=feedback, history_index=history_index)
        api.chat_feedback(message_id=message_id,
                          score=score_int,
                          reason=reason)
        st.session_state["need_rerun"] = True

    
    feedback_kwargs = {
        "feedback_type": "thumbs",
        "optional_text_label": "欢迎反馈您打分的理由" if language=="简体中文" else "Additional feedback on your ratings? Please share.",
    }

    if prompt := st.chat_input(chat_input_placeholder, key="prompt"):
        if parse_command(text=prompt, modal=modal):  # 用户输入自定义命令
            st.rerun()
        else:
            history = get_messages_history(history_len)
            chat_box.user_say(prompt)
            indicators = [{
                    '简体中文':"LLM 对话",
                    "English":"LLM Chat"
                },
                {
                    '简体中文':"自定义Agent问答",
                    "English":"Custom Agent QA",
                },
                {
                    "简体中文":"知识库问答",
                    "English":"Knowledge Base QA"
                },
                {
                    "简体中文":"文件对话",
                    "English":"File Chat"
                },
                {
                    "简体中文":"搜索引擎问答",
                    "English":"Search Engine QA"
                },
                ]
            if dialogue_mode == indicators[0][language]:
                indicator = {
                    '简体中文':"正在思考...",
                    "English":"Thinking..."
                }
                chat_box.ai_say(indicator[language])
                text = ""
                message_id = ""
                r = api.chat_chat(prompt,
                                  history=history,
                                  conversation_id=conversation_id,
                                  model=llm_model,
                                  prompt_name=prompt_template_name,
                                  temperature=temperature)
                for t in r:
                    if error_msg := check_error_msg(t):  # check whether error occured
                        st.error(error_msg)
                        break
                    text += t.get("text", "")
                    chat_box.update_msg(text)
                    message_id = t.get("message_id", "")

                metadata = {
                    "message_id": message_id,
                }
                chat_box.update_msg(text, streaming=False, metadata=metadata)  # 更新最终的字符串，去除光标
                chat_box.show_feedback(**feedback_kwargs,
                                       key=message_id,
                                       on_submit=on_feedback,
                                       kwargs={"message_id": message_id, "history_index": len(chat_box.history) - 1})

            elif dialogue_mode == indicators[1][language]:
                if not any(agent in llm_model for agent in SUPPORT_AGENT_MODEL):
                    indicator = {
                    '简体中文':f"正在思考... \n\n <span style='color:red'>该模型并没有进行Agent对齐，请更换支持Agent的模型获得更好的体验！</span>\n\n\n",
                    "English":"Thinking... \n\n <span style='color:red'> This model does not align with the Agent. Please switch to a model that supports Agent alignment for a better experience!</span>\n\n\n"
                    }
                    title_indicator = {
                        "简体中文":"思考过程",
                        "English":"Thinking process"
                    }
                    chat_box.ai_say([
                        indicator[language],
                        Markdown("...", in_expander=True, title=title_indicator[language], state="complete"),

                    ])
                else:
                    indicator = {
                    '简体中文':"正在思考...",
                    "English":"Thinking..."
                    }
                    title_indicator = {
                        "简体中文":"思考过程",
                        "English":"Thinking process"
                    }
                    chat_box.ai_say([
                        indicator[language],
                        Markdown("...", in_expander=True, title=title_indicator[language], state="complete"),

                    ])
                text = ""
                ans = ""
                for d in api.agent_chat(prompt,
                                        history=history,
                                        model=llm_model,
                                        prompt_name=prompt_template_name,
                                        temperature=temperature,
                                        ):
                    try:
                        d = json.loads(d)
                    except:
                        pass
                    if error_msg := check_error_msg(d):  # check whether error occured
                        st.error(error_msg)
                    if chunk := d.get("answer"):
                        text += chunk
                        chat_box.update_msg(text, element_index=1)
                    if chunk := d.get("final_answer"):
                        ans += chunk
                        chat_box.update_msg(ans, element_index=0)
                    if chunk := d.get("tools"):
                        text += "\n\n".join(d.get("tools", []))
                        chat_box.update_msg(text, element_index=1)
                chat_box.update_msg(ans, element_index=0, streaming=False)
                chat_box.update_msg(text, element_index=1, streaming=False)
            elif dialogue_mode == indicators[2][language]:
                indicator = {
                    "简体中文":f"正在查询知识库 `{selected_kb}` ...",
                    "English":f"Looking into  `{selected_kb}` ..."
                }
                title_indicator = {
                    "简体中文":"知识库匹配结果",
                    "English":"Knowledge base match result"
                }
                chat_box.ai_say([
                    indicator[language],
                    Markdown("...", in_expander=True, title=title_indicator[language], state="complete"),
                ])
                text = ""
                for d in api.knowledge_base_chat(prompt,
                                                 knowledge_base_name=selected_kb,
                                                 top_k=kb_top_k,
                                                 score_threshold=score_threshold,
                                                 history=history,
                                                 model=llm_model,
                                                 prompt_name=prompt_template_name,
                                                 temperature=temperature,
                                                 language=language):
                    if error_msg := check_error_msg(d):  # check whether error occured
                        st.error(error_msg)
                    elif chunk := d.get("answer"):
                        text += chunk
                        chat_box.update_msg(text, element_index=0)
                chat_box.update_msg(text, element_index=0, streaming=False)
                chat_box.update_msg("\n\n".join(d.get("docs", [])), element_index=1, streaming=False)
            elif dialogue_mode == indicators[3][language]:
                if st.session_state["file_chat_id"] is None:
                    st.error("请先上传文件再进行对话")
                    st.stop()
                indicator = {
                    '简体中文':f"正在查询文件 `{st.session_state['file_chat_id']}` ...",
                    'English':f"Searching `{st.session_state['file_chat_id']}` ",
                }
                title_indicator = {
                    '简体中文':"文件匹配结果",
                    "English":"Matched results"
                }
                chat_box.ai_say([
                    indicator[language],
                    Markdown("...", in_expander=True, title=title_indicator[language], state="complete"),
                ])
                text = ""
                for d in api.file_chat(prompt,
                                       knowledge_id=st.session_state["file_chat_id"],
                                       top_k=kb_top_k,
                                       score_threshold=score_threshold,
                                       history=history,
                                       model=llm_model,
                                       prompt_name=prompt_template_name,
                                       temperature=temperature,
                                       language=language):
                    if error_msg := check_error_msg(d):  # check whether error occured
                        st.error(error_msg)
                    elif chunk := d.get("answer"):
                        text += chunk
                        chat_box.update_msg(text, element_index=0)
                chat_box.update_msg(text, element_index=0, streaming=False)
                chat_box.update_msg("\n\n".join(d.get("docs", [])), element_index=1, streaming=False)
            elif dialogue_mode == indicators[4][language]:
                title_indicator = {
                    '简体中文':"网络搜索结果",
                    "English":"Searched result"
                }
                chat_box.ai_say([
                    f"正在执行 `{search_engine}` 搜索..." if language=='简体中文' else f"Running `{search_engine}` search ..." ,
                    Markdown("...", in_expander=True, title=title_indicator[language], state="complete"),
                ])
                text = ""
                for d in api.search_engine_chat(prompt,
                                                search_engine_name=search_engine,
                                                top_k=se_top_k,
                                                history=history,
                                                model=llm_model,
                                                prompt_name=prompt_template_name,
                                                temperature=temperature,
                                                split_result=se_top_k > 1):
                    if error_msg := check_error_msg(d):  # check whether error occured
                        st.error(error_msg)
                    elif chunk := d.get("answer"):
                        text += chunk
                        chat_box.update_msg(text, element_index=0)
                chat_box.update_msg(text, element_index=0, streaming=False)
                chat_box.update_msg("\n\n".join(d.get("docs", [])), element_index=1, streaming=False)

    if st.session_state.get("need_rerun"):
        st.session_state["need_rerun"] = False
        st.rerun()

    now = datetime.now()
    with st.sidebar:

        cols = st.columns(2)
        export_btn = cols[0]
        if cols[1].button(
                "清空对话" if language == "简体中文" else "Clear Chat",
                use_container_width=True,
        ):
            chat_box.reset_history()
            st.rerun()

    export_btn.download_button(
        "导出记录" if language == "简体中文" else "Export Chat",
        "".join(chat_box.export2md()),
        file_name=f"{now:%Y-%m-%d %H.%M}_对话记录.md" if language == "简体中文" else f"{now:%Y-%m-%d %H.%M}_record.md" ,
        mime="text/markdown",
        use_container_width=True,
    )
