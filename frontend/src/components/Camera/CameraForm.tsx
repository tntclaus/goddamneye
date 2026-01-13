import { useState, useEffect } from 'react'
import {
  Modal,
  Form,
  Input,
  Switch,
  Space,
  Divider,
  Button,
  Alert,
  Select,
  Tabs,
  Descriptions,
  Spin,
  Typography,
} from 'antd'
import {
  SearchOutlined,
  CheckCircleOutlined,
  WarningOutlined,
} from '@ant-design/icons'
import { probeCamera, type CameraProbeResponse, type CameraProbeStream } from '../../api/client'
import type { Camera, CameraCreate, CameraUpdate } from '../../types'

const { Text } = Typography

interface CameraFormProps {
  open: boolean
  camera?: Camera // If provided, we're editing
  onSubmit: (values: CameraCreate | CameraUpdate) => void
  onCancel: () => void
  loading?: boolean
}

type FormMode = 'simple' | 'advanced'

export function CameraForm({
  open,
  camera,
  onSubmit,
  onCancel,
  loading = false,
}: CameraFormProps) {
  const [simpleForm] = Form.useForm()
  const [advancedForm] = Form.useForm()
  const isEditing = !!camera

  const [mode, setMode] = useState<FormMode>('simple')
  const [probing, setProbing] = useState(false)
  const [probeResult, setProbeResult] = useState<CameraProbeResponse | null>(null)
  const [probeError, setProbeError] = useState<string | null>(null)
  const [selectedStream, setSelectedStream] = useState<CameraProbeStream | null>(null)

  // Reset state when modal opens/closes
  useEffect(() => {
    if (open) {
      if (camera) {
        // Editing - always use advanced mode
        setMode('advanced')
        advancedForm.setFieldsValue({
          name: camera.name,
          description: camera.description,
          rtsp_url: camera.rtsp_url,
          onvif_host: camera.onvif_host,
          onvif_port: camera.onvif_port,
          username: camera.username,
          password: '',
          enabled: camera.enabled,
          recording_enabled: camera.recording_enabled,
        })
      } else {
        // New camera - start with simple mode
        setMode('simple')
        simpleForm.resetFields()
        advancedForm.resetFields()
        advancedForm.setFieldsValue({
          enabled: true,
          recording_enabled: true,
          onvif_port: 80,
        })
        setProbeResult(null)
        setProbeError(null)
        setSelectedStream(null)
      }
    }
  }, [open, camera, simpleForm, advancedForm])

  // Handle probe button click
  const handleProbe = async () => {
    try {
      const values = await simpleForm.validateFields(['host', 'username', 'password'])
      setProbing(true)
      setProbeError(null)
      setProbeResult(null)
      setSelectedStream(null)

      const result = await probeCamera({
        host: values.host,
        port: 80,
        username: values.username,
        password: values.password,
      })

      setProbeResult(result)

      // Auto-select first stream
      if (result.streams.length > 0) {
        setSelectedStream(result.streams[0])
      }

      // Pre-fill the camera name
      if (result.name) {
        simpleForm.setFieldValue('name', result.name)
      }
    } catch (error: unknown) {
      const err = error as { response?: { data?: { detail?: string } }; message?: string }
      setProbeError(err.response?.data?.detail || err.message || 'Failed to probe camera')
    } finally {
      setProbing(false)
    }
  }

  // Handle simple form submit
  const handleSimpleSubmit = async () => {
    if (!selectedStream) {
      setProbeError('Please select a stream')
      return
    }

    try {
      const values = await simpleForm.validateFields(['name'])

      onSubmit({
        name: values.name,
        rtsp_url: selectedStream.url,
        onvif_host: probeResult?.host,
        onvif_port: probeResult?.port || 80,
        username: simpleForm.getFieldValue('username'),
        password: simpleForm.getFieldValue('password'),
        enabled: true,
        recording_enabled: true,
      })
    } catch {
      // Form validation failed
    }
  }

  // Handle advanced form submit
  const handleAdvancedSubmit = (values: CameraCreate | CameraUpdate) => {
    if (isEditing && !values.password) {
      delete values.password
    }
    onSubmit(values)
  }

  const renderSimpleForm = () => (
    <Form form={simpleForm} layout="vertical" autoComplete="off">
      {/* Step 1: Camera Connection */}
      <div style={{ marginBottom: 16 }}>
        <Text strong>Step 1: Connect to Camera</Text>
      </div>

      <Form.Item
        name="host"
        label="Camera IP Address"
        rules={[{ required: true, message: 'Enter the camera IP address' }]}
      >
        <Input placeholder="192.168.1.100" disabled={probing} />
      </Form.Item>

      <Space style={{ width: '100%' }} size="middle">
        <Form.Item
          name="username"
          label="Username"
          style={{ flex: 1, marginBottom: 0 }}
        >
          <Input placeholder="admin" disabled={probing} />
        </Form.Item>

        <Form.Item
          name="password"
          label="Password"
          style={{ flex: 1, marginBottom: 0 }}
        >
          <Input.Password placeholder="password" disabled={probing} />
        </Form.Item>
      </Space>

      <div style={{ marginTop: 16, marginBottom: 24 }}>
        <Button
          type="primary"
          icon={<SearchOutlined />}
          onClick={handleProbe}
          loading={probing}
          block
        >
          {probing ? 'Detecting Camera...' : 'Detect Camera'}
        </Button>
      </div>

      {/* Probe Error */}
      {probeError && (
        <Alert
          type="error"
          message={probeError}
          showIcon
          style={{ marginBottom: 16 }}
        />
      )}

      {/* Step 2: Camera Info & Stream Selection */}
      {probeResult && (
        <>
          <Divider />
          <div style={{ marginBottom: 16 }}>
            <Text strong>Step 2: Camera Detected</Text>
          </div>

          {/* Camera Info */}
          <Alert
            type={probeResult.onvif_supported ? 'success' : 'warning'}
            icon={probeResult.onvif_supported ? <CheckCircleOutlined /> : <WarningOutlined />}
            message={probeResult.onvif_supported ? 'ONVIF Camera Detected' : 'ONVIF Not Available'}
            description={
              probeResult.onvif_supported ? (
                <Descriptions size="small" column={1} style={{ marginTop: 8 }}>
                  {probeResult.manufacturer && (
                    <Descriptions.Item label="Manufacturer">
                      {probeResult.manufacturer}
                    </Descriptions.Item>
                  )}
                  {probeResult.model && (
                    <Descriptions.Item label="Model">
                      {probeResult.model}
                    </Descriptions.Item>
                  )}
                </Descriptions>
              ) : (
                'Showing common RTSP URL patterns. You may need to try different options.'
              )
            }
            showIcon
            style={{ marginBottom: 16 }}
          />

          {/* Stream Selection */}
          <Form.Item label="Select Stream" required>
            <Select
              value={selectedStream?.url}
              onChange={(url) => {
                const stream = probeResult.streams.find((s) => s.url === url)
                setSelectedStream(stream || null)
              }}
              placeholder="Select a video stream"
            >
              {probeResult.streams.map((stream) => (
                <Select.Option key={stream.url} value={stream.url}>
                  <div>
                    <div>{stream.name}</div>
                    <Text type="secondary" style={{ fontSize: 12 }}>
                      {stream.description}
                    </Text>
                  </div>
                </Select.Option>
              ))}
            </Select>
          </Form.Item>

          {/* Step 3: Name */}
          <Divider />
          <div style={{ marginBottom: 16 }}>
            <Text strong>Step 3: Name Your Camera</Text>
          </div>

          <Form.Item
            name="name"
            label="Camera Name"
            rules={[{ required: true, message: 'Give your camera a name' }]}
          >
            <Input placeholder="e.g., Front Door, Backyard, Garage" />
          </Form.Item>
        </>
      )}
    </Form>
  )

  const renderAdvancedForm = () => (
    <Form
      form={advancedForm}
      layout="vertical"
      onFinish={handleAdvancedSubmit}
      autoComplete="off"
    >
      <Form.Item
        name="name"
        label="Camera Name"
        rules={[{ required: true, message: 'Please enter a camera name' }]}
      >
        <Input placeholder="e.g., Front Door" />
      </Form.Item>

      <Form.Item name="description" label="Description">
        <Input.TextArea
          placeholder="Optional description"
          rows={2}
          showCount
          maxLength={500}
        />
      </Form.Item>

      <Divider>Connection Settings</Divider>

      <Form.Item
        name="rtsp_url"
        label="RTSP URL"
        rules={[{ required: true, message: 'Please enter the RTSP URL' }]}
        extra="e.g., rtsp://user:pass@192.168.1.100:554/stream1"
      >
        <Input placeholder="rtsp://..." />
      </Form.Item>

      <Space style={{ width: '100%' }} size="middle">
        <Form.Item
          name="onvif_host"
          label="ONVIF Host"
          style={{ flex: 2, marginBottom: 0 }}
        >
          <Input placeholder="192.168.1.100" />
        </Form.Item>

        <Form.Item
          name="onvif_port"
          label="Port"
          style={{ flex: 1, marginBottom: 0 }}
        >
          <Input type="number" placeholder="80" />
        </Form.Item>
      </Space>

      <div style={{ height: 24 }} />

      <Space style={{ width: '100%' }} size="middle">
        <Form.Item
          name="username"
          label="Username"
          style={{ flex: 1, marginBottom: 0 }}
        >
          <Input placeholder="admin" />
        </Form.Item>

        <Form.Item
          name="password"
          label={isEditing ? 'New Password' : 'Password'}
          style={{ flex: 1, marginBottom: 0 }}
        >
          <Input.Password
            placeholder={isEditing ? 'Leave empty to keep' : 'password'}
          />
        </Form.Item>
      </Space>

      <Divider>Options</Divider>

      <Space size="large">
        <Form.Item
          name="enabled"
          label="Enabled"
          valuePropName="checked"
          style={{ marginBottom: 0 }}
        >
          <Switch />
        </Form.Item>

        <Form.Item
          name="recording_enabled"
          label="Recording"
          valuePropName="checked"
          style={{ marginBottom: 0 }}
        >
          <Switch />
        </Form.Item>
      </Space>
    </Form>
  )

  const handleOk = () => {
    if (mode === 'simple') {
      handleSimpleSubmit()
    } else {
      advancedForm.submit()
    }
  }

  // Can only submit simple form if we have a selected stream
  const canSubmitSimple = mode === 'simple' && selectedStream !== null

  return (
    <Modal
      title={isEditing ? 'Edit Camera' : 'Add Camera'}
      open={open}
      onCancel={onCancel}
      onOk={handleOk}
      confirmLoading={loading}
      okButtonProps={{
        disabled: mode === 'simple' && !canSubmitSimple,
      }}
      okText={mode === 'simple' ? 'Add Camera' : isEditing ? 'Save' : 'Create'}
      width={550}
      destroyOnClose
    >
      {probing && (
        <div style={{ textAlign: 'center', padding: '20px 0' }}>
          <Spin size="large" />
          <div style={{ marginTop: 16 }}>Probing camera...</div>
        </div>
      )}

      {!isEditing ? (
        <Tabs
          activeKey={mode}
          onChange={(key) => setMode(key as FormMode)}
          items={[
            {
              key: 'simple',
              label: 'Simple Setup',
              children: renderSimpleForm(),
            },
            {
              key: 'advanced',
              label: 'Advanced',
              children: renderAdvancedForm(),
            },
          ]}
        />
      ) : (
        renderAdvancedForm()
      )}
    </Modal>
  )
}
