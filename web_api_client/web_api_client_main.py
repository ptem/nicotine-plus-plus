from fastapi import FastAPI
import uvicorn
import asyncio

app = FastAPI()


@app.get("/response/search/global")
async def root():
    return {"message": "Hello World"}


if __name__ == "__main__":
    asyncio.run(uvicorn.run(app, port=7771, log_level="debug"))
