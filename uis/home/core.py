# coding=utf-8
import time
from concurrent.futures import ThreadPoolExecutor

import config
from feishu.excel_tools import create_worksheet
from feishu.feishu_sdk import FeiShuSdk
from roleplay_bot import RoleplayBot
from tools import generate_random_id


class RoleInfo:
    def __init__(self, role_id: int, name: str, brief_intro: str, first: str):
        self.role_id = role_id
        self.name = name
        self.brief_intro = brief_intro
        self.first = first


def test_conv_by_dialogue(test_id: int, model: str, role: RoleInfo, dialogues: list[str], conv_length: int,
                          nsfw: bool, open_translate: bool,
                          pbar):
    bot = RoleplayBot(
        test_id=test_id,
        model=model,
        name=role.name,
        brief_intro=role.brief_intro,
        first=role.first,
        nsfw=nsfw
    )
    for index in range(conv_length):
        bot.ask(
            msg=dialogues[index % len(dialogues)]
        )
        time.sleep(config.dialogue_sleep)
        pbar.set_description(f"{role.name} Conversation test {test_id}, chat order: {index}")
        pbar.update(1)
    return bot.get_conversation(open_translate)


def start_test(model: str, roles: list[RoleInfo], dialogues: list[str], rounds: int, conv_length: int,
               open_translate: bool, progress):
    messages_map = {}
    total = len(roles) * rounds * conv_length
    with progress.tqdm(total=total) as pbar:
        with ThreadPoolExecutor(max_workers=config.max_workers) as executor:
            for role in roles:
                futures = []
                # 提交所有任务到线程池
                for test_id in range(1, rounds + 1):
                    future = executor.submit(
                        test_conv_by_dialogue,
                        test_id=test_id,
                        model=model,
                        role=role,
                        dialogues=dialogues,
                        conv_length=conv_length,
                        nsfw=True,
                        open_translate=open_translate,
                        pbar=pbar
                    )
                    futures.append((test_id, future))

                # 按 test_id 收集结果
                all_messages = []
                for test_id, future in sorted(futures, key=lambda x: x[0]):
                    messages = future.result()
                    all_messages.extend(messages)

                messages_map[role.name] = all_messages
    return messages_map


def start_gen(model: str, roles: list[RoleInfo], dialogue: list[str], rounds: int, conv_length: int,
              open_translate: bool, progress) -> str:
    feishu_sdk = FeiShuSdk()
    map_data = start_test(
        model=model,
        roles=roles,
        dialogues=dialogue,
        rounds=rounds,
        conv_length=conv_length,
        open_translate=open_translate,
        progress=progress
    )
    path = create_worksheet(f"{model}对话测试-{generate_random_id(4)}", map_data)
    url, _ = feishu_sdk.create_cloud_docs(path, "sheet")
    return url
