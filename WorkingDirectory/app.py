from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage, TemplateSendMessage, PostbackAction, ButtonsTemplate, PostbackEvent
import flightradar24
import datetime
import MySQLdb


app = Flask(__name__, static_url_path="/static")
line_bot_api = LineBotApi("CHANNEL_ACCESS_TOKEN")
handler = WebhookHandler("CHANNEL_SECRET")

#Webhook初期化
@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        print("Invalid signature. Please check your channel access token/channel secret.")
        abort(400)

    return 'OK'


# 画像を便名から選択
def imageSelector(flightNum):
    if flightNum == "CI":
        return "ChinaAirlines"
    elif flightNum == "BR":
        return "EvaAir"
    elif flightNum == "IT":
        return "TigerAir"
    elif flightNum == "NH":
        return "ANA"
    elif flightNum == "JL":
        return "JapanAirlines"
    elif flightNum == "CX":
        return "CatheyPacific"
    elif flightNum == "MM":
        return "Peach"
    else:
        return "Others"


# メッセージを受信したときの処理
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    fr = flightradar24.Api()
    flight = fr.get_flight(event.message.text)

    # 該当のフライト検索結果がある場合
    if flight["result"]["response"]["item"]["current"] > 0:
        sendMessage = TextSendMessage(text="現在オンラインのフライトがありません。")

        for data in flight["result"]["response"]["data"]:
            # 有効なフライトの場合
            if data["status"]["generic"]["status"]["text"] == "estimated" and data["time"]["estimated"]["arrival"] is not None:
                imageURL = imageSelector(event.message.text[:2])
                sendMessage = TemplateSendMessage(
                    alt_text='Buttons template',
                    template=ButtonsTemplate(
                        thumbnail_image_url= "https://..." + imageURL + "jpg",
                        title= event.message.text + " " + data["airport"]["origin"]["code"]["iata"] + " → " + data["airport"]["destination"]["code"]["iata"],
                        text='トラッキングしますか？',
                        image_size="cover",
                        actions=[
                            PostbackAction(label='はい', display_text='はい', data='True' + event.message.text),
                            PostbackAction(label='いいえ', display_text='いいえ', data='False')
                        ]
                    )
                )
                break
    
    # 該当のフライトがない場合
    else:
        sendMessage = TextSendMessage(text="フライトが存在しません。")


    line_bot_api.reply_message(event.reply_token, sendMessage)


# ポストバックを受けた時の処理
@handler.add(PostbackEvent)
def on_postback(event):
    userID = line_bot_api.get_profile(event.source.user_id).user_id

    # トラッキングする場合
    if "True" in event.postback.data:
        # Databaseに接続
        connection = MySQLdb.connect(
            host='mineiohara.mysql.pythonanywhere-services.com',
            user='mineiohara',
            passwd='A010203a0856@',
            db='mineiohara$UserConfiguration')
        cursor = connection.cursor()

        # データ取得
        sql = ('SELECT userID, trackFlightNumber FROM users WHERE userID = %s')
        cursor.execute(sql, (userID,))

        # 新規ユーザーの場合
        if len(cursor.fetchall()) == 0:
            cursor.execute('INSERT INTO users(userID, trackFlightNumber, alarm5, alarm10, alarm30) VALUES(%s, %s, true, true, true)', (userID, event.postback.data[4:],))
            connection.commit()

        # 既存のユーザーの場合
        else:
            cursor.execute('UPDATE users SET trackFlightNumber = %s WHERE userID = %s', (event.postback.data[4:], userID, ))
            cursor.execute('UPDATE users SET alarm5 = true WHERE userID = %s', (userID, ))
            cursor.execute('UPDATE users SET alarm10 = true WHERE userID = %s', (userID, ))
            cursor.execute('UPDATE users SET alarm30 = true WHERE userID = %s', (userID, ))
            connection.commit()

        line_bot_api.push_message(userID, messages=TextSendMessage(text="トラッキングを開始しました。"))
        
        # 希望のフライトの検索
        fr = flightradar24.Api()
        flight = fr.get_flight(event.postback.data[4:])

        for data in flight["result"]["response"]["data"]:

            # 有効なフライトの場合
            if data["status"]["generic"]["status"]["text"] == "estimated" and data["time"]["estimated"]["arrival"] is not None:
                print(data["time"]["estimated"]["arrival"])
                ETA = datetime.datetime.fromtimestamp(data["time"]["estimated"]["arrival"])
                delta = (ETA - datetime.datetime.now()).seconds // 60
                ETA = ETA + datetime.timedelta(hours=9)

                # アラームの初期化
                if delta < 30:
                    cursor.execute('UPDATE users SET alarm30 = false WHERE userID = %s', (userID, ))

                if delta < 10:
                    cursor.execute('UPDATE users SET alarm10 = false WHERE userID = %s', (userID, ))

                if delta < 5:
                    sendMessage = TextSendMessage(text="まもなく到着します！")
                    cursor.execute('UPDATE users SET alarm5 = false WHERE userID = %s', (userID, ))
                    cursor.execute('UPDATE users SET trackFlightNumber = null WHERE userID = %s', (userID,))

                else:
                    sendMessage = TextSendMessage(text="【到着予定時刻】\n" + ETA.strftime('%m月%d日 %H:%M'))

                connection.commit()
                line_bot_api.push_message(userID, messages=sendMessage)

    # トラッキングしない場合
    else:
        line_bot_api.push_message(userID, messages=TextSendMessage(text="なんやねん。"))


if __name__ == "__main__":
    app.run()