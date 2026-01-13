/**
 * Tests for API client functions.
 *
 * These tests verify that the API client correctly:
 * - Constructs URLs
 * - Handles responses
 * - Manages HLS stream URLs
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import axios from 'axios'
import {
  getHlsStreamUrl,
  getRecordingDownloadUrl,
  getCameras,
  createCamera,
  probeCamera,
  type CameraProbeResponse,
} from './client'
import type { Camera } from '../types'

// Mock axios
vi.mock('axios', () => {
  const mockAxios = {
    create: vi.fn(() => mockAxios),
    get: vi.fn(),
    post: vi.fn(),
    put: vi.fn(),
    delete: vi.fn(),
    interceptors: {
      response: {
        use: vi.fn(),
      },
    },
  }
  return { default: mockAxios }
})

describe('API Client', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  describe('getHlsStreamUrl', () => {
    it('returns correct HLS URL for camera ID', () => {
      const cameraId = 'abc-123-def'
      const url = getHlsStreamUrl(cameraId)
      expect(url).toBe('/hls/abc-123-def/stream.m3u8')
    })

    it('handles camera IDs with special characters', () => {
      const cameraId = '12345678-1234-1234-1234-123456789012'
      const url = getHlsStreamUrl(cameraId)
      expect(url).toBe('/hls/12345678-1234-1234-1234-123456789012/stream.m3u8')
    })
  })

  describe('getRecordingDownloadUrl', () => {
    it('returns correct download URL for recording ID', () => {
      const recordingId = 'rec-123'
      const url = getRecordingDownloadUrl(recordingId)
      expect(url).toBe('/api/recordings/rec-123/download')
    })
  })

  describe('getCameras', () => {
    it('fetches all cameras', async () => {
      const mockCameras: Camera[] = [
        {
          id: '1',
          name: 'Camera 1',
          rtsp_url: 'rtsp://192.168.1.100/stream',
          enabled: true,
          recording_enabled: true,
          is_online: true,
          created_at: '2024-01-01',
          updated_at: '2024-01-01',
        },
      ]

      vi.mocked(axios.get).mockResolvedValue({ data: mockCameras })

      const result = await getCameras()
      expect(result).toEqual(mockCameras)
    })

    it('filters enabled cameras when requested', async () => {
      vi.mocked(axios.get).mockResolvedValue({ data: [] })

      await getCameras(true)
      expect(axios.get).toHaveBeenCalledWith('/cameras', {
        params: { enabled_only: true },
      })
    })
  })

  describe('createCamera', () => {
    it('creates camera with clean RTSP URL', async () => {
      const newCamera = {
        name: 'Test Camera',
        rtsp_url: 'rtsp://192.168.1.100:554/stream1',
        username: 'admin',
        password: 'password',
        enabled: true,
      }

      const mockResponse: Camera = {
        id: 'new-id',
        ...newCamera,
        recording_enabled: true,
        is_online: false,
        created_at: '2024-01-01',
        updated_at: '2024-01-01',
      }

      vi.mocked(axios.post).mockResolvedValue({ data: mockResponse })

      const result = await createCamera(newCamera)
      expect(result.rtsp_url).toBe('rtsp://192.168.1.100:554/stream1')
      expect(result.rtsp_url).not.toContain('@')
    })
  })

  describe('probeCamera', () => {
    it('sends probe request with host and credentials', async () => {
      const mockResponse: CameraProbeResponse = {
        host: '192.168.1.100',
        port: 80,
        onvif_supported: true,
        name: 'Test Camera',
        manufacturer: 'TestMfg',
        model: 'Model1',
        firmware_version: '1.0',
        serial_number: '12345',
        streams: [
          {
            name: 'Main Stream',
            url: 'rtsp://192.168.1.100:554/stream1',
            description: 'Profile 1',
          },
        ],
        error: null,
      }

      vi.mocked(axios.post).mockResolvedValue({ data: mockResponse })

      const result = await probeCamera({
        host: '192.168.1.100',
        username: 'admin',
        password: 'secret%^password',
      })

      expect(result.streams[0].url).toBe('rtsp://192.168.1.100:554/stream1')
      // URL should NOT contain credentials
      expect(result.streams[0].url).not.toContain('admin')
      expect(result.streams[0].url).not.toContain('secret')
      expect(result.streams[0].url).not.toContain('@')
    })

    it('returns clean URLs without embedded credentials', async () => {
      const mockResponse: CameraProbeResponse = {
        host: '192.168.1.100',
        port: 80,
        onvif_supported: true,
        name: 'Camera',
        manufacturer: null,
        model: null,
        firmware_version: null,
        serial_number: null,
        streams: [
          {
            name: 'Stream 1',
            url: 'rtsp://192.168.1.100:554/media/video1',
            description: 'Main',
          },
          {
            name: 'Stream 2',
            url: 'rtsp://192.168.1.100:554/media/video2',
            description: 'Sub',
          },
        ],
        error: null,
      }

      vi.mocked(axios.post).mockResolvedValue({ data: mockResponse })

      const result = await probeCamera({ host: '192.168.1.100' })

      // All streams should have clean URLs
      for (const stream of result.streams) {
        expect(stream.url).toMatch(/^rtsp:\/\/[\d.]+:\d+\//)
        expect(stream.url).not.toContain('@')
      }
    })
  })
})


describe('CameraProbeResponse Types', () => {
  it('should have correct stream structure', () => {
    const response: CameraProbeResponse = {
      host: '192.168.1.100',
      port: 80,
      onvif_supported: true,
      name: 'Camera',
      manufacturer: null,
      model: null,
      firmware_version: null,
      serial_number: null,
      streams: [
        {
          name: 'Main Stream',
          url: 'rtsp://host/path',
          description: 'Description',
        },
      ],
      error: null,
    }

    expect(response.streams[0]).toHaveProperty('name')
    expect(response.streams[0]).toHaveProperty('url')
    expect(response.streams[0]).toHaveProperty('description')
  })
})
