import { theme, ThemeConfig } from 'antd'

/**
 * GodDamnEye Dark Theme
 * Surveillance operations aesthetic with high contrast
 */
export const darkTheme: ThemeConfig = {
  algorithm: theme.darkAlgorithm,
  token: {
    // Primary colors - electric blue for active elements
    colorPrimary: '#1890ff',
    colorInfo: '#1890ff',

    // Status colors
    colorSuccess: '#52c41a',
    colorWarning: '#faad14',
    colorError: '#ff4d4f',

    // Background colors
    colorBgContainer: '#1f1f1f',
    colorBgElevated: '#262626',
    colorBgLayout: '#141414',

    // Border
    colorBorder: '#303030',
    colorBorderSecondary: '#424242',

    // Text
    colorText: 'rgba(255, 255, 255, 0.85)',
    colorTextSecondary: 'rgba(255, 255, 255, 0.65)',
    colorTextTertiary: 'rgba(255, 255, 255, 0.45)',

    // Font
    fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif',
    fontSize: 14,

    // Border radius
    borderRadius: 6,
    borderRadiusLG: 8,
    borderRadiusSM: 4,

    // Motion
    motionDurationMid: '0.2s',
    motionDurationSlow: '0.3s',
  },
  components: {
    Layout: {
      siderBg: '#141414',
      headerBg: '#1f1f1f',
      bodyBg: '#0a0a0a',
    },
    Menu: {
      darkItemBg: '#141414',
      darkItemSelectedBg: '#1890ff20',
      darkItemHoverBg: '#1890ff10',
    },
    Card: {
      colorBgContainer: '#1f1f1f',
    },
    Table: {
      colorBgContainer: '#1f1f1f',
      headerBg: '#262626',
    },
    Modal: {
      contentBg: '#1f1f1f',
      headerBg: '#1f1f1f',
    },
    Button: {
      primaryShadow: '0 2px 0 rgba(24, 144, 255, 0.1)',
    },
  },
}

// Camera status colors
export const statusColors = {
  online: '#52c41a',
  offline: '#ff4d4f',
  recording: '#1890ff',
  connecting: '#faad14',
  error: '#ff4d4f',
}
