# Discord Webhook AQI 通知模組規格

## 1. 目的與範圍

本模組只負責在上游確認取得「新的一批空氣品質資料」後，將資料依
`county`（縣市）分組，透過 Discord Webhook 發送各縣市所有監測站的
AQI，並將每次發送結果寫入 `dc_webhook.log`。

不負責：取得政府 API、判斷資料是否為新資料、MySQL
儲存、前端功能，以及自行計算 AQI 等級。

## 2. 必要輸入資料

每筆資料至少需要：

  欄位            用途
  --------------- ---------------------
  `county`        縣市分組
  `sitename`      監測站名稱
  `aqi`           AQI
  `status`        政府提供的 AQI 狀態
  `publishtime`   資料發布時間

範例：

``` json
{
  "county": "臺中市",
  "sitename": "西屯",
  "aqi": "60",
  "status": "普通",
  "publishtime": "2026/09/22 08:00:00"
}
```

## 3. AQI 狀態規則

直接使用政府資料的 `status`，不根據 AQI 數值重新計算。支援：

-   良好
-   普通
-   對敏感族群不健康
-   對所有族群不健康
-   非常不健康
-   危害

`status` 為空或不屬於上述六種狀態時顯示 `未知`，不得自行推測。

## 4. 觸發條件

上游確認資料為新資料後才呼叫通知模組：

``` text
上游取得資料
→ 確認為新資料
→ 呼叫 Discord 通知模組
→ 按縣市分組
→ 發送 Discord
```

通知模組本身不判斷資料是否更新。

## 5. 分組與發送規則

1.  使用 `county` 將所有測站分組。
2.  每個縣市建立一則獨立 Discord 訊息。
3.  一個縣市的一次發送失敗，不得中止其他縣市。
4.  實際 Webhook request 數量等於該批資料中的縣市數量。

## 6. Discord 訊息格式

第一版使用純文字：

``` text
【{county} 空氣品質】

更新時間：{publishtime}

{sitename}｜AQI {aqi}｜{status}
{sitename}｜AQI {aqi}｜{status}
...
```

範例：

``` text
【臺中市 空氣品質】

更新時間：2026/09/22 08:00:00

豐原｜AQI 58｜普通
沙鹿｜AQI 52｜普通
大里｜AQI 42｜良好
忠明｜AQI 52｜普通
西屯｜AQI 60｜普通
```

## 7. Webhook Request

每個縣市各執行一次：

``` text
POST {DISCORD_WEBHOOK_URL}
Content-Type: application/json
```

Payload：

``` json
{
  "content": "【臺中市 空氣品質】\n\n更新時間：2026/09/22 08:00:00\n\n豐原｜AQI 58｜普通\n..."
}
```

Webhook URL 應由環境變數或 `.env` 提供，不得寫死在程式、前端、Git
repository 或 Log。

## 8. 發送流程

``` text
收到新資料
    ↓
驗證必要欄位
    ↓
按 county 分組
    ↓
逐一處理縣市
    ↓
建立 Discord 訊息
    ↓
POST Webhook
    ↓
 ┌───┴───┐
成功     失敗
 ↓         ↓
INFO      ERROR
Log       Log
 └────┬────┘
      ↓
處理下一縣市
      ↓
全部完成
```

## 9. Log 規格

檔案：

``` text
dc_webhook.log
```

每個縣市的一次 Webhook request 對應一筆主要發送 Log。

### 成功

``` text
{log_time} | INFO | county={county} | publish_time={publishtime} | status=SUCCESS | http_status={status_code}
```

範例：

``` text
2026-09-24 17:10:03 | INFO | county=臺中市 | publish_time=2026/09/22 08:00:00 | status=SUCCESS | http_status=204
```

### 失敗

``` text
{log_time} | ERROR | county={county} | publish_time={publishtime} | status=FAILED | http_status={status_code} | error={error}
```

無 HTTP status，例如 timeout：

``` text
2026-09-24 17:10:04 | ERROR | county=桃園市 | publish_time=2026/09/22 08:00:00 | status=FAILED | http_status=N/A | error=Request timeout
```

Log 絕對不得包含完整 Discord Webhook URL。

## 10. 失敗處理

以下情況視為失敗並記錄 ERROR：

-   Discord 回傳非成功 HTTP response
-   Connection Error
-   Timeout
-   DNS / Network Error
-   Webhook 無效
-   其他發送例外

任何單一縣市失敗後，必須繼續處理下一縣市。

## 11. 異常資料

-   `aqi` 缺失：顯示 `AQI N/A`。
-   `status` 缺失或無法識別：顯示 `未知`。
-   `county` 缺失：該筆無法分組，不發送該筆並記錄 ERROR。
-   `sitename` 缺失：不加入訊息並記錄 ERROR。
-   不得根據 AQI 數值自行補算 `status`。

## 12. 模組介面

對上游提供一個主要操作：

``` text
send_aqi_notifications(air_quality_data)
```

內部責任：

``` text
send_aqi_notifications()
        ├── validate_data()
        ├── group_by_county()
        ├── build_discord_message()
        ├── send_webhook()
        └── write_log()
```

函式名稱僅為規格建議，不要求實作完全相同。

## 13. 驗收條件

1.  能接收一批已確認為新的空氣品質資料。
2.  正確按照 `county` 分組。
3.  每個縣市各發送一則 Discord 訊息。
4.  每個有效測站顯示 `sitename`、`aqi`、`status`。
5.  支援六種指定 AQI 狀態。
6.  狀態直接使用政府 `status`，不自行重新計算。
7.  單一縣市失敗不影響其他縣市。
8.  每次成功發送寫入 `dc_webhook.log`。
9.  每次失敗發送寫入 `dc_webhook.log`。
10. Log 記錄縣市、資料發布時間、結果及 HTTP Status Code（若有）。
11. Log 不包含 Discord Webhook URL。
12. 所有縣市均處理完成後，通知流程才結束。
