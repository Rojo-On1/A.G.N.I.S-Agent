from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, TypeVar

from dotenv import load_dotenv
from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


@dataclass(frozen=True)
class ModelParameters:
    """Parámetros de generación ajustados al contrato de cada agente."""

    temperature: float
    top_p: float
    max_tokens: int


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


def create_openai_model(parameters: ModelParameters) -> Any:
    load_dotenv()
    try:
        from langchain_openai import ChatOpenAI
    except ImportError as exc:
        raise RuntimeError(
            "Instala el extra del proveedor: pip install 'agnis-agent[openai]'"
        ) from exc
    return ChatOpenAI(
        model="gpt-4o-mini",
        temperature=parameters.temperature,
        top_p=parameters.top_p,
        max_tokens=parameters.max_tokens,
    )


ModelFactory = Callable[[ModelParameters], Any]
