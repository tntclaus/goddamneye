/**
 * TypeScript interfaces for GodDamnEye
 */

export interface Camera {
  id: string
  name: string
  description: string | null
  rtsp_url: string
  onvif_host: string | null
  onvif_port: number
  username: string | null
  manufacturer: string | null
  model: string | null
  firmware_version: string | null
  serial_number: string | null
  enabled: boolean
  recording_enabled: boolean
  is_online: boolean
  created_at: string
  updated_at: string
  last_seen_at: string | null
}

export interface CameraCreate {
  name: string
  description?: string
  rtsp_url: string
  onvif_host?: string
  onvif_port?: number
  username?: string
  password?: string
  enabled?: boolean
  recording_enabled?: boolean
}

export interface CameraUpdate {
  name?: string
  description?: string
  rtsp_url?: string
  onvif_host?: string
  onvif_port?: number
  username?: string
  password?: string
  enabled?: boolean
  recording_enabled?: boolean
}

export interface CameraDiscovered {
  host: string
  port: number
  name: string | null
  manufacturer: string | null
  model: string | null
  firmware_version: string | null
  serial_number: string | null
  rtsp_urls: string[]
  onvif_url: string | null
}

export interface Recording {
  id: string
  camera_id: string
  file_path: string
  file_size: number | null
  start_time: string
  end_time: string | null
  duration_seconds: number | null
  created_at: string
  camera_name?: string
}

export interface RecordingStats {
  total_recordings: number
  total_size_bytes: number
  oldest_recording: string | null
  newest_recording: string | null
  cameras_with_recordings: number
}

export interface StreamStatus {
  active_streams: number
  streams: StreamInfo[]
}

export interface StreamInfo {
  camera_id: string
  is_active: boolean
  hls_url: string | null
  error: string | null
}

export interface HealthResponse {
  status: string
  version: string
  timestamp: string
}

export interface SystemInfo {
  app_name: string
  version: string
  debug: boolean
  storage_path: string
  database_url: string
}

export type CameraStatus = 'online' | 'offline' | 'connecting' | 'error'
