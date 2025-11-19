"""
Cloud Tasks job management module.

This module provides:
- Job enqueueing to Google Cloud Tasks
- Job status tracking
- Task scheduling and retry logic
- Worker endpoint handling
"""

from google.cloud import tasks_v2
from google.cloud.tasks_v2 import Task, HttpRequest
from google.protobuf import timestamp_pb2, duration_pb2
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
import json
import logging
import uuid

from .config import settings


# Configure logging
logger = logging.getLogger(__name__)


# ============================================
# CLOUD TASKS CLIENT
# ============================================

class CloudTasksClient:
    """
    Wrapper for Google Cloud Tasks client with helper methods.
    """

    def __init__(self):
        """Initialize Cloud Tasks client."""
        self._client: Optional[tasks_v2.CloudTasksClient] = None
        self._project = settings.cloud_tasks_project
        self._location = settings.CLOUD_TASKS_LOCATION

    @property
    def client(self) -> tasks_v2.CloudTasksClient:
        """
        Get or create Cloud Tasks client.

        Returns:
            Cloud Tasks client instance
        """
        if self._client is None:
            try:
                self._client = tasks_v2.CloudTasksClient()
                logger.info("Cloud Tasks client initialized")
            except Exception as e:
                logger.error(f"Failed to initialize Cloud Tasks client: {e}", exc_info=True)
                raise
        return self._client

    def get_queue_path(self, queue_name: str) -> str:
        """
        Get full queue path.

        Args:
            queue_name: Queue name

        Returns:
            Full queue path
        """
        return self.client.queue_path(
            self._project,
            self._location,
            queue_name
        )

    def create_http_task(
        self,
        queue_name: str,
        url: str,
        payload: Dict[str, Any],
        schedule_time: Optional[datetime] = None,
        task_name: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Task:
        """
        Create an HTTP task in Cloud Tasks queue.

        Args:
            queue_name: Name of the queue
            url: Target URL for the task
            payload: Task payload (will be JSON encoded)
            schedule_time: Optional scheduled execution time
            task_name: Optional task name
            headers: Optional HTTP headers

        Returns:
            Created task

        Raises:
            Exception: If task creation fails
        """
        try:
            # Get queue path
            queue_path = self.get_queue_path(queue_name)

            # Prepare payload
            json_payload = json.dumps(payload).encode()

            # Build HTTP request
            http_request = HttpRequest(
                url=url,
                http_method=tasks_v2.HttpMethod.POST,
                body=json_payload,
            )

            # Add headers
            http_request.headers = headers or {}
            http_request.headers["Content-Type"] = "application/json"

            # Build task
            task = Task(http_request=http_request)

            # Add task name if provided
            if task_name:
                task_path = f"{queue_path}/tasks/{task_name}"
                task.name = task_path

            # Add schedule time if provided
            if schedule_time:
                timestamp = timestamp_pb2.Timestamp()
                timestamp.FromDatetime(schedule_time)
                task.schedule_time = timestamp

            # Create the task
            response = self.client.create_task(
                request={"parent": queue_path, "task": task}
            )

            logger.info(f"Created task: {response.name}")
            return response

        except Exception as e:
            logger.error(f"Failed to create task: {e}", exc_info=True)
            raise

    def delete_task(self, task_name: str):
        """
        Delete a task from the queue.

        Args:
            task_name: Full task name/path
        """
        try:
            self.client.delete_task(name=task_name)
            logger.info(f"Deleted task: {task_name}")
        except Exception as e:
            logger.error(f"Failed to delete task {task_name}: {e}", exc_info=True)
            raise

    def get_task(self, task_name: str) -> Task:
        """
        Get task details.

        Args:
            task_name: Full task name/path

        Returns:
            Task details
        """
        try:
            return self.client.get_task(name=task_name)
        except Exception as e:
            logger.error(f"Failed to get task {task_name}: {e}", exc_info=True)
            raise


# Global client instance
_tasks_client = CloudTasksClient()


# ============================================
# JOB ENQUEUEING
# ============================================

async def enqueue_lead_extraction_job(
    campaign_id: str,
    target_count: int,
    sources: List[str],
    filters: Optional[Dict[str, Any]] = None
) -> str:
    """
    Enqueue a lead extraction job to Cloud Tasks.

    Args:
        campaign_id: Campaign ID
        target_count: Target number of leads to extract
        sources: List of extraction sources
        filters: Optional extraction filters

    Returns:
        Job ID for tracking
    """
    job_id = str(uuid.uuid4())

    # Build payload
    payload = {
        "job_id": job_id,
        "job_type": "lead_extraction",
        "campaign_id": campaign_id,
        "target_count": target_count,
        "sources": sources,
        "filters": filters or {},
        "created_at": datetime.utcnow().isoformat(),
    }

    # Get worker URL
    worker_url = settings.WORKER_SERVICE_URL
    if not worker_url:
        logger.warning("WORKER_SERVICE_URL not configured, using local endpoint")
        worker_url = f"{settings.API_BASE_URL}/worker/extract-leads"
    else:
        worker_url = f"{worker_url}/worker/extract-leads"

    try:
        # Create task
        task = _tasks_client.create_http_task(
            queue_name=settings.LEAD_EXTRACTION_QUEUE,
            url=worker_url,
            payload=payload,
            task_name=f"extraction-{job_id}",
        )

        logger.info(
            f"Enqueued lead extraction job {job_id} for campaign {campaign_id}"
        )

        # Store job status (in production, use Firestore or database)
        await _store_job_status(
            job_id=job_id,
            job_type="extraction",
            status="pending",
            metadata={
                "campaign_id": campaign_id,
                "target_count": target_count,
                "task_name": task.name,
            }
        )

        return job_id

    except Exception as e:
        logger.error(f"Failed to enqueue lead extraction job: {e}", exc_info=True)
        raise


async def enqueue_outreach_job(
    campaign_id: str,
    lead_ids: List[str],
    channels: List[str],
    schedule: Optional[Dict[str, Any]] = None
) -> str:
    """
    Enqueue an outreach job to Cloud Tasks.

    Args:
        campaign_id: Campaign ID
        lead_ids: List of lead IDs to contact
        channels: Communication channels to use
        schedule: Optional outreach schedule

    Returns:
        Job ID for tracking
    """
    job_id = str(uuid.uuid4())

    # Build payload
    payload = {
        "job_id": job_id,
        "job_type": "outreach",
        "campaign_id": campaign_id,
        "lead_ids": lead_ids,
        "channels": channels,
        "schedule": schedule or {},
        "created_at": datetime.utcnow().isoformat(),
    }

    # Get worker URL
    worker_url = settings.WORKER_SERVICE_URL
    if not worker_url:
        logger.warning("WORKER_SERVICE_URL not configured, using local endpoint")
        worker_url = f"{settings.API_BASE_URL}/worker/run-outreach"
    else:
        worker_url = f"{worker_url}/worker/run-outreach"

    try:
        # Create task
        task = _tasks_client.create_http_task(
            queue_name=settings.OUTREACH_QUEUE,
            url=worker_url,
            payload=payload,
            task_name=f"outreach-{job_id}",
        )

        logger.info(
            f"Enqueued outreach job {job_id} for campaign {campaign_id} "
            f"({len(lead_ids)} leads)"
        )

        # Store job status
        await _store_job_status(
            job_id=job_id,
            job_type="outreach",
            status="pending",
            metadata={
                "campaign_id": campaign_id,
                "lead_count": len(lead_ids),
                "channels": channels,
                "task_name": task.name,
            }
        )

        return job_id

    except Exception as e:
        logger.error(f"Failed to enqueue outreach job: {e}", exc_info=True)
        raise


async def enqueue_scheduled_task(
    task_type: str,
    payload: Dict[str, Any],
    schedule_time: datetime,
    task_id: Optional[str] = None
) -> str:
    """
    Enqueue a task scheduled for future execution.

    Args:
        task_type: Type of task (determines which queue to use)
        payload: Task payload
        schedule_time: When to execute the task
        task_id: Optional task ID

    Returns:
        Task ID
    """
    task_id = task_id or str(uuid.uuid4())

    # Determine queue and URL based on task type
    if task_type == "email_followup":
        queue_name = settings.OUTREACH_QUEUE
        endpoint = "/worker/send-email"
    elif task_type == "sms_followup":
        queue_name = settings.OUTREACH_QUEUE
        endpoint = "/worker/send-sms"
    elif task_type == "call_followup":
        queue_name = settings.OUTREACH_QUEUE
        endpoint = "/worker/make-call"
    else:
        raise ValueError(f"Unknown task type: {task_type}")

    # Build worker URL
    worker_url = settings.WORKER_SERVICE_URL
    if not worker_url:
        worker_url = f"{settings.API_BASE_URL}{endpoint}"
    else:
        worker_url = f"{worker_url}{endpoint}"

    try:
        # Create scheduled task
        task = _tasks_client.create_http_task(
            queue_name=queue_name,
            url=worker_url,
            payload=payload,
            schedule_time=schedule_time,
            task_name=f"{task_type}-{task_id}",
        )

        logger.info(
            f"Scheduled {task_type} task {task_id} for {schedule_time.isoformat()}"
        )

        return task_id

    except Exception as e:
        logger.error(f"Failed to schedule task: {e}", exc_info=True)
        raise


# ============================================
# JOB STATUS TRACKING
# ============================================

# In-memory job status cache (use Firestore or Redis in production)
_job_status_cache: Dict[str, Dict[str, Any]] = {}


async def _store_job_status(
    job_id: str,
    job_type: str,
    status: str,
    metadata: Optional[Dict[str, Any]] = None
):
    """
    Store job status.

    In production, this should use Firestore or a database.

    Args:
        job_id: Job ID
        job_type: Type of job
        status: Job status
        metadata: Optional metadata
    """
    now = datetime.utcnow()

    _job_status_cache[job_id] = {
        "job_id": job_id,
        "job_type": job_type,
        "status": status,
        "metadata": metadata or {},
        "created_at": now,
        "updated_at": now,
        "progress": 0,
    }

    logger.debug(f"Stored status for job {job_id}: {status}")


async def update_job_status(
    job_id: str,
    status: str,
    progress: Optional[int] = None,
    results: Optional[Dict[str, Any]] = None,
    error: Optional[str] = None
):
    """
    Update job status.

    Args:
        job_id: Job ID
        status: New status
        progress: Optional progress percentage (0-100)
        results: Optional results data
        error: Optional error message
    """
    if job_id not in _job_status_cache:
        logger.warning(f"Job {job_id} not found in cache")
        return

    job_status = _job_status_cache[job_id]
    job_status["status"] = status
    job_status["updated_at"] = datetime.utcnow()

    if progress is not None:
        job_status["progress"] = progress

    if results is not None:
        job_status["results"] = results

    if error is not None:
        job_status["error"] = error

    if status == "completed":
        job_status["completed_at"] = datetime.utcnow()
        job_status["progress"] = 100

    logger.info(f"Updated job {job_id} status to {status}")


async def get_job_status(job_id: str, job_type: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """
    Get job status.

    Args:
        job_id: Job ID
        job_type: Optional job type for filtering

    Returns:
        Job status dict or None if not found
    """
    job_status = _job_status_cache.get(job_id)

    if job_status and job_type and job_status.get("job_type") != job_type:
        return None

    return job_status


async def list_jobs(
    job_type: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 100
) -> List[Dict[str, Any]]:
    """
    List jobs with optional filtering.

    Args:
        job_type: Optional job type filter
        status: Optional status filter
        limit: Maximum number of jobs to return

    Returns:
        List of job status dicts
    """
    jobs = list(_job_status_cache.values())

    # Filter by type
    if job_type:
        jobs = [j for j in jobs if j.get("job_type") == job_type]

    # Filter by status
    if status:
        jobs = [j for j in jobs if j.get("status") == status]

    # Sort by created_at (newest first)
    jobs.sort(key=lambda x: x.get("created_at", datetime.min), reverse=True)

    # Limit results
    return jobs[:limit]


# ============================================
# TASK MANAGEMENT
# ============================================

async def cancel_task(task_name: str):
    """
    Cancel a scheduled task.

    Args:
        task_name: Full task name/path
    """
    try:
        _tasks_client.delete_task(task_name)
        logger.info(f"Cancelled task: {task_name}")
    except Exception as e:
        logger.error(f"Failed to cancel task {task_name}: {e}", exc_info=True)
        raise


async def cancel_campaign_tasks(campaign_id: str):
    """
    Cancel all tasks associated with a campaign.

    Args:
        campaign_id: Campaign ID
    """
    # In production, query Firestore for all tasks associated with campaign
    # and delete them from Cloud Tasks
    logger.info(f"Cancelling all tasks for campaign {campaign_id}")

    # Find jobs for this campaign
    jobs_to_cancel = [
        job for job in _job_status_cache.values()
        if job.get("metadata", {}).get("campaign_id") == campaign_id
        and job.get("status") in ["pending", "running"]
    ]

    for job in jobs_to_cancel:
        task_name = job.get("metadata", {}).get("task_name")
        if task_name:
            try:
                await cancel_task(task_name)
                await update_job_status(
                    job["job_id"],
                    status="cancelled",
                    error="Cancelled by user"
                )
            except Exception as e:
                logger.error(f"Failed to cancel task for job {job['job_id']}: {e}")


# ============================================
# UTILITY FUNCTIONS
# ============================================

def calculate_schedule_time(
    base_time: Optional[datetime] = None,
    delay_days: int = 0,
    delay_hours: int = 0,
    delay_minutes: int = 0
) -> datetime:
    """
    Calculate a scheduled execution time.

    Args:
        base_time: Base time (defaults to now)
        delay_days: Days to add
        delay_hours: Hours to add
        delay_minutes: Minutes to add

    Returns:
        Scheduled execution time
    """
    if base_time is None:
        base_time = datetime.utcnow()

    return base_time + timedelta(
        days=delay_days,
        hours=delay_hours,
        minutes=delay_minutes
    )


def batch_leads_for_processing(
    lead_ids: List[str],
    batch_size: int = 100
) -> List[List[str]]:
    """
    Split leads into batches for processing.

    Args:
        lead_ids: List of lead IDs
        batch_size: Size of each batch

    Returns:
        List of lead ID batches
    """
    return [
        lead_ids[i:i + batch_size]
        for i in range(0, len(lead_ids), batch_size)
    ]


# ============================================
# EXPORTS
# ============================================

__all__ = [
    # Client
    "CloudTasksClient",
    # Job enqueueing
    "enqueue_lead_extraction_job",
    "enqueue_outreach_job",
    "enqueue_scheduled_task",
    # Job status
    "get_job_status",
    "update_job_status",
    "list_jobs",
    # Task management
    "cancel_task",
    "cancel_campaign_tasks",
    # Utilities
    "calculate_schedule_time",
    "batch_leads_for_processing",
]
