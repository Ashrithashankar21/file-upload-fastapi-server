from fastapi import FastAPI

app = FastAPI()


@app.get("/")
def print_hi():
    return {"message": "Hi!"}
