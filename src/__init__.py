import firebase_admin
from firebase_admin import firestore
from datetime import timedelta, timezone
from linebot import LineBotApi

from src import config

# 環境変数
DEBUG = config.DEBUG
LINE_CHANNEL_ACCESS_TOKEN = config.LINE_CHANNEL_ACCESS_TOKEN
SERVICE_ACCOUNT_KEY = config.SERVICE_ACCOUNT_KEY

# 日本標準時
jst = timezone(timedelta(hours=+9), 'JST')

# line-bot-sdk初期化
line = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)

# firestore初期化
if DEBUG:
    from firebase_admin import credentials
    cred = credentials.Certificate(SERVICE_ACCOUNT_KEY)
    firebase_admin.initialize_app(cred)
else:
    firebase_admin.initialize_app()
db = firestore.client()
