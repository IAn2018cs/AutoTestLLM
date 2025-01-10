# coding=utf-8
import time
from typing import Optional

import config
from llm.conv_bot import ConvBot
from translate_factory import translate_text, LangType


class RoleplayBot:

    def __init__(self, test_id: int, model: str, name: str, brief_intro: str, first: str,
                 nsfw: bool = True, jailbreak: bool = True,
                 base_system: Optional[str] = None,
                 nsfw_system: Optional[str] = None,
                 jailbreak_system: Optional[str] = None,
                 temperature: float = 1, max_tokens = 200):
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
        self.max_tokens = max_tokens
        self.is_ollama_model = model in config.ollama_models
        self.bot = ConvBot(model, self.is_ollama_model)
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
        if self.is_ollama_model:
            return self.bot.ask(
                msg,
                num_predict=self.max_tokens,
                temperature=self.temperature,
                mirostat=0,
                mirostat_eta=0.1,
                mirostat_tau=5.0,
                top_k=40,
                top_p=0.9,
                min_p=0.0,
                repeat_penalty=1.1,
                repeat_last_n=64,
                tfs_z=1,
                num_ctx=2048,
                jailbreak=False,
                jailbreak_system=self.jailbreak_system
            )
        else:
            return self.bot.ask(
                msg,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                jailbreak=self.jailbreak,
                jailbreak_system=self.jailbreak_system
            )

    def get_last_message(self) -> str:
        return self.bot.messages[-1]['content']

    def get_conversation(self, open_translate: bool) -> list[dict]:
        result = []
        if not self.is_ollama_model:
            result.extend([
                {
                    'test_id': self.test_id,
                    'order_id': 1,
                    'role': 'system',
                    'content': self.brief_intro,
                    'translate': ""
                },
                {
                    'test_id': self.test_id,
                    'order_id': 2,
                    'role': 'assistant',
                    'content': self.first,
                    'translate': ""
                }
            ])
        if self.is_ollama_model:
            sub_length = 1
            order_id = 1
        else:
            sub_length = 5 if self.nsfw else 4
            order_id = 3
        if open_translate:
            print(f'start translate')
        for message in self.bot.messages[sub_length:]:
            translate_msg = ""
            if open_translate:
                translate_msg = translate_text(
                    message['content'],
                    source=LangType.EN,
                    target=LangType.ZH
                )
            result.append(
                {
                    'test_id': self.test_id,
                    'order_id': order_id,
                    'role': message['role'],
                    'content': message['content'],
                    'translate': translate_msg
                }
            )
            order_id += 1
            if open_translate:
                time.sleep(config.translate_sleep)
        if open_translate:
            print(f'end translate')
        return result
