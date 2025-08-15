#This is just a random text

from pynicotine import slskmessages
from pynicotine.events import events
from pynicotine.config import config
from pynicotine.logfacility import log
from pynicotine.core import core
from pynicotine.slskmessages import FileListMessage
from pynicotine.core import core
from pynicotine.logfacility import log
from pynicotine.transfers import TransferStatus
from pynicotine.webapi_models import WebApiSearchResult, FileDownloadedNotification, WebApiSearchModel, FileToDownload, TransferModel, BrowseUserRequest, BrowseUserResponse, BrowseStatusResponse, BrowseFileInfo, EnhancedTransferModel, UserQueueStatsModel, QueueInvestigationRequest, QueueInvestigationResponse, UserStatusModel, BulkUserStatusRequest, BulkUserStatusResponse

from threading import Thread
import pathlib
from difflib import SequenceMatcher
import requests
from fastapi import FastAPI
import uvicorn
import time
import asyncio

class AsyncUvicorn:

    exception_caught = False
    
    def __init__(self, local_ip: str, local_port: int):
        uvicorn_config = uvicorn.Config(app, local_ip, local_port)
        self.server = uvicorn.Server(uvicorn_config)
        self.thread = Thread(name="WebApiThread", daemon=True, target=self.__run_server)

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

    excepthook = thread_excepthook

#####################
# WEB API COMPONENT #
#####################

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

##########################
# WEB API IMPLEMENTATION #
##########################
app = FastAPI()

@app.get("/foo")
async def root():
    return {"message": "Hello World"}

@app.get("/search/global")
async def do_web_api_global_search(search: WebApiSearchModel):

    max_simultaneous_searches = config.sections["web_api"]["max_simultaneous_searches"]
    if len(core.search.searches) < max_simultaneous_searches:
        search_token = core.search.do_search(search.search_term, mode="global")
        await asyncio.sleep(search.wait_for_seconds)
        search_req = core.search.searches.get(search_token)
        if search_req:
            search_req.is_ignored = True
        core.search.remove_search(search_token)
        
        if not hasattr(search_req,"results"):
            return "No results found. Please, try with another search string."
        else:
            return search_req
    else:
        return "Too many simultaneous searches. Please, try again later."


@app.get("/download")
async def download_file(file: FileToDownload):

    core.downloads.enqueue_download(file.file_owner, file.file_virtual_path, folder_path=None, size=file.file_size, file_attributes=file.file_attributes)
    return f"Download enqueued: {file.file_virtual_path}"

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
    core.downloads.clear_downloads(statuses=[TransferStatus.FINISHED, TransferStatus.CANCELLED])
    return "All downloads will be aborted and cleaned"


# Enhanced Download/Queue Investigation Endpoints

def _convert_to_enhanced_transfer(transfer) -> EnhancedTransferModel:
    """Convert a Transfer object to EnhancedTransferModel with detailed queue information."""
    
    # Calculate download percentage
    download_percentage = "0%"
    if transfer.current_byte_offset and transfer.size > 0:
        percentage = (transfer.current_byte_offset * 100) / transfer.size
        download_percentage = f"{percentage:.2f}%"
    
    # Calculate if transfer is stalled (no progress for extended time)
    is_stalled = False
    if (transfer.status == TransferStatus.TRANSFERRING and 
        transfer.last_update and 
        time.time() - transfer.last_update > 60 and  # No update for 1 minute
        transfer.speed == 0):
        is_stalled = True
    
    # Calculate wait time in queue
    wait_time = None
    if transfer.start_time and transfer.status in [TransferStatus.QUEUED, TransferStatus.GETTING_STATUS]:
        wait_time = time.time() - transfer.start_time
    
    # Calculate ETA
    eta_seconds = None
    if (transfer.speed and transfer.speed > 0 and 
        transfer.current_byte_offset and transfer.size > 0):
        remaining_bytes = transfer.size - transfer.current_byte_offset
        eta_seconds = remaining_bytes / transfer.speed
    
    return EnhancedTransferModel(
        username=transfer.username,
        virtual_path=transfer.virtual_path,
        download_path=transfer.folder_path,
        status=transfer.status,
        size=transfer.size,
        current_byte_offset=transfer.current_byte_offset,
        download_percentage=download_percentage,
        file_attributes=transfer.file_attributes,
        queue_position=getattr(transfer, 'queue_position', None),
        speed=getattr(transfer, 'speed', None),
        time_elapsed=getattr(transfer, 'time_elapsed', None),
        time_left=getattr(transfer, 'time_left', None),
        start_time=getattr(transfer, 'start_time', None),
        last_update=getattr(transfer, 'last_update', None),
        modifier=getattr(transfer, 'modifier', None),
        token=getattr(transfer, 'token', None),
        eta_seconds=eta_seconds,
        is_stalled=is_stalled,
        wait_time=wait_time
    )


@app.get("/download/enhanced")
async def get_enhanced_downloads():
    """Get detailed transfer information with queue positions and timing data."""
    
    core_transfers = core.downloads.get_transfer_list()
    enhanced_transfers = []
    
    for transfer in core_transfers:
        enhanced_transfer = _convert_to_enhanced_transfer(transfer)
        enhanced_transfers.append(enhanced_transfer)
    
    return enhanced_transfers


@app.get("/download/queue-stats/{username}")
async def get_user_queue_stats(username: str):
    """Get detailed queue statistics for a specific user."""
    
    # Get all transfers for this user
    user_transfers = [t for t in core.downloads.get_transfer_list() if t.username == username]
    
    # Categorize transfers
    queued_transfers = [t for t in user_transfers if t.status == TransferStatus.QUEUED]
    active_transfers = [t for t in user_transfers if t.status == TransferStatus.TRANSFERRING]
    failed_transfers = [t for t in user_transfers if t.status in [
        TransferStatus.CONNECTION_CLOSED, TransferStatus.CONNECTION_TIMEOUT,
        TransferStatus.USER_LOGGED_OFF, TransferStatus.DOWNLOAD_FOLDER_ERROR,
        TransferStatus.LOCAL_FILE_ERROR
    ]]
    
    # Calculate statistics
    total_queued_size = sum(t.size for t in queued_transfers if t.size)
    
    # Calculate average queue position
    queue_positions = [t.queue_position for t in queued_transfers if hasattr(t, 'queue_position') and t.queue_position]
    average_queue_position = sum(queue_positions) / len(queue_positions) if queue_positions else None
    
    # Estimate total wait time based on queue positions and typical transfer speeds
    estimated_total_wait_time = None
    if queue_positions:
        # Rough estimate: assume 1 minute per queue position
        estimated_total_wait_time = sum(queue_positions) * 60
    
    # Check user online status properly using core.users.statuses
    user_status = core.users.statuses.get(username)
    is_online = user_status is not None and user_status != 0  # 0 = OFFLINE, 1 = AWAY, 2 = ONLINE
    
    # Convert status to human-readable string
    status_strings = {0: "Offline", 1: "Away", 2: "Online"}
    status_string = status_strings.get(user_status, "Unknown") if user_status is not None else "Unknown"
    
    # Get queue size limit if available
    queue_size_limit = core.downloads._user_queue_limits.get(username)
    
    return UserQueueStatsModel(
        username=username,
        total_queued_files=len(queued_transfers),
        active_transfers=len(active_transfers),
        failed_transfers=len(failed_transfers),
        queue_size_limit=queue_size_limit,
        is_online=is_online,
        status_value=user_status,
        status_string=status_string,
        queued_transfers=[t.virtual_path for t in queued_transfers],
        active_transfer_paths=[t.virtual_path for t in active_transfers],
        failed_transfer_paths=[t.virtual_path for t in failed_transfers],
        total_queued_size=total_queued_size,
        average_queue_position=average_queue_position,
        estimated_total_wait_time=estimated_total_wait_time
    )


@app.post("/download/investigate")
async def investigate_download_queues(request: QueueInvestigationRequest):
    """Perform comprehensive investigation of download queues and status."""
    
    investigation_start = time.time()
    
    # Get all transfers
    all_transfers = core.downloads.get_transfer_list()
    
    # Filter transfers based on request
    filtered_transfers = all_transfers
    if request.username:
        filtered_transfers = [t for t in filtered_transfers if t.username == request.username]
    
    if request.virtual_path:
        filtered_transfers = [t for t in filtered_transfers if t.virtual_path == request.virtual_path]
    
    # Filter by status
    if not request.include_completed:
        filtered_transfers = [t for t in filtered_transfers if t.status != TransferStatus.FINISHED]
    
    if not request.include_failed:
        failed_statuses = [
            TransferStatus.CONNECTION_CLOSED, TransferStatus.CONNECTION_TIMEOUT,
            TransferStatus.USER_LOGGED_OFF, TransferStatus.DOWNLOAD_FOLDER_ERROR,
            TransferStatus.LOCAL_FILE_ERROR, TransferStatus.CANCELLED
        ]
        filtered_transfers = [t for t in filtered_transfers if t.status not in failed_statuses]
    
    # Limit results
    if request.max_results and len(filtered_transfers) > request.max_results:
        filtered_transfers = filtered_transfers[:request.max_results]
    
    # Convert to enhanced models
    enhanced_transfers = [_convert_to_enhanced_transfer(t) for t in filtered_transfers]
    
    # Calculate system-wide statistics
    total_active = len([t for t in all_transfers if t.status == TransferStatus.TRANSFERRING])
    total_queued = len([t for t in all_transfers if t.status == TransferStatus.QUEUED])
    total_failed = len([t for t in all_transfers if t.status in [
        TransferStatus.CONNECTION_CLOSED, TransferStatus.CONNECTION_TIMEOUT,
        TransferStatus.USER_LOGGED_OFF, TransferStatus.DOWNLOAD_FOLDER_ERROR,
        TransferStatus.LOCAL_FILE_ERROR
    ]])
    
    # Count specific issue types
    connection_issues = len([t for t in all_transfers if t.status in [
        TransferStatus.CONNECTION_CLOSED, TransferStatus.USER_LOGGED_OFF
    ]])
    timeout_issues = len([t for t in all_transfers if t.status == TransferStatus.CONNECTION_TIMEOUT])
    
    # Calculate average queue wait time
    queued_transfers_with_start = [t for t in all_transfers 
                                  if t.status == TransferStatus.QUEUED and hasattr(t, 'start_time') and t.start_time]
    average_queue_wait_time = None
    if queued_transfers_with_start:
        current_time = time.time()
        wait_times = [current_time - t.start_time for t in queued_transfers_with_start]
        average_queue_wait_time = sum(wait_times) / len(wait_times)
    
    # Find most queued user
    user_queue_counts = {}
    for transfer in all_transfers:
        if transfer.status == TransferStatus.QUEUED:
            user_queue_counts[transfer.username] = user_queue_counts.get(transfer.username, 0) + 1
    
    most_queued_user = max(user_queue_counts.keys(), key=user_queue_counts.get) if user_queue_counts else None
    
    # Generate per-user statistics for users with transfers in the filtered results
    user_stats = []
    unique_users = list(set(t.username for t in filtered_transfers))
    
    for username in unique_users:
        # This would normally call the queue stats endpoint, but we'll generate it inline
        user_transfers = [t for t in all_transfers if t.username == username]
        
        queued = [t for t in user_transfers if t.status == TransferStatus.QUEUED]
        active = [t for t in user_transfers if t.status == TransferStatus.TRANSFERRING]
        failed = [t for t in user_transfers if t.status in [
            TransferStatus.CONNECTION_CLOSED, TransferStatus.CONNECTION_TIMEOUT,
            TransferStatus.USER_LOGGED_OFF, TransferStatus.DOWNLOAD_FOLDER_ERROR,
            TransferStatus.LOCAL_FILE_ERROR
        ]]
        
        # Check user online status properly using core.users.statuses
        user_status = core.users.statuses.get(username)
        is_online = user_status is not None and user_status != 0  # 0 = OFFLINE, 1 = AWAY, 2 = ONLINE
        
        # Convert status to human-readable string
        status_strings = {0: "Offline", 1: "Away", 2: "Online"}
        status_string = status_strings.get(user_status, "Unknown") if user_status is not None else "Unknown"
        
        user_stats.append(UserQueueStatsModel(
            username=username,
            total_queued_files=len(queued),
            active_transfers=len(active),
            failed_transfers=len(failed),
            queue_size_limit=core.downloads._user_queue_limits.get(username),
            is_online=is_online,
            status_value=user_status,
            status_string=status_string,
            queued_transfers=[t.virtual_path for t in queued],
            active_transfer_paths=[t.virtual_path for t in active],
            failed_transfer_paths=[t.virtual_path for t in failed],
            total_queued_size=sum(t.size for t in queued if t.size),
            average_queue_position=None,  # Would need more complex calculation
            estimated_total_wait_time=None  # Would need more complex calculation
        ))
    
    investigation_end = time.time()
    investigation_duration_ms = (investigation_end - investigation_start) * 1000
    
    return QueueInvestigationResponse(
        total_active_downloads=total_active,
        total_queued_downloads=total_queued,
        total_failed_downloads=total_failed,
        user_stats=user_stats,
        transfers=enhanced_transfers,
        average_queue_wait_time=average_queue_wait_time,
        most_queued_user=most_queued_user,
        connection_issues_count=connection_issues,
        timeout_issues_count=timeout_issues,
        investigation_timestamp=investigation_start,
        investigation_duration_ms=investigation_duration_ms
    )


# User Browse Endpoints

@app.post("/browse/user")
async def browse_user_shares(request: BrowseUserRequest):
    """Browse a user's shared files and folders."""
    
    try:
        # Check if userbrowse is available
        if not hasattr(core, 'userbrowse') or not core.userbrowse:
            return BrowseUserResponse(
                username=request.username,
                status="error",
                error="User browse functionality not available"
            )
        
        # Check if user is already browsed
        browsed_user = core.userbrowse.users.get(request.username)
        
        if browsed_user is None or request.new_request:
            # Start new browse request
            core.userbrowse.browse_user(
                request.username, 
                path=request.path, 
                new_request=request.new_request,
                switch_page=False
            )
            
            # Wait for browse to complete (with timeout)
            max_wait_time = request.timeout
            wait_interval = 0.5
            elapsed_time = 0
            
            while elapsed_time < max_wait_time:
                await asyncio.sleep(wait_interval)
                elapsed_time += wait_interval
                
                # Check if browse completed
                browsed_user = core.userbrowse.users.get(request.username)
                if browsed_user and (browsed_user.public_folders or browsed_user.private_folders):
                    break
            
            # Check final status
            browsed_user = core.userbrowse.users.get(request.username)
            if not browsed_user:
                return BrowseUserResponse(
                    username=request.username,
                    status="timeout",
                    error=f"Browse request timed out after {request.timeout} seconds"
                )
        
        # Convert browsed data to API response format
        public_folders = {}
        private_folders = {}
        total_files = 0
        total_size = 0
        
        if browsed_user.public_folders:
            for folder_path, files in browsed_user.public_folders.items():
                file_list = []
                for file_info in files:
                    # file_info format: [file_id, filename, filesize, extension, attributes]
                    if len(file_info) >= 3:
                        browse_file = BrowseFileInfo(
                            file_id=str(file_info[0]) if len(file_info) > 0 else None,
                            filename=file_info[1] if len(file_info) > 1 else "",
                            size=file_info[2] if len(file_info) > 2 else 0,
                            extension=file_info[3] if len(file_info) > 3 else "",
                            attributes=file_info[4] if len(file_info) > 4 else None
                        )
                        file_list.append(browse_file)
                        total_files += 1
                        total_size += browse_file.size
                
                public_folders[folder_path] = file_list
        
        if browsed_user.private_folders:
            for folder_path, files in browsed_user.private_folders.items():
                file_list = []
                for file_info in files:
                    if len(file_info) >= 3:
                        browse_file = BrowseFileInfo(
                            file_id=str(file_info[0]) if len(file_info) > 0 else None,
                            filename=file_info[1] if len(file_info) > 1 else "",
                            size=file_info[2] if len(file_info) > 2 else 0,
                            extension=file_info[3] if len(file_info) > 3 else "",
                            attributes=file_info[4] if len(file_info) > 4 else None
                        )
                        file_list.append(browse_file)
                        total_files += 1
                        total_size += browse_file.size
                
                private_folders[folder_path] = file_list
        
        # Get user online status information
        user_status = core.users.statuses.get(request.username)
        is_user_online = user_status is not None and user_status != 0  # 0 = OFFLINE, 1 = AWAY, 2 = ONLINE
        
        # Convert status to human-readable string
        status_strings = {0: "Offline", 1: "Away", 2: "Online"}
        user_status_string = status_strings.get(user_status, "Unknown") if user_status is not None else "Unknown"
        
        return BrowseUserResponse(
            username=request.username,
            status="success",
            public_folders=public_folders,
            private_folders=private_folders,
            total_files=total_files,
            total_size=total_size,
            user_status_value=user_status,
            user_status_string=user_status_string,
            is_user_online=is_user_online
        )
        
    except Exception as e:
        log.add(f"Error browsing user {request.username}: {e}")
        return BrowseUserResponse(
            username=request.username,
            status="error",
            error=str(e)
        )


@app.get("/browse/status/{username}")
async def get_browse_status(username: str):
    """Get the current browse status for a user."""
    
    try:
        if not hasattr(core, 'userbrowse') or not core.userbrowse:
            return BrowseStatusResponse(
                username=username,
                status="error",
                message="User browse functionality not available"
            )
        
        browsed_user = core.userbrowse.users.get(username)
        
        if browsed_user is None:
            return BrowseStatusResponse(
                username=username,
                status="not_found",
                message="User has not been browsed"
            )
        
        # Calculate folder and file counts
        folder_count = len(browsed_user.public_folders) + len(browsed_user.private_folders)
        file_count = 0
        
        for files in browsed_user.public_folders.values():
            file_count += len(files)
        for files in browsed_user.private_folders.values():
            file_count += len(files)
        
        return BrowseStatusResponse(
            username=username,
            status="completed" if folder_count > 0 or file_count > 0 else "empty",
            message=f"Browse completed with {file_count} files in {folder_count} folders",
            folder_count=folder_count,
            file_count=file_count
        )
        
    except Exception as e:
        log.add(f"Error getting browse status for {username}: {e}")
        return BrowseStatusResponse(
            username=username,
            status="error",
            message=str(e)
        )


# User Status Endpoints

def _get_user_status_info(username: str, request_if_unknown: bool = True) -> UserStatusModel:
    """Helper function to get user status information."""
    user_status = core.users.statuses.get(username)
    
    # If status is unknown and we should request it, try to get it by watching the user
    if user_status is None and request_if_unknown:
        try:
            # Watch the user to trigger a status request
            core.users.watch_user(username)
            
            # Give a brief moment for the status to be received
            import time
            time.sleep(0.1)
            
            # Check again
            user_status = core.users.statuses.get(username)
        except Exception as e:
            log.add(f"Failed to watch user {username} for status: {e}")
    
    is_online = user_status is not None and user_status != 0  # 0 = OFFLINE, 1 = AWAY, 2 = ONLINE
    
    # Convert status to human-readable string
    status_strings = {0: "Offline", 1: "Away", 2: "Online"}
    status_string = status_strings.get(user_status, "Unknown") if user_status is not None else "Unknown"
    
    return UserStatusModel(
        username=username,
        status_value=user_status,
        status_string=status_string,
        is_online=is_online,
        is_available=is_online
    )

@app.get("/user/status/{username}")
async def get_user_status(username: str):
    """Get online status for a specific user."""
    
    try:
        return _get_user_status_info(username)
        
    except Exception as e:
        log.add(f"Error getting user status for {username}: {e}")
        return UserStatusModel(
            username=username,
            status_value=None,
            status_string="Unknown",
            is_online=False,
            is_available=False
        )

@app.post("/user/status")
async def get_bulk_user_status(request: BulkUserStatusRequest):
    """Get online status for multiple users."""
    
    try:
        user_statuses = []
        online_count = 0
        offline_count = 0
        
        for username in request.usernames:
            try:
                user_status = _get_user_status_info(username)
                user_statuses.append(user_status)
                
                if user_status.is_online:
                    online_count += 1
                else:
                    offline_count += 1
                    
            except Exception as e:
                log.add(f"Error getting status for user {username}: {e}")
                # Add error entry for this user
                user_statuses.append(UserStatusModel(
                    username=username,
                    status_value=None,
                    status_string="Unknown",
                    is_online=False,
                    is_available=False
                ))
                offline_count += 1
        
        return BulkUserStatusResponse(
            user_statuses=user_statuses,
            total_users=len(request.usernames),
            online_count=online_count,
            offline_count=offline_count
        )
        
    except Exception as e:
        log.add(f"Error in bulk user status check: {e}")
        # Return empty response on error
        return BulkUserStatusResponse(
            user_statuses=[],
            total_users=0,
            online_count=0,
            offline_count=0
        )

'''
    Data needed for a download:

                "user") => 'merciero23'
                "file_path_data") => '@@xpgbc\\TEMAS COMPARTIDOS 2\\mp3\\4635732_Love___Happiness__Yemaya___Ochun__Feat__India_David_Penn_Vocal_Mix.mp3'
                "size_data") => 18527131
                "file_attributes_data") => 
'''
