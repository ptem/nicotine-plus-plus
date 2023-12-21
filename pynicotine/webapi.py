

from pynicotine import slskmessages
from pynicotine.events import events
from pynicotine.config import config
from pynicotine.logfacility import log
from pynicotine.core import core

from fastapi import FastAPI
import uvicorn
import threading
import time
from pydantic import BaseModel

app = FastAPI()

class WebApi:

    def __init__(self):

        self.app = None
        self.server = None
        self.search_list = []
        self.current_search = None

        for event_name, callback in (
            ("quit", self._quit),
            ("start", self._start),
            ("file-search-response", self._file_search_response),
            ("download-notification", self._download_notification)
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

        if msg.token not in slskmessages.SEARCH_TOKENS_ALLOWED:
            msg.token = None
            return

        search = core.search.searches.get(msg.token)
        if search and hasattr(search, "is_web_api_search") and search.is_web_api_search:
            if msg.token == self.current_search:
                print(search.term, msg)
                self.search_list.extend(msg.list)
            else:
                self.search_list.clear()
                self.search_list.extend(msg.list)

                #In case a new search is performed, we remove the old search to ignore the incoming messages for that token.
                core.search.remove_search(self.current_search)
                self.current_search = msg.token

    def _download_notification(self, status=None):
        if status:
            print("Download finished")
        else:
            print("Download just started")

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

class WebApiSearchModel(BaseModel):
    search_term: str
    search_filters: dict

@app.get("/")
def read_root():
    log.add("NEW MESSAGE RECEIVED!!")

    core.search.do_search_from_web_api("david penn", "global")
    
    return {"Hello": "World"}

@app.get("/search/{search_term}")
async def search_item(search_term):
    print(f"{search_term}")
    return {"item_id": search_term}

@app.get("/search/global/")
async def do_global_search(search: WebApiSearchModel):
    print("do global search")
    print(search.search_term)
    print(search.search_filters)

    core.search.do_search_from_web_api(search.search_term, mode="global", search_filters=search.search_filters)
    
    return search


'''
Data needed for a download:

            "user")
            "file_path_data")
            "size_data")
            "file_attributes_data")
'''

