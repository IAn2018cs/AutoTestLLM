import json

import requests


class OllamaLLMClient:

    def __init__(
            self,
            api_url: str = None,
            timeout: float = None
    ) -> None:
        self.api_url: str = api_url or "http://localhost:11434"
        self.timeout: float = timeout
        self.session = requests.Session()

    def _generate_request(
            self,
            model: str,
            messages: list,
            **kwargs,
    ):
        url = (
            f"{self.api_url}/api/chat"
        )

        payload = {
            "model": model,
            "messages": messages,
            "stream": False,
        }
        options = {}
        for key, value in kwargs.items():
            options[key] = value
        payload['options'] = options
        print(json.dumps(payload, indent=4))
        response = self.session.post(
            url,
            json=payload,
            timeout=kwargs.get("timeout", self.timeout),
            stream=False,
        )
        if response.status_code != 200:
            raise Exception(
                f"{response.status_code} {response.reason} {response.text}\n{json.dumps(messages, indent=4)}",
            )
        resp: dict = response.json()
        message = resp.get("message")
        content = message.get("content")
        prompt_tokens = resp.get("prompt_eval_count", 0)
        completion_tokens = resp.get("eval_count", 0)
        finish_reason = resp.get("done_reason", '')
        tokens_exceed = finish_reason in ["length", "max_tokens", "MAX_TOKENS"]
        return content, prompt_tokens, completion_tokens, tokens_exceed

    def generate(
            self,
            model: str,
            messages: list[dict],
            json_format: bool = False,
            **kwargs,
    ):
        content, prompt_tokens, completion_tokens, tokens_exceed = self._generate_request(
            model=model, messages=messages, **kwargs
        )
        return content, prompt_tokens, completion_tokens, tokens_exceed

    def close(self):
        self.session.close()
