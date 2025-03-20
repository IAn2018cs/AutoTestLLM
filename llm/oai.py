import json

import requests
from requests.adapters import HTTPAdapter, Retry

import config


class LLMClient:

    def __init__(
            self,
            api_key: str,
            api_url: str = None,
            timeout: float = None,
    ):
        self.api_url: str = api_url or "https://api.openai.com"
        self.api_key: str = api_key
        self.timeout: float = timeout
        retries = Retry(total=3, backoff_factor=3,
                        allowed_methods=["HEAD", "GET", "PUT", "OPTIONS", "POST"],
                        status_forcelist=[429])
        self.session = requests.Session()
        self.session.mount('http://', HTTPAdapter(max_retries=retries))
        self.session.mount('https://', HTTPAdapter(max_retries=retries))

    def _generate_request(self, model: str, messages: list[dict], **kwargs):
        url = (
            f"{self.api_url}/v1/chat/completions"
        )
        headers = {"Authorization": f"Bearer {kwargs.get('api_key', self.api_key)}"}

        timeout = kwargs.pop("timeout", self.timeout)

        payload = {
            "model": model,
            "messages": messages,
            "stream": False
        }
        for key, value in kwargs.items():
            payload[key] = value

        # print(json.dumps(payload, indent=4))

        if config.is_local_debug:
            return f"{len(messages)}"

        response = self.session.post(
            url,
            headers=headers,
            json=payload,
            timeout=timeout,
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
        return content

    def generate(self, model: str, messages: list[dict], **kwargs):
        content = self._generate_request(
            model=model, messages=messages, **kwargs
        )
        return content

    def close(self):
        self.session.close()
