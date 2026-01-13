import { Table, Button, Space, Tag } from 'antd'
import type { ColumnsType } from 'antd/es/table'
import {
  PlayCircleOutlined,
  DownloadOutlined,
  DeleteOutlined,
} from '@ant-design/icons'
import { getRecordingDownloadUrl } from '../../api/client'
import { formatFileSize, formatDuration } from '../../hooks/useCameras'
import type { Recording } from '../../types'
import dayjs from 'dayjs'

interface RecordingsTableProps {
  recordings: Recording[]
  loading?: boolean
  onPlay?: (recording: Recording) => void
  onDelete?: (recording: Recording) => void
}

export function RecordingsTable({
  recordings,
  loading = false,
  onPlay,
  onDelete,
}: RecordingsTableProps) {
  const columns: ColumnsType<Recording> = [
    {
      title: 'Camera',
      dataIndex: 'camera_name',
      key: 'camera',
      width: 200,
      render: (name: string | undefined) => name || 'Unknown',
    },
    {
      title: 'Date',
      dataIndex: 'start_time',
      key: 'date',
      width: 120,
      render: (date: string) => dayjs(date).format('YYYY-MM-DD'),
    },
    {
      title: 'Time',
      dataIndex: 'start_time',
      key: 'time',
      width: 100,
      render: (date: string) => dayjs(date).format('HH:mm:ss'),
    },
    {
      title: 'Duration',
      dataIndex: 'duration_seconds',
      key: 'duration',
      width: 100,
      render: (seconds: number | null) => (
        <Tag>{formatDuration(seconds)}</Tag>
      ),
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
            onClick={() => onPlay?.(record)}
          />
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
            onClick={() => onDelete?.(record)}
          />
        </Space>
      ),
    },
  ]

  return (
    <Table
      columns={columns}
      dataSource={recordings}
      rowKey="id"
      loading={loading}
      pagination={{
        pageSize: 20,
        showSizeChanger: true,
        showTotal: (total) => `${total} recordings`,
      }}
      size="middle"
    />
  )
}
