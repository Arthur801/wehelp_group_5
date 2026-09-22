from fastapi import FastAPI, Request
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from controllers.air_quality import router as air_quality_router

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
app.include_router(air_quality_router)

@app.get("/", include_in_schema=False)
async def index(request: Request):
	return FileResponse("./views/index.html", media_type="text/html")
