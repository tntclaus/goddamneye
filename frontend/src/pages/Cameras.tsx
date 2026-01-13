import { useState } from 'react'
import {
  Table,
  Button,
  Space,
  Tag,
  Switch,
  Modal,
  Tooltip,
  Input,
} from 'antd'
import type { ColumnsType } from 'antd/es/table'
import {
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  SearchOutlined,
  ScanOutlined,
} from '@ant-design/icons'
import { CameraForm } from '../components/Camera/CameraForm'
import {
  useCameras,
  useCreateCamera,
  useUpdateCamera,
  useDeleteCamera,
  useToggleCamera,
  useDiscoverCameras,
} from '../hooks/useApi'
import { formatCameraStatus } from '../hooks/useCameras'
import type { Camera, CameraCreate, CameraUpdate } from '../types'
import dayjs from 'dayjs'

export function Cameras() {
  const { data: cameras, isLoading } = useCameras()
  const createCamera = useCreateCamera()
  const updateCamera = useUpdateCamera()
  const deleteCamera = useDeleteCamera()
  const toggleCamera = useToggleCamera()
  const discoverCameras = useDiscoverCameras()

  const [searchText, setSearchText] = useState('')
  const [formOpen, setFormOpen] = useState(false)
  const [editingCamera, setEditingCamera] = useState<Camera | undefined>()
  const [cameraToDelete, setCameraToDelete] = useState<Camera | null>(null)

  const filteredCameras = cameras?.filter(
    (camera) =>
      camera.name.toLowerCase().includes(searchText.toLowerCase()) ||
      camera.rtsp_url.toLowerCase().includes(searchText.toLowerCase())
  )

  const handleSubmit = (values: CameraCreate | CameraUpdate) => {
    if (editingCamera) {
      updateCamera.mutate(
        { id: editingCamera.id, data: values as CameraUpdate },
        { onSuccess: () => closeForm() }
      )
    } else {
      createCamera.mutate(values as CameraCreate, {
        onSuccess: () => closeForm(),
      })
    }
  }

  const closeForm = () => {
    setFormOpen(false)
    setEditingCamera(undefined)
  }

  const handleEdit = (camera: Camera) => {
    setEditingCamera(camera)
    setFormOpen(true)
  }

  const handleDeleteConfirm = () => {
    if (cameraToDelete) {
      deleteCamera.mutate(cameraToDelete.id, {
        onSuccess: () => setCameraToDelete(null),
      })
    }
  }

  const columns: ColumnsType<Camera> = [
    {
      title: 'Name',
      dataIndex: 'name',
      key: 'name',
      sorter: (a, b) => a.name.localeCompare(b.name),
      render: (name: string, record: Camera) => (
        <div>
          <div style={{ fontWeight: 500 }}>{name}</div>
          {record.description && (
            <div
              style={{
                fontSize: 12,
                color: 'rgba(255,255,255,0.45)',
                maxWidth: 200,
                overflow: 'hidden',
                textOverflow: 'ellipsis',
                whiteSpace: 'nowrap',
              }}
            >
              {record.description}
            </div>
          )}
        </div>
      ),
    },
    {
      title: 'Status',
      key: 'status',
      width: 100,
      render: (_, record: Camera) => {
        const status = formatCameraStatus(record)
        return <Tag color={status.color}>{status.text}</Tag>
      },
    },
    {
      title: 'Recording',
      dataIndex: 'recording_enabled',
      key: 'recording',
      width: 100,
      render: (enabled: boolean, record: Camera) => (
        <Tag color={enabled && record.is_online ? 'processing' : 'default'}>
          {enabled ? 'ON' : 'OFF'}
        </Tag>
      ),
    },
    {
      title: 'RTSP URL',
      dataIndex: 'rtsp_url',
      key: 'rtsp_url',
      ellipsis: true,
      render: (url: string) => (
        <Tooltip title={url}>
          <code style={{ fontSize: 12 }}>{url}</code>
        </Tooltip>
      ),
    },
    {
      title: 'Model',
      key: 'model',
      width: 150,
      render: (_, record: Camera) => {
        if (!record.model) return '-'
        return (
          <div style={{ fontSize: 12 }}>
            {record.manufacturer && <div>{record.manufacturer}</div>}
            <div style={{ color: 'rgba(255,255,255,0.65)' }}>{record.model}</div>
          </div>
        )
      },
    },
    {
      title: 'Last Seen',
      dataIndex: 'last_seen_at',
      key: 'last_seen_at',
      width: 150,
      render: (date: string | null) =>
        date ? dayjs(date).format('YYYY-MM-DD HH:mm') : 'Never',
    },
    {
      title: 'Enabled',
      key: 'enabled',
      width: 80,
      render: (_, record: Camera) => (
        <Switch
          size="small"
          checked={record.enabled}
          loading={toggleCamera.isPending}
          onChange={(checked) =>
            toggleCamera.mutate({ id: record.id, enable: checked })
          }
        />
      ),
    },
    {
      title: 'Actions',
      key: 'actions',
      width: 100,
      render: (_, record: Camera) => (
        <Space>
          <Tooltip title="Edit">
            <Button
              type="text"
              size="small"
              icon={<EditOutlined />}
              onClick={() => handleEdit(record)}
            />
          </Tooltip>
          <Tooltip title="Delete">
            <Button
              type="text"
              size="small"
              danger
              icon={<DeleteOutlined />}
              onClick={() => setCameraToDelete(record)}
            />
          </Tooltip>
        </Space>
      ),
    },
  ]

  return (
    <div>
      {/* Toolbar */}
      <Space style={{ marginBottom: 16 }} wrap>
        <Input
          placeholder="Search cameras..."
          prefix={<SearchOutlined />}
          value={searchText}
          onChange={(e) => setSearchText(e.target.value)}
          style={{ width: 250 }}
          allowClear
        />
        <Button
          type="primary"
          icon={<PlusOutlined />}
          onClick={() => setFormOpen(true)}
        >
          Add Camera
        </Button>
        <Button
          icon={<ScanOutlined />}
          loading={discoverCameras.isPending}
          onClick={() => discoverCameras.mutate(5)}
        >
          Discover
        </Button>
      </Space>

      {/* Camera Table */}
      <Table
        columns={columns}
        dataSource={filteredCameras}
        rowKey="id"
        loading={isLoading}
        pagination={{
          pageSize: 10,
          showSizeChanger: true,
          showTotal: (total) => `${total} cameras`,
        }}
        size="middle"
      />

      {/* Camera Form Modal */}
      <CameraForm
        open={formOpen}
        camera={editingCamera}
        onSubmit={handleSubmit}
        onCancel={closeForm}
        loading={createCamera.isPending || updateCamera.isPending}
      />

      {/* Delete Confirmation */}
      <Modal
        title="Delete Camera"
        open={!!cameraToDelete}
        onOk={handleDeleteConfirm}
        onCancel={() => setCameraToDelete(null)}
        confirmLoading={deleteCamera.isPending}
        okText="Delete"
        okButtonProps={{ danger: true }}
      >
        <p>
          Are you sure you want to delete camera{' '}
          <strong>{cameraToDelete?.name}</strong>?
        </p>
        <p>This action cannot be undone.</p>
      </Modal>
    </div>
  )
}
