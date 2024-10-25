# coding=utf-8
import config
from llm.V4 import LLMClient


class ConvBot:

    def __init__(self, model: str):
        self.model = model
        self.llm_client = LLMClient(config.openai_api_key, config.openai_api_host, timeout=300)
        self.messages = []

    def __add_message__(self, role: str, content: str):
        self.messages.append({
            'role': role,
            'content': content
        })

    def add_system_message(self, content: str):
        self.__add_message__('system', content)
        return self

    def add_user_message(self, content: str):
        self.__add_message__('user', content)
        return self

    def add_assistant_message(self, content: str):
        self.__add_message__('assistant', content)
        return self

    def ask(self, msg: str, **kwargs) -> str:
        self.add_user_message(msg)
        result, _, _, _ = self.llm_client.generate(self.model, self.messages, False, **kwargs)
        self.add_assistant_message(result)
        return result

    def clear(self):
        self.messages.clear()
