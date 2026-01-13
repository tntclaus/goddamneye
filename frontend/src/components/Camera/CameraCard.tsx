import { Card, Tag, Typography, Space, Dropdown, Switch, Tooltip } from 'antd'
import type { MenuProps } from 'antd'
import {
  MoreOutlined,
  EditOutlined,
  DeleteOutlined,
  VideoCameraOutlined,
  PlayCircleOutlined,
} from '@ant-design/icons'
import type { Camera } from '../../types'
import { formatCameraStatus } from '../../hooks/useCameras'
import { VideoPlayer } from '../Video/VideoPlayer'
import { getHlsStreamUrl } from '../../api/client'

interface CameraCardProps {
  camera: Camera
  onEdit?: (camera: Camera) => void
  onDelete?: (camera: Camera) => void
  onToggle?: (camera: Camera, enabled: boolean) => void
  showStream?: boolean
}

export function CameraCard({
  camera,
  onEdit,
  onDelete,
  onToggle,
  showStream = true,
}: CameraCardProps) {
  const status = formatCameraStatus(camera)

  const menuItems: MenuProps['items'] = [
    {
      key: 'edit',
      icon: <EditOutlined />,
      label: 'Edit Camera',
      onClick: () => onEdit?.(camera),
    },
    {
      type: 'divider',
    },
    {
      key: 'delete',
      icon: <DeleteOutlined />,
      label: 'Delete Camera',
      danger: true,
      onClick: () => onDelete?.(camera),
    },
  ]

  return (
    <Card
      size="small"
      styles={{
        body: { padding: 0 },
      }}
      style={{
        overflow: 'hidden',
        background: '#1f1f1f',
        border: '1px solid #303030',
      }}
    >
      {/* Video Preview Area */}
      <div
        style={{
          position: 'relative',
          paddingTop: '56.25%', // 16:9 aspect ratio
          background: '#0a0a0a',
        }}
      >
        {showStream && camera.enabled && camera.is_online ? (
          <div
            style={{
              position: 'absolute',
              top: 0,
              left: 0,
              right: 0,
              bottom: 0,
            }}
          >
            <VideoPlayer
              src={getHlsStreamUrl(camera.id)}
              autoPlay
              muted
              style={{ width: '100%', height: '100%', objectFit: 'cover' }}
            />
          </div>
        ) : (
          <div
            style={{
              position: 'absolute',
              top: 0,
              left: 0,
              right: 0,
              bottom: 0,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              flexDirection: 'column',
              color: 'rgba(255,255,255,0.25)',
            }}
          >
            <VideoCameraOutlined style={{ fontSize: 48 }} />
            <Typography.Text
              style={{
                marginTop: 8,
                color: 'rgba(255,255,255,0.45)',
                fontSize: 12,
              }}
            >
              {!camera.enabled
                ? 'Camera Disabled'
                : !camera.is_online
                ? 'Camera Offline'
                : 'No Stream'}
            </Typography.Text>
          </div>
        )}

        {/* Status overlay */}
        <div
          style={{
            position: 'absolute',
            top: 8,
            left: 8,
            right: 8,
            display: 'flex',
            justifyContent: 'space-between',
          }}
        >
          <Tag color={status.color}>{status.text}</Tag>
          {camera.recording_enabled && camera.is_online && (
            <Tag color="processing" icon={<PlayCircleOutlined />}>
              REC
            </Tag>
          )}
        </div>
      </div>

      {/* Camera Info */}
      <div style={{ padding: 12 }}>
        <Space style={{ width: '100%', justifyContent: 'space-between' }}>
          <div style={{ flex: 1, minWidth: 0 }}>
            <Typography.Text
              strong
              style={{
                display: 'block',
                overflow: 'hidden',
                textOverflow: 'ellipsis',
                whiteSpace: 'nowrap',
              }}
            >
              {camera.name}
            </Typography.Text>
            {camera.model && (
              <Typography.Text
                type="secondary"
                style={{
                  fontSize: 12,
                  display: 'block',
                  overflow: 'hidden',
                  textOverflow: 'ellipsis',
                  whiteSpace: 'nowrap',
                }}
              >
                {camera.manufacturer} {camera.model}
              </Typography.Text>
            )}
          </div>

          <Space>
            <Tooltip title={camera.enabled ? 'Disable' : 'Enable'}>
              <Switch
                size="small"
                checked={camera.enabled}
                onChange={(checked) => onToggle?.(camera, checked)}
              />
            </Tooltip>
            <Dropdown menu={{ items: menuItems }} trigger={['click']}>
              <MoreOutlined
                style={{
                  fontSize: 16,
                  cursor: 'pointer',
                  padding: 4,
                }}
              />
            </Dropdown>
          </Space>
        </Space>
      </div>
    </Card>
  )
}
