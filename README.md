# GodDamnEye

Open-source CCTV camera management system with RTSP/ONVIF support, local video storage, and web interface. Built for self-hosting.

## Features

- **ONVIF Discovery** - Automatically discover cameras on your network
- **RTSP Streaming** - Connect to any RTSP-compatible camera
- **Live View** - HLS streaming for browser-native playback
- **Recording** - Continuous recording with hourly MP4 segments
- **Storage Management** - Automatic cleanup based on retention policy
- **Dark Theme UI** - Modern React interface with Ant Design

## Quick Start

### Using Docker (Recommended)

```bash
# Clone the repository
git clone https://github.com/yourusername/goddamneye.git
cd goddamneye

# Copy environment file
cp .env.example .env

# Start services
docker-compose up -d

# Open in browser
# Backend API: http://localhost:8000
# Frontend UI: http://localhost:3000
```

### Manual Setup

#### Backend

```bash
# Python 3.11+ required
cd goddamneye

# Install dependencies
pip install -e .

# Or with uv (faster)
uv pip install -e .

# Run the server
python -m backend.main
```

#### Frontend

```bash
cd frontend

# Install dependencies
npm install

# Development server
npm run dev

# Production build
npm run build
```

## Configuration

Environment variables can be set in `.env` file:

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `sqlite+aiosqlite:///./data/goddamneye.db` | Database connection URL |
| `STORAGE_PATH` | `./storage` | Path for video recordings |
| `HLS_PATH` | `/tmp/goddamneye/hls` | Path for HLS stream segments |
| `RECORDING_RETENTION_DAYS` | `30` | Days to keep recordings |
| `RECORDING_SEGMENT_DURATION` | `3600` | Recording segment length (seconds) |
| `FFMPEG_PATH` | `ffmpeg` | Path to FFmpeg binary |
| `HOST` | `0.0.0.0` | Server bind address |
| `PORT` | `8000` | Server port |
| `DEBUG` | `false` | Enable debug mode |

## API Reference

### Cameras

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/cameras` | GET | List all cameras |
| `/api/cameras` | POST | Add a new camera |
| `/api/cameras/{id}` | GET | Get camera details |
| `/api/cameras/{id}` | PUT | Update camera |
| `/api/cameras/{id}` | DELETE | Delete camera |
| `/api/cameras/discover` | POST | ONVIF network discovery |
| `/api/cameras/probe` | POST | Probe specific camera |
| `/api/cameras/{id}/enable` | POST | Enable camera |
| `/api/cameras/{id}/disable` | POST | Disable camera |

### Streams

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/streams/status` | GET | All streams status |
| `/api/streams/{id}/status` | GET | Stream status |
| `/api/streams/{id}/start` | POST | Start streaming |
| `/api/streams/{id}/stop` | POST | Stop streaming |
| `/api/streams/{id}/restart` | POST | Restart stream |
| `/api/streams/{id}/hls/{file}` | GET | HLS segment files |

### Recordings

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/recordings` | GET | List recordings (with filters) |
| `/api/recordings/stats` | GET | Recording statistics |
| `/api/recordings/storage/stats` | GET | Storage statistics |
| `/api/recordings/scan` | POST | Scan for new files |
| `/api/recordings/cleanup` | POST | Cleanup old recordings |
| `/api/recordings/{id}` | GET | Get recording details |
| `/api/recordings/{id}/download` | GET | Download recording |
| `/api/recordings/{id}` | DELETE | Delete recording |

### System

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/api/system/status` | GET | System status |
| `/api/system/settings` | GET | Current settings |

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         GodDamnEye                               │
├─────────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐   │
│  │   Frontend   │  │   Backend    │  │   Stream Workers     │   │
│  │   (React)    │◄─┤   (FastAPI)  │◄─┤   (FFmpeg procs)     │   │
│  │   Port 3000  │  │   Port 8000  │  │   Per-camera         │   │
│  └──────────────┘  └──────┬───────┘  └──────────┬───────────┘   │
│                           │                      │               │
│                    ┌──────▼───────┐      ┌──────▼───────┐       │
│                    │   SQLite DB  │      │  Video Files │       │
│                    │  (metadata)  │      │  (storage/)  │       │
│                    └──────────────┘      └──────────────┘       │
└─────────────────────────────────────────────────────────────────┘
                              │
                    ┌─────────▼─────────┐
                    │   ONVIF/RTSP      │
                    │   IP Cameras      │
                    └───────────────────┘
```

## Storage Structure

Recordings are stored in hourly MP4 files:

```
storage/
└── recordings/
    └── {camera_id}/
        └── {YYYY-MM-DD}/
            ├── 00.mp4    # 00:00-01:00
            ├── 01.mp4    # 01:00-02:00
            ├── ...
            └── 23.mp4    # 23:00-24:00
```

## Technology Stack

| Component | Technology |
|-----------|------------|
| Backend | Python 3.11+ / FastAPI |
| Frontend | React 18 + TypeScript + Vite |
| UI Library | Ant Design 5 (dark theme) |
| Database | SQLite (SQLAlchemy ORM) |
| Video Processing | FFmpeg |
| Camera Discovery | ONVIF (python-onvif-zeep) |
| Streaming | HLS via FFmpeg |
| Video Playback | HLS.js |
| Deployment | Docker + Docker Compose |

## Development

### Project Structure

```
goddamneye/
├── backend/
│   ├── api/routes/      # API endpoints
│   ├── core/            # Database, security
│   ├── models/          # SQLAlchemy models
│   ├── schemas/         # Pydantic schemas
│   ├── services/        # Business logic
│   │   ├── camera_manager.py    # Camera lifecycle
│   │   ├── stream_worker.py     # FFmpeg processes
│   │   ├── storage_manager.py   # Recording cleanup
│   │   └── onvif_discovery.py   # Camera discovery
│   └── main.py          # App entry point
├── frontend/
│   └── src/
│       ├── components/  # React components
│       ├── pages/       # Page components
│       ├── hooks/       # Custom hooks
│       └── api/         # API client
├── docker-compose.yml
├── Dockerfile
└── pyproject.toml
```

### Running Tests

```bash
# Backend tests
pytest tests/ -v

# With coverage
pytest tests/ --cov=backend
```

### API Documentation

When running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Future Plans

- [ ] SSO/OAuth authentication integration
- [ ] Motion detection alerts
- [ ] PTZ camera control
- [ ] Multi-server federation
- [ ] Mobile app support
- [ ] Event timeline view
- [ ] PostgreSQL support for larger deployments

## Troubleshooting

### Camera not connecting

1. Verify RTSP URL is correct
2. Check camera credentials
3. Ensure camera is on the same network
4. Try TCP transport: `rtsp_transport=tcp`

### HLS stream not playing

1. Check FFmpeg is installed: `ffmpeg -version`
2. Verify stream is running: `GET /api/streams/{id}/status`
3. Check HLS files exist in `/tmp/goddamneye/hls/{camera_id}/`
4. Check browser console for errors

### Recording not saving

1. Verify storage path exists and is writable
2. Check `recording_enabled` is true for camera
3. Check disk space availability
4. Review logs for FFmpeg errors

### ONVIF discovery not finding cameras

1. Ensure Docker uses host networking (for multicast)
2. Check firewall allows UDP ports 3702, 49152-65535
3. Some cameras need ONVIF enabled in settings
4. Try manual probe with known IP address

## License

This project is licensed under the GNU Affero General Public License v3.0 (AGPL-3.0).

## Contributing

Contributions welcome! Please open an issue to discuss significant changes first.

---

*"The eye that sees all, so you don't have to watch."*
