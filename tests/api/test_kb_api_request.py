import requests
import json
import sys
from pathlib import Path

root_path = Path(__file__).parent.parent.parent
sys.path.append(str(root_path))
from server.utils import api_address
from configs import VECTOR_SEARCH_TOP_K
from server.knowledge_base.utils import get_kb_path, get_file_path
from webui_pages.utils import ApiRequest

from pprint import pprint


api_base_url = api_address()
api: ApiRequest = ApiRequest(api_base_url)


kb = "kb_for_api_test"
test_files = {
    "FAQ.MD": str(root_path / "docs" / "FAQ.MD"),
    "README.MD": str(root_path / "README.MD"),
    "test.txt": get_file_path("samples", "test.txt"),
}

print("\n\nInvoke ApiRquest\n")


def test_delete_kb_before():
    if not Path(get_kb_path(kb)).exists():
        return

    data = api.delete_knowledge_base(kb)
    pprint(data)
    assert data["code"] == 200
    assert isinstance(data["data"], list) and len(data["data"]) > 0
    assert kb not in data["data"]


def test_create_kb():
    print(f"\nAttempting to create a knowledge base with an empty name: ")
    data = api.create_knowledge_base(" ")
    pprint(data)
    assert data["code"] == 404
    assert data["msg"] == "知识库名称不能为空，请重新填写知识库名称"

    print(f"\nCreating a new knowledge base: {kb}")
    data = api.create_knowledge_base(kb)
    pprint(data)
    assert data["code"] == 200
    assert data["msg"] == f"已新增知识库 {kb}"

    print(f"\nAttempting to create a knowledge base with the same name: {kb}")
    data = api.create_knowledge_base(kb)
    pprint(data)
    assert data["code"] == 404
    assert data["msg"] == f"已存在同名知识库 {kb}"


def test_list_kbs():
    data = api.list_knowledge_bases()
    pprint(data)
    assert isinstance(data, list) and len(data) > 0
    assert kb in data


def test_upload_docs():
    files = list(test_files.values())

    print(f"\nUploading knowledge file")
    data = {"knowledge_base_name": kb, "override": True}
    data = api.upload_kb_docs(files, **data)
    pprint(data)
    assert data["code"] == 200
    assert len(data["data"]["failed_files"]) == 0

    print(f"\nAttempting to re-upload knowledge file without overwriting")
    data = {"knowledge_base_name": kb, "override": False}
    data = api.upload_kb_docs(files, **data)
    pprint(data)
    assert data["code"] == 200
    assert len(data["data"]["failed_files"]) == len(test_files)

    print(f"\nAttempting to re-upload knowledge file with overwriting and customize docs")
    docs = {"FAQ.MD": [{"page_content": "custom docs", "metadata": {}}]}
    data = {"knowledge_base_name": kb, "override": True, "docs": docs}
    data = api.upload_kb_docs(files, **data)
    pprint(data)
    assert data["code"] == 200
    assert len(data["data"]["failed_files"]) == 0


def test_list_files():
    print("\nFetching the list of files in the knowledge base: ")
    data = api.list_kb_docs(knowledge_base_name=kb)
    pprint(data)
    assert isinstance(data, list)
    for name in test_files:
        assert name in data


def test_search_docs():
    query = "介绍一下langchain-chatchat项目"
    print("\nRetrieving from the knowledge base: ")
    print(query)
    data = api.search_kb_docs(query, kb)
    pprint(data)
    assert isinstance(data, list) and len(data) == VECTOR_SEARCH_TOP_K


def test_update_docs():
    print(f"\nUpdating knowledge file")
    data = api.update_kb_docs(knowledge_base_name=kb, file_names=list(test_files))
    pprint(data)
    assert data["code"] == 200
    assert len(data["data"]["failed_files"]) == 0


def test_delete_docs():
    print(f"\nDeleting knowledge file")
    data = api.delete_kb_docs(knowledge_base_name=kb, file_names=list(test_files))
    pprint(data)
    assert data["code"] == 200
    assert len(data["data"]["failed_files"]) == 0

    query = "介绍一下langchain-chatchat项目"
    print("\nAttempting to retrieve from the knowledge base after deletion: ")
    print(query)
    data = api.search_kb_docs(query, kb)
    pprint(data)
    assert isinstance(data, list) and len(data) == 0


def test_recreate_vs():
    print("\nRebuilding the knowledge base: ")
    r = api.recreate_vector_store(kb)
    for data in r:
        assert isinstance(data, dict)
        assert data["code"] == 200
        print(data["msg"])

    query = "本项目支持哪些文件格式?"
    print("\nAttempting to retrieve from the rebuilt knowledge base: ")
    print(query)
    data = api.search_kb_docs(query, kb)
    pprint(data)
    assert isinstance(data, list) and len(data) == VECTOR_SEARCH_TOP_K


def test_delete_kb_after():
    print("\nDeleting knowledge base")
    data = api.delete_knowledge_base(kb)
    pprint(data)

    # check kb not exists anymore
    print("\nFetching the list of knowledge bases: ")
    data = api.list_knowledge_bases()
    pprint(data)
    assert isinstance(data, list) and len(data) > 0
    assert kb not in data
