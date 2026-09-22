import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

DATA_FILE = Path(__file__).resolve().parent / "fake_data" / "fake_data.json"
PUBLISH_TIME_FORMAT = "%Y/%m/%d %H:%M:%S"


class AirQualityRecord(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    siteid: int
    sitename: str
    aqi: int | None
    pollutant: str
    status: str
    so2: float | None
    co: float | None
    o3: float | None
    o3_8hr: float | None
    pm10: float | None
    pm2_5: float | None = Field(alias="pm2.5")
    no2: float | None
    nox: float | None
    no: float | None
    wind_speed: float | None
    wind_direc: float | None
    co_8hr: float | None
    pm2_5_avg: float | None = Field(alias="pm2.5_avg")
    pm10_avg: float | None
    so2_avg: float | None
    publishtime: datetime
    longitude: float | None
    latitude: float | None


class LatestAirQualityResponse(BaseModel):
    county: str | None
    data: list[AirQualityRecord]


class RegionSite(BaseModel):
    siteid: int
    sitename: str


class Region(BaseModel):
    county: str
    sites: list[RegionSite]


class RegionsResponse(BaseModel):
    regions: list[Region]


class Metric(BaseModel):
    id: str
    name: str


class MetricsResponse(BaseModel):
    metrics: list[Metric]


METRIC_DEFINITIONS = (
    ("aqi", "AQI"),
    ("so2", "SO2"),
    ("co", "CO"),
    ("o3", "O3"),
    ("o3_8hr", "O3 8hr"),
    ("pm10", "PM10"),
    ("pm2.5", "PM2.5"),
    ("no2", "NO2"),
    ("nox", "NOx"),
    ("no", "NO"),
    ("co_8hr", "CO 8hr"),
    ("pm2.5_avg", "PM2.5 AVG"),
    ("pm10_avg", "PM10 AVG"),
    ("so2_avg", "SO2 AVG"),
)


def _read_air_quality_data() -> list[dict[str, Any]]:
    with DATA_FILE.open(encoding="utf-8") as file:
        return json.load(file)


def _parse_publish_time(value: str) -> datetime:
    return datetime.strptime(value, PUBLISH_TIME_FORMAT).replace(tzinfo=timezone.utc)


def _to_int(value: Any) -> int | None:
    if value in (None, "", "-"):
        return None
    return int(float(value))


def _to_float(value: Any) -> float | None:
    if value in (None, "", "-"):
        return None
    return float(value)


def _to_air_quality_record(row: dict[str, Any]) -> AirQualityRecord:
    return AirQualityRecord(
        siteid=_to_int(row.get("siteid")),
        sitename=row.get("sitename", ""),
        aqi=_to_int(row.get("aqi")),
        pollutant=row.get("pollutant", ""),
        status=row.get("status", ""),
        so2=_to_float(row.get("so2")),
        co=_to_float(row.get("co")),
        o3=_to_float(row.get("o3")),
        o3_8hr=_to_float(row.get("o3_8hr")),
        pm10=_to_float(row.get("pm10")),
        pm2_5=_to_float(row.get("pm2.5")),
        no2=_to_float(row.get("no2")),
        nox=_to_float(row.get("nox")),
        no=_to_float(row.get("no")),
        wind_speed=_to_float(row.get("wind_speed")),
        wind_direc=_to_float(row.get("wind_direc")),
        co_8hr=_to_float(row.get("co_8hr")),
        pm2_5_avg=_to_float(row.get("pm2.5_avg")),
        pm10_avg=_to_float(row.get("pm10_avg")),
        so2_avg=_to_float(row.get("so2_avg")),
        publishtime=_parse_publish_time(row["publishtime"]),
        longitude=_to_float(row.get("longitude")),
        latitude=_to_float(row.get("latitude")),
    )


def get_latest_air_quality(
    county: str | None = None,
    siteid: int | None = None,
) -> LatestAirQualityResponse | None:
    rows = _read_air_quality_data()
    if not rows:
        return None

    latest_publish_time = max(
        _parse_publish_time(row["publishtime"]) for row in rows
    )
    latest_rows = [
        row
        for row in rows
        if _parse_publish_time(row["publishtime"]) == latest_publish_time
    ]

    if county is not None:
        latest_rows = [row for row in latest_rows if row.get("county") == county]
    if siteid is not None:
        latest_rows = [
            row for row in latest_rows if _to_int(row.get("siteid")) == siteid
        ]

    if not latest_rows:
        return None

    latest_rows.sort(key=lambda row: _to_int(row.get("siteid")) or 0)
    result_counties = {row.get("county") for row in latest_rows}
    response_county = county
    if response_county is None and len(result_counties) == 1:
        response_county = result_counties.pop()

    return LatestAirQualityResponse(
        county=response_county,
        data=[_to_air_quality_record(row) for row in latest_rows],
    )


def get_regions() -> RegionsResponse:
    sites_by_county: dict[str, dict[int, str]] = {}

    for row in _read_air_quality_data():
        county = row.get("county")
        siteid = _to_int(row.get("siteid"))
        sitename = row.get("sitename")
        if not county or siteid is None or not sitename:
            continue
        sites_by_county.setdefault(county, {})[siteid] = sitename

    regions = [
        Region(
            county=county,
            sites=[
                RegionSite(siteid=siteid, sitename=sites[siteid])
                for siteid in sorted(sites)
            ],
        )
        for county, sites in sorted(sites_by_county.items())
    ]
    return RegionsResponse(regions=regions)


def get_metrics() -> MetricsResponse:
    return MetricsResponse(
        metrics=[
            Metric(id=metric_id, name=name)
            for metric_id, name in METRIC_DEFINITIONS
        ]
    )
