from fastapi import FastAPI
from routers import file_upload_tracker
import uvicorn


app = FastAPI()


app.include_router(file_upload_tracker.router)

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="local\
host",
        port=8000,
        reload=False,
        workers=1,
    )
