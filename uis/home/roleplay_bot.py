# coding=utf-8
import time

import config
from llm.conv_bot import ConvBot
from utils.translate_factory import translate_text, LangType


class RoleplayBot:

    def __init__(self, test_id: int, **kwargs):
        self.test_id = test_id
        self.model = kwargs.get('model')
        self.name = kwargs.get('name')
        self.brief_intro = kwargs.get('brief_intro')
        self.first = kwargs.get('first')
        self.scene_id = int(kwargs.get('scene_id'))
        self.nsfw = kwargs.get('nsfw', False)
        self.jailbreak = kwargs.get('jailbreak', False)
        self.base_system = (kwargs.get('base_system', config.base_system)
                            .replace('{{char}}', self.name)
                            .replace('{{角色名字}}', self.name)
                            .replace('{{角色背景信息}}', self.brief_intro)
                            .replace('{{角色首条消息}}', self.first)
                            )
        self.nsfw_system = kwargs.get('nsfw_system', config.nsfw_system)
        self.jailbreak_system = kwargs.get('jailbreak_system', config.jailbreak_system)
        self.temperature = kwargs.get('temperature', 1.0)
        self.max_tokens = kwargs.get('max_tokens', 200)
        self.presence_penalty = kwargs.get('presence_penalty', 1.1)
        self.top_p = kwargs.get('top_p', 1.0)
        self.use_temperature = kwargs.get('use_temperature', True)
        self.use_top_p = kwargs.get('use_top_p', False)
        self.max_conv_length = kwargs.get('max_conv_length', 0)

        self.is_ollama_model = self.model in config.ollama_models
        self.is_gpt_model = self.model in config.gpt_models
        self.is_poly_model = self.model in config.poly_models

        self.bot = ConvBot(self.model)
        self.__init_conv__()

    def __init_conv__(self):
        if self.is_gpt_model:
            self.bot.add_base_system_message(self.base_system)
            self.bot.add_base_system_message(self.brief_intro)
            if self.nsfw:
                self.bot.add_base_system_message(self.nsfw_system)
            self.bot.add_base_system_message("[Start a new Chat]")
            self.bot.add_base_assistant_message(self.first)
        else:
            self.bot.add_base_system_message(self.base_system)

    def ask(self, msg: str) -> str:
        args = {
            'jailbreak_system': self.jailbreak_system,
            'max_conv_length': self.max_conv_length
        }
        if self.use_temperature:
            args['temperature'] = self.temperature
        if self.use_top_p:
            args['top_p'] = self.top_p

        if self.is_ollama_model:
            args.update({
                'num_predict': self.max_tokens,
                'presence_penalty': self.presence_penalty,
                'mirostat': 0,
                'mirostat_eta': 0.1,
                'mirostat_tau': 5.0,
                'top_k': 40,
                'min_p': 0.0,
                'repeat_penalty': 1.1,
                'repeat_last_n': 64,
                'tfs_z': 1,
                'num_ctx': 2048,
                'frequency_penalty': 0,
                'jailbreak': False
            })
        elif self.is_poly_model:
            args.update({
                'scene_id': self.scene_id,
                'jailbreak': False
            })
        else:
            args.update({
                'max_tokens': self.max_tokens,
            })
            if self.is_gpt_model:
                args.update({
                    'jailbreak': self.jailbreak
                })
            else:
                args.update({
                    'presence_penalty': self.presence_penalty,
                    'jailbreak': False
                })
        return self.bot.ask(
            msg,
            **args
        )

    def get_conversation(self, open_translate: bool) -> list[dict]:
        result = []
        if self.is_gpt_model:
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
            order_id = 3
        else:
            order_id = 1

        if open_translate:
            print(f'start translate')

        for message in self.bot.history_messages:
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
