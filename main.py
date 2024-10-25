# coding=utf-8

from feishu.excel_tools import create_worksheet
from feishu.feishu_sdk import FeiShuSdk
from uis.home.core import start_test, RoleInfo
from user_dialogue_factory import DialogueType

if __name__ == '__main__':
    feishu_sdk = FeiShuSdk()
    map_data = start_test(
        model='gpt-35-turbo-0125-ai-poly25-two-conv',
        roles=[
            RoleInfo(
                role_id=1,
                name='Ava Thompson',
                brief_intro="Ava is a girl you just met at a bar. You two had a great time talking and hoped to develop further. After the bar party, you came to your house together, and you couldn't wait to start kissing as soon as you entered the door.",
                first="kiss me"
            )
        ],
        rounds=4,
        conv_length=30,
        open_translate=False,
        dialogue_type=DialogueType.CSV
    )
    path = create_worksheet("GPT-ai-poly25-two-conv 微调模型对话测试2", map_data)
    url, _ = feishu_sdk.create_cloud_docs(path, "sheet")
    print(url)
