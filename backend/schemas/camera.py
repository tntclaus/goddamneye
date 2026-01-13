"""Pydantic schemas for Camera API."""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, SecretStr


class CameraStatusEnum(str, Enum):
    """Camera connection status."""

    ONLINE = "online"
    OFFLINE = "offline"
    CONNECTING = "connecting"
    ERROR = "error"


class CameraBase(BaseModel):
    """Base schema with common camera fields."""

    name: str = Field(..., min_length=1, max_length=255, examples=["Front Door"])
    description: str | None = Field(None, max_length=1000)
    rtsp_url: str = Field(..., examples=["rtsp://192.168.1.100:554/stream1"])
    onvif_host: str | None = Field(None, examples=["192.168.1.100"])
    onvif_port: int = Field(default=80, ge=1, le=65535)
    username: str | None = Field(None, max_length=255)
    enabled: bool = Field(default=True)
    recording_enabled: bool = Field(default=True)


class CameraCreate(CameraBase):
    """Schema for creating a new camera."""

    password: SecretStr | None = Field(None)


class CameraUpdate(BaseModel):
    """Schema for updating an existing camera."""

    name: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = None
    rtsp_url: str | None = None
    onvif_host: str | None = None
    onvif_port: int | None = Field(None, ge=1, le=65535)
    username: str | None = None
    password: SecretStr | None = None
    enabled: bool | None = None
    recording_enabled: bool | None = None


class CameraResponse(BaseModel):
    """Schema for camera response (no sensitive data)."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    description: str | None
    rtsp_url: str
    onvif_host: str | None
    onvif_port: int
    username: str | None

    # Metadata
    manufacturer: str | None
    model: str | None
    firmware_version: str | None
    serial_number: str | None

    # Status
    enabled: bool
    recording_enabled: bool
    is_online: bool

    # Timestamps
    created_at: datetime
    updated_at: datetime
    last_seen_at: datetime | None


class CameraStatus(BaseModel):
    """Schema for camera status update."""

    id: str
    status: CameraStatusEnum
    is_recording: bool = False
    stream_url: str | None = None
    error_message: str | None = None


class CameraDiscovered(BaseModel):
    """Schema for discovered camera from ONVIF."""

    host: str
    port: int = 80
    name: str | None = None
    manufacturer: str | None = None
    model: str | None = None
    firmware_version: str | None = None
    serial_number: str | None = None
    rtsp_urls: list[str] = Field(default_factory=list)
    onvif_url: str | None = None
