import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
import config

def weather_judge(max_temp, min_temp, prob_precip):
    max_temp = int(max_temp)
    min_temp = int(min_temp)
    if max_temp >= 30 :
        temp_status = "日中は、非常に暑く過ごしにくいです。"
    elif 25 <= max_temp < 30 :
        temp_status = "日中は、暑くやや過ごしにくいです。"
    elif 20 <= max_temp < 25 :
        temp_status = "日中は、過ごしやすいです。"
    elif 15 <= max_temp < 20 :
        temp_status = "日中は、肌寒く軽い上着が必要なくらいです。"
    else :
        temp_status = "日中は、寒くコートなどの重い上着が必要です。"

    if min_temp >=25:
        temp_status += "夜中は、非常に暑く過ごしにくいです"
    elif 20 <= min_temp < 25 :
        temp_status += "夜中は、暑くやや過ごしにくいです"
    elif 15 <= min_temp < 20 :
        temp_status += "夜中は、過ごしやすいです"
    elif 10 <= min_temp < 15 :
        temp_status += "夜中は、肌寒く軽い上着が必要なくらいです"
    else :
        temp_status += "夜中は、寒くコートなどの重い上着が必要です"

    if int(prob_precip) == 0:
        prob_status = "雨は降りません。```\n"
    elif int(prob_precip) < 20 and int(prob_precip) > 0:
        prob_status = "雨の心配は少ないです。```\n"
    elif int(prob_precip) >= 20 and int(prob_precip) < 50:
        prob_status = "少し雨模様が心配です。```\n"
    elif int(prob_precip) >= 50 and int(prob_precip) < 80:
        prob_status = "おそらく雨が降ります。```\n<!channel>\n"
    else:
        prob_status = "雨が降ります。```\n<!channel>\n"

    #気温の過ごしやすさと、降水確率の不安度をテキスト化したものを返す
    return [temp_status, prob_status]

#天気予報をスクレイピングする関数
def weather_scraping():
    #URLを指定し
    url = "https://weather.yahoo.co.jp/weather/"
    #requestsでGETする
    html = requests.get(url, timeout=10.0)
    #そしてbs4のパーサーに食わせる
    soup = BeautifulSoup(html.content, "html.parser")

    weather_time= soup.select_one('#navHeader > span.time').text

    #最高気温は以下のセレクタで取れる（福岡:8210）
    max_temp = soup.select_one('#map > ul > li.point.pt8210 > a > dl > dd > p.temp > em.high').text
    #最低気温も同様
    min_temp = soup.select_one('#map > ul > li.point.pt8210 > a > dl > dd > p.temp > em.low').text
    #降水確率も同様
    prob_precip = soup.select_one('#map > ul > li.point.pt8210 > a > dl > dd > p.precip').text.replace('%', '')

    #先ほどの気温と降水確率の判定を呼び出し
    weather_status = weather_judge(max_temp, min_temp, prob_precip)

    #辞書にまとめて返す
    total_status = {'weather_status': weather_status, 'temps': [max_temp, min_temp, prob_precip],'time': weather_time}
    return total_status


url = "https://weather.yahoo.co.jp/weather/jp/40/8210.html"
# Slack通知メッセージ用
fields = []
# スクレイピング
html = requests.get(url)
soup = BeautifulSoup(html.content, "html.parser")
# 場所
title = soup.find('title').text;idx = title.find(' -')
place = title[:idx]

main = soup.find('div', id='wrapper').find('div', id='contents').find('div', id='contents-body').find('div', id='main')

# 現時点の天気情報取得
todays_weather = main.find('div', class_='forecastCity').find('table').find('tr').find('td').find('div')
tomorrow_weather = main.find('div', class_='forecastCity').find('table').find('tr').find('td').find_next_sibling('td').find('div')

# 日付
date_today = todays_weather.find('p', class_='date').text.replace('\n', '').strip()
#print(date_today)
date_tomorrow = tomorrow_weather.find('p', class_='date').text.replace('\n', '').strip()
#print(date_tomorrow)

# 天気情報
weather_text_today = todays_weather.find('img')['alt'].replace('\n', '')
weather_text_tomorrow = tomorrow_weather.find('img')['alt'].replace('\n', '')
# 天気画像
weather_image_url_today = todays_weather.find('img')['src']
weather_image_url_tomorrow = tomorrow_weather.find('img')['src']
# 降水情報取得
table_today = todays_weather.find('table')
table_tomorrow = tomorrow_weather.find('table')
# 時間帯
time_rows = table_today.find('tr', class_='time').find_all('td')
time = [i.text for i in time_rows] # ['0-6', '6-12', '12-18', '18-24']
time_text = '|'.join(time)
# 降水確率
precip_rows_today = table_today.find('tr', class_='precip').find_all('td')
precip_today = [i.text for i in precip_rows_today]
precip_text_today = '|'.join(precip_today)

precip_rows_tomorrow = table_tomorrow.find('tr', class_='precip').find_all('td')
precip_tomorrow = [i.text for i in precip_rows_tomorrow]
precip_text_tomorrow = '|'.join(precip_tomorrow)

#先ほどの気温と降水確率の判定を辞書化したものを呼び出し
status = weather_scraping()

#任意のテキストに落とし込む
query = f"{status['time']}の福岡市の天気予報\n```最高気温は{status['temps'][0]}度、最低気温は{status['temps'][1]}度、\n{status['weather_status'][0]}。\n降水確率は{status['temps'][2]}％で、{status['weather_status'][1]}```{date_today}{weather_text_today}\n時間|{time_text}\n降水|{precip_text_today}\n```\n"
query2 = f"```{date_tomorrow}{weather_text_tomorrow}\n時間|{time_text}\n降水|{precip_text_tomorrow}\n```"
#print(query)

# Slackにメッセージを送信する関数
def send_message(channel, message, attachments=None, thread_ts=None):
    client = WebClient(token=config.slack_token) #ここに自分のSlack APIトークンを入力してください
    try:
        response = client.chat_postMessage(
            channel=channel,
            text=message,
            attachments=attachments,
            thread_ts=thread_ts
        )
        print("Message sent: ", response['ts'])
    except SlackApiError as e:
        print("Error sending message: ", e)

#slackのタイムスタンプを得る関数
def get_previous_message_timestamp(channel):
    client = WebClient(token=config.slack_token)
    try:
        response = client.conversations_history(
            channel=channel,
            limit=1
        )
        messages = response['messages']
        if len(messages) > 0:
            previous_message = messages[0]
            return previous_message['ts']
    except SlackApiError as e:
        print("Error retrieving previous message: ", e)

attachments_today = [
    {
        "blocks": [
            {
                "type": "image",
                "image_url": weather_image_url_today,
                "alt_text": "weather_image_url_today"
            }
        ]
    }
]

attachments_tomorrow = [
    {
        "blocks": [
            {
                "type": "image",
                "image_url": weather_image_url_tomorrow,
                "alt_text": "weather_image_url_tomorrow"
            }
        ]
    }
]

send_message(config.slack_channel, query, attachments=attachments_today)
previous_message_ts = get_previous_message_timestamp(channel=config.slack_channel)
send_message(config.slack_channel, query2, attachments=attachments_tomorrow, thread_ts=previous_message_ts)
