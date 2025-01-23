# coding=utf-8
import json
import os
import time

import jwt
import requests

from utils.tools import create_path
from utils.tools import root_relative_path


def create_jwt_token(private_key: str, sa_email: str, scope: str, valid_for_sec: int = 3600) -> dict:
    now = int(time.time())
    exp = now + valid_for_sec
    payload = {
        "iss": sa_email,
        "scope": scope,
        "aud": "https://www.googleapis.com/oauth2/v4/token",
        "exp": exp,
        "iat": now
    }

    headers = {
        "alg": "RS256",
        "typ": "JWT"
    }

    return {
        "exp": exp,
        "token": jwt.encode(payload, private_key, algorithm='RS256', headers=headers)
    }


def get_access_token(private_key: str, sa_email: str,
                     scope: str = 'https://www.googleapis.com/auth/cloud-platform') -> str:
    now = int(time.time())
    auth_root_path = root_relative_path('auth')
    create_path(auth_root_path)
    token_path = f"{auth_root_path}/token.json"
    access_token_info = None
    if os.path.exists(token_path):
        with open(token_path, 'r') as f:
            access_token_info = json.loads(f.read())
    if access_token_info and access_token_info['exp'] > now:
        return access_token_info['access_token']

    token_info = create_jwt_token(private_key, sa_email, scope)
    exp = token_info['exp']
    jwt_token = token_info['token']

    response = requests.post(
        "https://www.googleapis.com/oauth2/v4/token",
        data={
            'grant_type': 'urn:ietf:params:oauth:grant-type:jwt-bearer',
            'assertion': jwt_token
        }
    )

    response_data = response.json()

    if 'access_token' not in response_data:
        raise Exception(f"Failed to retrieve access token: {response_data}")

    access_token = response_data['access_token']
    with open(token_path, 'w') as f:
        f.write(json.dumps({'exp': exp, 'access_token': access_token}))
    return access_token
