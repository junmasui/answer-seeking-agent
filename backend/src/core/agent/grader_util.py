
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser

from pydantic import BaseModel

from ..providers.chat_llm import get_chat_llm
from global_config import get_global_config

def build_grader(system_message, human_message, output_cls: BaseModel, run_name):

    config = get_global_config()
    # LLM
    llm = get_chat_llm()

    # HuggingFace does not have native support for structured output
    # See https://python.langchain.com/docs/how_to/structured_output/#custom-parsing
    #
    # Thus we support two modes:
    # - structured output
    # - custom instructions and parsing
    has_structured_output = config.llm_has_structured_output

    if not has_structured_output:
        system_message = system_message + '\nWrap the output in `json` tags\n{format_instructions}'  

    prompt = ChatPromptTemplate.from_messages(
        [
            ('system', system_message),
            ('human', human_message),
        ]
    )

    # Chain
    if has_structured_output:
        structured_llm_grader = llm.with_structured_output(output_cls)

        chain = prompt | structured_llm_grader
    else:
        custom_parser = PydanticOutputParser(pydantic_object=output_cls)
        modified_prompt = prompt.partial(format_instructions=custom_parser.get_format_instructions())

        chain = modified_prompt | llm | custom_parser

    chain = chain.with_config({'run_name': run_name})

    return chain

