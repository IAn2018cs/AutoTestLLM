# coding=utf-8

import base64
import json
import os
import random
import string
from datetime import datetime
from os import PathLike
from typing import AnyStr

import pandas as pd


def resolve_relative_path(file: PathLike[AnyStr], path: str) -> str:
    return os.path.abspath(os.path.join(os.path.dirname(file), path))


def root_relative_path(path: str) -> str:
    return os.path.abspath(os.path.join(os.path.dirname(__file__), f'./{path}'))


def create_path(path):
    if not os.path.exists(path):
        os.makedirs(path)


# 编码
def encode_base64(string):
    string_bytes = string.encode('utf-8')
    base64_bytes = base64.b64encode(string_bytes)
    base64_string = base64_bytes.decode('utf-8')
    return base64_string


# 解码
def decode_base64(base64_string):
    base64_bytes = base64_string.encode('utf-8')
    string_bytes = base64.b64decode(base64_bytes)
    string = string_bytes.decode('utf-8')
    return string


def extract_json(response):
    response = response.replace("JSON\n", "").replace("json\n", "").replace("```", "")
    json_start = response.index("{")
    json_end = response.rfind("}")
    return json.loads(response[json_start:json_end + 1])


def save_txt_to_file(file_path: str, content: str):
    # 获取文件所在的目录
    directory = os.path.dirname(file_path)

    # 如果目录不存在，创建它
    if not os.path.exists(directory):
        os.makedirs(directory)
    with open(file_path, 'w', encoding='utf-8') as file:
        file.write(content)


def load_data_with_upload(csv_path, usecols):
    try:
        df = pd.read_csv(csv_path, usecols=usecols)
        authors = df.to_dict(orient='records')
        return authors
    except Exception as e:
        print(e)
        return []


def load_data(csv_path, usecols):
    try:
        csv_path = root_relative_path(csv_path)
        df = pd.read_csv(csv_path, usecols=usecols)
        authors = df.to_dict(orient='records')
        return authors
    except Exception as e:
        print(e)
        return []


def generate_random_id(length=10):
    characters = string.ascii_letters + string.digits  # 包含所有字母（大写和小写）和数字
    return ''.join(random.choice(characters) for _ in range(length))  # 随机选择字符


def get_current_time(format='%Y-%m-%d-%H-%M'):
    """
    获取当前时间的格式化字符串
    :param format: 时间格式，默认为'%Y-%m-%d-%H-%M'
    :return: 格式化后的时间字符串
    """
    return datetime.now().strftime(format)
