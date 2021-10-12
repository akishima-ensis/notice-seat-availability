from datetime import datetime

from src import jst, DEBUG
from src.script import get_rooms, get_reservations, check, delete_all_reservations


def run(Request):

    now = datetime.now(jst)

    print('run...')
    print(now)

    # 学習室の座席情報の取得
    rooms = get_rooms(now)

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
