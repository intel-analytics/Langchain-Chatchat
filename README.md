***This application (Knowledge Base QA using RAG pipeline) is ported from [chatchat-space/Langchain-Chatchat](https://github.com/chatchat-space/Langchain-Chatchat) to run on Intel GPU (e.g., local PC with iGPU, discrete GPU such as Arc, Flex and Max) using [IPEX-LLM](https://github.com/intel-analytics/ipex-llm).***

# Langchain-Chatchat with IPEX-LLM Acceleration on Intel GPUs

See the demo of running `Langchain-Chatchat` (Knowledge Base QA using RAG pipeline) on Intel Core Ultra using `ipex-llm` below. If you have any issues or suggestions, please submit them to the [IPEX-LLM Project](https://github.com/intel-analytics/ipex-llm/issues).
>You can change the UI language in the left-side menu. We currently support **English** and **简体中文** (see video demos below). 

<br/>

<table width="100%">
  <tr>
    <td align="center" width="50%"><b>English</b></td>
    <td align="center" width="50%"><b>简体中文</b></td>
  </tr>
  <tr>
    <td>
      <video src="https://github.com/intel-analytics/Langchain-Chatchat/assets/1995599/92bc5697-f633-4b26-b47f-1914228c659a" alt="english-video">english</video>
    </td>
    <td>
      <video src="https://github.com/intel-analytics/Langchain-Chatchat/assets/1995599/709bdc4d-dff9-45fa-bd55-90879ff8a5a8" alt="chinese-video">chinese</video>
    </td>
  </tr>
</table>

<br/>

The following sections introduce how to install and run Langchain-chatchat on systems equipped with Intel GPUs, utilizing the GPU to run both LLMs and embedding models. 

## Table of Contents
1. [LangChain-Chatchat Architecture](#langchain-chatchat-architecture)
2. [Install and Run](#install-and-run)
3. [How to Use](#usage)
4. [Trouble Shooting & Tips](#trouble-shooting--tips)

## Langchain-Chatchat Architecture

See the Langchain-Chatchat architecture below ([source](https://github.com/chatchat-space/Langchain-Chatchat/blob/master/img/langchain%2Bchatglm.png)).

<img src="img/langchain%2Bchatglm.png" height="350px">
  
## Install and Run

 Follow the guide that corresponds to your specific system and GPU type from the links provided below:

- For systems with Intel Core Ultra integrated GPU: [Windows Guide](./INSTALL_win_mtl.md)
- For systems with Intel Arc A-Series GPU: [Windows Guide](./INSTALL_win_arc.md) | [Linux Guide](./INSTALL_linux_arc.md)
- For systems with Intel Data Center Max Series GPU: [Linux Guide](./INSTALL_linux_max.md)


## Usage

To start chatting with LLMs, simply type your messages in the textbox at the bottom of the UI. 

### How to use RAG

#### Step 1: Create Knowledge Base

- Select `Manage Knowledge Base` from the menu on the left, then choose `New Knowledge Base` from the dropdown menu on the right side.
  <p align="center"><img src="img/new-kb.png" alt="image1" width="70%" align="center"></p>
- Fill in the name of your new knowledge base (example: "test") and press the `Create` button. Adjust any other settings as needed. 
  <p align="center"><img src="img/create-kb.png" alt="image1" width="70%" align="center"></p>
- Upload knowledge files from your computer and allow some time for the upload to complete. Once finished, click on `Add files to Knowledge Base` button to build the vector store. Note: this process may take several minutes.
  <p align="center"><img src="img/build-kb.png" alt="image1" width="70%" align="center"></p>


#### Step 2: Chat with RAG

You can now click `Dialogue` on the left-side menu to return to the chat UI. Then in `Knowledge base settings` menu, choose the Knowledge Base you just created, e.g, "test". Now you can start chatting. 

<p align="center"><img src="img/rag-menu.png" alt="rag-menu" width="60%" align="center"></p>

<br/>

For more information about how to use Langchain-Chatchat, refer to Official Quickstart guide in [English](./README_en.md), [Chinese](./README_chs.md), or the [Wiki](https://github.com/chatchat-space/Langchain-Chatchat/wiki/).



### Trouble Shooting & Tips

#### 1. Version Compatibility

Ensure that you have installed `ipex-llm>=2.1.0b20240327`. To upgrade `ipex-llm`, use
```bash
pip install --pre --upgrade ipex-llm[xpu] -f https://developer.intel.com/ipex-whl-stable-xpu
```

#### 2. Prompt Templates

In the left-side menu, you have the option to choose a prompt template. There're several pre-defined templates - those ending with '_cn' are Chinese templates, and those ending with '_en' are English templates. You can also define your own prompt templates in `configs/prompt_config.py`. Remember to restart the service to enable these changes. 
