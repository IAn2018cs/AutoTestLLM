import json
from json import JSONDecodeError
from typing import Dict, Any, Type

import instructor
import requests
from openai import OpenAI
from pydantic import BaseModel
from requests.adapters import HTTPAdapter, Retry

from llm.llm_tools import try_fix_json_format
from tools import extract_json


class AppBaseModel(BaseModel):
    class Config:
        @staticmethod
        def json_schema_extra(schema: Dict[str, Any], model: Type[Any]) -> None:
            for prop in schema.get('properties', {}).values():
                title = prop.pop('title', None)
                if title:
                    prop['description'] = title


class LLMClient:

    def __init__(
            self,
            api_key: str,
            api_url: str = None,
            timeout: float = None,
            temperature: float = 0.5,
    ) -> None:
        self.api_url: str = api_url or "https://api.openai.com"
        self.api_key: str = api_key
        self.temperature: float = temperature
        self.timeout: float = timeout
        retries = Retry(total=3, backoff_factor=1,
                        allowed_methods=["HEAD", "GET", "PUT", "OPTIONS", "POST"],
                        status_forcelist=[429, 503, 504, 529])
        self.session = requests.Session()
        self.session.mount('http://', HTTPAdapter(max_retries=retries))
        self.session.mount('https://', HTTPAdapter(max_retries=retries))
        self.client = instructor.from_openai(OpenAI(
            api_key=self.api_key,
            base_url=f"{self.api_url}/v1",
            timeout=self.timeout,
            max_retries=3,
        ))

    def _generate_request(
            self,
            model: str,
            messages: list,
            json_format: bool = False,
            **kwargs,
    ):
        # Get response
        url = (
            f"{self.api_url}/v1/chat/completions"
        )
        headers = {"Authorization": f"Bearer {kwargs.get('api_key', self.api_key)}"}

        payload = {
            "model": model,
            "messages": messages,
            "stream": False,
            # kwargs
            "temperature": kwargs.get("temperature", self.temperature),
        }
        if json_format:
            payload["response_format"] = {
                "type": "json_object"
            }
        for key, value in kwargs.items():
            payload[key] = value
        print(json.dumps(payload, indent=4))
        response = self.session.post(
            url,
            headers=headers,
            json=payload,
            timeout=kwargs.get("timeout", self.timeout),
            stream=False,
        )
        if response.status_code != 200:
            raise Exception(
                f"{response.status_code} {response.reason} {response.text}\n{json.dumps(messages, indent=4)}",
            )
        resp: dict = response.json()
        choices = resp.get("choices")
        delta = choices[0].get("message")
        content = delta["content"]
        usage = resp.get("usage", None)
        prompt_tokens = 0
        completion_tokens = 0
        if usage:
            prompt_tokens = usage.get("prompt_tokens", 0)
            completion_tokens = usage.get("completion_tokens", 0)
        finish_reason = choices[0].get("finish_reason")
        tokens_exceed = finish_reason in ["length", "max_tokens", "MAX_TOKENS"]
        return content, prompt_tokens, completion_tokens, tokens_exceed

    def _generate_instructor(
            self,
            model: str,
            messages: list,
            response_model: type[AppBaseModel],
            **kwargs,
    ):
        param = {
            "temperature": kwargs.get("temperature", self.temperature),
            "n": kwargs.get("n", 1),
        }
        if kwargs:
            param.update(kwargs)
        result_info, com = self.client.chat.completions.create_with_completion(
            model=model,
            response_model=response_model,
            messages=messages,
            **param
        )
        finish_reason = com.choices[0].finish_reason
        tokens_exceed = finish_reason in ["length", "max_tokens", "MAX_TOKENS"]
        prompt_tokens = com.usage.prompt_tokens
        completion_tokens = com.usage.completion_tokens
        if isinstance(result_info, AppBaseModel):
            content = result_info.model_dump_json()
        else:
            print(result_info)
            content = json.dumps(result_info)
        return content, prompt_tokens, completion_tokens, tokens_exceed

    def generate(
            self,
            model: str,
            messages: list[dict],
            json_format: bool = False,
            **kwargs,
    ):
        response_model = kwargs.pop("response_model", None)
        content, prompt_tokens, completion_tokens, tokens_exceed = self._generate_request(
            model=model, messages=messages, json_format=json_format, **kwargs
        )
        if not json_format:
            return content, prompt_tokens, completion_tokens, tokens_exceed
        try:
            # 校验 JSON 格式
            content = json.dumps(extract_json(content))
            return content, prompt_tokens, completion_tokens, tokens_exceed
        except JSONDecodeError as e:
            print(f"json error: {e}")
            fix_content = try_fix_json_format(content)
            if fix_content:
                return fix_content, prompt_tokens, completion_tokens, tokens_exceed
            if not (isinstance(response_model, type) and issubclass(response_model, AppBaseModel)):
                return content, prompt_tokens, completion_tokens, tokens_exceed
            return self._generate_instructor(model=model, messages=messages, response_model=response_model, **kwargs)

    def close(self):
        self.session.close()
        self.client.client.close()
