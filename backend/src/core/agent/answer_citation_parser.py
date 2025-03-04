import logging

import re
from typing import Union, Optional, Any

from langchain_core.messages import BaseMessage
from langchain_core.outputs import Generation, ChatGeneration
from langchain_core.output_parsers import BaseGenerationOutputParser
from langchain_core.runnables import RunnableConfig

logger = logging.getLogger(__name__)

class AnswerCitationParser(BaseGenerationOutputParser[dict[str, str]]):
    """Parse the output of an LLM call into a Dictionary using a regex."""

    regex_footnote: str = re.compile(r'''
        \s*  # whitespace
        <footnote>
        <docId>(?P<docId>[^<>]+)</docId>
        (?:<fileName>(?P<fileName>[^<>]+)</fileName>)?
        (?:<pageNumber>(?P<pageNumber>[^<>]+)</pageNumber>)?
        </footnote>
        \s*  # whitespace
        ''',
        re.VERBOSE)

    @property
    def _type(self) -> str:
        """Return the type key."""
        return "citation_parser"

    def parse(self, text: str) -> dict[str, str]:
        raise NotImplementedError(
            "This OutputParser can only be called by the `parse_with_prompt` method."
        )
    
    def invoke(
        self,
        input: Union[str, BaseMessage],
        config: Optional[RunnableConfig] = None,
        **kwargs: Any,
    ) -> dict[str, str]:
        """Critical override to bypass an internal lambda function that is preventing
        the parse_result method from seeing the config object.

        See v0.3.41 codebase: https://github.com/langchain-ai/langchain/blob/langchain-core%3D%3D0.3.41/libs/core/langchain_core/output_parsers/base.py#L90
        Monitor the latest to see if the internal lambda function is removed:
        https://github.com/langchain-ai/langchain/blob/master/libs/core/langchain_core/output_parsers/base.py#L90
        """
        
        if not isinstance(input, BaseMessage):
            raise TypeError(
                f"Input must be a BaseMessage, but got {type(input).__name__}."
            )

        return self._call_with_config(
            self.parse_result,
            [ChatGeneration(message=input)],
            config,
            run_type="parser",
        )

       

    def parse_result(self, result: list[Generation], *, partial: bool = False, config: dict = None) -> dict[str, str]:
        """Parse the output of an LLM call."""

        documents = config['configurable'].get('documents', [])
        documents = {doc.id: doc for doc in documents}

        text = result[0].text


        answer = ""
        citations = []
        pos = 0

        logger.info('first text: %d "%s"', pos, text[pos: min(len(text), pos+30)])
        while (match := self.regex_footnote.search(text, pos)):
            doc_id = match.group('docId')
            file_name = match.group('fileName')
            page_number = match.group('pageNumber')

            page_content = documents[doc_id].page_content if doc_id in documents else ''

            answer += text[pos:match.start()]

            import pprint
            logger.info('---CITATION---\n%s', pprint.pformat(dict(match.groupdict()), indent=4, width=200))

            citations.append({
                'doc_id': doc_id,
                'text': page_content,
                'file_name': file_name,
                'page_number': page_number
            })

            pos = match.end()


        output = {
            'generation': text,
            'answer': answer,
            'citations': citations
        }

        return output