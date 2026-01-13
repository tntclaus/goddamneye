import { Row, Col, Empty, Spin } from 'antd'
import { CameraCard } from './CameraCard'
import type { Camera } from '../../types'

interface CameraGridProps {
  cameras: Camera[]
  loading?: boolean
  columns?: 1 | 2 | 3 | 4
  onEdit?: (camera: Camera) => void
  onDelete?: (camera: Camera) => void
  onToggle?: (camera: Camera, enabled: boolean) => void
  showStream?: boolean
}

export function CameraGrid({
  cameras,
  loading = false,
  columns = 2,
  onEdit,
  onDelete,
  onToggle,
  showStream = true,
}: CameraGridProps) {
  if (loading) {
    return (
      <div
        style={{
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
          minHeight: 300,
        }}
      >
        <Spin size="large" />
      </div>
    )
  }

  if (cameras.length === 0) {
    return (
      <Empty
        image={Empty.PRESENTED_IMAGE_SIMPLE}
        description="No cameras configured"
        style={{ marginTop: 60 }}
      />
    )
  }

  const colSpan = 24 / columns

  return (
    <Row gutter={[16, 16]}>
      {cameras.map((camera) => (
        <Col key={camera.id} xs={24} sm={12} md={colSpan} lg={colSpan}>
          <CameraCard
            camera={camera}
            onEdit={onEdit}
            onDelete={onDelete}
            onToggle={onToggle}
            showStream={showStream}
          />
        </Col>
      ))}
    </Row>
  )
}
