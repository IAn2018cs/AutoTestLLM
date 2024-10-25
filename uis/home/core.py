# coding=utf-8
import time

from tqdm import tqdm

from feishu.excel_tools import create_worksheet
from feishu.feishu_sdk import FeiShuSdk
from roleplay_bot import RoleplayBot
from tools import generate_random_id
from user_dialogue_factory import fetch_dialogue, DialogueType


class RoleInfo:
    def __init__(self, role_id: int, name: str, brief_intro: str, first: str):
        self.role_id = role_id
        self.name = name
        self.brief_intro = brief_intro
        self.first = first


def test_conv(test_id: int, model: str, role: RoleInfo, conv_length: int,
              nsfw: bool, open_translate: bool, dialogue_type: DialogueType):
    bot = RoleplayBot(
        test_id=test_id,
        model=model,
        name=role.name,
        brief_intro=role.brief_intro,
        first=role.first,
        nsfw=nsfw
    )
    for index in tqdm(range(conv_length), desc=f"Conversation test {test_id}"):
        bot.ask(
            msg=fetch_dialogue(index, bot.get_last_message(), dialogue_type=dialogue_type)
        )
        time.sleep(3)
    return bot.get_conversation(open_translate)


def start_test(model: str, roles: list[RoleInfo], rounds: int, conv_length: int,
               open_translate: bool, dialogue_type: DialogueType, progress):
    messages_map = {}
    for role in progress.tqdm(roles):
        all_messages = []
        for test_id in range(1, rounds + 1):
            messages = test_conv(
                test_id=test_id,
                model=model,
                role=role,
                conv_length=conv_length,
                nsfw=True,
                open_translate=open_translate,
                dialogue_type=dialogue_type
            )
            all_messages.extend(messages)
        messages_map[role.name] = all_messages
    return messages_map


def start_gen(model: str, roles: list[RoleInfo], rounds: int, conv_length: int, open_translate: bool, progress) -> str:
    feishu_sdk = FeiShuSdk()
    map_data = start_test(
        model=model,
        roles=roles,
        rounds=rounds,
        conv_length=conv_length,
        open_translate=open_translate,
        dialogue_type=DialogueType.CSV,
        progress=progress
    )
    path = create_worksheet(f"{model}对话测试-{generate_random_id(4)}", map_data)
    url, _ = feishu_sdk.create_cloud_docs(path, "sheet")
    return url
