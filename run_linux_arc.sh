source /opt/intel/oneapi/setvars.sh
export USE_XETLA=OFF
export SYCL_PI_LEVEL_ZERO_USE_IMMEDIATE_COMMANDLISTS=1
export SYCL_CACHE_PERSISTENT=1
export BIGDL_QUANTIZE_KV_CACHE=1
export BIGDL_LLM_XMX_DISABLED=1

export no_proxy='localhost,127.0.0.1'
export BIGDL_IMPORT_IPEX=0

python startup.py -a