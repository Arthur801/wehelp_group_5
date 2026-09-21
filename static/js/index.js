let allStations = [];
//抓資料
async function fetchStations() {
  const apiUrl = `https://data.moenv.gov.tw/api/v2/aqx_p_432?api_key=${API_KEY}&limit=1000&format=JSON`;
  const res = await fetch(apiUrl);
  const data = await res.json();
  return data;
}
//AQI 空氣品質指標
function getLevelInfo(aqiRaw) {
  const aqi = Number(aqiRaw);
  if (aqiRaw === "" || isNaN(aqi)) return { color: "#ccc" };
  if (aqi <= 50)  return { color: "#639922" };
  if (aqi <= 100) return { color: "#BA7517" };
  if (aqi <= 150) return { color: "#D85A30" };
  if (aqi <= 200) return { color: "#E24B4A" };
  if (aqi <= 300) return { color: "#993C1D" };
  return { color: "#5C1A0F" };
}
//渲染畫面
function render(stations) {
  const container = document.querySelector("#station-list");
  const emptyMessage = document.querySelector("#empty-message");
  container.replaceChildren();

  if (stations.length === 0) {
    emptyMessage.style.display = "block";
    return;
  }

  emptyMessage.style.display = "none";
  stations.forEach(station => {
    const level = getLevelInfo(station.aqi);

    const card = document.createElement("div");
    card.className = "station-card";
    card.style.backgroundColor = level.color;

    const timeDiv = document.createElement("div");
    timeDiv.className = "station-time";
    timeDiv.textContent = station.publishtime;

    const nameDiv = document.createElement("div");
    nameDiv.className = "station-name";
    nameDiv.textContent = `${station.county} . ${station.sitename}`;

    const aqiLabel = document.createElement("div");
    aqiLabel.className = "aqi-label";
    aqiLabel.textContent = "空氣品質指標 AQI";

    const aqiNumber = document.createElement("div");
    aqiNumber.className = "aqi-number";
    aqiNumber.textContent = station.aqi;

    const aqiStatus = document.createElement("div");
    aqiStatus.className = "aqi-status";
    aqiStatus.textContent = station.status || "無資料";

    const detail = document.createElement("div");
    detail.className = "station-detail";
    //detail
    const detailItems = [
        { label: "首要污染物", value: station.pollutant || "無", unit: "" },
        { label: "PM2.5 細懸浮微粒", value: station["pm2.5"], unit: "μg/m³" },
        { label: "PM10 懸浮微粒", value: station.pm10, unit: "μg/m³" },
        { label: "O3 臭氧", value: station.o3, unit: "ppb" },
        { label: "SO2 二氧化硫", value: station.so2, unit: "ppb" },
        { label: "NO2 二氧化氮", value: station.no2, unit: "ppb" },
        { label: "CO 一氧化碳", value: station.co, unit: "ppm" }
    ];
    
    detailItems.forEach(item => {
    const row = document.createElement("div");
    row.className = "detail-row";

    const labelSpan = document.createElement("span");
    labelSpan.className = "detail-label";
    labelSpan.textContent = item.label;

    const valueSpan = document.createElement("span");
    valueSpan.className = "detail-value";
    const hasValue = item.value !== undefined && item.value !== null && item.value !== "";
    valueSpan.textContent = hasValue
    ? (item.unit ? `${item.value} ${item.unit}` : item.value)
    : "無資料";

    row.appendChild(labelSpan); 
    row.appendChild(valueSpan);
    detail.appendChild(row);
    });

    card.appendChild(timeDiv);
    card.appendChild(nameDiv);
    card.appendChild(aqiLabel);
    card.appendChild(aqiNumber);
    card.appendChild(aqiStatus);
    card.appendChild(detail);

    card.addEventListener("click", () => {
      card.classList.toggle("expanded");
    });

    container.appendChild(card);
  });
}
//縣市下拉式選單
function setupCountyOptions(stations) {
  const select = document.querySelector("#county-select");
  const counties = [...new Set(stations.map(s => s.county))];
  counties.forEach(c => {
    const option = document.createElement("option");
    option.value = c;
    option.textContent = c;
    select.appendChild(option);
  });
}
// 搜尋篩選功能
document.querySelector("#county-select").addEventListener("change", applyFilters);
document.querySelector("#search-input").addEventListener("input", applyFilters);
function applyFilters() {
  const county = document.querySelector("#county-select").value;
  const keyword = document.querySelector("#search-input").value.trim();

  let result = allStations;
  if (county !== "全部") {
    result = result.filter(s => s.county === county);
  }
  if (keyword) {
    result = result.filter(s =>
    s.sitename.includes(keyword) || s.county.includes(keyword)
    );
  }
  render(result);
}

async function init() {
  allStations = await fetchStations();
  allStations.sort((a, b) => Number(b.aqi) - Number(a.aqi));
  setupCountyOptions(allStations);
  render(allStations);
  initMap(allStations);
}

init();
