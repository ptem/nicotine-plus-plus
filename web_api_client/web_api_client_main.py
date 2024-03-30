from fastapi import FastAPI
import uvicorn
import asyncio
from pydantic import BaseModel
from typing import Optional

from telebot.async_telebot import AsyncTeleBot
from telebot.types import InputFile, InlineKeyboardMarkup, InlineKeyboardButton
import requests

class WebApiSearchResult(BaseModel):
    token: int
    search_term: str
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
    file_h_lenght: str
    bitrate: int
    search_similarity: float
    file_attributes: Optional[dict] = None

class FileDownloadedNotification(BaseModel):
    user: str
    virtual_file_path: str
    file_download_path: str

app = FastAPI()
async_bot = AsyncTeleBot("YOUR_BOT_API_KEY") 
chat_id = "YOUR_CHAT_ID"
searches = {}

async def main():
    config = uvicorn.Config(app, port=7771, log_level="debug")
    server = uvicorn.Server(config)

    async with asyncio.TaskGroup() as tg:
        tg.create_task(async_bot.polling())
        tg.create_task(server.serve())

#####################
# FAST API HANDLERS #
#####################
@app.post("/response/search/global")
async def do_search(search_results: list[WebApiSearchResult]):
    print(len(search_results))
    message = searches[search_results[0].search_term]

    asyncio.ensure_future(process_results(search_results, message)) #Fire and forget
    return True

async def process_results(results_list: list[WebApiSearchResult], message):
    try:
        markup = InlineKeyboardMarkup()
        for track in results_list:
            markup.add(InlineKeyboardButton("\U00002b07 " + track.file_name +" | " + track.file_h_lenght + ";" + str(track.bitrate), callback_data=track.file_name))
        await async_bot.send_message(message.chat.id, f'Received {len(results_list)} tracks', reply_markup=markup)
    except Exception as ex:
        pass


@app.post("/download/notification")
async def download_notification(download: FileDownloadedNotification):
    print(download.file_download_path)
    async_bot.send_document(chat_id, InputFile(download.file_download_path))
    return download


#####################
# TELEGRAM HANDLERS #
#####################

# # Handle '/start' and '/help'
# @async_bot.message_handler(commands=['help', 'start'])
# async def send_welcome(message):
#     await async_bot.reply_to(message, """\
#             Hi there, I am EchoBot.
#             I am here to echo your kind words back to you. Just say anything nice and I'll say the exact same thing to you!\
#             """)

@async_bot.message_handler(commands=['search'])
async def do_search(message):
    parsed_message = message.text.replace("/search", "").strip()

    await async_bot.send_message(message.chat.id, f"Waiting for results for your track...: {parsed_message}")
    
    body = f'{{"search_term": "{parsed_message}","smart_filters": true}}'
    
    searches[parsed_message] = message

    requests.get("http://127.0.0.1:7770/search/global", data=body)

@async_bot.message_handler(commands=['searchh'])
async def do_search(message):
    if "/searchh" in message.text:
        parsed_message = message.text.replace("/searchh", "").strip()
        pass
    
    print(parsed_message)
    await async_bot.send_message(message.chat.id, f"You want to search for: {parsed_message}")

@async_bot.callback_query_handler(func=lambda call: call)
async def product_one_callback(call):
    print(call.message.text)
    pass
    # await bot.answer_callback_query(callback_query_id=call.id, text='Not available :(', show_alert=True)

if __name__ == "__main__":
    asyncio.run(main())