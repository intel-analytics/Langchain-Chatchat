import torch
import gc
from pathlib import Path

from ipex_llm.transformers import AutoModel, AutoModelForCausalLM
from transformers import AutoTokenizer, LlamaTokenizer
import intel_extension_for_pytorch as ipex

from configs.model_config import MODEL_ROOT_PATH

llm_warmup_prompts = ["Once upon a time, there existed a little girl who liked to have adventures. She wanted to go to places and meet new people, and have fun. ", "Once upon a time"]
embedding_warmup_prompt = """
In the year 2048, the world was a very different place from what it had been just two decades before. The pace of technological progress had quickened to an almost unimaginable degree, and the changes that had swept through society as a result were nothing short of revolutionary.
In many ways, the year 2048 represented the culmination of a long and tumultuous journey that humanity had been on since the dawn of civilization. The great leaps forward in science and technology that had occurred over the course of the previous century had laid the groundwork for a future that was beyond anything anyone could have imagined.
One of the most striking aspects of life in 2048 was the degree to which technology had become an integral part of nearly every aspect of daily existence. From the moment people woke up in the morning until they went to bed at night, they were surrounded by devices and systems that were powered by advanced artificial intelligence and machine learning algorithms.
In fact, it was hard to find anything in people's lives that wasn't touched by technology in some way. Every aspect of society had been transformed, from the way people communicated with one another to the way they worked, played, and even socialized. And as the years went on, it seemed as though there was no limit to what technology could achieve.
Despite all of these advances, however, not everyone was happy with the state of the world in 2048. Some people saw the increasing reliance on technology as a sign that humanity was losing touch with its own humanity, and they worried about the implications of this for the future.
Others were more pragmatic, recognizing that,
"""

print(">> NOTE: The one-time warmup may take several minutes. Please be patient until it finishes warm-up...")
print("-"*15, " Start warming-up LLM chatglm3-6b on Intel Core Ultra integrated GPU ", "-"*15)
model_path = Path(MODEL_ROOT_PATH) / "chatglm3-6b"

model = AutoModel.from_pretrained(model_path,
                                  load_in_4bit=True,
                                  optimize_model=True,
                                  trust_remote_code=True,
                                  use_cache=True,
                                  cpu_embedding=True)
model = model.to('xpu')

# Load tokenizer
tokenizer = AutoTokenizer.from_pretrained(model_path,
                                          trust_remote_code=True)

with torch.inference_mode():
    for prompt in llm_warmup_prompts:
        input_ids = tokenizer.encode(prompt, return_tensors="pt").to('xpu')
        output = model.generate(input_ids,
                                max_new_tokens=32)
print("-"*15, " Warming-up of LLM chatglm3-6b on Intel Core Ultra integrated GPU is completed (1/4) ", "-"*15)

model.to('cpu')
torch.xpu.synchronize()
torch.xpu.empty_cache()
del model
gc.collect()

print("-"*15, " Start warming-up LLM Llama-2-7b-chat-hf on Intel Core Ultra integrated GPU ", "-"*15)
model_path = Path(MODEL_ROOT_PATH) / "Llama-2-7b-chat-hf"

model = AutoModelForCausalLM.from_pretrained(model_path,
                                             load_in_4bit=True,
                                             optimize_model=True,
                                             trust_remote_code=True,
                                             use_cache=True,
                                             cpu_embedding=True)
model = model.to('xpu')

# Load tokenizer
tokenizer = LlamaTokenizer.from_pretrained(model_path,
                                           trust_remote_code=True)

with torch.inference_mode():
    for prompt in llm_warmup_prompts:
        input_ids = tokenizer.encode(prompt, return_tensors="pt").to('xpu')
        output = model.generate(input_ids,
                                max_new_tokens=32)
print("-"*15, " Warming-up of LLM Llama-2-7b-chat-hf on Intel Core Ultra integrated GPU is completed (2/4) ", "-"*15)

model.to('cpu')
torch.xpu.synchronize()
torch.xpu.empty_cache()
del model
gc.collect()

print("-"*15, " Start warming-up embedding model bge-large-zh-v1.5 on Intel Core Ultra integrated GPU ", "-"*15)
# Refering: https://huggingface.co/BAAI/bge-large-zh-v1.5#using-huggingface-transformers
model_path = Path(MODEL_ROOT_PATH) / "bge-large-zh-v1.5"

model = AutoModel.from_pretrained(model_path,
                                  load_in_low_bit="fp16",
                                  optimize_model=True)
    
model = model.to('xpu')

# Load tokenizer
tokenizer = AutoTokenizer.from_pretrained(model_path,
                                          trust_remote_code=True)

with torch.inference_mode():
    encoded_input = tokenizer([embedding_warmup_prompt],
                              padding=True,
                              truncation=True,
                              return_tensors='pt').to('xpu')

    model_output = model(**encoded_input)
print("-"*15, " Warming-up of embedding model bge-large-zh-v1.5 on Intel Core Ultra integrated GPU is completed (3/4) ", "-"*15)

model.to('cpu')
torch.xpu.synchronize()
torch.xpu.empty_cache()
del model
gc.collect()

print("-"*15, " Start warming-up embedding model bge-large-en-v1.5 on Intel Core Ultra integrated GPU ", "-"*15)
# Refering: https://huggingface.co/BAAI/bge-large-en-v1.5#using-huggingface-transformers
model_path = Path(MODEL_ROOT_PATH) / "bge-large-en-v1.5"

model = AutoModel.from_pretrained(model_path,
                                  load_in_low_bit="fp16",
                                  optimize_model=True)
    
model = model.to('xpu')

# Load tokenizer
tokenizer = AutoTokenizer.from_pretrained(model_path,
                                          trust_remote_code=True)

with torch.inference_mode():
    encoded_input = tokenizer([embedding_warmup_prompt],
                              padding=True,
                              truncation=True,
                              return_tensors='pt').to('xpu')

    model_output = model(**encoded_input)
print("-"*15, " Warming-up of embedding model bge-large-en-v1.5 on Intel Core Ultra integrated GPU is completed (4/4) ", "-"*15)

model.to('cpu')
torch.xpu.synchronize()
torch.xpu.empty_cache()
del model
gc.collect()
