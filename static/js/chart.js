let currentChart = null;
let currentRange = "24h";

function setupChartCountyOptions(stations) {
  const select = document.querySelector("#chart-county-select");
  select.replaceChildren();
  const counties = [...new Set(stations.map(s => s.county))]
    .sort((a, b) => a.localeCompare(b, "zh-Hant"));
  counties.forEach(c => {
    const option = document.createElement("option");
    option.value = c;
    option.textContent = c;
    select.appendChild(option);
  });
}

function setupChartStationOptions(stations) {
  const county = document.querySelector("#chart-county-select").value;
  const select = document.querySelector("#chart-station-select");
  select.replaceChildren();

  const filtered = stations
    .filter(s => s.county === county)
    .sort((a, b) => a.sitename.localeCompare(b.sitename, "zh-Hant"));

  filtered.forEach(s => {
    const option = document.createElement("option");
    option.value = s.siteid;
    option.textContent = s.sitename;
    select.appendChild(option);
  });
}

document.querySelector("#chart-county-select").addEventListener("change", () => {
  setupChartStationOptions(allStations);
  loadChart();
});

async function fetchHistory(siteid, metric, range) {
  const res = await fetch(`/api/air-quality/history?siteid=${siteid}&metric=${encodeURIComponent(metric)}&range=${range}`);
  if (!res.ok) throw new Error("無法取得歷史資料");
  return res.json();
}

function formatChartTime(isoString) {
  const match = isoString.match(/^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2})/);
  if (!match) return isoString;
  const [, , month, day, hour, minute] = match;
  return `${month}/${day} ${hour}:${minute}`;
}

function renderChart(historyData) {
  const canvas = document.querySelector("#history-chart");
  const labels = historyData.data.map(point => formatChartTime(point.time));
  const values = historyData.data.map(point => point.value);

  if (currentChart) {
    currentChart.destroy();
  }

  currentChart = new Chart(canvas, {
    type: "line",
    data: {
      labels,
      datasets: [{
        label: `${historyData.sitename}（${historyData.metric}）`,
        data: values,
        borderColor: "#2c3e50",
        backgroundColor: "rgba(44, 62, 80, 0.1)",
        tension: 0.3,
        spanGaps: true
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        y: { beginAtZero: false }
      }
    }
  });
}

async function loadChart() {
  const siteid = document.querySelector("#chart-station-select").value;
  const metric = document.querySelector("#chart-metric-select").value;
  const chartStatus = document.querySelector("#chart-status");
  const canvas = document.querySelector("#history-chart");

  if (!siteid) return;

  chartStatus.classList.remove("hidden", "error");
  chartStatus.textContent = "圖表載入中...";
  canvas.style.display = "none";

  try {
    const historyData = await fetchHistory(siteid, metric, currentRange);
    chartStatus.classList.add("hidden");
    canvas.style.display = "block";
    renderChart(historyData);
  } catch (err) {
    console.error(err);
    chartStatus.textContent = "歷史資料載入失敗，請稍後再試";
    chartStatus.classList.add("error");
    canvas.style.display = "none";
  }
}

document.querySelector("#chart-station-select").addEventListener("change", loadChart);
document.querySelector("#chart-metric-select").addEventListener("change", loadChart);

document.querySelectorAll(".range-btn").forEach(btn => {
  btn.addEventListener("click", () => {
    document.querySelectorAll(".range-btn").forEach(b => b.classList.remove("active"));
    btn.classList.add("active");
    currentRange = btn.dataset.range;
    loadChart();
  });
});
