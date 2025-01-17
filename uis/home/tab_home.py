# coding=utf-8

import gradio as gr

import config
from tools import load_data_with_upload
from uis.home.core import start_gen, RoleInfo
from uis.tab_ids import TabId

all_models = config.ft_models + config.ollama_models


def start_gan(ai_model, rounds, conv_length, open_translate, nsfw, jailbreak, role_file, dialogue_file,
              base_system, nsfw_system, jailbreak_system, temperature, max_tokens, presence_penalty,
              progress=gr.Progress(track_tqdm=True)):
    try:
        if not str(role_file).endswith('csv') or not str(dialogue_file).endswith('csv'):
            raise gr.Error("只支持上传 csv 文件")
        role_list = load_data_with_upload(role_file, ['Name', 'first_message', 'system'])
        if len(role_list) == 0:
            raise gr.Error("请检查角色 csv 文件中是否包含 'Name', 'first_message', 'system'")
        roles = []
        for i, item in enumerate(role_list):
            roles.append(RoleInfo(
                role_id=i + 1,
                name=item['Name'],
                brief_intro=item['system'],
                first=item['first_message']
            ))
        dialogue_list = load_data_with_upload(dialogue_file, ['content'])
        if len(dialogue_list) == 0:
            raise gr.Error("请检查对话 csv 文件中是否包含 'content'")
        dialogue = []
        for item in dialogue_list:
            dialogue.append(item['content'])
        result_url = start_gen(ai_model, roles, dialogue, rounds, conv_length, open_translate,
                               nsfw, jailbreak, base_system, nsfw_system, jailbreak_system,
                               temperature, max_tokens, presence_penalty)
        return gr.Markdown(f"## 飞书文档链接: [{result_url}]({result_url})")
    except Exception as e:
        raise gr.Error(f"{e}")


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
                maximum=20,
                step=1,
                label="测试多少遍"
            )
            conv_length = gr.Slider(
                value=30,
                minimum=1,
                maximum=100,
                step=1,
                label="每遍对话几轮"
            )
        nsfw = gr.Checkbox(value=True, label="是否加入 NSFW 提示词")
        jailbreak = gr.Checkbox(value=True, label="是否加入 越狱提示词")
        open_translate = gr.Checkbox(value=False, label="是否翻译结果")
        temperature = gr.Slider(minimum=0, maximum=2, value=0.99, step=0.01, label='temperature')
        max_tokens = gr.Slider(minimum=1, maximum=4096, value=128, step=1, label='max tokens')
        presence_penalty = gr.Slider(minimum=-2, maximum=2, value=1.1, step=0.01, label='presence penalty')

        base_system = gr.TextArea(value=config.base_system, label='主提示词（注意一定要有 {{char}}，这是角色名字的占位）', lines=2)
        nsfw_system = gr.TextArea(value=config.nsfw_system, label='NSFW 提示词', lines=1)
        jailbreak_system = gr.TextArea(value=config.jailbreak_system, label='越狱提示词', lines=1)

        with gr.Row():
            with gr.Column():
                role_file = gr.File(label="角色列表", file_types=['.csv'])
            with gr.Column():
                dialogue_file = gr.File(label="对话列表", file_types=['.csv'])

        start_gen_btn = gr.Button("开始测试", variant="primary")
        markdown_url = gr.Markdown(value="## 测试结果飞书文档链接：", min_height=100)

    start_gen_btn.click(
        fn=start_gan,
        inputs=[
            ai_model, rounds, conv_length, open_translate, nsfw, jailbreak,
            role_file, dialogue_file,
            base_system, nsfw_system, jailbreak_system,
            temperature, max_tokens, presence_penalty
        ],
        outputs=[
            markdown_url
        ],
        scroll_to_output=True
    )
