# coding=utf-8
import time
from concurrent.futures import ThreadPoolExecutor

from tqdm import tqdm

import config
from feishu.excel_tools import create_worksheet
from feishu.feishu_sdk import FeiShuSdk
from roleplay_bot import RoleplayBot
from tools import generate_random_id, get_current_time


class RoleInfo:
    def __init__(self, role_id: int, name: str, brief_intro: str, first: str):
        self.role_id = role_id
        self.name = name
        self.brief_intro = brief_intro
        self.first = first


def test_conv_by_dialogue(test_id: int, model: str, role: RoleInfo, dialogues: list[str], conv_length: int,
                          nsfw: bool, open_translate: bool, jailbreak: bool,
                          base_system: str, nsfw_system: str, jailbreak_system: str):
    bot = RoleplayBot(
        test_id=test_id,
        model=model,
        name=role.name,
        brief_intro=role.brief_intro,
        first=role.first,
        nsfw=nsfw,
        jailbreak=jailbreak,
        base_system=base_system,
        nsfw_system=nsfw_system,
        jailbreak_system=jailbreak_system
    )
    for index in range(conv_length):
        bot.ask(
            msg=dialogues[index % len(dialogues)]
        )
        time.sleep(config.dialogue_sleep)
    return bot.get_conversation(open_translate)


def start_test(model: str, roles: list[RoleInfo], dialogues: list[str], rounds: int, conv_length: int,
               open_translate: bool, nsfw: bool, jailbreak: bool,
               base_system: str, nsfw_system: str, jailbreak_system: str):
    messages_map = {}
    total = len(roles) * rounds
    with tqdm(total=total) as pbar:
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
                        nsfw=nsfw,
                        open_translate=open_translate,
                        jailbreak=jailbreak,
                        base_system=base_system,
                        nsfw_system=nsfw_system,
                        jailbreak_system=jailbreak_system
                    )
                    futures.append((test_id, future))

                # 按 test_id 收集结果
                all_messages = []
                for test_id, future in sorted(futures, key=lambda x: x[0]):
                    messages = future.result()
                    all_messages.extend(messages)
                    pbar.set_description(f"{role.name} Conversation test {test_id}")
                    pbar.update(1)

                messages_map[role.name] = all_messages
    return messages_map


def start_gen(model: str, roles: list[RoleInfo], dialogue: list[str], rounds: int, conv_length: int,
              open_translate: bool, nsfw: bool, jailbreak: bool,
              base_system: str = None, nsfw_system: str = None, jailbreak_system: str = None) -> str:
    task_id = f"{get_current_time()}-{generate_random_id()}"
    print(
        f'{task_id}: start test, model: {model}, rounds: {rounds}, conv_length: {conv_length}, open_translate: {open_translate}, nsfw: {nsfw}, jailbreak: {jailbreak}')
    feishu_sdk = FeiShuSdk()
    map_data = start_test(
        model=model,
        roles=roles,
        dialogues=dialogue,
        rounds=rounds,
        conv_length=conv_length,
        open_translate=open_translate,
        nsfw=nsfw,
        jailbreak=jailbreak,
        base_system=base_system,
        nsfw_system=nsfw_system,
        jailbreak_system=jailbreak_system
    )
    path = create_worksheet(f"{model.replace('/', '-')}对话测试-{generate_random_id(4)}", map_data)
    url, _ = feishu_sdk.create_cloud_docs(path, "sheet")
    print(f'{task_id}: end test')
    return url
