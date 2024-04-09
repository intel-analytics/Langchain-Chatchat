# Setup Guide for Windows with Intel Core Ultra integrated GPU (MTL)

1. [Installation](#installation)
2. [One-time Warmup](#one-time-warm-up)
3. [Start the Service](#start-the-service)

## Installation

### Download Langchain-Chatchat

Download the Langchain-Chatchat with IPEX-LLM integrations from [this link](https://github.com/intel-analytics/Langchain-Chatchat/archive/refs/heads/ipex-llm.zip). Unzip the content into a directory, e.g.,`C:\Users\arda\Downloads\Langchain-Chatchat-ipex-llm`. 

### Install Prerequisites

Visit the [Install IPEX-LLM on Windows with Intel GPU Guide](https://ipex-llm.readthedocs.io/en/latest/doc/LLM/Quickstart/install_windows_gpu.html), and follow [**Install Prerequisites**](https://ipex-llm.readthedocs.io/en/latest/doc/LLM/Quickstart/install_windows_gpu.html#install-prerequisites) to install [Visual Studio](https://ipex-llm.readthedocs.io/en/latest/doc/LLM/Quickstart/install_windows_gpu.html#install-visual-studio-2022), [GPU driver](https://ipex-llm.readthedocs.io/en/latest/doc/LLM/Quickstart/install_windows_gpu.html#install-gpu-driver), and [Conda](https://ipex-llm.readthedocs.io/en/latest/doc/LLM/Quickstart/install_windows_gpu.html#install-miniconda).  

### Install Python Dependencies

#### 1. Create a Conda Environment
Open **Anaconda Prompt (miniconda3)**, and run the following commands to create a new python environment:
```cmd
conda create -n ipex-llm-langchain-chatchat python=3.11 libuv 
conda activate ipex-llm-langchain-chatchat
```

#### 2. Install Intel oneAPI Base Toolkit 2024.0
```cmd
pip install dpcpp-cpp-rt==2024.0.2 mkl-dpcpp==2024.0.0 onednn==2024.0.0
```

#### 3.  Install `ipex-llm` 
```cmd
pip install --pre --upgrade ipex-llm[xpu] -f https://developer.intel.com/ipex-whl-stable-xpu
pip install --pre --upgrade torchaudio==2.1.0a0  -f https://developer.intel.com/ipex-whl-stable-xpu
```

#### 4. Install Langchain-Chatchat Dependencies 
Switch to the root directory of Langchain-Chatchat you've downloaded (refer to the [download section](#download-langchain-chatchat)), and install the dependencies with the commands below. **Note: In the example commands we assume the root directory is `C:\Users\arda\Downloads\Langchain-Chatchat-ipex-llm`. Remember to change it to your own path**.
```cmd
cd C:\Users\arda\Downloads\Langchain-Chatchat-ipex-llm
pip install -r requirements_ipex_llm.txt 
pip install -r requirements_api_ipex_llm.txt
pip install -r requirements_webui.txt
```

### Configuration
-  In root directory of Langchain-Chatchat, run the following command to create a config:
    ```cmd
    python copy_config_example.py
    ```
- Edit the file `configs\model_config.py`, change `MODEL_ROOT_PATH` to the absolute path of the parent directory where all the downloaded models (LLMs, embedding models, ranking models, etc.) are stored.

### Download Models
Download the models and place them in the directory `MODEL_ROOT_PATH` (refer to details in [Configuration](#configuration) section). 

Currently, we support only the LLM/embedding models specified in the table below. You can download these models using the link provided in the table. **Note: Ensure the model folder name matches the last segment of the model ID following "/", for example, for `THUDM/chatglm3-6b`, the model folder name should be `chatglm3-6b`.**


| Model |Category| download link | 
|:--|:--|:--|
|`THUDM/chatglm3-6b`|Chinese LLM| [HF](https://huggingface.co/THUDM/chatglm3-6b) or [ModelScope](https://www.modelscope.cn/models/ZhipuAI/chatglm3-6b/summary) |
|`meta-llama/Llama-2-7b-chat-hf`|English LLM| [HF](https://huggingface.co/meta-llama/Llama-2-7b-chat-hf) | 
|`BAAI/bge-large-zh-v1.5`|Chinese Embedding| [HF](https://huggingface.co/BAAI/bge-large-zh-v1.5) |
|`BAAI/bge-large-en-v1.5`| English Embedding|[HF](https://huggingface.co/BAAI/bge-large-en-v1.5) |

## One-time Warm-up
When you run this applcation on Intel GPU for the first time, it is highly recommended to do a one-time warmup (for GPU kernels compilation). 

In **Anaconda Prompt (miniconda3)**, under the root directory of Langchain-Chatchat, with conda environment activated, run the following commands:

```cmd
conda activate ipex-llm-langchain-chatchat

set SYCL_CACHE_PERSISTENT=1
set BIGDL_LLM_XMX_DISABLED=1

python warmup.py
```

> [!NOTE]
> The warmup may take several minutes. You just have to run it one-time on after installation. 

## Start the Service
Open **Anaconda Prompt (miniconda3)** and run the following commands:
```cmd
conda activate ipex-llm-langchain-chatchat

set SYCL_CACHE_PERSISTENT=1
set BIGDL_LLM_XMX_DISABLED=1

set BIGDL_IMPORT_IPEX=0
set no_proxy=localhost,127.0.0.1

python startup.py -a
```

You can find the Web UI's URL printted on the terminal logs, e.g. http://localhost:8501/.

Open a browser and navigate to the URL to use the Web UI. 