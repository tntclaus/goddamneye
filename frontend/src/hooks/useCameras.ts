/**
 * Camera-specific hooks and utilities
 */

import { useMemo } from 'react'
import { useCameras } from './useApi'
import type { Camera } from '../types'

export interface CameraStats {
  total: number
  online: number
  offline: number
  recording: number
  disabled: number
}

export function useCameraStats(): CameraStats {
  const { data: cameras } = useCameras()

  return useMemo(() => {
    if (!cameras) {
      return {
        total: 0,
        online: 0,
        offline: 0,
        recording: 0,
        disabled: 0,
      }
    }

    return {
      total: cameras.length,
      online: cameras.filter((c) => c.is_online && c.enabled).length,
      offline: cameras.filter((c) => !c.is_online && c.enabled).length,
      recording: cameras.filter((c) => c.recording_enabled && c.is_online).length,
      disabled: cameras.filter((c) => !c.enabled).length,
    }
  }, [cameras])
}

export function useCameraById(id: string): Camera | undefined {
  const { data: cameras } = useCameras()
  return cameras?.find((c) => c.id === id)
}

export function useOnlineCameras(): Camera[] {
  const { data: cameras } = useCameras()
  return useMemo(
    () => cameras?.filter((c) => c.is_online && c.enabled) || [],
    [cameras]
  )
}

export function formatCameraStatus(camera: Camera): {
  status: 'online' | 'offline' | 'disabled'
  color: string
  text: string
} {
  if (!camera.enabled) {
    return { status: 'disabled', color: 'default', text: 'Disabled' }
  }
  if (camera.is_online) {
    return { status: 'online', color: 'success', text: 'Online' }
  }
  return { status: 'offline', color: 'error', text: 'Offline' }
}

export function formatFileSize(bytes: number | null | undefined): string {
  if (!bytes) return '-'

  const units = ['B', 'KB', 'MB', 'GB', 'TB']
  let size = bytes
  let unitIndex = 0

  while (size >= 1024 && unitIndex < units.length - 1) {
    size /= 1024
    unitIndex++
  }

  return `${size.toFixed(1)} ${units[unitIndex]}`
}

export function formatDuration(seconds: number | null | undefined): string {
  if (!seconds) return '-'

  const hours = Math.floor(seconds / 3600)
  const minutes = Math.floor((seconds % 3600) / 60)
  const secs = seconds % 60

  if (hours > 0) {
    return `${hours}h ${minutes}m`
  }
  if (minutes > 0) {
    return `${minutes}m ${secs}s`
  }
  return `${secs}s`
}
