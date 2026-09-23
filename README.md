# wehelp_group_5


合作開發一個空氣品質監測或視覺化服務。
空氣品質政府公開資料https://data.gov.tw/dataset/40448

- 前端:沐勁宇
  - 處理網頁的HTML、CSS、JS，監測使用者選擇的指標與地區，並渲染成表格或圖
- 後端:林開弘
  - 將資料庫中的資料處理成前端可接受的型式
- 資料庫:許純宜
  - 把資料爬到資料庫

資料夾結構
air-quality-monitor/
│
├── main.py                # 後端
│
├── requirements.txt
│
├── models/
│   ├── database.py        # 資料庫(可以再建立另外一個爬蟲的檔案)
│   └── air_quality.py     # 後端
│
├── controllers/           # 後端
│   └── air_quality.py
│
├── views/                 # 前端
│   └── index.html
│
└── static/                # 前端
├── css/
│   └── style.css
└── js/
├── index.js
└── chart.js
