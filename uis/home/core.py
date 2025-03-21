# coding=utf-8
import time
from concurrent.futures import ThreadPoolExecutor

from tqdm import tqdm

import config
from feishu.excel_tools import create_worksheet
from feishu.feishu_sdk import FeiShuSdk
from uis.home.roleplay_bot import RoleplayBot
from utils.qa_quality import llm_dialogue_assessment, llm_nsfw_assessment
from utils.tools import generate_random_id, get_current_time


class RoleInfo:
    def __init__(self, role_id: int, name: str, brief_intro: str, first: str, scene_id: int = 0):
        self.role_id = role_id
        self.name = name
        self.brief_intro = brief_intro
        self.first = first
        self.scene_id = scene_id


def test_conv_by_dialogue(
        test_id: int, model: str, role: RoleInfo, dialogues: list[str],
        conv_length: int, open_translate: bool,
        **kwargs
):
    args = {
        "model": model,
        "name": role.name,
        "brief_intro": role.brief_intro,
        "first": role.first,
        "scene_id": role.scene_id
    }
    args.update(kwargs)
    bot = RoleplayBot(test_id=test_id, **args)
    print('start chat dialogue')
    for index in range(conv_length):
        bot.ask(
            msg=dialogues[index % len(dialogues)]
        )
        time.sleep(config.dialogue_sleep)
    print('start get conversation')
    return bot.get_conversation(open_translate)


def start_test(
        model: str, roles: list[RoleInfo], dialogues: list[str],
        rounds: int, conv_length: int, open_translate: bool,
        **kwargs
):
    test_params = [
        {
            '参数名': "微调模型",
            '参数值': model
        }, {
            '参数名': "测试多少遍",
            '参数值': rounds
        }, {
            '参数名': "每遍对话几轮",
            '参数值': conv_length
        }, {
            '参数名': "是否翻译结果",
            '参数值': open_translate
        }
    ]
    for key, value in kwargs.items():
        test_params.append({
            '参数名': key,
            '参数值': value
        })

    open_assessment = kwargs.pop('open_assessment', False)
    messages_map = {}
    assessment_list = []
    if open_assessment:
        total = len(roles) * rounds * 2
    else:
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
                        open_translate=open_translate,
                        **kwargs
                    )
                    futures.append((test_id, future))

                # 按 test_id 收集结果
                all_messages = []
                for test_id, future in sorted(futures, key=lambda x: x[0]):
                    messages = future.result()
                    all_messages.extend(messages)
                    pbar.set_description(f"{role.name} Conversation test {test_id}")
                    pbar.update(1)

                    if open_assessment:
                        # 评估对话质量
                        dialogue_assessment_result = llm_dialogue_assessment(role.name, role.brief_intro, role.first,
                                                                             messages)
                        nsfw_assessment_result = llm_nsfw_assessment(role.name, messages)
                        assessment_list.append({
                            '角色': role.name,
                            '遍数（test_id）': test_id,
                            '对话质量评估': dialogue_assessment_result,
                            'NSFW分析': nsfw_assessment_result
                        })
                        pbar.set_description(f"Evaluate conversation quality test {test_id}")
                        pbar.update(1)

                messages_map[role.name] = all_messages
    if open_assessment:
        messages_map['对话评估'] = assessment_list
    messages_map['参数'] = test_params
    return messages_map


def start_gen(
        model: str, roles: list[RoleInfo], dialogue: list[str],
        rounds: int, conv_length: int, open_translate: bool,
        **kwargs
) -> str:
    task_id = f"{get_current_time()}-{generate_random_id()}"
    print(
        f'{task_id}: start test, model: {model}, rounds: {rounds}, conv_length: {conv_length}, open_translate: {open_translate}'
    )
    feishu_sdk = FeiShuSdk()
    map_data = start_test(
        model=model,
        roles=roles,
        dialogues=dialogue,
        rounds=rounds,
        conv_length=conv_length,
        open_translate=open_translate,
        **kwargs
    )
    path = create_worksheet(f"{model.replace('/', '-')}对话测试-{generate_random_id(4)}", map_data)
    print('start upload docs')
    if config.is_local_debug:
        url = path
    else:
        url, _ = feishu_sdk.create_cloud_docs(path, "sheet")
    print(f'{task_id}: end test\n\n')
    return url
