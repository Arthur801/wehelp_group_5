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
    get_metrics,
    get_regions,
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
