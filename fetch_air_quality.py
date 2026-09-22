import os
import requests
from dotenv import load_dotenv
from models.database import get_connection

load_dotenv()

def clean_value(value):
    if value in ("", "-"):
        return None
    return value

api_key = os.getenv("MOENV_API_KEY")

url = (
    "https://data.moenv.gov.tw/api/v2/aqx_p_432"
    f"?api_key={api_key}"
    "&limit=1000"
    "&sort=ImportDate%20desc"
    "&format=JSON"
)

response = requests.get(url, verify=False)

data = response.json()

connection = get_connection()
cursor = connection.cursor()

sql = """
INSERT INTO air_quality_records (
    siteid, sitename, county,
    aqi, pollutant, status,
    so2, co, o3, o3_8hr,
    pm10, pm25,
    no2, nox, no,
    wind_speed, wind_direc,
    publishtime,
    co_8hr, pm25_avg, pm10_avg, so2_avg,
    longitude, latitude
)
VALUES (
    %s, %s, %s,
    %s, %s, %s,
    %s, %s, %s, %s,
    %s, %s,
    %s, %s, %s,
    %s, %s,
    %s,
    %s, %s, %s, %s,
    %s, %s
)
ON DUPLICATE KEY UPDATE
    aqi = VALUES(aqi)
"""

for record in data:
    values = (
        clean_value(record["siteid"]),
        clean_value(record["sitename"]),
        clean_value(record["county"]),

        clean_value(record["aqi"]),
        clean_value(record["pollutant"]),
        clean_value(record["status"]),

        clean_value(record["so2"]),
        clean_value(record["co"]),
        clean_value(record["o3"]),
        clean_value(record["o3_8hr"]),

        clean_value(record["pm10"]),
        clean_value(record["pm2.5"]),

        clean_value(record["no2"]),
        clean_value(record["nox"]),
        clean_value(record["no"]),

        clean_value(record["wind_speed"]),
        clean_value(record["wind_direc"]),

        clean_value(record["publishtime"]),

        clean_value(record["co_8hr"]),
        clean_value(record["pm2.5_avg"]),
        clean_value(record["pm10_avg"]),
        clean_value(record["so2_avg"]),

        clean_value(record["longitude"]),
        clean_value(record["latitude"])
    )

    cursor.execute(sql, values)

connection.commit()

print("全部資料寫入完成")

cursor.close()
connection.close()