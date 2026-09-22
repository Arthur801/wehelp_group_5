import json
from datetime import datetime
from pathlib import Path
from typing import Any

from models.database import get_connection

DATA_FILE = Path(__file__).resolve().parent / "models" / "fake_data" / "fake_data.json"
PUBLISH_TIME_FORMAT = "%Y/%m/%d %H:%M:%S"

UPSERT_SQL = """
INSERT INTO air_quality_records (
    siteid, sitename, county, aqi, pollutant, status,
    so2, co, o3, o3_8hr, pm10, pm25, no2, nox, `no`,
    wind_speed, wind_direc, publishtime, co_8hr, pm25_avg,
    pm10_avg, so2_avg, longitude, latitude
)
VALUES (
    %s, %s, %s, %s, %s, %s,
    %s, %s, %s, %s, %s, %s, %s, %s, %s,
    %s, %s, %s, %s, %s,
    %s, %s, %s, %s
)
AS new
ON DUPLICATE KEY UPDATE
    sitename = new.sitename,
    county = new.county,
    aqi = new.aqi,
    pollutant = new.pollutant,
    status = new.status,
    so2 = new.so2,
    co = new.co,
    o3 = new.o3,
    o3_8hr = new.o3_8hr,
    pm10 = new.pm10,
    pm25 = new.pm25,
    no2 = new.no2,
    nox = new.nox,
    `no` = new.`no`,
    wind_speed = new.wind_speed,
    wind_direc = new.wind_direc,
    co_8hr = new.co_8hr,
    pm25_avg = new.pm25_avg,
    pm10_avg = new.pm10_avg,
    so2_avg = new.so2_avg,
    longitude = new.longitude,
    latitude = new.latitude
"""


def clean_value(value: Any) -> Any | None:
    if value in (None, "", "-"):
        return None
    return value


def to_values(record: dict[str, Any]) -> tuple[Any, ...]:
    return (
        int(record["siteid"]),
        record["sitename"],
        clean_value(record.get("county")),
        clean_value(record.get("aqi")),
        clean_value(record.get("pollutant")),
        clean_value(record.get("status")),
        clean_value(record.get("so2")),
        clean_value(record.get("co")),
        clean_value(record.get("o3")),
        clean_value(record.get("o3_8hr")),
        clean_value(record.get("pm10")),
        clean_value(record.get("pm2.5")),
        clean_value(record.get("no2")),
        clean_value(record.get("nox")),
        clean_value(record.get("no")),
        clean_value(record.get("wind_speed")),
        clean_value(record.get("wind_direc")),
        datetime.strptime(record["publishtime"], PUBLISH_TIME_FORMAT),
        clean_value(record.get("co_8hr")),
        clean_value(record.get("pm2.5_avg")),
        clean_value(record.get("pm10_avg")),
        clean_value(record.get("so2_avg")),
        clean_value(record.get("longitude")),
        clean_value(record.get("latitude")),
    )


def load_fake_data() -> int:
    records = json.loads(DATA_FILE.read_text(encoding="utf-8"))
    values = [to_values(record) for record in records]

    connection = get_connection()
    cursor = connection.cursor()
    try:
        cursor.executemany(UPSERT_SQL, values)
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        cursor.close()
        connection.close()

    return len(values)


if __name__ == "__main__":
    imported_count = load_fake_data()
    print(f"Imported {imported_count} air quality records")
