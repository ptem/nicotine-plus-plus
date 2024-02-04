    
from fastapi import FastAPI
import uvicorn
import asyncio
from pydantic import BaseModel
from typing import Optional

import telebot
from telebot.types import InputFile

class WebApiSearchResult(BaseModel):
    token: int
    user: str
    ip_address: str
    port: int
    has_free_slots: bool
    inqueue: int
    ulspeed: int
    file_name: str
    file_extension: str
    file_path: str
    file_size: int
    bitrate: int
    search_similarity: float
    file_attributes: Optional[dict] = None

class FileDownloadedNotification(BaseModel):
    user: str
    virtual_file_path: str
    file_download_path: str

app = FastAPI()

@app.post("/response/search/global")
async def do_search(search_result: WebApiSearchResult):
    print(search_result.file_name)
    if search_result.user == 'platano2':
        print("success")
    return search_result

@app.post("/download/notification")
async def download_notification(download: FileDownloadedNotification):
    print(download.file_download_path)
    bot.send_document(chat_id, InputFile(download.file_download_path))
    return download

if __name__ == "__main__":
    asyncio.run(uvicorn.run(app, port=7771, log_level="critical"))
    asyncio.run(uvicorn.run(app, port=7771, log_level="debug"))