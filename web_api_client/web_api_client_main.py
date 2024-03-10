from fastapi import FastAPI
import uvicorn
import asyncio
from pydantic import BaseModel
from typing import Optional

from telebot.async_telebot import AsyncTeleBot
from telebot.types import InputFile
import requests

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
async def do_search(search_results: list[WebApiSearchResult]):
    print(len(search_results))
    
    asyncio.ensure_future(process_results(search_results)) #Fire and forget
    return True

async def process_results(results_list: list[WebApiSearchResult]):
    await async_bot.send_message(chat_id, f'received {len(results_list)} tracks')
    for track in results_list:
        await async_bot.send_message(chat_id, f'{track.file_name}')
    pass

@app.post("/download/notification")
async def download_notification(download: FileDownloadedNotification):
    print(download.file_download_path)
    async_bot.send_document(chat_id, InputFile(download.file_download_path))
    return download

# Handle '/start' and '/help'
@async_bot.message_handler(commands=['help', 'start'])
async def send_welcome(message):
    await async_bot.reply_to(message, """\
Hi there, I am EchoBot.
I am here to echo your kind words back to you. Just say anything nice and I'll say the exact same thing to you!\
""")

@async_bot.message_handler(commands=['search'])
async def do_search(message):
    await async_bot.send_message(chat_id, "Select Search Type")
    body = '{"search_term": "moloko sing it back extended","smart_filters": true}'
    requests.get("http://127.0.0.1:7770/search/global", data=body)

@async_bot.message_handler(commands=['searchh'])
async def do_search(message):
    print(message)
    await async_bot.send_message(chat_id, "Select Search Type")

async def main():
    config = uvicorn.Config(app, port=7771, log_level="debug")
    server = uvicorn.Server(config)

    async with asyncio.TaskGroup() as tg:
        tg.create_task(async_bot.polling())
        tg.create_task(server.serve())

if __name__ == "__main__":
    asyncio.run(main())