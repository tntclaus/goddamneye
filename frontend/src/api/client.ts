/**
 * API client for GodDamnEye backend
 */

import axios, { AxiosError } from 'axios'
import type {
  Camera,
  CameraCreate,
  CameraUpdate,
  CameraDiscovered,
  Recording,
  RecordingStats,
  StreamStatus,
  HealthResponse,
  SystemInfo,
} from '../types'

// Re-export types for convenience
export type { CameraCreate, CameraUpdate } from '../types'

// Base API URL - in development, Vite proxies to backend
const API_BASE = '/api'

const api = axios.create({
  baseURL: API_BASE,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Error handler
api.interceptors.response.use(
  (response) => response,
  (error: AxiosError) => {
    console.error('API Error:', error.response?.data || error.message)
    return Promise.reject(error)
  }
)

// Health & System
export const getHealth = async (): Promise<HealthResponse> => {
  const { data } = await api.get<HealthResponse>('/health')
  return data
}

export const getSystemInfo = async (): Promise<SystemInfo> => {
  const { data } = await api.get<SystemInfo>('/system/info')
  return data
}

// Cameras
export const getCameras = async (enabledOnly = false): Promise<Camera[]> => {
  const { data } = await api.get<Camera[]>('/cameras', {
    params: { enabled_only: enabledOnly },
  })
  return data
}

export const getCamera = async (id: string): Promise<Camera> => {
  const { data } = await api.get<Camera>(`/cameras/${id}`)
  return data
}

export const createCamera = async (camera: CameraCreate): Promise<Camera> => {
  const { data } = await api.post<Camera>('/cameras', camera)
  return data
}

export const updateCamera = async (id: string, camera: CameraUpdate): Promise<Camera> => {
  const { data } = await api.put<Camera>(`/cameras/${id}`, camera)
  return data
}

export const deleteCamera = async (id: string): Promise<void> => {
  await api.delete(`/cameras/${id}`)
}

export const enableCamera = async (id: string): Promise<Camera> => {
  const { data } = await api.post<Camera>(`/cameras/${id}/enable`)
  return data
}

export const disableCamera = async (id: string): Promise<Camera> => {
  const { data } = await api.post<Camera>(`/cameras/${id}/disable`)
  return data
}

export const discoverCameras = async (timeout = 5): Promise<CameraDiscovered[]> => {
  const { data } = await api.post<CameraDiscovered[]>('/cameras/discover', null, {
    params: { timeout },
  })
  return data
}

// Camera probe for simplified setup
export interface CameraProbeRequest {
  host: string
  port?: number
  username?: string
  password?: string
}

export interface CameraProbeStream {
  name: string
  url: string
  description: string
}

export interface CameraProbeResponse {
  host: string
  port: number
  onvif_supported: boolean
  name: string | null
  manufacturer: string | null
  model: string | null
  firmware_version: string | null
  serial_number: string | null
  streams: CameraProbeStream[]
  error: string | null
}

export const probeCamera = async (request: CameraProbeRequest): Promise<CameraProbeResponse> => {
  const { data } = await api.post<CameraProbeResponse>('/cameras/probe', request)
  return data
}

// Streams
export const getStreamsStatus = async (): Promise<StreamStatus> => {
  const { data } = await api.get<StreamStatus>('/streams/status')
  return data
}

export const startStream = async (cameraId: string): Promise<void> => {
  await api.post(`/streams/${cameraId}/start`)
}

export const stopStream = async (cameraId: string): Promise<void> => {
  await api.post(`/streams/${cameraId}/stop`)
}

// Recordings
export interface RecordingListParams {
  camera_id?: string
  start_date?: string
  end_date?: string
  limit?: number
  offset?: number
}

export const getRecordings = async (params: RecordingListParams = {}): Promise<Recording[]> => {
  const { data } = await api.get<Recording[]>('/recordings', { params })
  return data
}

export const getRecording = async (id: string): Promise<Recording> => {
  const { data } = await api.get<Recording>(`/recordings/${id}`)
  return data
}

export const getRecordingStats = async (): Promise<RecordingStats> => {
  const { data } = await api.get<RecordingStats>('/recordings/stats')
  return data
}

export const deleteRecording = async (id: string): Promise<void> => {
  await api.delete(`/recordings/${id}`)
}

export const getRecordingDownloadUrl = (id: string): string => {
  return `${API_BASE}/recordings/${id}/download`
}

// HLS stream URL helper
export const getHlsStreamUrl = (cameraId: string): string => {
  return `/hls/${cameraId}/stream.m3u8`
}

export default api
