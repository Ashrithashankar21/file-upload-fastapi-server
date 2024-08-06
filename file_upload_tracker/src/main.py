from fastapi import FastAPI
from routers.file_tracker_router import router
import uvicorn


app = FastAPI()


app.include_router(router)

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="localhost",
        port=8000,
        reload=True,
        workers=1,
    )
