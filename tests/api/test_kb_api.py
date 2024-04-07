import requests
import json
import sys
from pathlib import Path

root_path = Path(__file__).parent.parent.parent
sys.path.append(str(root_path))
from server.utils import api_address
from configs import VECTOR_SEARCH_TOP_K
from server.knowledge_base.utils import get_kb_path, get_file_path

from pprint import pprint


api_base_url = api_address()


kb = "kb_for_api_test"
test_files = {
    "wiki/Home.MD": get_file_path("samples", "wiki/Home.md"),
    "wiki/开发环境部署.MD": get_file_path("samples", "wiki/开发环境部署.md"),
    "test_files/test.txt": get_file_path("samples", "test_files/test.txt"),
}

print("\n\nDirect URL access\n")


def test_delete_kb_before(api="/knowledge_base/delete_knowledge_base"):
    if not Path(get_kb_path(kb)).exists():
        return

    url = api_base_url + api
    print("\nTesting knowledge base existence, requires deletion")
    r = requests.post(url, json=kb)
    data = r.json()
    pprint(data)

    # check kb not exists anymore
    url = api_base_url + "/knowledge_base/list_knowledge_bases"
    print("\nFetching the list of knowledge bases: ")
    r = requests.get(url)
    data = r.json()
    pprint(data)
    assert data["code"] == 200
    assert isinstance(data["data"], list) and len(data["data"]) > 0
    assert kb not in data["data"]


def test_create_kb(api="/knowledge_base/create_knowledge_base"):
    url = api_base_url + api

    print(f"\nAttempting to create a knowledge base with an empty name: ")
    r = requests.post(url, json={"knowledge_base_name": " "})
    data = r.json()
    pprint(data)
    assert data["code"] == 404
    assert data["msg"] == "知识库名称不能为空，请重新填写知识库名称"

    print(f"\nCreating a new knowledge base: {kb}")
    r = requests.post(url, json={"knowledge_base_name": kb})
    data = r.json()
    pprint(data)
    assert data["code"] == 200
    assert data["msg"] == f"已新增知识库 {kb}"

    print(f"\nAttempting to create a knowledge base with the same name: {kb}")
    r = requests.post(url, json={"knowledge_base_name": kb})
    data = r.json()
    pprint(data)
    assert data["code"] == 404
    assert data["msg"] == f"已存在同名知识库 {kb}"


def test_list_kbs(api="/knowledge_base/list_knowledge_bases"):
    url = api_base_url + api
    print("\nFetching the list of knowledge bases: ")
    r = requests.get(url)
    data = r.json()
    pprint(data)
    assert data["code"] == 200
    assert isinstance(data["data"], list) and len(data["data"]) > 0
    assert kb in data["data"]


def test_upload_docs(api="/knowledge_base/upload_docs"):
    url = api_base_url + api
    files = [("files", (name, open(path, "rb"))) for name, path in test_files.items()]

    print(f"\nUploading knowledge file")
    data = {"knowledge_base_name": kb, "override": True}
    r = requests.post(url, data=data, files=files)
    data = r.json()
    pprint(data)
    assert data["code"] == 200
    assert len(data["data"]["failed_files"]) == 0

    print(f"\nAttempting to re-upload knowledge file without overwriting")
    data = {"knowledge_base_name": kb, "override": False}
    files = [("files", (name, open(path, "rb"))) for name, path in test_files.items()]
    r = requests.post(url, data=data, files=files)
    data = r.json()
    pprint(data)
    assert data["code"] == 200
    assert len(data["data"]["failed_files"]) == len(test_files)

    print(f"\nAttempting to re-upload knowledge file with overwriting and customize docs")
    docs = {"FAQ.MD": [{"page_content": "custom docs", "metadata": {}}]}
    data = {"knowledge_base_name": kb, "override": True, "docs": json.dumps(docs)}
    files = [("files", (name, open(path, "rb"))) for name, path in test_files.items()]
    r = requests.post(url, data=data, files=files)
    data = r.json()
    pprint(data)
    assert data["code"] == 200
    assert len(data["data"]["failed_files"]) == 0


def test_list_files(api="/knowledge_base/list_files"):
    url = api_base_url + api
    print("\nFetching the list of files in the knowledge base: ")
    r = requests.get(url, params={"knowledge_base_name": kb})
    data = r.json()
    pprint(data)
    assert data["code"] == 200
    assert isinstance(data["data"], list)
    for name in test_files:
        assert name in data["data"]


def test_search_docs(api="/knowledge_base/search_docs"):
    url = api_base_url + api
    query = "介绍一下langchain-chatchat项目"
    print("\nRetrieving from the knowledge base: ")
    print(query)
    r = requests.post(url, json={"knowledge_base_name": kb, "query": query})
    data = r.json()
    pprint(data)
    assert isinstance(data, list) and len(data) == VECTOR_SEARCH_TOP_K


def test_update_info(api="/knowledge_base/update_info"):
    url = api_base_url + api
    print("\nUpdating knowledge base description")
    r = requests.post(url, json={"knowledge_base_name": "samples", "kb_info": "你好"})
    data = r.json()
    pprint(data)
    assert data["code"] == 200

def test_update_docs(api="/knowledge_base/update_docs"):
    url = api_base_url + api

    print(f"\nUpdating knowledge file")
    r = requests.post(url, json={"knowledge_base_name": kb, "file_names": list(test_files)})
    data = r.json()
    pprint(data)
    assert data["code"] == 200
    assert len(data["data"]["failed_files"]) == 0


def test_delete_docs(api="/knowledge_base/delete_docs"):
    url = api_base_url + api

    print(f"\nDeleting knowledge file")
    r = requests.post(url, json={"knowledge_base_name": kb, "file_names": list(test_files)})
    data = r.json()
    pprint(data)
    assert data["code"] == 200
    assert len(data["data"]["failed_files"]) == 0

    url = api_base_url + "/knowledge_base/search_docs"
    query = "介绍一下langchain-chatchat项目"
    print("\nAttempting to retrieve from the knowledge base after deletion: ")
    print(query)
    r = requests.post(url, json={"knowledge_base_name": kb, "query": query})
    data = r.json()
    pprint(data)
    assert isinstance(data, list) and len(data) == 0


def test_recreate_vs(api="/knowledge_base/recreate_vector_store"):
    url = api_base_url + api
    print("\nRebuilding the knowledge base: ")
    r = requests.post(url, json={"knowledge_base_name": kb}, stream=True)
    for chunk in r.iter_content(None):
        data = json.loads(chunk[6:])
        assert isinstance(data, dict)
        assert data["code"] == 200
        print(data["msg"])

    url = api_base_url + "/knowledge_base/search_docs"
    query = "本项目支持哪些文件格式?"
    print("\nAttempting to retrieve from the rebuilt knowledge base: ")
    print(query)
    r = requests.post(url, json={"knowledge_base_name": kb, "query": query})
    data = r.json()
    pprint(data)
    assert isinstance(data, list) and len(data) == VECTOR_SEARCH_TOP_K


def test_delete_kb_after(api="/knowledge_base/delete_knowledge_base"):
    url = api_base_url + api
    print("\nDeleting knowledge base")
    r = requests.post(url, json=kb)
    data = r.json()
    pprint(data)

    # check kb not exists anymore
    url = api_base_url + "/knowledge_base/list_knowledge_bases"
    print("\nFetching the list of knowledge bases: ")
    r = requests.get(url)
    data = r.json()
    pprint(data)
    assert data["code"] == 200
    assert isinstance(data["data"], list) and len(data["data"]) > 0
    assert kb not in data["data"]
