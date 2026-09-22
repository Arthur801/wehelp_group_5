from typing import Annotated

from fastapi import APIRouter, HTTPException, Query

from models.air_quality import LatestAirQualityResponse, get_latest_air_quality


router = APIRouter(prefix="/api/air-quality", tags=["air-quality"])


@router.get("/latest", response_model=LatestAirQualityResponse)
def latest_air_quality(
    county: Annotated[str | None, Query()] = None,
    siteid: Annotated[int | None, Query()] = None,
) -> LatestAirQualityResponse:
    result = get_latest_air_quality(county=county, siteid=siteid)
    if result is None:
        raise HTTPException(status_code=404, detail="Air quality data not found")
    return result
