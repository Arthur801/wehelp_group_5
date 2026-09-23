// 建立地圖上圓形色塊標記，裡面顯示數字
function createAqiIcon(value, color) {
  return L.divIcon({
    className: "aqi-marker",
    html: `<div style="
      background-color: ${color};
      color: white;
      width: 22px;
      height: 22px;
      border-radius: 50%;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 10px;
      font-weight: bold;
    ">${value}</div>`,
    iconSize: [22, 22],
    iconAnchor: [11, 11]
  });
}
// 各指標設定總表
const POLLUTANT_CONFIG = {
  "aqi":   { field: "aqi",    label: "AQI",   unit: "",     breakpoints: [50, 100, 150, 200, 300] },
  "pm2.5": { field: "pm2.5",  label: "PM2.5", unit: "μg/m³", breakpoints: [12.4, 30.4, 50.4, 125.4, 225.4] },
  "pm10":  { field: "pm10",   label: "PM10",  unit: "μg/m³", breakpoints: [30, 75, 190, 354, 424] },
  "o3":    { field: "o3_8hr", label: "O3",    unit: "ppb",  breakpoints: [54, 70, 85, 105, 200] },
  "so2":   { field: "so2",    label: "SO2",   unit: "ppb",  breakpoints: [8, 65, 160, 304, 604] },
  "no2":   { field: "no2",    label: "NO2",   unit: "ppb",  breakpoints: [21, 100, 360, 649, 1249] },
  "co":    { field: "co_8hr", label: "CO",    unit: "ppm",  breakpoints: [4.4, 9.4, 12.4, 15.4, 30.4] }
};
// 6個等級共用的顏色與文字標籤，跟現有AQI配色一致
const LEVEL_COLORS = ["#639922", "#BA7517", "#D85A30", "#E24B4A", "#993C1D", "#5C1A0F"];
const LEVEL_LABELS = ["良好", "普通", "對敏感族群不健康", "對所有族群不健康", "非常不健康", "危害"];

// 根據指標種類與原始數值，回傳 { color, label }
function getIndicatorLevel(indicatorKey, rawValue) {
  const value = Number(rawValue);
  // 沒有資料的情況
  if (rawValue === "" || rawValue === null || rawValue === undefined || isNaN(value)) {
    return { color: "#ccc", label: "無資料" };
  }
  // 拿這個指標專屬的門檻表
  const breakpoints = POLLUTANT_CONFIG[indicatorKey].breakpoints;
  // 由小到大依序比對，找到第一個「數值 <= 門檻」的位置，就是該落在的等級
  for (let i = 0; i < breakpoints.length; i++) {
    if (value <= breakpoints[i]) {
      return { color: LEVEL_COLORS[i], label: LEVEL_LABELS[i] };
    }
  }
  // 比全部門檻都大，代表是最嚴重的等級，回傳最後一組顏色/標籤
  return { color: LEVEL_COLORS[LEVEL_COLORS.length - 1], label: LEVEL_LABELS[LEVEL_LABELS.length - 1] };
}

// 存放每個測站對應的 marker 與資料，方便切換指標時重繪
let stationMarkers = [];
let currentIndicator = "aqi";
//Init
function initMap(stations) {
  //建立地圖物件
  const map = L.map("map").setView([23.7, 121], 7);
  //底圖圖磚
  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    attribution: "&copy; OpenStreetMap contributors"
  }).addTo(map);

  // 每次呼叫initMap都重新清空一次，避免舊資料殘留
  stationMarkers = [];

  stations.forEach(station => {
    const lat = station.latitude;
    const lng = station.longitude;
    if (!lat || !lng) return;
    //算出測站該顯示什麼顏色
    const level = getIndicatorLevel(currentIndicator, station[POLLUTANT_CONFIG[currentIndicator].field]);
    //地圖上座標畫點
    const icon = createAqiIcon(station.aqi, level.color);
    const marker = L.marker([lat, lng], { icon }).addTo(map);
    //滑鼠移上去跳出內容
    marker.bindTooltip(buildTooltipHtml(station, currentIndicator), {
      direction: "top",
      offset: [0, -10]
    });
    //點擊時觸發搜尋
    marker.on("click", () => {
      document.getElementById("search-input").value = station.sitename;
      document.getElementById("county-select").value = station.county;
      const exactMatch = allStations.filter(s => s.siteid === station.siteid);
      render(exactMatch);
    });
    // 把這個marker記錄起來，方便之後切換指標時能找回來改
    stationMarkers.push({ marker, station });
  });

  setupIndicatorButtons();
}

// 產生 tooltip 內容，依目前選擇的指標顯示對應數值
function buildTooltipHtml(station, indicatorKey) {
  const config = POLLUTANT_CONFIG[indicatorKey];
  const rawValue = station[config.field];
  const level = getIndicatorLevel(indicatorKey, rawValue);
  const displayValue = (rawValue === "" || rawValue === null || rawValue === undefined) ? "無資料" : rawValue + config.unit;

  return `
    <div>
      <strong>${station.county} ${station.sitename}</strong><br>
      ${config.label}：${displayValue}<br>
      等級：${level.label}
    </div>
  `;
}

// 切換指標按鈕：更新按鈕樣式 + 重繪所有 marker
function setupIndicatorButtons() {
  const buttons = document.querySelectorAll(".indicator-btn");
  buttons.forEach(btn => {
    btn.addEventListener("click", () => {
      currentIndicator = btn.dataset.indicator;

      buttons.forEach(b => b.classList.remove("active"));
      btn.classList.add("active");

      stationMarkers.forEach(({ marker, station }) => {
        const config = POLLUTANT_CONFIG[currentIndicator];
        const rawValue = station[config.field];
        const level = getIndicatorLevel(currentIndicator, rawValue);
        const displayValue = (rawValue === "" || rawValue === null || rawValue === undefined) ? "-" : rawValue;

        marker.setIcon(createAqiIcon(displayValue, level.color));
        marker.setTooltipContent(buildTooltipHtml(station, currentIndicator));
      });
    });
  });
}