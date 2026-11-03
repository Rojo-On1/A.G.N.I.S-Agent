from __future__ import annotations

from typing import Any, TypeVar

from dotenv import load_dotenv
from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


class StructuredAgent:
    """Thin adapter around LangChain structured output."""

    def __init__(self, model: Any, system_prompt: str, output_type: type[T]) -> None:
        self._chain = (
            model.with_structured_output(output_type)
            | (lambda value: value)
        )
        self._system_prompt = system_prompt

    def invoke(self, user_prompt: str) -> T:
        return self._chain.invoke(
            [
                ("system", self._system_prompt),
                ("human", user_prompt),
            ]
        )


def create_openai_model() -> Any:
    load_dotenv()
    try:
        from langchain_openai import ChatOpenAI
    except ImportError as exc:
        raise RuntimeError(
            "Instala el extra del proveedor: pip install 'agnis-agent[openai]'"
        ) from exc
    return ChatOpenAI(model="gpt-4o-mini", temperature=0)
