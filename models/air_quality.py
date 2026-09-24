import logging
import os
import time
from datetime import datetime, timedelta, timezone
from typing import Any, Literal, Mapping  # noqa: UP035

import requests
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


# Discord webhook AQI notifications (docs/discord_webhook_aqi_spec.md)

VALID_AQI_STATUSES = (
    "良好",
    "普通",
    "對敏感族群不健康",
    "對所有族群不健康",
    "非常不健康",
    "危害",
)
UNKNOWN_AQI_STATUS = "未知"
DC_WEBHOOK_LOG_FILE = "dc_webhook.log"
DISCORD_SEND_INTERVAL_SECONDS = 1
DISCORD_TIMEOUT_SECONDS = 10
PUBLISH_TIME_FORMAT = "%Y/%m/%d %H:%M:%S"


def _get_webhook_logger() -> logging.Logger:
    logger = logging.getLogger("dc_webhook")
    if not logger.handlers:
        handler = logging.FileHandler(DC_WEBHOOK_LOG_FILE, encoding="utf-8")
        handler.setFormatter(
            logging.Formatter(
                "%(asctime)s | %(levelname)s | %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
        )
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        logger.propagate = False
    return logger


def _is_blank(value: Any) -> bool:
    return value is None or str(value).strip() in ("", "-")


def _format_publish_time(value: Any) -> str:
    if isinstance(value, datetime):
        return value.strftime(PUBLISH_TIME_FORMAT)
    if _is_blank(value):
        return "N/A"
    return str(value)


def _format_aqi(value: Any) -> str:
    if _is_blank(value):
        return "N/A"
    return str(value).strip()


def _format_status(value: Any) -> str:
    status = "" if value is None else str(value).strip()
    if status in VALID_AQI_STATUSES:
        return status
    return UNKNOWN_AQI_STATUS


def get_latest_notification_batch() -> list[dict[str, Any]]:
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)
    try:
        cursor.execute(
            """
            SELECT county, sitename, aqi, status, publishtime
            FROM air_quality_records
            WHERE publishtime = (
                SELECT MAX(publishtime) FROM air_quality_records
            )
            ORDER BY siteid
            """
        )
        rows = cursor.fetchall()
    finally:
        cursor.close()
        connection.close()

    return [
        {
            "county": row["county"],
            "sitename": row["sitename"],
            "aqi": row["aqi"],
            "status": row["status"],
            "publishtime": _format_publish_time(row["publishtime"]),
        }
        for row in rows
    ]


def write_log(
    county: str,
    publish_time: str,
    http_status: int | None,
    error: str | None = None,
) -> None:
    logger = _get_webhook_logger()
    status_code = "N/A" if http_status is None else str(http_status)
    message = (
        f"county={county} | publish_time={publish_time} | "
        f"status={'FAILED' if error else 'SUCCESS'} | http_status={status_code}"
    )
    if error:
        logger.error(f"{message} | error={error}")
    else:
        logger.info(message)


def validate_data(
    air_quality_data: list[Mapping[str, Any]],
) -> list[Mapping[str, Any]]:
    logger = _get_webhook_logger()
    valid_records = []
    for record in air_quality_data:
        county = record.get("county")
        sitename = record.get("sitename")
        publish_time = _format_publish_time(record.get("publishtime"))
        if _is_blank(county):
            logger.error(
                f"county=N/A | publish_time={publish_time} | "
                f"sitename={_to_text(sitename) or 'N/A'} | "
                "status=INVALID_RECORD | error=Missing county"
            )
            continue
        if _is_blank(sitename):
            logger.error(
                f"county={county} | publish_time={publish_time} | "
                "sitename=N/A | status=INVALID_RECORD | error=Missing sitename"
            )
            continue
        valid_records.append(record)
    return valid_records


def group_by_county(
    records: list[Mapping[str, Any]],
) -> dict[str, list[Mapping[str, Any]]]:
    groups: dict[str, list[Mapping[str, Any]]] = {}
    for record in records:
        groups.setdefault(str(record["county"]).strip(), []).append(record)
    return groups


def build_discord_message(
    county: str,
    records: list[Mapping[str, Any]],
) -> str:
    publish_time = _format_publish_time(records[0].get("publishtime"))
    lines = [
        f"{record['sitename']}｜AQI {_format_aqi(record.get('aqi'))}｜"
        f"{_format_status(record.get('status'))}"
        for record in records
    ]
    return f"【{county} 空氣品質】\n\n更新時間：{publish_time}\n\n" + "\n".join(lines)


def send_webhook(webhook_url: str, content: str) -> tuple[int | None, str | None]:
    # Never surface str(exc): requests exceptions embed the webhook URL/token.
    try:
        response = requests.post(
            webhook_url,
            json={"content": content},
            timeout=DISCORD_TIMEOUT_SECONDS,
        )
    except requests.exceptions.Timeout:
        return None, "Request timeout"
    except (requests.exceptions.MissingSchema, requests.exceptions.InvalidSchema,
            requests.exceptions.InvalidURL):
        return None, "Invalid webhook URL"
    except requests.exceptions.ConnectionError:
        return None, "Connection error"
    except Exception as exc:
        return None, type(exc).__name__

    if 200 <= response.status_code < 300:
        return response.status_code, None
    return response.status_code, f"HTTP {response.status_code}"


def send_aqi_notifications(
    air_quality_data: list[Mapping[str, Any]],
) -> dict[str, int]:
    webhook_url = os.getenv("DISCORD_WEBHOOK_URL")
    groups = group_by_county(validate_data(air_quality_data))

    result = {"sent": 0, "failed": 0}
    for index, (county, records) in enumerate(groups.items()):
        if index > 0:
            time.sleep(DISCORD_SEND_INTERVAL_SECONDS)

        publish_time = _format_publish_time(records[0].get("publishtime"))
        try:
            if not webhook_url:
                http_status, error = None, "DISCORD_WEBHOOK_URL not set"
            else:
                content = build_discord_message(county, records)
                http_status, error = send_webhook(webhook_url, content)
        except Exception as exc:
            http_status, error = None, type(exc).__name__

        write_log(county, publish_time, http_status, error)
        result["failed" if error else "sent"] += 1

    return result
