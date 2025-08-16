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


# Share Accessibility Verification Models

class ShareVerificationRequest(BaseModel):
    """Request model for verifying share accessibility."""
    usernames: List[str]  # List of usernames to verify
    verify_browse: Optional[bool] = True  # Test if we can browse their shares
    verify_download: Optional[bool] = False  # Test if we can download from them
    timeout_seconds: Optional[int] = 30  # Timeout for each verification
    include_file_sampling: Optional[bool] = False  # Sample files for availability testing

class ShareHealthMetrics(BaseModel):
    """Detailed health metrics for a user's share."""
    username: str
    is_accessible: bool
    connection_success: bool
    browse_success: bool
    download_test_success: Optional[bool] = None
    
    # Connection metrics
    connection_time_ms: Optional[float] = None
    response_time_ms: Optional[float] = None
    
    # Share content metrics
    total_files: Optional[int] = None
    total_size: Optional[int] = None
    accessible_folders: Optional[int] = None
    
    # Quality metrics
    reliability_score: Optional[float] = None  # 0-100 score
    last_successful_connection: Optional[str] = None
    consecutive_failures: Optional[int] = 0
    
    # Error details
    error_type: Optional[str] = None  # "timeout", "connection_failed", "browse_failed", etc.
    error_message: Optional[str] = None
    
    # Verification timestamp
    verified_at: float

class ShareVerificationResponse(BaseModel):
    """Response model for share verification."""
    total_users_verified: int
    successful_verifications: int
    failed_verifications: int
    
    # Detailed results per user
    share_health_reports: List[ShareHealthMetrics]
    
    # Summary statistics
    average_connection_time_ms: Optional[float] = None
    average_reliability_score: Optional[float] = None
    
    # Verification metadata
    verification_started_at: float
    verification_completed_at: float
    total_verification_time_ms: float

class ShareMonitoringRequest(BaseModel):
    """Request model for continuous share monitoring."""
    usernames: List[str]
    check_interval_minutes: Optional[int] = 60  # How often to check
    alert_on_failure: Optional[bool] = True
    max_consecutive_failures: Optional[int] = 3
    notification_webhook: Optional[str] = None

class ShareMonitoringResponse(BaseModel):
    """Response model for share monitoring setup."""
    monitoring_id: str
    usernames: List[str]
    status: str  # "active", "paused", "error"
    next_check_at: Optional[str] = None
    created_at: float


# Performance Metrics Models

class ApiPerformanceMetrics(BaseModel):
    """Current API performance metrics."""
    # Request metrics
    total_requests: int
    requests_per_minute: float
    average_response_time_ms: float
    
    # Endpoint-specific metrics
    endpoint_stats: Dict[str, Dict] = {}  # endpoint -> {count, avg_time, errors}
    
    # Error metrics
    total_errors: int
    error_rate_percentage: float
    recent_errors: List[str] = []  # Last few error messages
    
    # Resource usage
    active_connections: int
    memory_usage_mb: Optional[float] = None
    cpu_usage_percentage: Optional[float] = None
    
    # Transfer metrics
    active_downloads: int
    download_speed_mbps: Optional[float] = None
    total_downloaded_mb: Optional[float] = None
    
    # Queue metrics
    queued_operations: int
    longest_queue_wait_time_ms: Optional[float] = None
    
    # Timestamp
    measured_at: float

class SystemLimitsInfo(BaseModel):
    """Current system limits and usage."""
    # Connection limits
    max_simultaneous_connections: int
    current_connections: int
    connection_usage_percentage: float
    
    # Search limits
    max_simultaneous_searches: int
    current_searches: int
    search_usage_percentage: float
    
    # Download limits
    max_downloads: Optional[int] = None
    current_downloads: int
    download_queue_size: int
    
    # Rate limiting info
    rate_limit_per_minute: Optional[int] = None
    current_rate: float
    rate_limit_usage_percentage: Optional[float] = None
    
    # Memory and storage
    available_memory_mb: Optional[float] = None
    used_memory_mb: Optional[float] = None
    available_storage_gb: Optional[float] = None
    
    # Timestamp
    measured_at: float

class PerformanceOptimizationRequest(BaseModel):
    """Request model for performance optimization."""
    optimize_connections: Optional[bool] = True
    clear_old_data: Optional[bool] = True
    rebuild_indexes: Optional[bool] = False
    max_optimization_time_minutes: Optional[int] = 5

class PerformanceOptimizationResponse(BaseModel):
    """Response model for performance optimization."""
    optimization_id: str
    status: str  # "running", "completed", "error"
    actions_performed: List[str] = []
    performance_improvement: Optional[str] = None
    
    # Before/after metrics
    before_metrics: Optional[Dict] = None
    after_metrics: Optional[Dict] = None
    
    # Timing
    started_at: float
    completed_at: Optional[float] = None
    duration_ms: Optional[float] = None