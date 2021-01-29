import os
from typing import List, Dict, Optional
import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime, timedelta, timezone
from linebot import LineBotApi
from linebot.models import TextSendMessage

import config


# デバッグ
DEBUG = config.DEBUG

# 日本標準時
jst = timezone(timedelta(hours=+9), 'JST')

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


def get_rooms_data(now: datetime) -> Optional[Dict]:
    """
    現在の学習室の空席情報の取得

    Args:
        now(datetime): 現在時刻

    Returns:
        dict or None: 空席情報を取得した場合はDictを返す
    """
    print('### get_rooms ###')
    # Debug用変数
    # date = '20210129'
    # time = '1705'
    date = now.strftime('%Y%m%d')
    time = now.strftime('%H%M')
    rooms_ref = db.collection('rooms').document(date).get()
    if rooms_ref.exists:
        rooms_data = rooms_ref.to_dict().get(time)
        if not rooms_data:
            before = (now - timedelta(minutes=1)).strftime('%H%M')
            rooms_data = rooms_ref.to_dict().get(before)
        return rooms_data


def get_reservations(now: datetime) -> List[Optional[Dict]]:
    """
    空席通知予約を行ったユーザーと対象学習室名を取得
    予約から60分以上経った場合はusersコレクションからuser_idに基づくドキュメントを削除する

    Args:
        now(datetime): 現在時刻

    Returns:
        list
    """
    print('### get_users ###')
    reservations = []
    users_ref = db.collection('users').stream()
    for user in users_ref:
        doc_dic = user.to_dict()
        delta = int((now - doc_dic['reserve_time']).total_seconds() / 60)
        user_id = user.id
        if delta < 60:
            room_name = doc_dic['room_name']
            reservations.append({'user_id': user_id, 'room_name': room_name})
        else:
            delete_reservation(user_id)
    return reservations


def push_messages(user_id: str, room_name: str) -> None:
    """
    クライアントにメッセージを送信する

    Args:
        user_id(str): LINEのユーザーID
        room_name(str): 学習室名
    """
    message = TextSendMessage(text=f'【{room_name}】空席ができました。')
    line_bot_api.push_message(user_id, message)
    print(f'* Message has been pushed -> user_id: {user_id}')


def delete_reservation(user_id: str) -> None:
    """
    users内のuser_idに基づくドキュメントを削除する

    Args:
        user_id: LINEのユーザーID
    """
    db.collection('users').document(user_id).delete()
    print(f'* Deleted the document -> user_id: {user_id}')


def delete_all_reservations() -> None:
    """
    usersコレクション内のドキュメントを全て削除する
    """
    print('## delete_all_reservations ##')
    users_ref = db.collection('users')
    for user in users_ref.stream():
        users_ref.document(user.id).delete()
        print(f'* Deleted the document -> user_id: {user.id}')


def check(rooms: Dict, reservations: List) -> None:
    """
    空席通知予約を行った学習室に空席があったら通知する
    通知を行った場合通知を行ったユーザーをusersコレクションから削除する

    Args:
        rooms(dict): 各学習室の空席情報
        reservations(list)): 空席通知予約を行ったユーザーIDと学習室名
    """
    print('### check ###')
    for reservation in reservations:
        for room in rooms['data']:
            if reservation['room_name'] == room['name']:
                if room['seats_num'] > 0:
                    push_messages(reservation['user_id'], reservation['room_name'])
                    delete_reservation(reservation['user_id'])


def run(Request):

    now = datetime.now(jst)

    print('run...')
    print(now)

    # 学習室の座席情報の取得
    rooms = get_rooms_data(now)

    if rooms:
        # 空席通知予約を行ったユーザーと学習室名の取得
        reservations = get_reservations(now)
        # 予約ごとに空席を確認しメッセージ送信
        check(rooms, reservations)
    else:
        # 空席情報が取得できなかった場合（開館時間外）usersコレクション内の全てのドキュメントを削除する
        delete_all_reservations()

    return 'ok'


if DEBUG:
    run('ok')
