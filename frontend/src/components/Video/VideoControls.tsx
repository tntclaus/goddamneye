import { Space, Button, Slider, Typography, Tooltip } from 'antd'
import {
  PlayCircleOutlined,
  PauseCircleOutlined,
  SoundOutlined,
  MutedOutlined,
  FullscreenOutlined,
  FullscreenExitOutlined,
} from '@ant-design/icons'

interface VideoControlsProps {
  playing: boolean
  muted: boolean
  volume: number
  currentTime: number
  duration: number
  fullscreen: boolean
  onPlayPause: () => void
  onMuteToggle: () => void
  onVolumeChange: (volume: number) => void
  onSeek: (time: number) => void
  onFullscreenToggle: () => void
}

export function VideoControls({
  playing,
  muted,
  volume,
  currentTime,
  duration,
  fullscreen,
  onPlayPause,
  onMuteToggle,
  onVolumeChange,
  onSeek,
  onFullscreenToggle,
}: VideoControlsProps) {
  const formatTime = (seconds: number): string => {
    const h = Math.floor(seconds / 3600)
    const m = Math.floor((seconds % 3600) / 60)
    const s = Math.floor(seconds % 60)

    if (h > 0) {
      return `${h}:${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`
    }
    return `${m}:${s.toString().padStart(2, '0')}`
  }

  return (
    <div
      style={{
        display: 'flex',
        alignItems: 'center',
        padding: '8px 12px',
        background: 'rgba(0, 0, 0, 0.8)',
        borderRadius: 6,
        gap: 12,
      }}
    >
      {/* Play/Pause */}
      <Tooltip title={playing ? 'Pause' : 'Play'}>
        <Button
          type="text"
          size="small"
          icon={playing ? <PauseCircleOutlined /> : <PlayCircleOutlined />}
          onClick={onPlayPause}
          style={{ color: '#fff' }}
        />
      </Tooltip>

      {/* Timeline */}
      <div style={{ flex: 1, display: 'flex', alignItems: 'center', gap: 8 }}>
        <Typography.Text style={{ color: '#fff', fontSize: 12, minWidth: 40 }}>
          {formatTime(currentTime)}
        </Typography.Text>

        <Slider
          min={0}
          max={duration || 100}
          value={currentTime}
          onChange={onSeek}
          tooltip={{ formatter: (value) => formatTime(value || 0) }}
          style={{ flex: 1, margin: 0 }}
        />

        <Typography.Text style={{ color: '#fff', fontSize: 12, minWidth: 40 }}>
          {formatTime(duration)}
        </Typography.Text>
      </div>

      {/* Volume */}
      <Space size={4}>
        <Tooltip title={muted ? 'Unmute' : 'Mute'}>
          <Button
            type="text"
            size="small"
            icon={muted ? <MutedOutlined /> : <SoundOutlined />}
            onClick={onMuteToggle}
            style={{ color: '#fff' }}
          />
        </Tooltip>
        <Slider
          min={0}
          max={100}
          value={muted ? 0 : volume}
          onChange={onVolumeChange}
          style={{ width: 60, margin: 0 }}
        />
      </Space>

      {/* Fullscreen */}
      <Tooltip title={fullscreen ? 'Exit Fullscreen' : 'Fullscreen'}>
        <Button
          type="text"
          size="small"
          icon={fullscreen ? <FullscreenExitOutlined /> : <FullscreenOutlined />}
          onClick={onFullscreenToggle}
          style={{ color: '#fff' }}
        />
      </Tooltip>
    </div>
  )
}
