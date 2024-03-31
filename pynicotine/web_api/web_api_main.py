

from typing import Optional
from pynicotine.core import core
from pynicotine.logfacility import log

from fastapi import FastAPI
from pydantic import BaseModel
import uvicorn
import threading
import time
import asyncio
import json

class WebApiSearchModel(BaseModel):
    search_term: str
    wait_for_seconds: int
    search_filters: Optional[dict] = None
    smart_filters: Optional[bool] = None
    

class FileToDownload(BaseModel):
    file_owner: str
    file_path: str
    file_size: int
    file_attributes: Optional[dict] = None

class TransferModel(BaseModel):
      
    username: str
    virtual_path: str
    download_path: str
    status: str
    size: int
    current_byte_offset: Optional[int] = None
    download_percentage: Optional[str] = None
    file_attributes: Optional[dict] = None

class SearchReqResponseModel(BaseModel):
    pass

class SearchResultModel(BaseModel):
    pass

class AsyncUvicorn:

    exception_caught = False

    def __init__(self, local_ip: str, local_port: int):
        uvicorn_config = uvicorn.Config(app, local_ip, local_port)
        self.server = uvicorn.Server(uvicorn_config)
        self.thread = threading.Thread(name="WebApiThread", daemon=True, target=self.__run_server)

    def __run_server(self): 
        try:
            if not self.server.started:
                self.server.run()
        except SystemExit:
            print("Error while starting the Web API server.")
            time.sleep(5)
            self.__run_server()

    def start(self):
            self.thread.start()

    def stop(self):
        if self.thread.is_alive():
            self.server.should_exit = True
            while self.thread.is_alive():
                continue
    
    def thread_excepthook(args):
        print(f"EXCEPTION! {args[1]}")

    threading.excepthook = thread_excepthook


app = FastAPI()

@app.get("/")
def read_root():
    log.add("NEW MESSAGE RECEIVED!!")
    core.search.do_search_from_web_api("david penn", "global")
    return {"Hello": "World"}

@app.get("/search/global")
async def do_web_api_global_search(search: WebApiSearchModel):
    # search_token = core.search.do_search_from_web_api(search.search_term, mode="global", search_filters=search.search_filters, smart_filters=search.smart_filters)
    search_token = core.search.do_search(search.search_term, mode="global", search_filters=search.search_filters, smart_filters=search.smart_filters)
    await asyncio.sleep(search.wait_for_seconds)
    search_req = core.search.searches.get(search_token)
    if search_req:
        search_req.is_ignored = True
    # search_req.my_variable = "this just a random variable added dynamically"
    return search_req

@app.get("/download")
async def download_file(file: FileToDownload):
    core.downloads.enqueue_download(file.file_owner, file.file_path, folder_path=None, size=file.file_size, file_attributes=file.file_attributes)
    return f"Download enqueued: {file.file_path}"

@app.get("/download/getdownloads")
async def get_dowloads():
    core_transfers = core.downloads.get_transfer_list()
    list_to_send = []
    for transfer in core_transfers:
        list_to_send.append(TransferModel(
                                username=transfer.username, 
                                virtual_path=transfer.virtual_path,
                                download_path=transfer.folder_path,
                                status=transfer.status,
                                size=transfer.size,
                                current_byte_offset=transfer.current_byte_offset,
                                download_percentage=f"{transfer.current_byte_offset*100/transfer.size:.2f}%" if transfer.current_byte_offset else "0%",
                                file_attributes=transfer.file_attributes))
    return list_to_send

@app.delete("/download/abortandclean")
async def abort_and_clean_all_downloads():
    core.downloads.clear_downloads()
    return "All downloads will be aborted and cleaned"

'''
    Data needed for a download:

                "user") => 'merciero23'
                "file_path_data") => '@@xpgbc\\TEMAS COMPARTIDOS 2\\mp3\\4635732_Love___Happiness__Yemaya___Ochun__Feat__India_David_Penn_Vocal_Mix.mp3'
                "size_data") => 18527131
                "file_attributes_data") => 
'''
