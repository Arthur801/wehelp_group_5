# 空氣品質監測與視覺化服務 API 文件

## 1. 文件概述

本文件依據提供的政府空氣品質 JSON 資料格式，定義本系統第一版後端 API。

來源 JSON 共包含 **84
筆測站資料**。資料的基本單位是「監測站」，每筆資料包含
`siteid`、`sitename`、`county`、AQI、污染物濃度、風速風向、發布時間與經緯度等欄位。

系統架構：

```text
政府空氣品質資料
        ↓
   FastAPI 定期取得
        ↓
      MySQL
        ↓
   FastAPI REST API
        ↓
HTML5 / JavaScript
        ↓
     圖表顯示
```

### Base URL

```text
/api
```

---

## 2. 政府來源資料欄位

實際 JSON 中的欄位如下：

欄位            說明

---

`siteid`        監測站 ID
`sitename`      監測站名稱
`county`        縣市
`aqi`           空氣品質指標 AQI
`pollutant`     主要污染物
`status`        空氣品質狀態
`so2`           二氧化硫
`co`            一氧化碳
`o3`            臭氧
`o3_8hr`        臭氧 8 小時平均
`pm10`          PM10
`pm2.5`         PM2.5
`no2`           二氧化氮
`nox`           氮氧化物
`no`            一氧化氮
`wind_speed`    風速
`wind_direc`    風向
`publishtime`   資料發布時間
`co_8hr`        CO 8 小時平均
`pm2.5_avg`     PM2.5 平均值
`pm10_avg`      PM10 平均值
`so2_avg`       SO2 平均值
`longitude`     經度
`latitude`      緯度

> 原始政府 JSON 的數值欄位以字串表示，且部分欄位可能出現空字串或
> `-`。匯入 MySQL 時應先進行型別轉換與缺失值處理。

---

## 3. API 一覽

Method   Endpoint                     用途

---

GET      `/api/air-quality/latest`    查詢測站最新空氣品質資料
GET      `/api/air-quality/history`   查詢指定測站與指標的歷史資料
GET      `/api/regions`               取得縣市與其監測站
GET      `/api/metrics`               取得可用於圖表的空氣品質指標

---

# 4. 最新空氣品質

## GET `/api/air-quality/latest`

取得資料庫中最新一批監測資料。

可使用 `county` 或 `siteid`
篩選。由於政府資料同一縣市可能包含多個監測站，因此指定縣市時回傳該縣市所有測站，而不是將數值自行平均。

### Query Parameters

Parameter   Type      Required   說明

---

`county`    string    No         縣市，例如 `臺中市`
`siteid`    integer   No         監測站 ID，例如 `32`

### Request

```http
GET /api/air-quality/latest?county=臺中市
```

### Response

```json
{
  "county": "臺中市",
  "data": [
    {
      "siteid": 28,
      "sitename": "豐原",
      "aqi": 58,
      "pollutant": "細懸浮微粒",
      "status": "普通",
      "so2": 0.6,
      "co": 0.25,
      "o3": 34,
      "o3_8hr": 36,
      "pm10": 35,
      "pm2.5": 19,
      "no2": 5,
      "nox": 6.6,
      "no": 1.1,
      "wind_speed": 1.4,
      "wind_direc": 42,
      "co_8hr": 0.2,
      "pm2.5_avg": 15,
      "pm10_avg": 30,
      "so2_avg": 0,
      "publishtime": "2026-09-22T08:00:00",
      "longitude": 120.74252,
      "latitude": 24.256998
    }
  ]
}
```

### Error

```text
404 Not Found
```

```json
{
  "detail": "Air quality data not found"
}
```

---

# 5. 歷史空氣品質

## GET `/api/air-quality/history`

取得 MySQL 中累積的歷史監測資料，主要提供前端折線圖使用。

因為政府來源資料以「監測站」為資料單位，因此歷史圖表以 `siteid`
指定測站，避免同一縣市多個測站的數值被混合。

### Query Parameters

Parameter   Type      Required   說明

---

`siteid`    integer   Yes        監測站 ID
`metric`    string    Yes        要查詢的指標
`range`     string    Yes        時間範圍，目前支援 `24h`、`48h`、`72h`

### Request

```http
GET /api/air-quality/history?siteid=32&metric=pm2.5&range=24h
```

### Response

```json
{
  "siteid": 32,
  "sitename": "西屯",
  "county": "臺中市",
  "metric": "pm2.5",
  "range": "24h",
  "data": [
    {
      "time": "2026-09-22T07:00:00",
      "value": 21
    },
    {
      "time": "2026-09-22T08:00:00",
      "value": 24
    }
  ]
}
```

前端圖表：

```text
data[].time  → X 軸
data[].value → Y 軸
```

### Error

不支援的指標：

```text
400 Bad Request
```

```json
{
  "detail": "Invalid metric"
}
```

找不到監測站：

```text
404 Not Found
```

```json
{
  "detail": "Monitoring station not found"
}
```

---

# 6. 地區與監測站

## GET `/api/regions`

取得政府資料中存在的縣市以及各縣市的監測站。

這個 API 主要提供前端的兩層選單：

```text
縣市
 ↓
監測站
```

### Parameters

無。

### Request

```http
GET /api/regions
```

### Response Example

```json
{
  "regions": [
    {
      "county": "臺中市",
      "sites": [
        {
          "siteid": 28,
          "sitename": "豐原"
        },
        {
          "siteid": 29,
          "sitename": "沙鹿"
        },
        {
          "siteid": 30,
          "sitename": "大里"
        },
        {
          "siteid": 31,
          "sitename": "忠明"
        },
        {
          "siteid": 32,
          "sitename": "西屯"
        }
      ]
    }
  ]
}
```

---

# 7. 空氣品質指標

## GET `/api/metrics`

取得可以用於歷史查詢及圖表的指標。

### Parameters

無。

### Request

```http
GET /api/metrics
```

### Response

```json
{
  "metrics": [
    {"id": "aqi", "name": "AQI"},
    {"id": "so2", "name": "SO2"},
    {"id": "co", "name": "CO"},
    {"id": "o3", "name": "O3"},
    {"id": "o3_8hr", "name": "O3 8hr"},
    {"id": "pm10", "name": "PM10"},
    {"id": "pm2.5", "name": "PM2.5"},
    {"id": "no2", "name": "NO2"},
    {"id": "nox", "name": "NOx"},
    {"id": "no", "name": "NO"},
    {"id": "co_8hr", "name": "CO 8hr"},
    {"id": "pm2.5_avg", "name": "PM2.5 AVG"},
    {"id": "pm10_avg", "name": "PM10 AVG"},
    {"id": "so2_avg", "name": "SO2 AVG"}
  ]
}
```

> 本文件只將來源 JSON
> 中明確屬於空氣品質數值的欄位列為圖表指標。各污染物的單位沒有在提供的
> JSON 中出現，因此本文件不自行推測單位。

---

# 8. 前端操作流程

```text
GET /api/regions
        ↓
選擇縣市
        ↓
選擇監測站
        ↓
GET /api/metrics
        ↓
選擇 AQI / PM2.5 / PM10 / O3 ...
        ↓
選擇時間範圍
        ↓
GET /api/air-quality/history
        ↓
取得時間序列
        ↓
繪製折線圖
```

首頁即時資訊則可以：

```text
GET /api/air-quality/latest?county=臺中市
        ↓
取得臺中市各監測站最新資料
        ↓
顯示 AQI / status / pollutant 等資訊
```

---

# 9. 資料處理注意事項

## 原始數值不是 JSON number

提供的來源資料中，例如：

```json
{
  "aqi": "60",
  "pm2.5": "24",
  "longitude": "120.61692"
}
```

都是字串。

系統匯入 MySQL 時應轉換成適當的數值型別，自己的 API 再以 JSON number
回傳：

```json
{
  "aqi": 60,
  "pm2.5": 24,
  "longitude": 120.61692
}
```

## 缺失值

來源資料確實存在：

```json
{
  "wind_speed": "",
  "wind_direc": ""
}
```

以及：

```json
{
  "wind_speed": "-",
  "wind_direc": "-"
}
```

因此建議匯入資料庫時統一轉換為 `NULL`，自己的 API 則回傳：

```json
{
  "wind_speed": null,
  "wind_direc": null
}
```

## 時間格式

政府來源：

```text
2026/09/22 08:00:00
```

建議資料庫使用 DATETIME，API 統一輸出 ISO 8601：

```text
2026-09-22T08:00:00
```

---

# 10. 第一版 API 邊界

目前四個 API 的責任可以明確區分為：

```text
/api/regions
    → 有哪些縣市與測站？

/api/metrics
    → 可以看哪些空污指標？

/api/air-quality/latest
    → 現在各測站的狀況如何？

/api/air-quality/history
    → 某個測站的某個指標如何隨時間變化？
```

這四個 API 已足以支援第一版「地區選擇 → 測站選擇 → 指標選擇 →
歷史圖表」的核心功能。
