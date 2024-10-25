# coding=utf-8
import json
from typing import Optional

import requests

import config
from tools import extract_json


def generate_by_openai(model: str, messages: list[dict], temperature: float = 0.5, json_format: bool = False,
                       max_tokens: int = 4096):
    try:
        url = f'{config.openai_api_host}/v1/chat/completions'
        data = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": False
        }
        if json_format:
            data["response_format"] = {
                "type": "json_object"
            }
        response = requests.post(
            url,
            headers={
                "Authorization": f"Bearer {config.openai_api_key}"
            },
            json=data
        )
        return response.json()['choices'][0]['message']['content']
    except Exception as e:
        print(f"generate_by_openai error: {e}")
        return None


def try_fix_json_format(json_str: str, retry_times: int = 1) -> Optional[str]:
    result = None
    try:
        messages = [
            {
                "role": "system",
                "content": """根据输入的包含 JSON 的字符串，修复或者提取文本中的 JSON 字符串。请严格按照以下步骤处理：
1. 判断内容，这一步不要输出内容
    1.1 如果仅仅包含 JSON，执行如下判断：
        - 如果 JSON 格式正确，输出原字符串。
        - 如果 JSON 格式错误，尝试修复错误，并输出修复后的 JSON 字符串。
        - 请尽量保证修复后的 JSON 字符串格式正确且数据内容未改变。
    1.2 如果还有其他内容，执行如下判断
        - 提取 JSON 对象，并输出提取后的 JSON 字符串。
2. 输出修复或者提取的 JSON 字符串，注意不要有其他任何解释性的文字。"""
            },
            {
                "role": "user",
                "content": '{"name": "John", "name2": "Haha", }'
            },
            {
                "role": "assistant",
                "content": '{"name": "John", "name2": "Haha"}'
            },
            {
                "role": "user",
                "content": '{"name": "John "sun" has dog" "age": 30,}'
            },
            {
                "role": "assistant",
                "content": r'{"name": "John \"sun\" has dog", "age": 30}'
            },
            {
                "role": "user",
                "content": '{"name": "John say: "sun", has dog", "age": 30}'
            },
            {
                "role": "assistant",
                "content": r'{"name": "John say\: \"sun\", has dog", "age": 30}'
            },
            {
                "role": "user",
                "content": '### JSON格式输出\n{"name": "John" "age": 30} \n此JSON格式详细阐述了个人信息'
            },
            {
                "role": "assistant",
                "content": '{"name": "John", "age": 30}'
            },
            {
                "role": "user",
                "content": f"{json_str}"
            }
        ]
        result = generate_by_openai("gpt-4o", messages, temperature=1, json_format=True)
        return json.dumps(extract_json(result))
    except Exception as e:
        if retry_times > 2:
            print(f"try_fix_json_format result:\n{result}\nerror: {e}")
            return None
        return try_fix_json_format(json_str, retry_times=retry_times + 1)
