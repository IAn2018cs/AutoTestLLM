# coding=utf-8
import os

from dotenv import load_dotenv

load_dotenv(override=True)

# openai
openai_api_host: str = os.getenv('OPENAI_API_HOST', default='https://api.openai.com/v1')
openai_api_key: str = os.getenv('OPENAI_API_KEY')

# gcp
gcp_project_id: str = os.getenv('GCP_PROJECT_ID')
gcp_private_key: str = os.getenv('GCP_PRIVATE_KEY')
gcp_sa_email: str = os.getenv('GCP_SA_EMAIL')

# feishu
feishu_app_id: str = os.getenv('FEISHU_APP_ID')
feishu_app_secret: str = os.getenv('FEISHU_APP_SECRET')

port: int = int(os.getenv('PORT'))

ft_models: list[str] = os.getenv('FT_MODELS').split(' ')
