
from functools import cache
from langchain_huggingface import ChatHuggingFace, HuggingFaceEndpoint, HuggingFacePipeline

#
# Create chat LLM.
#
# See: https://python.langchain.com/docs/integrations/chat/huggingface/
#
@cache
def get_chat_llm():

    model_id='microsoft/Phi-3.5-mini-instruct'

    base_llm = HuggingFaceEndpoint(
        # endpoint_url=endpoint_url,
        repo_id=model_id,
        max_new_tokens=2048,
        top_k=10,
        top_p=0.95,
        typical_p=0.95,
        temperature=0.01,
        streaming=False,
        do_sample=False,
        repetition_penalty=1.03,
    )

    from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline as hf_pipeline

    from langchain_core.globals import set_llm_cache    
    from langchain_core.caches import InMemoryCache

    set_llm_cache(InMemoryCache())

    model = AutoModelForCausalLM.from_pretrained(
        model_id, 
        torch_dtype= 'auto', 
        trust_remote_code=True, 
    )
    tokenizer = AutoTokenizer.from_pretrained(model_id)

    pipeline = hf_pipeline(
        "text-generation",
        device=0,
        model=model,
        tokenizer=tokenizer,
    )

    base_llm = HuggingFacePipeline(
        pipeline=pipeline,
        model_id=model_id,
        pipeline_kwargs=dict(
            max_new_tokens=2048,
            top_k=10,
            top_p=0.95,
            typical_p=0.95,
            temperature=0.01,
            streaming=False,
            do_sample=False,
            repetition_penalty=1.03,
        ),
    )

    
    llm = ChatHuggingFace(llm=base_llm, cache=True, streaming=False, disable_streaming=True, verbose=True)

    return llm
