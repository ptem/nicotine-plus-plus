
import asyncio
import sys
from fastapi import FastAPI
from pynicotine.events import events
from pynicotine.config import config
from pynicotine.logfacility import log, Logger
from pynicotine.core import core
import uvicorn
import threading
import time

app = FastAPI()

class WebApi:

    def __init__(self):

        self.app = None
        self.server = None

        for event_name, callback in (
            ("quit", self._quit),
            ("start", self._start),
            ("file-search-response", self._file_search_response),
        ):
            events.connect(event_name, callback)

    def _start(self):

        if config.sections["web_api"]["enable"]:
            log.add(f"Web API loaded")
            
            try:
                uvicorn_config = uvicorn.Config(app,config.sections["web_api"]["local_ip"],config.sections["web_api"]["local_port"])
                self.server = AsyncUvicorn(uvicorn_config)
                self.server.start()

            except Exception as error:
                print(f"Exception when starting the Web API Server: {error}")
                self.server.stop()

    def _quit(self):
        
        print("Stop the WebAPI")
        if self.server is not None:
            self.server.stop()
    
    def _file_search_response(self, msg):

        print(msg)
        

class AsyncUvicorn:

    exception_caught = False

    def __init__(self, config: uvicorn.Config):
        self.server = uvicorn.Server(config)
        self.thread = threading.Thread(daemon=True, target=self.__run_server)

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

@app.get("/")
def read_root():
    log.add("NEW MESSAGE RECEIVED!!")
    # core.search.do_search("david penn", "global")
    return {"Hello": "World"}

