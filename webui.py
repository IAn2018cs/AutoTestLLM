import gradio as gr

import config
from uis.home.tab_home import build_home_ui
from uis.tab_ids import TabId


def build_webui():
    with gr.Blocks(theme=gr.themes.Soft()) as webui:
        gr.Markdown("# GPT 微调模型对话效果测试")
        with gr.Tabs(selected=TabId.HOME.value):
            build_home_ui()
    webui.launch(show_api=False, server_name="0.0.0.0", server_port=config.port)


if __name__ == '__main__':
    build_webui()
