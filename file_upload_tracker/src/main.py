from fastapi import FastAPI
from routers.file_tracker_router import router
import uvicorn

# Initialize the FastAPI application
app = FastAPI()

# Include the router from the file_tracker_router module
app.include_router(router)

if __name__ == "__main__":
    # Run the application using uvicorn
    uvicorn.run(
        "main:app",  # The application instance to run
        host="localhost",  # The host to bind the server to
        port=8000,  # The port to bind the server to
        reload=True,  # Enable auto-reload for code changes
        workers=1,  # Number of worker processes
    )
