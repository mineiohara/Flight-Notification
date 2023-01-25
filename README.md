# Flight-Notification-LINE-API  
LINE APIを用いてフライトをトラッキングして、到着のN分前に通知をしてくれます。PythonのFlaskでWebhookを実装し、その他の処理は別のPythonプログラムに任せています。

# 使い方  
①LINEを追加後、ボットに便名を送信します。例:NH879  
②トラッキングするかどうか聞かれるので、はいをタップ。いいえをタップすると・・・  
③トラッキングが開始されたら、デフォルトでは到着時刻の5、10、30分前に通知を送信してくれます。  
※オンラインのフライトのみトラッキングします。また国際線のみトラッキングできます。

# LINEでボットを友達に追加する  
![flightNotificationBot](https://user-images.githubusercontent.com/42444881/214592142-7046f83d-c9f4-4d8b-84be-895e26140c03.png)
