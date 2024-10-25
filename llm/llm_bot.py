# coding=utf-8
from typing import Optional

import config
from llm.V4 import LLMClient, AppBaseModel


class LLMBot:
    def __init__(self):
        self.TAG = 'LLMBot'
        self.llm_client = LLMClient(config.openai_api_key, config.openai_api_host, timeout=300)

    def generate(self, model_id: str, system_prompt: Optional[str], prompt,
                 json_format: bool = False, response_model: type[AppBaseModel] = None,
                 other_config: dict = None) -> Optional[str]:
        result = None
        try:
            if isinstance(prompt, str):
                messages = []
                if system_prompt:
                    messages.append({
                        "role": "system",
                        "content": system_prompt
                    })
                messages.append({
                    "role": "user",
                    "content": prompt
                })
            else:
                messages = prompt

            kwargs = {
                "response_model": response_model
            }
            if other_config:
                kwargs.update(other_config)
            result, input_tokens, output_tokens, tokens_exceed = self.llm_client.generate(
                model=model_id,
                messages=messages,
                json_format=json_format,
                **kwargs
            )
            return result
        except Exception as e:
            error_msg = f"\n**generate error**\nmodel_id: {model_id}\nresult: {result}\nerror: {e}"
            print(error_msg)
            return None

    def close(self):
        self.llm_client.close()
