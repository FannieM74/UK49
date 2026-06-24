from typing import Any, List, Mapping, Optional
from langchain.callbacks.manager import CallbackManagerForLLMRun
from langchain.chat_models.base import BaseChatModel
from langchain.schema import (
    AIMessage,
    BaseMessage,
    ChatGeneration,
    ChatResult,
    HumanMessage,
    SystemMessage,
)
from google.genai import Client


GEMINI_ROLE_MAP = {
    "system": "user",
    "human": "user",
    "ai": "model",
}

def _convert_message(role: str, content: str) -> dict:
    gemini_role = GEMINI_ROLE_MAP.get(role.lower(), "user")
    return {"role": gemini_role, "parts": [{"text": content}]}


class GeminiChat(BaseChatModel):
    model: str = "gemini-2.0-flash"
    google_api_key: str = ""
    temperature: float = 0.7

    @property
    def _llm_type(self) -> str:
        return "gemini"

    @property
    def _identifying_params(self) -> Mapping[str, Any]:
        return {"model": self.model}

    def _convert_messages(self, messages: List[BaseMessage]) -> List[dict]:
        contents = []
        system_text = ""
        for msg in messages:
            if isinstance(msg, SystemMessage):
                system_text += msg.content + "\n"
            else:
                contents.append(_convert_message(msg.type, msg.content))
        if system_text.strip():
            # Prepend system as first user message (Gemini doesn't have system role)
            contents.insert(0, {"role": "user", "parts": [{"text": f"[System instruction]: {system_text}"}]})
        return contents

    def _generate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> ChatResult:
        client = Client(api_key=self.google_api_key)
        contents = self._convert_messages(messages)
        config = {"temperature": self.temperature}
        if stop:
            config["stop_sequences"] = stop

        resp = client.models.generate_content(
            model=self.model,
            contents=contents,
            config=config,
        )
        text = resp.text or ""
        message = AIMessage(content=text)
        gen = ChatGeneration(text=text, message=message)
        return ChatResult(generations=[gen])
