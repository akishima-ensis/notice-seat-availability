import os
import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime, timedelta, timezone
from linebot import LineBotApi
from linebot.models import TextSendMessage


# linebotsdk初期化
LINE_CHANNEL_ACCESS_TOKEN = os.environ.get('LINE_CHANNEL_ACCESS_TOKEN')
line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)

# firebase初期化
cred_key = 'sa_key.json'
if os.path.exists(cred_key):
    cred = credentials.Certificate(cred_key)
    firebase_admin.initialize_app(cred)
else:
    firebase_admin.initialize_app()
db = firestore.client()


rooms = {}
reservations = []
to = []
messages = []


def init_var():
    print('### init_var ###')
    global rooms, reservations, to, messages
    rooms = {}
    reservations = []
    to = []
    messages = []


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


def create_message(room_name):
    return TextSendMessage(text=f'【{room_name}】空席ができました。')


def push_messages():
    print('### push_messages ###')
    line_bot_api.multicast(to, messages)


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
    global to, messages
    print('### check ###')
    if rooms:
        for reservation in reservations:
            for room in rooms['data']:
                if reservation['room_name'] == room['name']:
                    print(room)
                    if room['seats_num'] > 0:
                        to.append(reservation['user_id'])
                        messages.append(create_message(reservation['room_name']))
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

    # 予約ごとに空席を確認
    check()

    # メッセージの送信
    if to:
        push_messages()

    return 'ok'


# debug
# run('ok')
