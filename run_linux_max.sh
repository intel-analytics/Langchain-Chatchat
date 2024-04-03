source /opt/intel/oneapi/setvars.sh

export LD_PRELOAD=${LD_PRELOAD}:${CONDA_PREFIX}/lib/libtcmalloc.so
export SYCL_PI_LEVEL_ZERO_USE_IMMEDIATE_COMMANDLISTS=1
export SYCL_CACHE_PERSISTENT=1
export ENABLE_SDP_FUSION=1
export BIGDL_LLM_XMX_DISABLED=1
export BIGDL_QUANTIZE_KV_CACHE=1

export BIGDL_IMPORT_IPEX=0
export no_proxy=localhost,127.0.0.1

python startup.py -a