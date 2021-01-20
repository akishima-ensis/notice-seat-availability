# notice-seat-availability

![deploy](https://github.com/akishima-ensis/notice-seat-availability/workflows/deploy/badge.svg)

## About
アキシマエンシス（昭島市教育福祉総合センター）の学習室において、空席ができた場合にLINE通知するスクリプトです。これは以下のリポジトリのLINEBotで利用されています。

・学習室の空席状況をリアルタイムで取得できるLINE Bot（[seat-availability-check-linebot](https://github.com/akishima-ensis/seat-availability-check-linebot)）



## How it works
CloudFirestoreから通知予約をしたユーザーのID、空席予約を行った学習室名、現在の学習室の空席状況を取得し、空席があった場合に通知するスクリプトです。このスクリプトはCloudFunctionsにデプロイされており、CloudSchedulerを用いて開館時間（10:00〜20:00）に１分間隔で実行されます。

![](https://user-images.githubusercontent.com/34241526/105141132-08477c00-5b3c-11eb-8c24-3e2c896eaf48.png)
[diagrams.net](https://app.diagrams.net/)