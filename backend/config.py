"""Application configuration using Pydantic Settings."""

from pathlib import Path
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Application
    app_name: str = "GodDamnEye"
    app_version: str = "0.1.0"
    debug: bool = False

    # Database
    database_url: str = "sqlite+aiosqlite:///./data/goddamneye.db"

    # Storage
    storage_path: Path = Path("./storage")
    hls_path: Path = Path("/tmp/goddamneye/hls")

    # Recording settings
    recording_segment_duration: int = 3600  # 1 hour in seconds
    recording_retention_days: int = 30

    # Recording encoding settings (H.265/HEVC via libx265)
    # CRF (Constant Rate Factor): 0-51, lower = better quality, higher = smaller files
    # 23 = good quality, 28 = good balance, 32 = smaller files
    recording_crf: int = 28
    # Encoding speed preset - tradeoff between encode time and file size:
    # - "fast": Quick encoding, larger files. Use if CPU is limited.
    # - "balanced": Good default. Moderate encode time, good compression.
    # - "compact": Slow encoding, smallest files. Maximum storage savings.
    recording_quality: str = "balanced"
    # Scale down recordings to save space (e.g., "1280:720" for 720p, "" to keep original)
    recording_scale: str = ""

    def get_x265_preset(self) -> str:
        """Get x265 preset based on quality setting.

        Returns:
            x265 preset string for FFmpeg.
        """
        presets = {
            "fast": "veryfast",      # Quick encode, larger files
            "balanced": "fast",       # Good balance (default)
            "compact": "medium",      # Slow encode, smallest files
        }
        return presets.get(self.recording_quality.lower(), presets["balanced"])

    # FFmpeg
    ffmpeg_path: str = "ffmpeg"

    # Server
    host: str = "0.0.0.0"
    port: int = 8000

    # CORS (for frontend)
    cors_origins: list[str] = ["http://localhost:3000", "http://localhost:5173"]

    # Future: SSO OAuth settings (placeholders)
    # oauth_enabled: bool = False
    # oauth_issuer_url: str = ""
    # oauth_client_id: str = ""

    def get_storage_path(self) -> Path:
        """Ensure storage path exists and return it."""
        self.storage_path.mkdir(parents=True, exist_ok=True)
        return self.storage_path

    def get_hls_path(self) -> Path:
        """Ensure HLS path exists and return it."""
        self.hls_path.mkdir(parents=True, exist_ok=True)
        return self.hls_path


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
