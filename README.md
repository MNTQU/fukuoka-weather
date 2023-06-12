# fukuoka-weather
福岡市の天気予報をSlackに送る

## 準備
Slack APIのトークンが必要

## 使い方
crontabでスケジュールを設定
```
$ crontab -e
```
(例だと6時間ごと)
```
* /6 * * * python fukuoka-weather.py
```