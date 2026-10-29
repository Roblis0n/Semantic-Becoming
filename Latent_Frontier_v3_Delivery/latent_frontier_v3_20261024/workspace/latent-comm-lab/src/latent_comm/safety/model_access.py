"""Complete future loading entrypoints behind the current unconditional gate."""
from .policy import require_research_action

def load_hf_model(model_id: str, *, revision: str,device: str,dtype_name: str,local_files_only: bool=True):
    require_research_action('model_load')
    import torch
    from transformers import AutoModelForCausalLM
    dtype=getattr(torch,dtype_name)
    model=AutoModelForCausalLM.from_pretrained(model_id,revision=revision,torch_dtype=dtype,local_files_only=local_files_only,trust_remote_code=False)
    return model.to(device)

def load_hf_tokenizer(model_id: str, *, revision: str,local_files_only: bool=True):
    require_research_action('model_load')
    from transformers import AutoTokenizer
    return AutoTokenizer.from_pretrained(model_id,revision=revision,local_files_only=local_files_only,trust_remote_code=False)

def initialize_from_config(config):
    require_research_action('model_initialize')
    from transformers import AutoModelForCausalLM
    return AutoModelForCausalLM.from_config(config,trust_remote_code=False)

def invoke_research_api(client,request: dict):
    require_research_action('model_api')
    return client.responses.create(**request)
