/**
 * Tests for CameraForm component.
 *
 * These tests verify the camera form's behavior:
 * - Simple setup mode with camera probing
 * - Advanced mode for manual configuration
 * - Clean URL handling (no embedded credentials)
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { CameraForm } from './CameraForm'
import * as api from '../../api/client'

// Mock the API
vi.mock('../../api/client', () => ({
  probeCamera: vi.fn(),
}))

describe('CameraForm', () => {
  const mockOnSubmit = vi.fn()
  const mockOnCancel = vi.fn()

  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('Simple Setup Mode', () => {
    it('renders simple setup tab by default for new camera', () => {
      render(
        <CameraForm
          open={true}
          onSubmit={mockOnSubmit}
          onCancel={mockOnCancel}
        />
      )

      // Should show simple setup tab
      expect(screen.getByText('Simple Setup')).toBeInTheDocument()
      expect(screen.getByText('Advanced')).toBeInTheDocument()

      // Should show IP address input
      expect(screen.getByLabelText(/Camera IP Address/i)).toBeInTheDocument()
    })

    it('shows probe button', () => {
      render(
        <CameraForm
          open={true}
          onSubmit={mockOnSubmit}
          onCancel={mockOnCancel}
        />
      )

      expect(screen.getByText('Detect Camera')).toBeInTheDocument()
    })

    it('calls probeCamera with IP and credentials', async () => {
      const mockProbeResponse: api.CameraProbeResponse = {
        host: '192.168.1.100',
        port: 80,
        onvif_supported: true,
        name: 'Test Camera',
        manufacturer: 'TestMfg',
        model: 'Model1',
        firmware_version: null,
        serial_number: null,
        streams: [
          {
            name: 'Main Stream',
            url: 'rtsp://192.168.1.100:554/stream1',
            description: 'Profile 1',
          },
        ],
        error: null,
      }

      vi.mocked(api.probeCamera).mockResolvedValue(mockProbeResponse)

      render(
        <CameraForm
          open={true}
          onSubmit={mockOnSubmit}
          onCancel={mockOnCancel}
        />
      )

      const user = userEvent.setup()

      // Enter IP address
      const ipInput = screen.getByLabelText(/Camera IP Address/i)
      await user.type(ipInput, '192.168.1.100')

      // Enter credentials
      const usernameInput = screen.getByLabelText(/Username/i)
      await user.type(usernameInput, 'admin')

      const passwordInput = screen.getByLabelText(/Password/i)
      await user.type(passwordInput, 'secret%^password')

      // Click detect
      const detectButton = screen.getByText('Detect Camera')
      await user.click(detectButton)

      // Verify probe was called with correct params
      await waitFor(() => {
        expect(api.probeCamera).toHaveBeenCalledWith({
          host: '192.168.1.100',
          port: 80,
          username: 'admin',
          password: 'secret%^password',
        })
      })
    })

    it('displays ONVIF detection success message', async () => {
      const mockProbeResponse: api.CameraProbeResponse = {
        host: '192.168.1.100',
        port: 80,
        onvif_supported: true,
        name: 'Test Camera',
        manufacturer: 'UNIVIEW',
        model: 'IPC2314',
        firmware_version: null,
        serial_number: null,
        streams: [
          {
            name: 'Main Stream',
            url: 'rtsp://192.168.1.100:554/stream1',
            description: 'Profile 1',
          },
        ],
        error: null,
      }

      vi.mocked(api.probeCamera).mockResolvedValue(mockProbeResponse)

      render(
        <CameraForm
          open={true}
          onSubmit={mockOnSubmit}
          onCancel={mockOnCancel}
        />
      )

      const user = userEvent.setup()

      // Enter IP and trigger probe
      const ipInput = screen.getByLabelText(/Camera IP Address/i)
      await user.type(ipInput, '192.168.1.100')
      await user.click(screen.getByText('Detect Camera'))

      // Should show success message
      await waitFor(() => {
        expect(screen.getByText('ONVIF Camera Detected')).toBeInTheDocument()
      })

      // Should show manufacturer
      expect(screen.getByText('UNIVIEW')).toBeInTheDocument()
    })

    it('shows stream selection dropdown after probe', async () => {
      const mockProbeResponse: api.CameraProbeResponse = {
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
            url: 'rtsp://192.168.1.100:554/stream1',
            description: 'High Quality',
          },
          {
            name: 'Sub Stream',
            url: 'rtsp://192.168.1.100:554/stream2',
            description: 'Lower Quality',
          },
        ],
        error: null,
      }

      vi.mocked(api.probeCamera).mockResolvedValue(mockProbeResponse)

      render(
        <CameraForm
          open={true}
          onSubmit={mockOnSubmit}
          onCancel={mockOnCancel}
        />
      )

      const user = userEvent.setup()

      const ipInput = screen.getByLabelText(/Camera IP Address/i)
      await user.type(ipInput, '192.168.1.100')
      await user.click(screen.getByText('Detect Camera'))

      // Should show stream selection
      await waitFor(() => {
        expect(screen.getByText(/Select Stream/i)).toBeInTheDocument()
      })
    })

    it('pre-fills camera name from probe result', async () => {
      const mockProbeResponse: api.CameraProbeResponse = {
        host: '192.168.1.100',
        port: 80,
        onvif_supported: true,
        name: 'Auto-Detected Camera Name',
        manufacturer: null,
        model: null,
        firmware_version: null,
        serial_number: null,
        streams: [
          {
            name: 'Stream',
            url: 'rtsp://192.168.1.100:554/stream1',
            description: 'Stream',
          },
        ],
        error: null,
      }

      vi.mocked(api.probeCamera).mockResolvedValue(mockProbeResponse)

      render(
        <CameraForm
          open={true}
          onSubmit={mockOnSubmit}
          onCancel={mockOnCancel}
        />
      )

      const user = userEvent.setup()

      const ipInput = screen.getByLabelText(/Camera IP Address/i)
      await user.type(ipInput, '192.168.1.100')
      await user.click(screen.getByText('Detect Camera'))

      // Name field should be pre-filled
      await waitFor(() => {
        const nameInput = screen.getByLabelText(/Camera Name/i)
        expect(nameInput).toHaveValue('Auto-Detected Camera Name')
      })
    })

    it('submits with clean RTSP URL (no embedded credentials)', async () => {
      const mockProbeResponse: api.CameraProbeResponse = {
        host: '192.168.1.100',
        port: 80,
        onvif_supported: true,
        name: 'Test Camera',
        manufacturer: null,
        model: null,
        firmware_version: null,
        serial_number: null,
        streams: [
          {
            name: 'Main Stream',
            url: 'rtsp://192.168.1.100:554/stream1', // Clean URL
            description: 'Stream',
          },
        ],
        error: null,
      }

      vi.mocked(api.probeCamera).mockResolvedValue(mockProbeResponse)

      render(
        <CameraForm
          open={true}
          onSubmit={mockOnSubmit}
          onCancel={mockOnCancel}
        />
      )

      const user = userEvent.setup()

      // Complete the form
      await user.type(screen.getByLabelText(/Camera IP Address/i), '192.168.1.100')
      await user.type(screen.getByLabelText(/Username/i), 'admin')
      await user.type(screen.getByLabelText(/Password/i), 'secret%^password')
      await user.click(screen.getByText('Detect Camera'))

      // Wait for probe to complete
      await waitFor(() => {
        expect(screen.getByText('ONVIF Camera Detected')).toBeInTheDocument()
      })

      // Change name and submit
      const nameInput = screen.getByLabelText(/Camera Name/i)
      await user.clear(nameInput)
      await user.type(nameInput, 'My Camera')

      // Submit the form - use button role with specific name in modal footer
      const submitButton = screen.getByRole('button', { name: /Add Camera/i })
      await user.click(submitButton)

      // Verify submitted data has clean URL and separate credentials
      await waitFor(() => {
        expect(mockOnSubmit).toHaveBeenCalledWith(
          expect.objectContaining({
            name: 'My Camera',
            rtsp_url: 'rtsp://192.168.1.100:554/stream1', // Clean URL
            username: 'admin',
            password: 'secret%^password', // Credentials stored separately
          })
        )
      })

      // Ensure URL doesn't have embedded credentials
      const submittedData = mockOnSubmit.mock.calls[0][0]
      expect(submittedData.rtsp_url).not.toContain('@')
      expect(submittedData.rtsp_url).not.toContain('admin')
    })
  })

  describe('Advanced Mode', () => {
    it('switches to advanced mode when tab clicked', async () => {
      render(
        <CameraForm
          open={true}
          onSubmit={mockOnSubmit}
          onCancel={mockOnCancel}
        />
      )

      const user = userEvent.setup()

      // Click advanced tab
      await user.click(screen.getByText('Advanced'))

      // Should show RTSP URL input
      expect(screen.getByLabelText(/RTSP URL/i)).toBeInTheDocument()
    })

    it('uses advanced mode when editing existing camera', () => {
      const existingCamera = {
        id: 'cam-123',
        name: 'Existing Camera',
        rtsp_url: 'rtsp://192.168.1.100:554/stream1',
        enabled: true,
        recording_enabled: true,
        is_online: true,
        username: 'admin',
        created_at: '2024-01-01',
        updated_at: '2024-01-01',
      }

      render(
        <CameraForm
          open={true}
          camera={existingCamera}
          onSubmit={mockOnSubmit}
          onCancel={mockOnCancel}
        />
      )

      // Should show RTSP URL input (advanced mode)
      expect(screen.getByLabelText(/RTSP URL/i)).toBeInTheDocument()

      // Should be pre-filled with existing values
      expect(screen.getByLabelText(/Camera Name/i)).toHaveValue('Existing Camera')
      expect(screen.getByLabelText(/RTSP URL/i)).toHaveValue('rtsp://192.168.1.100:554/stream1')
    })
  })

  describe('Error Handling', () => {
    it('displays error when probe fails', async () => {
      vi.mocked(api.probeCamera).mockRejectedValue({
        response: { data: { detail: 'Connection refused' } },
      })

      render(
        <CameraForm
          open={true}
          onSubmit={mockOnSubmit}
          onCancel={mockOnCancel}
        />
      )

      const user = userEvent.setup()

      await user.type(screen.getByLabelText(/Camera IP Address/i), '192.168.1.100')
      await user.click(screen.getByText('Detect Camera'))

      await waitFor(() => {
        expect(screen.getByText(/Connection refused/i)).toBeInTheDocument()
      })
    })

    it('shows fallback message when ONVIF not supported', async () => {
      const mockProbeResponse: api.CameraProbeResponse = {
        host: '192.168.1.100',
        port: 80,
        onvif_supported: false,
        name: null,
        manufacturer: null,
        model: null,
        firmware_version: null,
        serial_number: null,
        streams: [
          {
            name: 'Try: /stream1',
            url: 'rtsp://192.168.1.100:554/stream1',
            description: 'Common pattern',
          },
        ],
        error: 'ONVIF not available. Showing common RTSP URL patterns to try.',
      }

      vi.mocked(api.probeCamera).mockResolvedValue(mockProbeResponse)

      render(
        <CameraForm
          open={true}
          onSubmit={mockOnSubmit}
          onCancel={mockOnCancel}
        />
      )

      const user = userEvent.setup()

      await user.type(screen.getByLabelText(/Camera IP Address/i), '192.168.1.100')
      await user.click(screen.getByText('Detect Camera'))

      await waitFor(() => {
        expect(screen.getByText(/ONVIF Not Available/i)).toBeInTheDocument()
      })
    })
  })
})
