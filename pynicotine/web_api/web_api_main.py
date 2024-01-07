

from typing import Optional
from pynicotine.core import core
from pynicotine.logfacility import log

from fastapi import FastAPI
from pydantic import BaseModel
import uvicorn
import threading
import time

class WebApiSearchModel(BaseModel):
    search_term: str
    search_filters: Optional[dict] = None
    smart_filters: Optional[bool] = None

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

@app.get("/search/global/")
async def do_web_api_global_search(search: WebApiSearchModel):

    core.search.do_search_from_web_api(search.search_term, mode="global", search_filters=search.search_filters, smart_filters=search.smart_filters)
    
    return search


'''
    Data needed for a download:

                "user")
                "file_path_data")
                "size_data")k
                "file_attributes_data")
'''
