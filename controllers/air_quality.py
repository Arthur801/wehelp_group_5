from typing import Annotated

from fastapi import APIRouter, HTTPException, Query

from models.air_quality import (
    LatestAirQualityResponse,
    RegionsResponse,
    get_latest_air_quality,
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


@router.get("/regions", response_model=RegionsResponse, tags=["regions"])
def regions() -> RegionsResponse:
    return get_regions()
