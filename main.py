import os
import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime, timedelta, timezone
from linebot import LineBotApi
from linebot.models import TextSendMessage

import config

# デバッグ
DEBUG = config.DEBUG

# line-bot-sdk初期化
LINE_CHANNEL_ACCESS_TOKEN = os.environ.get('LINE_CHANNEL_ACCESS_TOKEN')
line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)

# firestore初期化
if DEBUG:
    SERVICE_ACCOUNT_KEY = config.SERVICE_ACCOUNT_KEY
    cred = credentials.Certificate(SERVICE_ACCOUNT_KEY)
    firebase_admin.initialize_app(cred)
else:
    firebase_admin.initialize_app()
db = firestore.client()

rooms = {}
reservations = []


def init_var():
    print('### init_var ###')
    global rooms, reservations
    rooms = {}
    reservations = []


def get_time():
    jst = timezone(timedelta(hours=+9), 'JST')
    return datetime.now(jst)


def get_rooms():
    print('### get_rooms ###')
    global rooms
    now = get_time()
    date = now.strftime('%Y%m%d')
    time = now.strftime('%H%M')
    rooms_ref = db.collection('rooms').document(date).get()
    if rooms_ref.exists:
        rooms = rooms_ref.to_dict().get(time)
        if not rooms:
            before = (now - timedelta(minutes=1)).strftime('%H%M')
            rooms = rooms_ref.to_dict().get(before)


def get_reservations():
    print('### get_users ###')
    global reservations
    now = get_time()
    users_ref = db.collection('users')
    query_ref = users_ref.where('reserved', '==', True)
    docs = query_ref.stream()
    for doc in docs:
        doc_dic = doc.to_dict()
        delta = int((now - doc_dic['reserve_time']).total_seconds() / 60)
        user_id = doc.id
        if delta < 60:
            room_name = doc_dic['room_name']
            reservations.append({
                'user_id': user_id,
                'room_name': room_name
            })
        else:
            users_ref.document(user_id).update({'reserved': False})


def push_messages(user_id, room_name):
    message = TextSendMessage(text=f'【{room_name}】空席ができました。')
    line_bot_api.push_message(user_id, message)
    print(f'* pushed --> {user_id}')


def delete_reservation(user_id):
    user_doc = db.collection('users').document(user_id)
    user_doc.update({'reserved': False})
    print(f'* delete reservation -> {user_id}')


def delete_all_reservation():
    print('### delete_all_reservation ###')
    users_ref = db.collection('users')
    query_ref = users_ref.where('reserved', '==', True).stream()
    for user in query_ref:
        users_ref.document(user.id).update({'reserved': False})


def check():
    print('### check ###')
    if rooms:
        for reservation in reservations:
            for room in rooms['data']:
                if reservation['room_name'] == room['name']:
                    if room['seats_num'] > 0:
                        push_messages(reservation['user_id'], reservation['room_name'])
                        delete_reservation(reservation['user_id'])
    else:
        delete_all_reservation()


def run(Request):
    print('run...')

    # グローバル変数の初期化
    init_var()

    # 学習室の座席情報の取得
    get_rooms()

    # 通知を行うユーザーの抽出
    get_reservations()

    # 予約ごとに空席を確認しメッセージ送信
    check()

    return 'ok'


if DEBUG:
    run('ok')
