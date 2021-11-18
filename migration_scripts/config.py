from json import load
import os

from dotenv import load_dotenv

load_dotenv()

CTFL_MGMT_API_KEY = os.environ["SYNC_CONTENTFUL_API_KEY"]
CTFL_SPACE_ID = os.environ["SYNC_CONTENTFUL_SPACE_ID"]
CTFL_ENV_ID = os.environ["SYNC_CONTENTFUL_ENVIRONMENT"]
DEFAULT_LOCALE = os.environ["SYNC_CONTENTFUL_DEFAULT_LOCALE"]
