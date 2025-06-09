from fastapi import FastAPI

app = FastAPI()


@app.get("/")
def root():
    return {"message": "Snipster API is alive!"}
