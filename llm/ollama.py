import json

import requests

import config


class OllamaLLMClient:

    def __init__(
            self,
            api_url: str = None,
            timeout: float = None
    ):
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

        timeout = kwargs.pop("timeout", self.timeout)

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

        if config.is_local_debug:
            return f"{len(messages)}"

        response = self.session.post(
            url,
            json=payload,
            timeout=timeout,
            stream=False,
        )
        if response.status_code != 200:
            raise Exception(
                f"{response.status_code} {response.reason} {response.text}\n{json.dumps(messages, indent=4)}",
            )
        resp: dict = response.json()
        message = resp.get("message")
        content = message.get("content")
        return content

    def generate(self, model: str, messages: list[dict], **kwargs):
        content = self._generate_request(
            model=model, messages=messages, **kwargs
        )
        return content

    def close(self):
        self.session.close()
