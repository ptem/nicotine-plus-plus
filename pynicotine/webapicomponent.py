


from pynicotine import slskmessages
from pynicotine.events import events
from pynicotine.config import config
from pynicotine.logfacility import log
from pynicotine.core import core
from pynicotine.slskmessages import FileListMessage
from pynicotine.web_api.web_api_main import AsyncUvicorn

from pydantic import BaseModel
from threading import Timer
import pathlib
from difflib import SequenceMatcher
import requests
import time
from typing import Optional
import json

class WebApiSearchResult(BaseModel):
    
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
    file_h_length: str
    bitrate: int
    search_similarity: float
    file_attributes: Optional[dict] = None

class FileDownloadedNotification(BaseModel):
    user: str
    virtual_file_path: str
    file_download_path: str

class WebApiComponent:

    def __init__(self):

        self.api_server = None
        self.active_searches = {}
        self.session = requests.Session()

        for event_name, callback in (
            ("quit", self._quit),
            ("start", self._start),
            ("file-search-response", self._file_search_response),
            # ("download-notification", self._download_notification),
            # ("download-notification-web-api", self._download_notification_web_api)
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
        if self.api_server is not None:
            self.api_server.stop()
    
    def _parse_search_response(self, msg, search):

            def get_string_similarity(a, b):
                return SequenceMatcher(None, a, b).ratio()

            items_to_return = []

            for _code, file_path, size, _ext, file_attributes, *_unused in msg.list:
                file_path_split = file_path.split("\\")
                file_path_split = reversed(file_path_split)
                file_name = next(file_path_split)
                file_extension = pathlib.Path(file_name).suffix[1:]
                h_quality, bitrate, h_length, length = FileListMessage.parse_audio_quality_length(size, file_attributes)
                if msg.freeulslots:
                    inqueue = 0
                else:
                    inqueue = msg.inqueue or 1  # Ensure value is always >= 1
                search_similarity = get_string_similarity(search.term, file_name)

                item = WebApiSearchResult(
                                        user = msg.username,
                                        ip_address = msg.addr[0],
                                        port = msg.addr[1],
                                        has_free_slots = msg.freeulslots,
                                        inqueue = inqueue,
                                        ulspeed = msg.ulspeed or 0, 
                                        file_name = file_name,
                                        file_extension=file_extension,
                                        file_path = file_path,
                                        file_size = size,
                                        file_h_length = h_length,
                                        bitrate = bitrate,
                                        search_similarity = search_similarity,
                                        file_attributes=file_attributes
                                    )

                items_to_return.append(item)
            
            return items_to_return
                
    def _file_search_response(self, msg):

        if msg.token not in slskmessages.SEARCH_TOKENS_ALLOWED:
            msg.token = None
            return

        search_req = core.search.searches.get(msg.token)
        if search_req:
            if not hasattr(search_req,"results"):
                search_req.results = []
            
            for item in self._parse_search_response(msg, search_req):
                search_req.results.append(item)
                

    def _download_notification(self, status=None):
        if status:
            print("Download finished")
        else:
            print("Download just started")

    def _download_notification_web_api(self, username, virtual_path, download_file_path):
        
        file = FileDownloadedNotification(user=username, virtual_file_path=virtual_path, file_download_path=download_file_path)
        print(f"Download finished in: {download_file_path}")
        data = file.model_dump()
        response = self.session.post(f'http://{config.sections["web_api"]["remote_ip"]}:{config.sections["web_api"]["remote_port"]}/download/notification', json=data)


    def _search_timeout(self, search):
        """Callback function that is triggered after the timeout elapses"""

        def _post_search_result(self, track_list: list[WebApiSearchResult]):
            try:
                response = self.session.post(f'http://{config.sections["web_api"]["remote_ip"]}:{config.sections["web_api"]["remote_port"]}/response/search/global', 
                                             json=[track.model_dump() for track in track_list])
                return response
            except Exception as ex:
                log.add("Something went wrong when sending the results to the client")

        if not search.token in self.active_searches:
            return
        
        #First thing is to remove the search from the core so that we do not process any other response for that token
        core.search.remove_web_api_search(search.token)
        #Delete the search from dict
        deleted_search = self.active_searches.pop(search.token)

        #filter the items
        filtered_list = [search_result for search_result in deleted_search if self._apply_filters(search_result, search.search_filters)]

        #Send the results based on the input given by the client in the api request
        free_slots_list = []
        if search.smart_filters:
            #Filter first by free slots
            free_slots_list = [file for file in filtered_list if file.has_free_slots]
            
            if len(free_slots_list) > 0:
                #Then order by upload speed
                free_slots_list.sort(key=lambda x: (x.search_similarity, x.ulspeed), reverse=True)
            start = time.time()
            if len(free_slots_list) > 0:
                _post_search_result(self, free_slots_list[:10])
            end = time.time()    

        else:
            start = time.time()
            if len(filtered_list) > 0:
                _post_search_result(self, filtered_list)
            end = time.time()


        print(f"=================================")
        print(f"Original: {len(deleted_search)}")
        print(f"Filtered: {len(filtered_list)}") 
        print(f"Free slots: {len(free_slots_list)}")
        print(f"Exec. time: {end - start}")
        print(f"=================================")

    def _apply_filters(self, search, search_filters) -> bool:

        result = None
        if search_filters is not None:
            for filter in search_filters:
                if hasattr(search,filter):
                    if getattr(search,filter) == search_filters[filter]:
                        result = True
                    else:
                        return False
                else:
                    return False
        else:
            return True

        return result

