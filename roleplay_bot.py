# coding=utf-8
import time
from typing import Optional

from tqdm import tqdm

import config
from llm.conv_bot import ConvBot
from translate_factory import translate_text, LangType


class RoleplayBot:

    def __init__(self, test_id: int, model: str, name: str, brief_intro: str, first: str,
                 nsfw: bool = True, jailbreak: bool = True,
                 base_system: Optional[str] = None,
                 nsfw_system: Optional[str] = None,
                 jailbreak_system: Optional[str] = None,
                 temperature: float = 1):
        self.test_id = test_id
        self.name = name
        self.brief_intro = brief_intro
        self.first = first
        self.nsfw = nsfw
        self.jailbreak = jailbreak
        self.base_system = base_system if base_system else config.base_system.replace('{{char}}', name)
        self.nsfw_system = nsfw_system if nsfw_system else config.nsfw_system
        self.jailbreak_system = jailbreak_system if jailbreak_system else config.jailbreak_system
        self.temperature = temperature
        self.is_ollama_model = model in config.ollama_models
        host = config.ollama_api_host if self.is_ollama_model else config.openai_api_host
        self.bot = ConvBot(model, host)
        self.__init_conv__()

    def __init_conv__(self):
        if self.is_ollama_model:
            self.bot.add_system_message(self.base_system)
        else:
            self.bot.add_system_message(self.base_system)
            self.bot.add_system_message(self.brief_intro)
            if self.nsfw:
                self.bot.add_system_message(self.nsfw_system)
            self.bot.add_system_message("[Start a new Chat]")
            self.bot.add_assistant_message(self.first)

    def ask(self, msg: str) -> str:
        return self.bot.ask(
            msg,
            temperature=self.temperature,
            max_tokens=200,
            jailbreak=False if self.is_ollama_model else self.jailbreak,
            jailbreak_system=self.jailbreak_system
        )

    def get_last_message(self) -> str:
        return self.bot.messages[-1]['content']

    def get_conversation(self, open_translate: bool) -> list[dict]:
        result = [
            {
                'test_id': self.test_id,
                'order_id': 1,
                'role': 'system',
                'content': self.brief_intro,
                'translate': translate_text(
                    self.brief_intro,
                    source=LangType.EN,
                    target=LangType.ZH
                ) if open_translate else ""
            },
            {
                'test_id': self.test_id,
                'order_id': 2,
                'role': 'assistant',
                'content': self.first,
                'translate': translate_text(
                    self.first,
                    source=LangType.EN,
                    target=LangType.ZH
                ) if open_translate else ""
            }
        ]
        sub_length = 5 if self.nsfw else 4
        order_id = 3
        for message in tqdm(self.bot.messages[sub_length:], desc="Translation conversation"):
            result.append(
                {
                    'test_id': self.test_id,
                    'order_id': order_id,
                    'role': message['role'],
                    'content': message['content'],
                    'translate': translate_text(
                        message['content'],
                        source=LangType.EN,
                        target=LangType.ZH
                    ) if open_translate else ""
                }
            )
            order_id += 1
            if open_translate:
                time.sleep(config.translate_sleep)
        return result
