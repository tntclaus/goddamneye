import { Modal, Typography } from 'antd'
import { getRecordingDownloadUrl } from '../../api/client'
import type { Recording } from '../../types'
import dayjs from 'dayjs'

interface RecordingPlayerProps {
  recording: Recording | null
  onClose: () => void
}

export function RecordingPlayer({ recording, onClose }: RecordingPlayerProps) {
  if (!recording) return null

  return (
    <Modal
      title={`Playing: ${recording.camera_name || 'Recording'}`}
      open={true}
      onCancel={onClose}
      footer={null}
      width={800}
      destroyOnClose
    >
      <video
        src={getRecordingDownloadUrl(recording.id)}
        controls
        autoPlay
        style={{ width: '100%', maxHeight: '60vh' }}
      />
      <div style={{ marginTop: 12 }}>
        <Typography.Text type="secondary">
          Recorded on{' '}
          {dayjs(recording.start_time).format('MMMM D, YYYY [at] HH:mm:ss')}
        </Typography.Text>
      </div>
    </Modal>
  )
}
