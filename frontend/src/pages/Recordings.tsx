import { useState } from 'react'
import {
  Table,
  Card,
  Row,
  Col,
  Statistic,
  DatePicker,
  Select,
  Button,
  Space,
  Modal,
  Typography,
} from 'antd'
import type { ColumnsType } from 'antd/es/table'
import {
  PlayCircleOutlined,
  DownloadOutlined,
  DeleteOutlined,
  DatabaseOutlined,
  ClockCircleOutlined,
  VideoCameraOutlined,
} from '@ant-design/icons'
import {
  useRecordings,
  useRecordingStats,
  useDeleteRecording,
  useCameras,
} from '../hooks/useApi'
import { getRecordingDownloadUrl } from '../api/client'
import { formatFileSize, formatDuration } from '../hooks/useCameras'
import type { Recording } from '../types'
import dayjs from 'dayjs'

const { RangePicker } = DatePicker

export function Recordings() {
  const { data: cameras } = useCameras()
  const { data: stats } = useRecordingStats()
  const deleteRecording = useDeleteRecording()

  const [cameraFilter, setCameraFilter] = useState<string | undefined>()
  const [dateRange, setDateRange] = useState<
    [dayjs.Dayjs, dayjs.Dayjs] | null
  >(null)
  const [playingRecording, setPlayingRecording] = useState<Recording | null>(
    null
  )
  const [recordingToDelete, setRecordingToDelete] = useState<Recording | null>(
    null
  )

  const { data: recordings, isLoading } = useRecordings({
    camera_id: cameraFilter,
    start_date: dateRange?.[0]?.toISOString(),
    end_date: dateRange?.[1]?.toISOString(),
    limit: 100,
  })

  const handleDelete = () => {
    if (recordingToDelete) {
      deleteRecording.mutate(recordingToDelete.id, {
        onSuccess: () => setRecordingToDelete(null),
      })
    }
  }

  const columns: ColumnsType<Recording> = [
    {
      title: 'Camera',
      dataIndex: 'camera_name',
      key: 'camera',
      width: 200,
      render: (name: string | undefined) => name || 'Unknown',
    },
    {
      title: 'Start Time',
      dataIndex: 'start_time',
      key: 'start_time',
      width: 180,
      sorter: (a, b) =>
        new Date(a.start_time).getTime() - new Date(b.start_time).getTime(),
      render: (date: string) => dayjs(date).format('YYYY-MM-DD HH:mm:ss'),
    },
    {
      title: 'Duration',
      dataIndex: 'duration_seconds',
      key: 'duration',
      width: 100,
      render: (seconds: number | null) => formatDuration(seconds),
    },
    {
      title: 'Size',
      dataIndex: 'file_size',
      key: 'size',
      width: 100,
      render: (bytes: number | null) => formatFileSize(bytes),
    },
    {
      title: 'Actions',
      key: 'actions',
      width: 150,
      render: (_, record: Recording) => (
        <Space>
          <Button
            type="text"
            size="small"
            icon={<PlayCircleOutlined />}
            onClick={() => setPlayingRecording(record)}
          >
            Play
          </Button>
          <Button
            type="text"
            size="small"
            icon={<DownloadOutlined />}
            href={getRecordingDownloadUrl(record.id)}
            target="_blank"
          />
          <Button
            type="text"
            size="small"
            danger
            icon={<DeleteOutlined />}
            onClick={() => setRecordingToDelete(record)}
          />
        </Space>
      ),
    },
  ]

  const cameraOptions = [
    { value: undefined, label: 'All Cameras' },
    ...(cameras?.map((c) => ({ value: c.id, label: c.name })) || []),
  ]

  return (
    <div>
      {/* Stats */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col xs={12} sm={6}>
          <Card size="small">
            <Statistic
              title="Total Recordings"
              value={stats?.total_recordings || 0}
              prefix={<DatabaseOutlined />}
            />
          </Card>
        </Col>
        <Col xs={12} sm={6}>
          <Card size="small">
            <Statistic
              title="Total Size"
              value={
                stats?.total_size_bytes
                  ? formatFileSize(stats.total_size_bytes)
                  : '0 B'
              }
              prefix={<DatabaseOutlined />}
            />
          </Card>
        </Col>
        <Col xs={12} sm={6}>
          <Card size="small">
            <Statistic
              title="Cameras with Recordings"
              value={stats?.cameras_with_recordings || 0}
              prefix={<VideoCameraOutlined />}
            />
          </Card>
        </Col>
        <Col xs={12} sm={6}>
          <Card size="small">
            <Statistic
              title="Oldest Recording"
              value={
                stats?.oldest_recording
                  ? dayjs(stats.oldest_recording).format('MMM D, YYYY')
                  : 'None'
              }
              prefix={<ClockCircleOutlined />}
            />
          </Card>
        </Col>
      </Row>

      {/* Filters */}
      <Space style={{ marginBottom: 16 }} wrap>
        <Select
          placeholder="Filter by camera"
          style={{ width: 200 }}
          value={cameraFilter}
          onChange={setCameraFilter}
          options={cameraOptions}
          allowClear
        />
        <RangePicker
          value={dateRange}
          onChange={(dates) =>
            setDateRange(dates as [dayjs.Dayjs, dayjs.Dayjs] | null)
          }
          showTime
        />
        <Button
          onClick={() => {
            setCameraFilter(undefined)
            setDateRange(null)
          }}
        >
          Clear Filters
        </Button>
      </Space>

      {/* Recordings Table */}
      <Table
        columns={columns}
        dataSource={recordings}
        rowKey="id"
        loading={isLoading}
        pagination={{
          pageSize: 20,
          showSizeChanger: true,
          showTotal: (total) => `${total} recordings`,
        }}
        size="middle"
      />

      {/* Playback Modal */}
      <Modal
        title={`Playing: ${playingRecording?.camera_name || 'Recording'}`}
        open={!!playingRecording}
        onCancel={() => setPlayingRecording(null)}
        footer={null}
        width={800}
        destroyOnClose
      >
        {playingRecording && (
          <div>
            <video
              src={getRecordingDownloadUrl(playingRecording.id)}
              controls
              autoPlay
              style={{ width: '100%', maxHeight: '60vh' }}
            />
            <div style={{ marginTop: 12 }}>
              <Typography.Text type="secondary">
                Recorded on{' '}
                {dayjs(playingRecording.start_time).format(
                  'MMMM D, YYYY [at] HH:mm:ss'
                )}
              </Typography.Text>
            </div>
          </div>
        )}
      </Modal>

      {/* Delete Confirmation */}
      <Modal
        title="Delete Recording"
        open={!!recordingToDelete}
        onOk={handleDelete}
        onCancel={() => setRecordingToDelete(null)}
        confirmLoading={deleteRecording.isPending}
        okText="Delete"
        okButtonProps={{ danger: true }}
      >
        <p>Are you sure you want to delete this recording?</p>
        <p>This will permanently remove the video file.</p>
      </Modal>
    </div>
  )
}
