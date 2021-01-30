import firebase_admin
from firebase_admin import credentials, firestore
from datetime import timedelta, timezone
from linebot import LineBotApi

import config


# デバッグ
DEBUG = config.DEBUG

# 日本標準時
jst = timezone(timedelta(hours=+9), 'JST')

# line-bot-sdk初期化
LINE_CHANNEL_ACCESS_TOKEN = config.LINE_CHANNEL_ACCESS_TOKEN
line = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)

# firestore初期化
if DEBUG:
    SERVICE_ACCOUNT_KEY = config.SERVICE_ACCOUNT_KEY
    cred = credentials.Certificate(SERVICE_ACCOUNT_KEY)
    firebase_admin.initialize_app(cred)
else:
    firebase_admin.initialize_app()
db = firestore.client()
