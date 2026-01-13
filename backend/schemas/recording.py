"""Pydantic schemas for Recording API."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class RecordingBase(BaseModel):
    """Base schema for recording fields."""

    camera_id: str
    file_path: str
    start_time: datetime
    end_time: datetime | None = None
    duration_seconds: int | None = None
    file_size: int | None = None


class RecordingResponse(BaseModel):
    """Schema for recording response."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    camera_id: str
    file_path: str
    file_size: int | None
    start_time: datetime
    end_time: datetime | None
    duration_seconds: int | None
    created_at: datetime

    # Computed fields for convenience
    camera_name: str | None = Field(None, description="Camera name (populated from join)")


class RecordingListParams(BaseModel):
    """Query parameters for listing recordings."""

    camera_id: str | None = None
    start_date: datetime | None = None
    end_date: datetime | None = None
    limit: int = Field(default=100, ge=1, le=1000)
    offset: int = Field(default=0, ge=0)


class RecordingStats(BaseModel):
    """Statistics about recordings."""

    total_recordings: int
    total_size_bytes: int
    oldest_recording: datetime | None
    newest_recording: datetime | None
    cameras_with_recordings: int


class StorageStats(BaseModel):
    """Storage statistics from filesystem."""

    storage_path: str
    total_size_bytes: int
    total_size_gb: float
    file_count: int
    retention_days: int
