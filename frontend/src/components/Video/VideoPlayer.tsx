import { useEffect, useRef, CSSProperties } from 'react'
import Hls from 'hls.js'

interface VideoPlayerProps {
  src: string
  autoPlay?: boolean
  muted?: boolean
  controls?: boolean
  style?: CSSProperties
  className?: string
  onError?: (error: Error) => void
}

export function VideoPlayer({
  src,
  autoPlay = false,
  muted = false,
  controls = false,
  style,
  className,
  onError,
}: VideoPlayerProps) {
  const videoRef = useRef<HTMLVideoElement>(null)
  const hlsRef = useRef<Hls | null>(null)

  useEffect(() => {
    const video = videoRef.current
    if (!video || !src) return

    // Cleanup previous instance
    if (hlsRef.current) {
      hlsRef.current.destroy()
      hlsRef.current = null
    }

    // Check HLS support
    if (Hls.isSupported()) {
      const hls = new Hls({
        enableWorker: true,
        lowLatencyMode: true,
        backBufferLength: 90,
        maxBufferLength: 30,
        maxMaxBufferLength: 60,
        liveSyncDurationCount: 3,
        liveMaxLatencyDurationCount: 10,
      })

      hls.loadSource(src)
      hls.attachMedia(video)

      hls.on(Hls.Events.MANIFEST_PARSED, () => {
        if (autoPlay) {
          video.play().catch(() => {
            // Autoplay was prevented, that's okay
          })
        }
      })

      hls.on(Hls.Events.ERROR, (_, data) => {
        if (data.fatal) {
          switch (data.type) {
            case Hls.ErrorTypes.NETWORK_ERROR:
              console.error('HLS network error, attempting to recover...')
              hls.startLoad()
              break
            case Hls.ErrorTypes.MEDIA_ERROR:
              console.error('HLS media error, attempting to recover...')
              hls.recoverMediaError()
              break
            default:
              console.error('Fatal HLS error:', data)
              hls.destroy()
              onError?.(new Error(`HLS error: ${data.type}`))
              break
          }
        }
      })

      hlsRef.current = hls
    } else if (video.canPlayType('application/vnd.apple.mpegurl')) {
      // Native HLS support (Safari)
      video.src = src
      if (autoPlay) {
        video.play().catch(() => {})
      }
    } else {
      onError?.(new Error('HLS is not supported in this browser'))
    }

    return () => {
      if (hlsRef.current) {
        hlsRef.current.destroy()
        hlsRef.current = null
      }
    }
  }, [src, autoPlay, onError])

  return (
    <video
      ref={videoRef}
      autoPlay={autoPlay}
      muted={muted}
      controls={controls}
      playsInline
      style={style}
      className={className}
    />
  )
}
