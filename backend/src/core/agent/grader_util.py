from langchain_core.output_parsers import PydanticOutputParser
from pydantic import BaseModel

from ..lib_config import get_lib_config
from ..providers.chat_llm import get_chat_llm


def build_grader(chat_prompt, output_cls: BaseModel, run_name):
    """
    Build a Langchain runnable for grading, using a chat model and an output parser.

    It supports both models with native structured output and models requiring custom parsing
    instructions. The resulting chain is configured with a specific run name.
    """
    config = get_lib_config()
    # LLM
    llm = get_chat_llm()

    # HuggingFace does not have native support for structured output
    # See https://python.langchain.com/docs/how_to/structured_output/#custom-parsing
    #
    # Thus we support two modes:
    # - structured output
    # - custom instructions and parsing
    has_structured_output = config.llm_has_structured_output

    # Chain
    if has_structured_output:
        structured_llm_grader = llm.with_structured_output(output_cls)

        chain = chat_prompt | structured_llm_grader
    else:
        custom_parser = PydanticOutputParser(pydantic_object=output_cls)
        modified_prompt = chat_prompt.partial(format_instructions=custom_parser.get_format_instructions())

        chain = modified_prompt | llm | custom_parser

    chain = chain.with_config({'run_name': run_name})

    return chain
