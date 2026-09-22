from fastapi import FastAPI, HTTPException, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from controllers.air_quality import router as air_quality_router

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
app.include_router(air_quality_router)


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
	return JSONResponse(status_code=exc.status_code, content={"error": True, "detail": exc.detail})


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
	return JSONResponse(
		status_code=422,
		content={"error": True, "detail": jsonable_encoder(exc.errors())},
	)


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
	return JSONResponse(status_code=500, content={"error": True, "detail": "Internal Server Error"})


@app.get("/", include_in_schema=False)
async def index(request: Request):
	return FileResponse("./views/index.html", media_type="text/html")
