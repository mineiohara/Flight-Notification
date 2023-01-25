from linebot import LineBotApi
from linebot.models import TextSendMessage
import flightradar24
from datetime import datetime
import time
import MySQLdb

def sendMessage(message: str, userID, displayName):
    line_bot_api.push_message(userID, messages=TextSendMessage(text=message))
    print("メッセージを" + displayName + "に送信しました。")


def main():
    while True:
        print(datetime.now().strftime('%Y-%m-%d %H:%M'))

        # Databaseに接続
        connection = MySQLdb.connect(
            host='mineiohara.mysql.pythonanywhere-services.com',
            user='mineiohara',
            passwd='A010203a0856@',
            db='mineiohara$UserConfiguration')
        cursor = connection.cursor()
        # すべてのデータを取得
        cursor.execute('SELECT * FROM users')

        # Databaseからはユーザー個分のデータが返ってくる
        for (userID, trackFlightNumber, alarm5, alarm10, alarm30) in cursor:
            if trackFlightNumber is None:
                continue

            displayName = line_bot_api.get_profile(userID).display_name
            print("Tracking: " + trackFlightNumber + " for " + displayName)

            # APIのエラーがたまに発生するので、エラーによってプログラムが止まらないように対策
            try:
                flight = fr.get_flight(trackFlightNumber)
            except Exception:
                continue

            for data in flight["result"]["response"]["data"]:
                if data["status"]["generic"]["status"]["text"] == "estimated" and data["time"]["estimated"]["arrival"] is not None:
                    ETA = datetime.fromtimestamp(data["time"]["estimated"]["arrival"])
                    delta = (ETA - datetime.now()).seconds // 60

                    if delta <= 5 and alarm5:
                        sendMessage("【" + trackFlightNumber + "】\nあと5分以内に到着します！", userID, displayName)
                        cursor.execute('UPDATE users SET trackFlightNumber = null WHERE userID = %s', (userID,))
                        cursor.execute('UPDATE users SET alarm5 = false WHERE userID = %s', (userID,))
                        connection.commit()

                    elif delta <= 10 and alarm10:
                        sendMessage("【" + trackFlightNumber + "】\nあと10分以内に到着します！", userID, displayName)
                        cursor.execute('UPDATE users SET alarm10 = false WHERE userID = %s', (userID,))
                        connection.commit()

                    elif delta <= 30 and alarm30:
                        sendMessage("【" + trackFlightNumber + "】\nあと30分以内に到着します！", userID, displayName)
                        cursor.execute('UPDATE users SET alarm30 = false WHERE userID = %s', (userID,))
                        connection.commit()

                    print("Arrive in", delta, "mins")
                    print()
                    break

        print()
        connection.close()
        time.sleep(60)


if __name__ == "__main__":
    line_bot_api = LineBotApi("CHANNEL_ACCESS_TOKEN")
    fr = flightradar24.Api()

    main()