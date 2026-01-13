"""ONVIF camera discovery service.

Uses WS-Discovery to find ONVIF-compliant cameras on the network
and extracts their capabilities and stream URLs.
"""

import asyncio
import logging
import re
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urlparse

from onvif import ONVIFCamera
from wsdiscovery.discovery import ThreadedWSDiscovery

from backend.schemas.camera import CameraDiscovered

logger = logging.getLogger(__name__)

# Thread pool for blocking ONVIF operations
_executor = ThreadPoolExecutor(max_workers=4)


class ONVIFDiscoveryService:
    """Service for discovering ONVIF cameras on the network."""

    def __init__(self):
        self._discovery_lock = asyncio.Lock()

    async def discover(self, timeout: int = 5) -> list[CameraDiscovered]:
        """Discover ONVIF cameras on the local network.

        Args:
            timeout: Discovery timeout in seconds.

        Returns:
            List of discovered cameras.
        """
        async with self._discovery_lock:
            logger.info(f"Starting ONVIF WS-Discovery (timeout: {timeout}s)...")

            try:
                # Run WS-Discovery in thread pool (it's blocking)
                loop = asyncio.get_event_loop()
                services = await loop.run_in_executor(
                    _executor,
                    self._run_ws_discovery,
                    timeout,
                )

                logger.info(f"WS-Discovery found {len(services)} services")

                # Filter and parse ONVIF services
                cameras = []
                for service in services:
                    try:
                        camera = self._parse_service(service)
                        if camera:
                            cameras.append(camera)
                    except Exception as e:
                        logger.debug(f"Failed to parse service: {e}")

                logger.info(f"Found {len(cameras)} ONVIF cameras")
                return cameras

            except Exception as e:
                logger.error(f"ONVIF discovery error: {e}")
                return []

    def _run_ws_discovery(self, timeout: int) -> list:
        """Run WS-Discovery (blocking operation)."""
        wsd = ThreadedWSDiscovery()
        wsd.start()

        # Search for ONVIF devices
        # ONVIF devices advertise with these types
        services = wsd.searchServices(
            types=[
                "tdn:NetworkVideoTransmitter",
                "tds:Device",
            ],
            timeout=timeout,
        )

        wsd.stop()
        return services

    def _parse_service(self, service) -> CameraDiscovered | None:
        """Parse WS-Discovery service into CameraDiscovered."""
        # Get XAddrs (service endpoints)
        xaddrs = service.getXAddrs()
        if not xaddrs:
            return None

        # Find ONVIF device service URL
        onvif_url = None
        for addr in xaddrs:
            if "onvif" in addr.lower() or "device_service" in addr.lower():
                onvif_url = addr
                break

        if not onvif_url:
            # Use first address as fallback
            onvif_url = xaddrs[0]

        # Parse host and port from URL
        parsed = urlparse(onvif_url)
        host = parsed.hostname
        port = parsed.port or 80

        if not host:
            return None

        # Get scopes for additional info
        scopes = service.getScopes()
        name = None
        manufacturer = None
        model = None

        for scope in scopes:
            scope_str = str(scope)
            # Parse ONVIF scope format: onvif://www.onvif.org/name/CameraName
            if "/name/" in scope_str:
                name = scope_str.split("/name/")[-1]
            elif "/hardware/" in scope_str:
                model = scope_str.split("/hardware/")[-1]
            elif "/manufacturer/" in scope_str or "/mfr/" in scope_str:
                if "/manufacturer/" in scope_str:
                    manufacturer = scope_str.split("/manufacturer/")[-1]
                else:
                    manufacturer = scope_str.split("/mfr/")[-1]

        return CameraDiscovered(
            host=host,
            port=port,
            name=name,
            manufacturer=manufacturer,
            model=model,
            onvif_url=onvif_url,
            rtsp_urls=[],  # Will be filled by probe_camera
        )

    async def probe_camera(
        self,
        host: str,
        port: int = 80,
        username: str | None = None,
        password: str | None = None,
    ) -> CameraDiscovered | None:
        """Probe a specific camera to get its capabilities and RTSP URLs.

        Args:
            host: Camera IP address or hostname.
            port: ONVIF port (usually 80 or 8080).
            username: Camera username.
            password: Camera password.

        Returns:
            Camera information or None if probe failed.
        """
        try:
            logger.info(f"Probing camera at {host}:{port}")

            # Run blocking ONVIF operations in thread pool
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                _executor,
                self._probe_camera_sync,
                host,
                port,
                username,
                password,
            )

            return result

        except Exception as e:
            logger.error(f"Failed to probe camera {host}:{port}: {e}")
            return None

    def _probe_camera_sync(
        self,
        host: str,
        port: int,
        username: str | None,
        password: str | None,
    ) -> CameraDiscovered | None:
        """Synchronous camera probe (runs in thread pool)."""
        try:
            # Create ONVIF camera connection
            camera = ONVIFCamera(
                host,
                port,
                username or "admin",
                password or "",
                no_cache=True,
            )

            # Get device information
            device_info = camera.devicemgmt.GetDeviceInformation()

            # Get media service and profiles
            media_service = camera.create_media_service()
            profiles = media_service.GetProfiles()

            # Get RTSP URLs for each profile
            rtsp_urls = []
            for profile in profiles:
                try:
                    stream_setup = {
                        "Stream": "RTP-Unicast",
                        "Transport": {"Protocol": "RTSP"},
                    }
                    uri_response = media_service.GetStreamUri(
                        {"StreamSetup": stream_setup, "ProfileToken": profile.token}
                    )
                    if uri_response and uri_response.Uri:
                        rtsp_urls.append(uri_response.Uri)
                except Exception as e:
                    logger.debug(f"Failed to get stream URI for profile {profile.token}: {e}")

            return CameraDiscovered(
                host=host,
                port=port,
                name=getattr(device_info, "Model", None) or f"Camera at {host}",
                manufacturer=getattr(device_info, "Manufacturer", None),
                model=getattr(device_info, "Model", None),
                firmware_version=getattr(device_info, "FirmwareVersion", None),
                serial_number=getattr(device_info, "SerialNumber", None),
                rtsp_urls=rtsp_urls,
                onvif_url=f"http://{host}:{port}/onvif/device_service",
            )

        except Exception as e:
            logger.error(f"ONVIF probe failed for {host}:{port}: {e}")
            return None

    async def get_rtsp_urls(
        self,
        host: str,
        port: int = 80,
        username: str | None = None,
        password: str | None = None,
    ) -> list[str]:
        """Get RTSP stream URLs from a camera.

        Args:
            host: Camera IP address.
            port: ONVIF port.
            username: Camera username.
            password: Camera password.

        Returns:
            List of RTSP URLs available from the camera.
        """
        camera = await self.probe_camera(host, port, username, password)
        if camera:
            return camera.rtsp_urls
        return []

    async def test_rtsp_url(self, rtsp_url: str, timeout: int = 5) -> bool:
        """Test if an RTSP URL is accessible.

        Args:
            rtsp_url: RTSP URL to test.
            timeout: Connection timeout in seconds.

        Returns:
            True if URL is accessible, False otherwise.
        """
        try:
            # Use FFprobe to test the stream
            proc = await asyncio.create_subprocess_exec(
                "ffprobe",
                "-v", "quiet",
                "-rtsp_transport", "tcp",
                "-i", rtsp_url,
                "-show_entries", "format=duration",
                "-of", "default=noprint_wrappers=1:nokey=1",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            try:
                await asyncio.wait_for(proc.communicate(), timeout=timeout)
                return proc.returncode == 0
            except asyncio.TimeoutError:
                proc.kill()
                await proc.wait()
                # Timeout on live stream is actually OK - means it's streaming
                return True

        except Exception as e:
            logger.debug(f"RTSP test failed for {rtsp_url}: {e}")
            return False


# Global discovery service instance
onvif_discovery = ONVIFDiscoveryService()
