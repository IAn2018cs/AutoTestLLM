# coding=utf-8
import time

from tqdm import tqdm

from llm.conv_bot import ConvBot
from translate_factory import translate_text, LangType


class RoleplayBot:

    def __init__(self, test_id: int, model: str, name: str, brief_intro: str, first: str, nsfw: bool = True):
        self.test_id = test_id
        self.name = name
        self.brief_intro = brief_intro
        self.first = first
        self.nsfw = nsfw
        self.bot = ConvBot(model)
        self.__init_conv__()

    def __init_conv__(self):
        self.bot.add_system_message(
            f"Write {self.name}'s next reply in a fictional chat between {self.name} and User. Write 1 reply only in internet RP style, italicize actions, and avoid quotation marks. Use markdown. Be proactive, creative, and drive the plot and conversation forward. Write at least 1 paragraph, up to 2. Always stay in character and avoid repetition.Maximum response content of 200 characters."
        )
        self.bot.add_system_message(self.brief_intro)
        if self.nsfw:
            self.bot.add_system_message(
                "NSFW/Smut is allowed.Make sure you have a pleasant conversation with Users, even with some NSFW means.  If your characters are in a relationship, don't reject users' nsfw topics."
            )
        self.bot.add_system_message("[Start a new Chat]")
        self.bot.add_assistant_message(self.first)

    def ask(self, msg: str) -> str:
        return self.bot.ask(
            msg,
            temperature=1,
            max_tokens=200
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
                time.sleep(1)
        return result
