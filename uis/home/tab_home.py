# coding=utf-8
import json

import gradio as gr

import config
from uis.home.core import start_gen, RoleInfo
from uis.tab_ids import TabId

all_models = config.ft_models


def start_gan(ai_model, rounds, conv_length, open_translate, role_info_box, progress=gr.Progress()):
    try:
        box_list = [h[0] for h in role_info_box if h[0]]
        if len(box_list) == 0:
            raise gr.Error("请填写角色信息")
        roles = []
        for item in box_list:
            obj = json.loads(item)
            roles.append(RoleInfo(
                role_id=obj['role_id'],
                name=obj['name'],
                brief_intro=obj['brief_intro'],
                first=obj['first']
            ))
        result_url = start_gen(ai_model, roles, rounds, conv_length, open_translate, progress)
        return gr.Markdown(f"## 飞书文档链接: [{result_url}]({result_url})")
    except Exception as e:
        raise gr.Error(f"{e}")


def add_role(role_name, role_system, role_first, role_info_box):
    if role_name.strip() == "" or role_system.strip() == "" or role_first.strip() == "":
        gr.Warning("请填写角色信息")
        return role_name, role_system, role_first, role_info_box
    line_str = "——" * 30
    role_info = {
        'role_id': len(role_info_box) + 1,
        'name': role_name,
        'brief_intro': role_system,
        'first': role_first
    }
    role_info_box.append((json.dumps(role_info, ensure_ascii=False, indent=4), line_str))
    return "", "", "", role_info_box


def build_home_ui():
    with gr.TabItem("Home", id=TabId.HOME.value):
        ai_model = gr.Dropdown(
            choices=all_models,
            value=all_models[0],
            multiselect=False,
            label="微调模型"
        )
        with gr.Row():
            rounds = gr.Slider(
                value=4,
                minimum=1,
                maximum=10,
                step=1,
                label="测试多少遍"
            )
            conv_length = gr.Slider(
                value=30,
                minimum=1,
                maximum=50,
                step=1,
                label="每遍对话几轮"
            )
        open_translate = gr.Checkbox(value=False, label="是否翻译结果")

        with gr.Column():
            role_name = gr.Textbox(label="角色名字", value="Ava Thompson")
            role_system = gr.Textbox(
                label="角色 system",
                value="Ava is a girl you just met at a bar. You two had a great time talking and hoped to develop further. After the bar party, you came to your house together, and you couldn't wait to start kissing as soon as you entered the door."
            )
            role_first = gr.Textbox(label="首条消息", value="kiss me")

        add_role_btn = gr.Button("添加测试角色信息")
        role_info_box = gr.Chatbot(label="整体方案阶段")

        add_role_btn.click(
            add_role,
            inputs=[role_name, role_system, role_first, role_info_box],
            outputs=[role_name, role_system, role_first, role_info_box]
        )
        start_gen_btn = gr.Button("开始测试", variant="primary")
        markdown_url = gr.Markdown(label="测试结果飞书文档链接", value="## 飞书文档链接:")

    start_gen_btn.click(
        fn=start_gan,
        inputs=[
            ai_model, rounds, conv_length, open_translate, role_info_box
        ],
        outputs=[
            markdown_url
        ],
        scroll_to_output=True
    )
