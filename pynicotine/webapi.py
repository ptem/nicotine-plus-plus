
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
from threading import Timer, active_count, enumerate
import time
import json
import pathlib

class WebApi:

    def __init__(self):

        self.api_server = None
        self.active_searches = {}

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
                self.api_server = AsyncUvicorn(config.sections["web_api"]["local_ip"], config.sections["web_api"]["local_port"])
                self.api_server.start()

            except Exception as error:
                print(f"Exception when starting the Web API Server: {error}")
                self.api_server.stop()

    def _quit(self):
        
        print("Stop the WebAPI")
        self.search_list.clear()
        if self.api_server is not None:
            self.api_server.stop()
    
    def _parse_search_response(self, msg):
                
        # print(search.term, msg)
        # print(msg.token)

        items_to_return = []

        for _code, file_path, size, _ext, file_attributes, *_unused in msg.list:
            # print(file_path)
            file_path_split = file_path.split("\\")
            file_path_split = reversed(file_path_split)
            file_name = next(file_path_split)
            file_extension = pathlib.Path(file_name).suffix[1:]
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
                                        file_extension=file_extension,
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
            
            if not msg.token in self.active_searches:
                self.active_searches[msg.token] = self._parse_search_response(msg)
                t = Timer(2.0,self._search_timeout, args=[msg.token, search.search_filters])
                t.start()
            else:
                self.active_searches[msg.token].extend(self._parse_search_response(msg))


    def _download_notification(self, status=None):
        if status:
            print("Download finished")
        else:
            print("Download just started")

    
    def _search_timeout(self, token, search_filters):
        """Callback function that is triggered after the timeout in seconds elapsed"""
        
        #First thing is to remove the search from the core so that we do not process any other response for that token
        core.search.remove_search(token)

        for item in self.active_searches[token]:
            print(item.json())

        log.add(f"Sort results. Received {len(self.active_searches[token])}")
        log.add(f"Total searches: {len(self.active_searches)}")
        # print(enumerate())
        print(f"Total number of threads: {active_count()}")
        if token in self.active_searches:
            del self.active_searches[token]

    
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
    bitrate: int
