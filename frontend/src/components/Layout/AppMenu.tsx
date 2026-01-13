import { useLocation, useNavigate } from 'react-router-dom'
import { Menu } from 'antd'
import type { MenuProps } from 'antd'
import {
  DashboardOutlined,
  VideoCameraOutlined,
  PlaySquareOutlined,
  SettingOutlined,
} from '@ant-design/icons'

type MenuItem = Required<MenuProps>['items'][number]

const menuItems: MenuItem[] = [
  {
    key: '/dashboard',
    icon: <DashboardOutlined />,
    label: 'Dashboard',
  },
  {
    key: '/cameras',
    icon: <VideoCameraOutlined />,
    label: 'Cameras',
  },
  {
    key: '/recordings',
    icon: <PlaySquareOutlined />,
    label: 'Recordings',
  },
  {
    type: 'divider',
  },
  {
    key: '/settings',
    icon: <SettingOutlined />,
    label: 'Settings',
  },
]

export function AppMenu() {
  const location = useLocation()
  const navigate = useNavigate()

  const handleClick: MenuProps['onClick'] = (e) => {
    navigate(e.key)
  }

  return (
    <Menu
      theme="dark"
      mode="inline"
      selectedKeys={[location.pathname]}
      items={menuItems}
      onClick={handleClick}
      style={{
        borderRight: 0,
        marginTop: 8,
      }}
    />
  )
}
