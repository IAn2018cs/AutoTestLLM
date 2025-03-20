import json
import random
from typing import Optional

import requests


class PolyLLMClient:

    def __init__(
            self,
            api_url: str = None,
            timeout: float = None
    ):
        self.api_url: str = api_url or "http://localhost:8000"
        self.timeout: float = timeout
        self.session = requests.Session()
        # 创建对象时，先创建用户
        self.user_cuid, self.user_session, self.user_uid = self._register_user()
        # 修改用户年龄
        self._edit_user()

    def _request(self, path: str, payload: dict, timeout: Optional[float] = None):
        url = (
            f"{self.api_url}/v1{path}"
        )
        response = self.session.post(
            url,
            json=payload,
            timeout=timeout if timeout else self.timeout
        )
        if response.status_code != 200:
            raise Exception(
                f"{response.status_code} {response.reason} {response.text}\n{json.dumps(payload, indent=4)}",
            )
        resp: dict = response.json()
        return resp

    def _register_user(self):
        result = self._request("/register", {})
        return result['cuid'], result['session'], result['uid']

    def _edit_user(self):
        self._request("/edit/user", {
            'cuid': self.user_cuid,
            'session': self.user_session,
            'uid': self.user_uid,
            'gender': random.choice([1, 2, 3]),
            'age': 3
        })

    def _generate_request(
            self,
            model: str,
            messages: list,
            **kwargs,
    ):
        timeout = kwargs.pop("timeout", self.timeout)
        scene_id = kwargs.pop("scene_id", 0)

        payload = {
            "model": "1",
            "messages": messages,
            "stream": False,
            "metadata": {
                "cuid": self.user_cuid,
                "session": self.user_session,
                "uid": self.user_uid,
                "scene_id": scene_id
            }
        }

        resp: dict = self._request("/chat/completions", payload, timeout)
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
