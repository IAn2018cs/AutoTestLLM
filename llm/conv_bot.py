# coding=utf-8
import config
from llm.oai import LLMClient
from llm.ollama import OllamaLLMClient


class ConvBot:

    def __init__(self, model: str, is_ollama_model: bool):
        self.model = model
        if is_ollama_model:
            self.llm_client = OllamaLLMClient(config.ollama_api_host, timeout=300)
        else:
            self.llm_client = LLMClient(config.openai_api_key, config.openai_api_host, timeout=300)
        self.base_messages = []
        self.history_messages = []

    def __add_message__(self, messages: list[dict], role: str, content: str):
        messages.append({
            'role': role,
            'content': content
        })

    def add_base_system_message(self, content: str):
        self.__add_message__(self.base_messages, 'system', content)
        return self

    def add_base_assistant_message(self, content: str):
        self.__add_message__(self.base_messages, 'assistant', content)
        return self

    def __add_system_message__(self, message: list[dict], content: str):
        self.__add_message__(message, 'system', content)
        return self

    def __add_user_message__(self, message: list[dict], content: str):
        self.__add_message__(message, 'user', content)
        return self

    def __add_assistant_message__(self, message: list[dict], content: str):
        self.__add_message__(message, 'assistant', content)
        return self

    def ask(self, msg: str, **kwargs) -> str:
        try:
            # 检查历史对话长度限制
            max_conv_length = kwargs.pop('max_conv_length')
            if max_conv_length > 0:
                history_messages = self.history_messages[-max_conv_length * 2:]
            else:
                history_messages = self.history_messages

            messages = self.base_messages + history_messages
            self.__add_user_message__(messages, msg)

            # 检查越狱提示词
            jailbreak = kwargs.pop('jailbreak')
            jailbreak_system = kwargs.pop('jailbreak_system')
            if jailbreak:
                self.__add_system_message__(messages, jailbreak_system)

            result = self.llm_client.generate(self.model, messages, **kwargs)

            # 成功了，更新历史消息
            self.__add_user_message__(self.history_messages, msg)
            self.__add_assistant_message__(self.history_messages, result)
            return result
        except Exception as e:
            print(f'generate conv error: {e}')
            return ""
