import { useState } from 'react'
import {
  Row,
  Col,
  Card,
  Statistic,
  Button,
  Space,
  Segmented,
  Modal,
} from 'antd'
import {
  VideoCameraOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
  PlayCircleOutlined,
  PlusOutlined,
  ReloadOutlined,
  AppstoreOutlined,
} from '@ant-design/icons'
import { CameraGrid } from '../components/Camera/CameraGrid'
import { CameraForm } from '../components/Camera/CameraForm'
import {
  useCameras,
  useCreateCamera,
  useDeleteCamera,
  useToggleCamera,
} from '../hooks/useApi'
import { useCameraStats } from '../hooks/useCameras'
import type { Camera, CameraCreate, CameraUpdate } from '../types'

type GridSize = 1 | 2 | 3 | 4

export function Dashboard() {
  const { data: cameras, isLoading, refetch } = useCameras()
  const stats = useCameraStats()
  const createCamera = useCreateCamera()
  const deleteCamera = useDeleteCamera()
  const toggleCamera = useToggleCamera()

  const [gridSize, setGridSize] = useState<GridSize>(2)
  const [formOpen, setFormOpen] = useState(false)
  const [cameraToDelete, setCameraToDelete] = useState<Camera | null>(null)

  const handleCreateCamera = (values: CameraCreate | CameraUpdate) => {
    createCamera.mutate(values as CameraCreate, {
      onSuccess: () => setFormOpen(false),
    })
  }

  const handleDeleteCamera = () => {
    if (cameraToDelete) {
      deleteCamera.mutate(cameraToDelete.id, {
        onSuccess: () => setCameraToDelete(null),
      })
    }
  }

  const handleToggleCamera = (camera: Camera, enabled: boolean) => {
    toggleCamera.mutate({ id: camera.id, enable: enabled })
  }

  return (
    <div>
      {/* Stats Cards */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col xs={12} sm={6}>
          <Card size="small">
            <Statistic
              title="Total Cameras"
              value={stats.total}
              prefix={<VideoCameraOutlined />}
            />
          </Card>
        </Col>
        <Col xs={12} sm={6}>
          <Card size="small">
            <Statistic
              title="Online"
              value={stats.online}
              valueStyle={{ color: '#52c41a' }}
              prefix={<CheckCircleOutlined />}
            />
          </Card>
        </Col>
        <Col xs={12} sm={6}>
          <Card size="small">
            <Statistic
              title="Offline"
              value={stats.offline}
              valueStyle={{ color: stats.offline > 0 ? '#ff4d4f' : undefined }}
              prefix={<CloseCircleOutlined />}
            />
          </Card>
        </Col>
        <Col xs={12} sm={6}>
          <Card size="small">
            <Statistic
              title="Recording"
              value={stats.recording}
              valueStyle={{ color: '#1890ff' }}
              prefix={<PlayCircleOutlined />}
            />
          </Card>
        </Col>
      </Row>

      {/* Toolbar */}
      <Row
        justify="space-between"
        align="middle"
        style={{ marginBottom: 16 }}
      >
        <Space>
          <Button
            type="primary"
            icon={<PlusOutlined />}
            onClick={() => setFormOpen(true)}
          >
            Add Camera
          </Button>
          <Button icon={<ReloadOutlined />} onClick={() => refetch()}>
            Refresh
          </Button>
        </Space>

        <Segmented
          value={gridSize}
          onChange={(value) => setGridSize(value as GridSize)}
          options={[
            { value: 1, icon: <AppstoreOutlined />, label: '1x1' },
            { value: 2, label: '2x2' },
            { value: 3, label: '3x3' },
            { value: 4, label: '4x4' },
          ]}
        />
      </Row>

      {/* Camera Grid */}
      <CameraGrid
        cameras={cameras || []}
        loading={isLoading}
        columns={gridSize}
        onDelete={setCameraToDelete}
        onToggle={handleToggleCamera}
        showStream={true}
      />

      {/* Add Camera Form */}
      <CameraForm
        open={formOpen}
        onSubmit={handleCreateCamera}
        onCancel={() => setFormOpen(false)}
        loading={createCamera.isPending}
      />

      {/* Delete Confirmation */}
      <Modal
        title="Delete Camera"
        open={!!cameraToDelete}
        onOk={handleDeleteCamera}
        onCancel={() => setCameraToDelete(null)}
        confirmLoading={deleteCamera.isPending}
        okText="Delete"
        okButtonProps={{ danger: true }}
      >
        <p>
          Are you sure you want to delete camera{' '}
          <strong>{cameraToDelete?.name}</strong>?
        </p>
        <p>This will also delete all associated recordings.</p>
      </Modal>
    </div>
  )
}
