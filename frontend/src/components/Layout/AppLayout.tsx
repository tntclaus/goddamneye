import { useState } from 'react'
import { Outlet, useLocation, useNavigate } from 'react-router-dom'
import { Layout, Typography } from 'antd'
import { AppMenu } from './AppMenu'
import {
  EyeOutlined,
  MenuFoldOutlined,
  MenuUnfoldOutlined,
} from '@ant-design/icons'

const { Header, Sider, Content } = Layout

export function AppLayout() {
  const [collapsed, setCollapsed] = useState(false)
  const location = useLocation()
  const navigate = useNavigate()

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Sider
        trigger={null}
        collapsible
        collapsed={collapsed}
        width={220}
        style={{
          overflow: 'auto',
          height: '100vh',
          position: 'fixed',
          left: 0,
          top: 0,
          bottom: 0,
          borderRight: '1px solid #303030',
        }}
      >
        {/* Logo */}
        <div
          style={{
            height: 64,
            display: 'flex',
            alignItems: 'center',
            justifyContent: collapsed ? 'center' : 'flex-start',
            padding: collapsed ? 0 : '0 16px',
            borderBottom: '1px solid #303030',
            cursor: 'pointer',
          }}
          onClick={() => navigate('/dashboard')}
        >
          <EyeOutlined
            style={{
              fontSize: 28,
              color: '#1890ff',
            }}
          />
          {!collapsed && (
            <Typography.Title
              level={4}
              style={{
                margin: '0 0 0 12px',
                color: '#fff',
                whiteSpace: 'nowrap',
              }}
            >
              GodDamnEye
            </Typography.Title>
          )}
        </div>

        {/* Navigation Menu */}
        <AppMenu />
      </Sider>

      <Layout
        style={{
          marginLeft: collapsed ? 80 : 220,
          transition: 'margin-left 0.2s',
        }}
      >
        <Header
          style={{
            padding: '0 24px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            borderBottom: '1px solid #303030',
          }}
        >
          {/* Collapse Toggle */}
          <div
            onClick={() => setCollapsed(!collapsed)}
            style={{
              cursor: 'pointer',
              fontSize: 18,
              padding: '8px 12px',
              borderRadius: 6,
              transition: 'background 0.2s',
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.background = '#262626'
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.background = 'transparent'
            }}
          >
            {collapsed ? <MenuUnfoldOutlined /> : <MenuFoldOutlined />}
          </div>

          {/* Page Title */}
          <Typography.Text
            style={{
              fontSize: 16,
              color: 'rgba(255,255,255,0.65)',
            }}
          >
            {getPageTitle(location.pathname)}
          </Typography.Text>

          {/* Placeholder for future user menu */}
          <div style={{ width: 40 }} />
        </Header>

        <Content
          style={{
            margin: 24,
            minHeight: 280,
          }}
        >
          <Outlet />
        </Content>
      </Layout>
    </Layout>
  )
}

function getPageTitle(pathname: string): string {
  switch (pathname) {
    case '/dashboard':
      return 'Live Dashboard'
    case '/cameras':
      return 'Camera Management'
    case '/recordings':
      return 'Recordings'
    case '/settings':
      return 'Settings'
    default:
      return ''
  }
}
