/**
 * React Query hooks for API calls
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  getCameras,
  getCamera,
  createCamera,
  updateCamera,
  deleteCamera,
  enableCamera,
  disableCamera,
  discoverCameras,
  getRecordings,
  getRecordingStats,
  deleteRecording,
  getHealth,
  getSystemInfo,
  getStreamsStatus,
} from '../api/client'
import type { CameraCreate, CameraUpdate, RecordingListParams } from '../api/client'
import { App } from 'antd'

// Query Keys
export const queryKeys = {
  cameras: ['cameras'] as const,
  camera: (id: string) => ['cameras', id] as const,
  recordings: (params?: RecordingListParams) => ['recordings', params] as const,
  recordingStats: ['recordings', 'stats'] as const,
  health: ['health'] as const,
  systemInfo: ['system', 'info'] as const,
  streamsStatus: ['streams', 'status'] as const,
}

// Camera Hooks
export function useCameras(enabledOnly = false) {
  return useQuery({
    queryKey: queryKeys.cameras,
    queryFn: () => getCameras(enabledOnly),
    refetchInterval: 10000, // Refresh every 10 seconds
  })
}

export function useCamera(id: string) {
  return useQuery({
    queryKey: queryKeys.camera(id),
    queryFn: () => getCamera(id),
    enabled: !!id,
  })
}

export function useCreateCamera() {
  const queryClient = useQueryClient()
  const { message } = App.useApp()

  return useMutation({
    mutationFn: (camera: CameraCreate) => createCamera(camera),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.cameras })
      message.success('Camera created successfully')
    },
    onError: (error: Error) => {
      message.error(`Failed to create camera: ${error.message}`)
    },
  })
}

export function useUpdateCamera() {
  const queryClient = useQueryClient()
  const { message } = App.useApp()

  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: CameraUpdate }) =>
      updateCamera(id, data),
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: queryKeys.cameras })
      queryClient.invalidateQueries({ queryKey: queryKeys.camera(id) })
      message.success('Camera updated successfully')
    },
    onError: (error: Error) => {
      message.error(`Failed to update camera: ${error.message}`)
    },
  })
}

export function useDeleteCamera() {
  const queryClient = useQueryClient()
  const { message } = App.useApp()

  return useMutation({
    mutationFn: (id: string) => deleteCamera(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.cameras })
      message.success('Camera deleted successfully')
    },
    onError: (error: Error) => {
      message.error(`Failed to delete camera: ${error.message}`)
    },
  })
}

export function useToggleCamera() {
  const queryClient = useQueryClient()
  const { message } = App.useApp()

  return useMutation({
    mutationFn: ({ id, enable }: { id: string; enable: boolean }) =>
      enable ? enableCamera(id) : disableCamera(id),
    onSuccess: (_, { enable }) => {
      queryClient.invalidateQueries({ queryKey: queryKeys.cameras })
      message.success(`Camera ${enable ? 'enabled' : 'disabled'}`)
    },
    onError: (error: Error) => {
      message.error(`Failed to toggle camera: ${error.message}`)
    },
  })
}

export function useDiscoverCameras() {
  const { message } = App.useApp()

  return useMutation({
    mutationFn: (timeout?: number) => discoverCameras(timeout ?? 5),
    onSuccess: (cameras) => {
      if (cameras.length === 0) {
        message.info('No cameras discovered on the network')
      } else {
        message.success(`Discovered ${cameras.length} camera(s)`)
      }
    },
    onError: (error: Error) => {
      message.error(`Discovery failed: ${error.message}`)
    },
  })
}

// Recording Hooks
export function useRecordings(params?: RecordingListParams) {
  return useQuery({
    queryKey: queryKeys.recordings(params),
    queryFn: () => getRecordings(params || {}),
  })
}

export function useRecordingStats() {
  return useQuery({
    queryKey: queryKeys.recordingStats,
    queryFn: getRecordingStats,
  })
}

export function useDeleteRecording() {
  const queryClient = useQueryClient()
  const { message } = App.useApp()

  return useMutation({
    mutationFn: (id: string) => deleteRecording(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['recordings'] })
      message.success('Recording deleted')
    },
    onError: (error: Error) => {
      message.error(`Failed to delete recording: ${error.message}`)
    },
  })
}

// System Hooks
export function useHealth() {
  return useQuery({
    queryKey: queryKeys.health,
    queryFn: getHealth,
    refetchInterval: 30000, // Check every 30 seconds
  })
}

export function useSystemInfo() {
  return useQuery({
    queryKey: queryKeys.systemInfo,
    queryFn: getSystemInfo,
  })
}

export function useStreamsStatus() {
  return useQuery({
    queryKey: queryKeys.streamsStatus,
    queryFn: getStreamsStatus,
    refetchInterval: 5000, // Refresh every 5 seconds
  })
}
