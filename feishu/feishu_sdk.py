# coding=utf-8
import json
import os
import time
from typing import Optional

import requests
from requests.adapters import HTTPAdapter, Retry
from requests_toolbelt import MultipartEncoder

import config


class FeiShuSdk(object):

    def __init__(self):
        self.TAG = 'FeiShuSdk'
        self.app_id = config.feishu_app_id
        self.app_secret = config.feishu_app_secret
        retries = Retry(total=3, backoff_factor=1,
                        allowed_methods=["HEAD", "GET", "PUT", "OPTIONS", "POST", "PATCH"],
                        status_forcelist=[429, 502, 503, 504, 500, 529])
        self.session = requests.Session()
        self.session.mount('http://', HTTPAdapter(max_retries=retries))
        self.session.mount('https://', HTTPAdapter(max_retries=retries))

    def __get_tenant_access_token__(self) -> str:
        url = 'https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal'
        headers = {'Content-Type': 'application/json'}
        params = {'app_id': self.app_id, 'app_secret': self.app_secret}
        response = requests.request('POST', url, params=params, headers=headers)
        token = response.json()
        return token['tenant_access_token']

    def __upload_file__(self, path: str, obj_type: str) -> Optional[str]:
        try:
            filename = os.path.basename(path)
            file_size = os.path.getsize(path)
            _, file_extension = os.path.splitext(filename)
            extension = file_extension.replace(".", "")

            url = "https://open.feishu.cn/open-apis/drive/v1/medias/upload_all"
            headers = {'Authorization': f'Bearer {self.__get_tenant_access_token__()}'}

            form = {
                'file_name': filename,
                'size': f"{file_size}",
                'parent_type': 'ccm_import_open',
                'extra': json.dumps({
                    "obj_type": obj_type,
                    "file_extension": extension
                }),
                'file': (open(path, 'rb'))
            }
            multi_form = MultipartEncoder(form)
            headers['Content-Type'] = multi_form.content_type
            response = self.session.post(url, headers=headers, data=multi_form)
            if response.ok:
                return response.json()['data']['file_token']
            print(f"__upload_file__ error: {response.text}")
            return None
        except Exception as e:
            print(f'__upload_file__ {e}')
            return None

    def __create_import_task__(self, file_token: str, file_name: str, file_extension: str, doc_type: str,
                               mount_key: str) -> Optional[str]:
        try:
            url = 'https://open.feishu.cn/open-apis/drive/v1/import_tasks'
            headers = {'Authorization': f'Bearer {self.__get_tenant_access_token__()}'}
            data = {
                'file_extension': file_extension,
                'file_token': file_token,
                'file_name': file_name,
                'point': {
                    'mount_key': mount_key,
                    'mount_type': 1
                },
                'type': doc_type
            }
            response = self.session.post(url, headers=headers, json=data)
            if response.ok:
                return response.json()['data']['ticket']
            print(f"__create_import_task__ error: {response.text}")
            return None
        except Exception as e:
            print(f'__create_import_task__ {e}')
            return None

    def __query_import_task__(self, ticket: str) -> Optional[dict]:
        try:
            url = f'https://open.feishu.cn/open-apis/drive/v1/import_tasks/{ticket}'
            headers = {'Authorization': f'Bearer {self.__get_tenant_access_token__()}'}
            response = self.session.get(url, headers=headers)
            if response.ok:
                result = response.json()['data']['result']
                if 'url' in result:
                    return result
            return None
        except Exception as e:
            print(f'__query_import_task__ {e}')
            return None

    def __query_cloud_root_folder__(self) -> Optional[str]:
        try:
            url = 'https://open.feishu.cn/open-apis/drive/explorer/v2/root_folder/meta'
            headers = {'Authorization': f'Bearer {self.__get_tenant_access_token__()}'}
            response = self.session.get(url, headers=headers)
            if response.ok:
                return response.json()['data']['token']
            print(f"__query_cloud_root_folder__ error: {response.text}")
            return None
        except Exception as e:
            print(f'__query_cloud_root_folder__ {e}')
            return None

    def __create_cloud_folder__(self, name: str, folder_token: str) -> Optional[str]:
        try:
            url = 'https://open.feishu.cn/open-apis/drive/v1/files/create_folder'
            headers = {'Authorization': f'Bearer {self.__get_tenant_access_token__()}'}
            data = {
                "name": name,
                "folder_token": folder_token
            }
            response = self.session.post(url, headers=headers, json=data)
            if response.ok:
                return response.json()['data']['token']
            print(f"__create_cloud_folder__ error: {response.text}")
            return None
        except Exception as e:
            print(f'__create_cloud_folder__ {e}')
            return None

    def __update_cloud_docs_permission__(self, token: str, obj_type: str) -> bool:
        try:
            url = f'https://open.feishu.cn/open-apis/drive/v1/permissions/{token}/public?type={obj_type}'
            headers = {'Authorization': f'Bearer {self.__get_tenant_access_token__()}'}
            data = {
                "external_access": True,
                "security_entity": "anyone_can_view",
                "comment_entity": "anyone_can_view",
                "share_entity": "anyone",
                "link_share_entity": "tenant_editable",
                "invite_external": False
            }
            response = self.session.patch(url, headers=headers, data=data)
            if response.ok:
                return True
            print(f"__update_cloud_docs_permission__ error: {response.text}")
            return False
        except Exception as e:
            print(f'__update_cloud_docs_permission__ {e}')
            return False

    def __query_all_files__(self, folder_token: Optional[str] = None, ori_list: Optional[list] = None,
                            page_token: Optional[str] = None) -> Optional[list]:
        try:
            url = f'https://open.feishu.cn/open-apis/drive/v1/files'
            headers = {'Authorization': f'Bearer {self.__get_tenant_access_token__()}'}
            params = {'page_size': 100}
            if folder_token:
                params['folder_token'] = folder_token
            if page_token:
                params['page_token'] = page_token
            response = self.session.get(url, headers=headers, params=params)
            data = response.json()
            has_more = data['data']['has_more']
            new_list = data['data']['files']
            if ori_list is None:
                ori_list = []
            ori_list.extend(new_list)
            if has_more:
                page_token = data['data']['page_token']
                return self.__query_all_files__(folder_token, ori_list, page_token)
            return ori_list
        except Exception as e:
            print(f'__query_all_files__ {e}')
            return None

    def create_cloud_docs(self, file_path: str, doc_type: str,
                          after_delete: bool = True) -> (Optional[str], Optional[str]):
        mount_key = None
        files = self.__query_all_files__()
        root_fold_name = 'AutoLLM2'
        for file in files:
            if file['name'] == root_fold_name:
                mount_key = file['token']
        if mount_key is None:
            root_folder_token = self.__query_cloud_root_folder__()
            mount_key = self.__create_cloud_folder__(root_fold_name, root_folder_token)

        filename = os.path.basename(file_path)
        filename_without_ext, file_extension = os.path.splitext(filename)
        extension = file_extension.replace(".", "")
        file_token = self.__upload_file__(file_path, doc_type)

        if file_token is None:
            print(f"create_cloud_docs error: file_token is None")
            return None, None
        if mount_key is None:
            print(f"create_cloud_docs error: mount_key is None")
            return None, None
        ticket = self.__create_import_task__(file_token, filename_without_ext, extension, doc_type, mount_key)
        if ticket is None:
            print(f"create_cloud_docs error: ticket is None")
            return None, None
        max_attempts = 10
        for attempt in range(max_attempts):
            result = self.__query_import_task__(ticket)
            if result is not None:
                url = result['url']
                token = result['token']
                obj_type = result['type']
                if self.__update_cloud_docs_permission__(token, obj_type) and after_delete:
                    os.remove(file_path)
                print(f"url: {url}")
                return url, token
            print(f"Attempt {attempt + 1}/{max_attempts} failed, retrying in 2 seconds...")
            time.sleep(2)  # Wait for 2 seconds before the next attempt
        print(f"create_cloud_docs error: fetch result failed")
        return None, None
