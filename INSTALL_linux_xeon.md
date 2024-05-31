# Setup Guide for Linux with Xeon-Series CPU

1. [Installation](#installation)
2. [Start the Service](#start-the-service)

## Installation

### Download Langchain-Chatchat

Download the Langchain-Chatchat with IPEX-LLM integrations from [this link](https://github.com/intel-analytics/Langchain-Chatchat/archive/refs/heads/ipex-llm.zip). Unzip the content into a directory, e.g. `/home/arda/Langchain-Chatchat-ipex-llm`. 

### Install Prerequisites

We recommend to use Conda to manage the running environment. For how to install Conda on your Linux distributions, please visit [here](https://conda-forge.org/download/).

### Install Python Dependencies

#### 1. Create a Conda Environment
Run the following commands to create a new python environment:
```bash
conda create -n ipex-llm-langchain-chatchat python=3.11
conda activate ipex-llm-langchain-chatchat
```

#### 2.  Install `ipex-llm` 
```bash
pip install --pre --upgrade ipex-llm[all]
pip3 install torch==2.1.2 torchvision==0.16.2 torchaudio==2.1.2
```

#### 3. Install Langchain-Chatchat Dependencies 
Switch to the root directory of Langchain-Chatchat you've downloaded (refer to the [download section](#download-langchain-chatchat)), and install the dependencies with the commands below. **Note: In the example commands we assume the root directory is `/home/arda/Langchain-Chatchat-ipex-llm`. Remember to change it to your own path**.
```bash
cd /home/arda/Langchain-Chatchat-ipex-llm
pip install -r requirements_ipex_llm.txt 
pip install -r requirements_api_ipex_llm.txt
pip install -r requirements_webui.txt
# Due to an known issue on CPU, run with Llama-2 model
# will require to install transformers==4.34.0 to generate the correct result.
pip install transformers==4.34.0
```

### Configuration
-  In root directory of Langchain-Chatchat, run the following command to create a config:
    ```bash
    python copy_config_example.py
    ```
- Edit the file `configs/model_config.py`, change `MODEL_ROOT_PATH` to the absolute path of the parent directory where all the downloaded models (LLMs, embedding models, ranking models, etc.) are stored.
- Edit the file `configs/model_config.py`, change `EMBEDDING_DEVICE` and `LLM_DEVICE` to `cpu`.

### Download Models
Download the models and place them in the directory `MODEL_ROOT_PATH` (refer to details in [Configuration](#configuration) section). 

Currently, we support only the LLM/embedding models specified in the table below. You can download these models using the link provided in the table. **Note: Ensure the model folder name matches the last segment of the model ID following "/", for example, for `THUDM/chatglm3-6b`, the model folder name should be `chatglm3-6b`.**


| Model |Category| download link | 
|:--|:--|:--|
|`THUDM/chatglm3-6b`|Chinese LLM| [HF](https://huggingface.co/THUDM/chatglm3-6b) or [ModelScope](https://www.modelscope.cn/models/ZhipuAI/chatglm3-6b/summary) |
|`meta-llama/Llama-2-7b-chat-hf`|English LLM| [HF](https://huggingface.co/meta-llama/Llama-2-7b-chat-hf) | 
|`BAAI/bge-large-zh-v1.5`|Chinese Embedding| [HF](https://huggingface.co/BAAI/bge-large-zh-v1.5) |
|`BAAI/bge-large-en-v1.5`| English Embedding|[HF](https://huggingface.co/BAAI/bge-large-en-v1.5) |

## Start the Service
Run the following commands:
```bash
conda activate ipex-llm-langchain-chatchat

source ipex-llm-init -t

export no_proxy='localhost,127.0.0.1'

# We recommend to use cores in one socket for the best performance.
# You may need to change the 0-47 below accordingly.
numactl -C 0-47 -m 0 python startup.py -a
```
>[!Note]
> The above numa configuration lead to optimal performance for **Intel(R) Xeon(R) Platinum 8468**.

You can find the Web UI's URL printted on the terminal logs, e.g. http://localhost:8501/.

Open a browser and navigate to the URL to use the Web UI. 