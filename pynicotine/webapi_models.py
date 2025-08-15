from pydantic import BaseModel
from typing import Optional, Dict, List

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

class WebApiSearchModel(BaseModel):
    search_term: str
    wait_for_seconds: int
    search_filters: Optional[dict] = None
    smart_filters: Optional[bool] = None
    

class FileToDownload(BaseModel):
    file_owner: str
    file_virtual_path: str
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


# User Browse API Models

class BrowseUserRequest(BaseModel):
    username: str
    path: Optional[str] = None
    new_request: Optional[bool] = True
    timeout: Optional[int] = 30

class BrowseFileInfo(BaseModel):
    file_id: Optional[str] = None
    filename: str
    size: int
    extension: Optional[str] = ""
    attributes: Optional[Dict] = None

class BrowseFolderData(BaseModel):
    folder_path: str
    files: List[BrowseFileInfo]

class BrowseUserResponse(BaseModel):
    username: str
    status: str  # "success", "error", "timeout", "pending"
    public_folders: Optional[Dict[str, List[BrowseFileInfo]]] = None
    private_folders: Optional[Dict[str, List[BrowseFileInfo]]] = None
    total_files: Optional[int] = 0
    total_size: Optional[int] = 0
    error: Optional[str] = None
    
    # User online status information
    user_status_value: Optional[int] = None  # 0 = Offline, 1 = Away, 2 = Online
    user_status_string: Optional[str] = None  # "Offline", "Away", "Online", "Unknown"
    is_user_online: Optional[bool] = None  # True if Away or Online, False if Offline

class BrowseStatusResponse(BaseModel):
    username: str
    status: str  # "browsing", "completed", "error", "not_found"
    message: Optional[str] = None
    last_updated: Optional[str] = None
    folder_count: Optional[int] = 0
    file_count: Optional[int] = 0


# User Status API Models

class UserStatusModel(BaseModel):
    """Individual user status information."""
    username: str
    status_value: Optional[int] = None  # 0 = Offline, 1 = Away, 2 = Online, None = Unknown
    status_string: str  # "Offline", "Away", "Online", "Unknown"
    is_online: bool  # True if Away or Online, False if Offline or Unknown
    is_available: bool  # Same as is_online - users are available when Away or Online

class BulkUserStatusRequest(BaseModel):
    """Request model for checking status of multiple users."""
    usernames: List[str]  # List of usernames to check

class BulkUserStatusResponse(BaseModel):
    """Response model for bulk user status checking."""
    user_statuses: List[UserStatusModel]
    total_users: int
    online_count: int  # Users with status Away or Online
    offline_count: int  # Users with status Offline or Unknown


# Enhanced Download/Queue Investigation Models

class EnhancedTransferModel(BaseModel):
    """Enhanced transfer model with detailed queue and status information."""
    username: str
    virtual_path: str
    download_path: str
    status: str
    size: int
    current_byte_offset: Optional[int] = None
    download_percentage: Optional[str] = None
    file_attributes: Optional[dict] = None
    
    # Enhanced queue investigation fields
    queue_position: Optional[int] = None
    speed: Optional[int] = None  # bytes per second
    time_elapsed: Optional[float] = None  # seconds
    time_left: Optional[float] = None  # estimated seconds remaining
    start_time: Optional[float] = None  # timestamp when transfer started
    last_update: Optional[float] = None  # timestamp of last status update
    
    # Error and connection details
    modifier: Optional[str] = None  # additional status modifier
    token: Optional[str] = None  # transfer token/id
    
    # Calculated fields
    eta_seconds: Optional[float] = None  # estimated time to completion
    is_stalled: Optional[bool] = False  # true if no progress for extended time
    wait_time: Optional[float] = None  # time spent waiting in queue


class UserQueueStatsModel(BaseModel):
    """Statistics about files queued for a specific user."""
    username: str
    total_queued_files: int
    active_transfers: int
    failed_transfers: int
    queue_size_limit: Optional[int] = None
    is_online: bool
    
    # Detailed online status information
    status_value: Optional[int] = None  # 0 = Offline, 1 = Away, 2 = Online
    status_string: Optional[str] = None  # "Offline", "Away", "Online", "Unknown"
    
    # Detailed breakdowns
    queued_transfers: List[str] = []  # virtual paths of queued files
    active_transfer_paths: List[str] = []  # currently downloading files
    failed_transfer_paths: List[str] = []  # failed transfer paths
    
    # Statistics
    total_queued_size: Optional[int] = None  # total bytes queued
    average_queue_position: Optional[float] = None
    estimated_total_wait_time: Optional[float] = None  # seconds


class QueueInvestigationRequest(BaseModel):
    """Request model for investigating download queues and status."""
    username: Optional[str] = None  # investigate specific user (None = all users)
    virtual_path: Optional[str] = None  # investigate specific file
    include_completed: Optional[bool] = False
    include_failed: Optional[bool] = True
    max_results: Optional[int] = 100


class QueueInvestigationResponse(BaseModel):
    """Detailed response for queue investigation."""
    total_active_downloads: int
    total_queued_downloads: int
    total_failed_downloads: int
    
    # Per-user statistics
    user_stats: List[UserQueueStatsModel] = []
    
    # Detailed transfer information
    transfers: List[EnhancedTransferModel] = []
    
    # System-wide queue analysis
    average_queue_wait_time: Optional[float] = None
    most_queued_user: Optional[str] = None
    connection_issues_count: int = 0
    timeout_issues_count: int = 0
    
    # Investigation metadata
    investigation_timestamp: float
    investigation_duration_ms: float