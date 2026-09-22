from datetime import datetime, timedelta, timezone
from typing import Any, Literal, Mapping  # noqa: UP035

from pydantic import BaseModel, ConfigDict, Field

from models.database import get_connection


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
    ok: Literal[True] = True
    county: str | None
    data: list[AirQualityRecord]


class RegionSite(BaseModel):
    siteid: int
    sitename: str


class Region(BaseModel):
    county: str
    sites: list[RegionSite]


class RegionsResponse(BaseModel):
    ok: Literal[True] = True
    regions: list[Region]


class Metric(BaseModel):
    id: str
    name: str


class MetricsResponse(BaseModel):
    ok: Literal[True] = True
    metrics: list[Metric]


class HistoryDataPoint(BaseModel):
    time: datetime
    value: float | None


class AirQualityHistoryResponse(BaseModel):
    ok: Literal[True] = True
    siteid: int
    sitename: str
    county: str
    metric: str
    range: str
    data: list[HistoryDataPoint]


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

METRIC_COLUMNS = {
    "aqi": "aqi",
    "so2": "so2",
    "co": "co",
    "o3": "o3",
    "o3_8hr": "o3_8hr",
    "pm10": "pm10",
    "pm2.5": "pm25",
    "no2": "no2",
    "nox": "nox",
    "no": "`no`",
    "co_8hr": "co_8hr",
    "pm2.5_avg": "pm25_avg",
    "pm10_avg": "pm10_avg",
    "so2_avg": "so2_avg",
}

RANGE_DELTAS = {
    "24h": timedelta(hours=24),
    "48h": timedelta(hours=48),
    "72h": timedelta(hours=72),
}


def _to_int(value: Any) -> int | None:
    if value is None:
        return None
    return int(float(value))


def _to_float(value: Any) -> float | None:
    if value is None:
        return None
    return float(value)


def _to_text(value: Any) -> str:
    if value is None:
        return ""
    return str(value)


def _to_publish_time(value: datetime) -> datetime:
    return value.replace(tzinfo=timezone.utc)


def _to_air_quality_record(row: Mapping[str, Any]) -> AirQualityRecord:
    return AirQualityRecord(
        siteid=_to_int(row.get("siteid")),
        sitename=_to_text(row.get("sitename")),
        aqi=_to_int(row.get("aqi")),
        pollutant=_to_text(row.get("pollutant")),
        status=_to_text(row.get("status")),
        so2=_to_float(row.get("so2")),
        co=_to_float(row.get("co")),
        o3=_to_float(row.get("o3")),
        o3_8hr=_to_float(row.get("o3_8hr")),
        pm10=_to_float(row.get("pm10")),
        pm2_5=_to_float(row.get("pm25")),
        no2=_to_float(row.get("no2")),
        nox=_to_float(row.get("nox")),
        no=_to_float(row.get("no")),
        wind_speed=_to_float(row.get("wind_speed")),
        wind_direc=_to_float(row.get("wind_direc")),
        co_8hr=_to_float(row.get("co_8hr")),
        pm2_5_avg=_to_float(row.get("pm25_avg")),
        pm10_avg=_to_float(row.get("pm10_avg")),
        so2_avg=_to_float(row.get("so2_avg")),
        publishtime=_to_publish_time(row["publishtime"]),
        longitude=_to_float(row.get("longitude")),
        latitude=_to_float(row.get("latitude")),
    )


def get_latest_air_quality(
    county: str | None = None,
    siteid: int | None = None,
) -> LatestAirQualityResponse | None:
    conditions = [
        "publishtime = (SELECT MAX(publishtime) FROM air_quality_records)"
    ]
    params: list[str | int] = []
    if county is not None:
        conditions.append("county = %s")
        params.append(county)
    if siteid is not None:
        conditions.append("siteid = %s")
        params.append(siteid)

    query = f"""
        SELECT
            siteid, sitename, county, aqi, pollutant, status,
            so2, co, o3, o3_8hr, pm10, pm25, no2, nox, `no`,
            wind_speed, wind_direc, co_8hr, pm25_avg, pm10_avg,
            so2_avg, publishtime, longitude, latitude
        FROM air_quality_records
        WHERE {' AND '.join(conditions)}
        ORDER BY siteid
    """

    connection = get_connection()
    cursor = connection.cursor(dictionary=True)
    try:
        cursor.execute(query, params)
        rows = cursor.fetchall()
    finally:
        cursor.close()
        connection.close()

    if not rows:
        return None

    result_counties = {row["county"] for row in rows}
    response_county = county
    if response_county is None and len(result_counties) == 1:
        response_county = result_counties.pop()

    return LatestAirQualityResponse(
        county=response_county,
        data=[_to_air_quality_record(row) for row in rows],
    )


def get_air_quality_history(
    siteid: int,
    metric: str,
    time_range: str,
) -> AirQualityHistoryResponse | None:
    metric_column = METRIC_COLUMNS[metric]
    range_delta = RANGE_DELTAS[time_range]

    connection = get_connection()
    cursor = connection.cursor(dictionary=True)
    try:
        cursor.execute(
            """
            SELECT sitename, county, publishtime
            FROM air_quality_records
            WHERE siteid = %s
            ORDER BY publishtime DESC
            LIMIT 1
            """,
            (siteid,),
        )
        station = cursor.fetchone()
        if station is None:
            return None

        latest_time = station["publishtime"]
        start_time = latest_time - range_delta
        cursor.execute(
            f"""
            SELECT publishtime AS time, {metric_column} AS value
            FROM air_quality_records
            WHERE siteid = %s
              AND publishtime BETWEEN %s AND %s
            ORDER BY publishtime
            """,
            (siteid, start_time, latest_time),
        )
        rows = cursor.fetchall()
    finally:
        cursor.close()
        connection.close()

    return AirQualityHistoryResponse(
        siteid=siteid,
        sitename=_to_text(station["sitename"]),
        county=_to_text(station["county"]),
        metric=metric,
        range=time_range,
        data=[
            HistoryDataPoint(
                time=_to_publish_time(row["time"]),
                value=_to_float(row["value"]),
            )
            for row in rows
        ],
    )


def get_regions() -> RegionsResponse:
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)
    try:
        cursor.execute(
            """
            SELECT county, siteid, MAX(sitename) AS sitename
            FROM air_quality_records
            WHERE county IS NOT NULL AND county <> '' AND sitename <> ''
            GROUP BY county, siteid
            ORDER BY county, siteid
            """
        )
        rows = cursor.fetchall()
    finally:
        cursor.close()
        connection.close()

    sites_by_county: dict[str, list[RegionSite]] = {}
    for row in rows:
        sites_by_county.setdefault(row["county"], []).append(
            RegionSite(siteid=row["siteid"], sitename=row["sitename"])
        )

    regions = [
        Region(county=county, sites=sites)
        for county, sites in sites_by_county.items()
    ]
    return RegionsResponse(regions=regions)


def get_metrics() -> MetricsResponse:
    return MetricsResponse(
        metrics=[
            Metric(id=metric_id, name=name)
            for metric_id, name in METRIC_DEFINITIONS
        ]
    )
