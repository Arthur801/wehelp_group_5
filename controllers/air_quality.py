import asyncio
import logging
from datetime import datetime, timedelta, timezone
from typing import Annotated

from fastapi import APIRouter, HTTPException, Query

from models.air_quality import (
    METRIC_COLUMNS,
    RANGE_DELTAS,
    AirQualityHistoryResponse,
    LatestAirQualityResponse,
    MetricsResponse,
    RegionsResponse,
    get_air_quality_history,
    get_latest_air_quality,
    get_latest_notification_batch,
    get_metrics,
    get_regions,
    send_aqi_notifications,
)

router = APIRouter(prefix="/api")


@router.get(
    "/air-quality/latest",
    response_model=LatestAirQualityResponse,
    tags=["air-quality"],
)
def latest_air_quality(
    county: Annotated[str | None, Query()] = None,
    siteid: Annotated[int | None, Query()] = None,
) -> LatestAirQualityResponse:
    result = get_latest_air_quality(county=county, siteid=siteid)
    if result is None:
        raise HTTPException(status_code=404, detail="Air quality data not found")
    return result


@router.get(
    "/air-quality/history",
    response_model=AirQualityHistoryResponse,
    tags=["air-quality"],
)
def air_quality_history(
    siteid: Annotated[int, Query()],
    metric: Annotated[str, Query()],
    range_: Annotated[str, Query(alias="range")],
) -> AirQualityHistoryResponse:
    if metric not in METRIC_COLUMNS:
        raise HTTPException(status_code=400, detail="Invalid metric")
    if range_ not in RANGE_DELTAS:
        raise HTTPException(status_code=400, detail="Invalid range")

    result = get_air_quality_history(
        siteid=siteid,
        metric=metric,
        time_range=range_,
    )
    if result is None:
        raise HTTPException(
            status_code=404,
            detail="Monitoring station not found",
        )
    return result


@router.get("/regions", response_model=RegionsResponse, tags=["regions"])
def regions() -> RegionsResponse:
    return get_regions()


@router.get("/metrics", response_model=MetricsResponse, tags=["metrics"])
def metrics() -> MetricsResponse:
    return get_metrics()


TAIPEI_TZ = timezone(timedelta(hours=8))
DISCORD_NOTIFY_MINUTE = 10

logger = logging.getLogger(__name__)
_last_notified_publishtime: str | None = None


def run_discord_notification_job() -> None:
    global _last_notified_publishtime

    try:
        batch = get_latest_notification_batch()
    except Exception:
        logger.exception("Failed to load air quality data for Discord notification")
        return

    if not batch:
        return
    publishtime = batch[0]["publishtime"]
    if publishtime == _last_notified_publishtime:
        return

    send_aqi_notifications(batch)
    _last_notified_publishtime = publishtime


def _seconds_until_next_run(now: datetime) -> float:
    next_run = now.replace(minute=DISCORD_NOTIFY_MINUTE, second=0, microsecond=0)
    if next_run <= now:
        next_run += timedelta(hours=1)
    return (next_run - now).total_seconds()


async def discord_notification_scheduler() -> None:
    while True:
        await asyncio.sleep(_seconds_until_next_run(datetime.now(TAIPEI_TZ)))
        try:
            await asyncio.to_thread(run_discord_notification_job)
        except Exception:
            logger.exception("Discord notification job failed")
