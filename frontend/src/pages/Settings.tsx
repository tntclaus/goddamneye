import { Card, Descriptions, Tag, Typography, Divider, Alert } from 'antd'
import { useHealth, useSystemInfo } from '../hooks/useApi'

export function Settings() {
  const { data: health, isLoading: healthLoading } = useHealth()
  const { data: systemInfo, isLoading: infoLoading } = useSystemInfo()

  return (
    <div style={{ maxWidth: 800 }}>
      <Typography.Title level={4}>System Information</Typography.Title>

      <Card loading={healthLoading || infoLoading}>
        <Descriptions column={1} bordered size="small">
          <Descriptions.Item label="Application">
            {systemInfo?.app_name}
          </Descriptions.Item>
          <Descriptions.Item label="Version">
            {systemInfo?.version}
          </Descriptions.Item>
          <Descriptions.Item label="Status">
            <Tag color={health?.status === 'healthy' ? 'success' : 'error'}>
              {health?.status?.toUpperCase() || 'UNKNOWN'}
            </Tag>
          </Descriptions.Item>
          <Descriptions.Item label="Debug Mode">
            <Tag color={systemInfo?.debug ? 'warning' : 'default'}>
              {systemInfo?.debug ? 'ENABLED' : 'DISABLED'}
            </Tag>
          </Descriptions.Item>
          <Descriptions.Item label="Storage Path">
            <code>{systemInfo?.storage_path}</code>
          </Descriptions.Item>
          <Descriptions.Item label="Database">
            <code>{systemInfo?.database_url}</code>
          </Descriptions.Item>
        </Descriptions>
      </Card>

      <Divider />

      <Typography.Title level={4}>Authentication</Typography.Title>

      <Alert
        message="No Authentication Configured"
        description={
          <>
            <p>
              This is the MVP version without authentication. All endpoints are
              publicly accessible.
            </p>
            <p>
              For production use, configure SSO OAuth integration with your
              Identity Management system.
            </p>
          </>
        }
        type="warning"
        showIcon
        style={{ marginBottom: 16 }}
      />

      <Card>
        <Descriptions column={1} bordered size="small">
          <Descriptions.Item label="Authentication">
            <Tag color="default">DISABLED</Tag>
          </Descriptions.Item>
          <Descriptions.Item label="SSO OAuth">
            <Tag color="default">NOT CONFIGURED</Tag>
          </Descriptions.Item>
        </Descriptions>

        <Divider />

        <Typography.Text type="secondary">
          To enable SSO OAuth authentication, set the following environment
          variables:
        </Typography.Text>
        <pre
          style={{
            background: '#0a0a0a',
            padding: 12,
            borderRadius: 6,
            marginTop: 12,
            fontSize: 12,
          }}
        >
          {`OAUTH_ENABLED=true
OAUTH_ISSUER_URL=https://your-idm.example.com
OAUTH_CLIENT_ID=goddamneye
OAUTH_CLIENT_SECRET=your-secret`}
        </pre>
      </Card>

      <Divider />

      <Typography.Title level={4}>About</Typography.Title>

      <Card>
        <Typography.Paragraph>
          <strong>GodDamnEye</strong> is an open-source CCTV camera management
          system with RTSP/ONVIF support, local video storage, and web
          interface.
        </Typography.Paragraph>
        <Typography.Paragraph>
          Licensed under the{' '}
          <Typography.Link
            href="https://www.gnu.org/licenses/agpl-3.0.html"
            target="_blank"
          >
            GNU Affero General Public License v3.0
          </Typography.Link>
        </Typography.Paragraph>
        <Typography.Paragraph type="secondary">
          "The first rule of surveillance: If you're not recording, it didn't
          happen."
        </Typography.Paragraph>
      </Card>
    </div>
  )
}
