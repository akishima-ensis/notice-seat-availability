from typing import Any, List, Dict
from datetime import datetime, timedelta
from linebot.models import TextSendMessage

from src import db, line


ROOM_NAME = {
  0: '学習席（有線LAN有）',
  1: '学習席',
  2: '研究個室',
  3: 'インターネット・DB席',
  4: 'グループ学習室',
  5: 'ティーンズ学習室',
}


def get_rooms(now: datetime) -> Any:
    """
    現在の学習室の空席情報の取得
    現在の学習室の空席状況がなかった場合は1分前の空席情報を取得
    それもなかったらNoneを返す

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
    else:
        None


def get_reservations(now: datetime) -> List[Dict[str, Any]]:
    """
    空席通知予約を行ったユーザーと対象学習室名を取得
    予約から60分以上経った場合はreservationsコレクションからuser_idに基づくドキュメントを削除する

    Args:
        now(datetime): 現在時刻

    Returns:
        list
    """
    print('### get_reservations ###')
    reservations = []
    reservations_ref = db.collection('reservations').stream()
    for user in reservations_ref:
        doc_dic = user.to_dict()
        delta = int((now - doc_dic['reservation_time']).total_seconds() / 60)
        user_id = user.id
        if delta < 60:
            room_num = doc_dic['room_num']
            reservations.append({'user_id': user_id, 'room_num': room_num})
        else:
            delete_reservation(user_id)
    return reservations


def send_message(user_id: str, room_name: str) -> None:
    """
    クライアントにメッセージを送信する

    Args:
        user_id(str): LINEのユーザーID
        room_name(str): 学習室名
    """
    message = TextSendMessage(text=f'【{room_name}】空席ができました。')
    line.push_message(user_id, message)
    print(f'* Message has been pushed -> user_id: {user_id}')


def delete_reservation(user_id: str) -> None:
    """
    reservationsコレクション内のuser_idに基づくドキュメントを削除する

    Args:
        user_id: LINEのユーザーID
    """
    db.collection('reservations').document(user_id).delete()
    print(f'* Deleted the document -> user_id: {user_id}')


def delete_all_reservations() -> None:
    """
    reservationsコレクション内のドキュメントを全て削除する
    """
    print('## delete_all_reservations ##')
    reservations_ref = db.collection('reservations')
    for user in reservations_ref.stream():
        reservations_ref.document(user.id).delete()
        print(f'* Deleted the document -> user_id: {user.id}')


def find_vacancy_and_send_message(rooms: Dict, reservations: List) -> None:
    """
    空席通知予約を行った学習室に空席があったら通知する
    通知を行ったユーザーをreservationsコレクションから削除する

    Args:
        rooms(dict): 各学習室の空席情報
        reservations(list)): 空席通知予約を行ったユーザーIDと学習室名
    """
    print('### check ###')
    for reservation in reservations:
        room_num = reservation['room_num']
        room = rooms['data'][room_num]
        if room['seats_num'] > 0:
            send_message(reservation['user_id'], ROOM_NAME[room])
            delete_reservation(reservation['user_id'])
