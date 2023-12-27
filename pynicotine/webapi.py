
from collections.abc import Callable, Iterable, Mapping
from typing import Any
from pynicotine import slskmessages
from pynicotine.events import events
from pynicotine.config import config
from pynicotine.logfacility import log
from pynicotine.core import core
from pynicotine.slskmessages import FileListMessage
from pynicotine.web_api.web_api_main import app, AsyncUvicorn

from pydantic import BaseModel
from threading import Thread, Event, Timer
import time

class WebApi:

    def __init__(self):

        self.app = None
        self.server = None
        self.search_list = []
        self.current_search = None
        self.counter = 0

        for event_name, callback in (
            ("quit", self._quit),
            ("start", self._start),
            ("file-search-response", self._file_search_response),
            ("download-notification", self._download_notification)
        ):
            events.connect(event_name, callback)

        self.send_results_thread = StoppableThread(name="SearchTimer", interval=1.5, target=self._sort_results)
        self.send_results_thread.start()


    def _start(self):

        if config.sections["web_api"]["enable"]:
            log.add(f"Web API loaded")
            
            try:
                self.server = AsyncUvicorn(config.sections["web_api"]["local_ip"], config.sections["web_api"]["local_port"])
                self.server.start()

            except Exception as error:
                print(f"Exception when starting the Web API Server: {error}")
                self.server.stop()

    def _quit(self):
        
        print("Stop the WebAPI")
        self.search_list.clear()
        if self.server is not None:
            self.server.stop()
    
    def _parse_search_response(self, msg):
                
        # print(search.term, msg)
        # print(msg.token)

        items_to_return = []

        for _code, file_path, size, _ext, file_attributes, *_unused in msg.list:
            # print(file_path)
            file_path_split = file_path.split("\\")
            file_path_split = reversed(file_path_split)
            file_name = next(file_path_split)
            h_quality, bitrate, h_length, length = FileListMessage.parse_audio_quality_length(size, file_attributes)

            items_to_return.append(WebApiSearchResult(
                                        token = msg.token,
                                        user = msg.username,
                                        ip_address = msg.addr[0],
                                        port = msg.addr[1],
                                        has_free_slots = msg.freeulslots,
                                        inqueue = msg.inqueue or 1,
                                        ulspeed = msg.ulspeed or 0, 
                                        file_name = file_name,
                                        file_path = file_path,
                                        bitrate = bitrate
                                   ))
        
        return items_to_return
                
    def _file_search_response(self, msg):

        if msg.token not in slskmessages.SEARCH_TOKENS_ALLOWED:
            msg.token = None
            return

        search = core.search.searches.get(msg.token)
        if search and hasattr(search, "is_web_api_search") and search.is_web_api_search:
            # if self.counter == 0 and self.send_results_thread.stopped():
            #     self.send_results_thread.restart()
            #     self.counter += 1
            
            if self.current_search is None:
                self.send_results_thread.restart()
                self.current_search = msg.token
                log.add("New search arrived for the first time.")
            
            if msg.token == self.current_search:
                self.search_list.extend(self._parse_search_response(msg))
            else:
                #In case a new search is performed, we remove the old search to ignore the incoming messages for that token.
                core.search.remove_search(self.current_search)
                self.current_search = msg.token
                self.counter = 0
                self.send_results_thread.restart()

                self.search_list.clear()
                self.search_list.extend(self._parse_search_response(msg))
                log.add("New search arrived.")


    def _download_notification(self, status=None):
        if status:
            print("Download finished")
        else:
            print("Download just started")

    def _sort_results(self):
        log.add(f"Sort results. Received {len(self.search_list)}")
        self.send_results_thread.stop()
        


class WebApiSearchResult(BaseModel):
    token: int
    user: str
    ip_address: str
    port: int
    has_free_slots: bool
    inqueue: int
    ulspeed: int
    file_name: str
    file_path: str
    bitrate: int


class StoppableThread(Thread):
    """Thread class with a stop() method. The thread itself has to check
        regularly for the stopped() condition."""

    def __init__(self, name, target, interval):
        super().__init__(name=name, target=target)
        self._stop_event = Event()
        self.interval = interval
        self.target = target
        
    def stop(self):
        # print("Thread stopped")
        self._stop_event.set()

    def stopped(self):
        return self._stop_event.is_set()
    
    def restart(self):
        # print("Thread restarted.")
        self._stop_event.clear()
    
    def run(self):

        while True:
            time.sleep(0.5)
            if not self.stopped():
                time.sleep(self.interval)
                self.target(*self._args, **self._kwargs)

