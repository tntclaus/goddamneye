# GodDamnEye Test Scenarios
# Based on bugs encountered during trial run (2026-01-13)

Feature: RTSP URL Credential Handling
  As a user with cameras that have special characters in passwords
  I want the system to properly handle URL encoding
  So that I can connect to cameras without authentication failures

  Background:
    Given a camera with special character password "2XkRHya8%^Ysmd7jTihQ4pdK"

  Scenario: Camera probe returns clean URLs without embedded credentials
    When I probe a camera at "192.168.90.98" with username "admin"
    Then the returned RTSP URLs should not contain credentials
    And the URLs should be in format "rtsp://host:port/path"
    And the probe response should include camera info separately

  Scenario: Camera is stored with clean RTSP URL
    When I create a camera with RTSP URL "rtsp://192.168.1.100:554/stream1"
    And username "admin" and password "2XkRHya8%^Ysmd7jTihQ4pdK"
    Then the camera's stored rtsp_url should be "rtsp://192.168.1.100:554/stream1"
    And the password should be stored separately in password_encrypted field

  Scenario: Stream worker properly encodes credentials at runtime
    Given a camera with clean URL "rtsp://192.168.1.100:554/stream1"
    And username "admin" and password "2XkRHya8%^Ysmd7jTihQ4pdK"
    When the stream worker builds the FFmpeg RTSP URL
    Then the URL should encode "%" as "%25"
    And the URL should encode "^" as "%5E"
    And the final URL should be "rtsp://admin:2XkRHya8%25%5EYsmd7jTihQ4pdK@192.168.1.100:554/stream1"

  Scenario: Password with @ symbol is properly encoded
    Given a camera with password "pass@word123"
    When the stream worker builds the FFmpeg RTSP URL
    Then the "@" in password should be encoded as "%40"
    And the URL should not break the host:port parsing

  Scenario: Password with colon is properly encoded
    Given a camera with password "pass:word:123"
    When the stream worker builds the FFmpeg RTSP URL
    Then the ":" in password should be encoded as "%3A"


Feature: Camera Stream Lifecycle Management
  As a system administrator
  I want camera streams to automatically start and stop
  So that I don't have to manually manage each camera's streaming process

  Scenario: Stream auto-starts when camera is created with enabled=true
    When I create a new camera with enabled=true
    Then the camera stream should start automatically
    And the camera should appear in active streams list

  Scenario: Stream auto-starts when camera is enabled
    Given an existing disabled camera
    When I enable the camera via POST /api/cameras/{id}/enable
    Then the camera stream should start automatically
    And the HLS playlist should be accessible

  Scenario: Stream stops when camera is disabled
    Given an existing enabled camera with active stream
    When I disable the camera via POST /api/cameras/{id}/disable
    Then the camera stream should stop
    And the camera should not appear in active streams list

  Scenario: Stream stops when camera is deleted
    Given an existing enabled camera with active stream
    When I delete the camera via DELETE /api/cameras/{id}
    Then the camera stream should stop
    And no orphaned FFmpeg process should remain

  Scenario: Camera created with enabled=false does not start stream
    When I create a new camera with enabled=false
    Then no stream should be started for the camera


Feature: Camera Probe and Auto-Discovery
  As a user adding a new camera
  I want to provide just an IP address and credentials
  So that the system can auto-detect ONVIF settings and available streams

  Scenario: Successful ONVIF camera probe
    Given an ONVIF-compatible camera at "192.168.1.100"
    When I probe with valid credentials
    Then the response should indicate onvif_supported=true
    And the response should include manufacturer and model
    And the response should include a list of available streams
    And each stream should have name, url, and description

  Scenario: Camera probe with ONVIF not available
    Given a camera that doesn't support ONVIF
    When I probe the camera
    Then the response should indicate onvif_supported=false
    And the response should include common RTSP URL patterns to try
    And an error message should explain ONVIF is not available

  Scenario: Camera probe with invalid credentials
    Given an ONVIF camera at "192.168.1.100"
    When I probe with invalid credentials
    Then the response should indicate authentication failure
    Or the response should fall back to common RTSP patterns


Feature: Camera CRUD Operations
  As an API consumer
  I want full CRUD operations on cameras
  So that I can manage the camera inventory

  Scenario: Create camera with all fields
    When I POST to /api/cameras with valid data
    Then the camera should be created with HTTP 201
    And an auto-generated UUID should be assigned
    And created_at and updated_at should be set

  Scenario: Create camera rejects duplicate names
    Given a camera named "Front Door" exists
    When I try to create another camera named "Front Door"
    Then the request should fail with HTTP 409
    And the error should explain the name already exists

  Scenario: Update camera preserves unspecified fields
    Given an existing camera with all fields populated
    When I update only the name field
    Then the name should be updated
    And all other fields should remain unchanged

  Scenario: Update camera password is optional
    Given an existing camera with a password
    When I update the camera without providing a password
    Then the existing password should be preserved


Feature: Stream Status and Health Monitoring
  As a system operator
  I want to monitor stream health status
  So that I can identify and troubleshoot issues

  Scenario: Stream status reports all active streams
    Given multiple cameras with active streams
    When I GET /api/streams/status
    Then I should see count of active_streams
    And each stream should report camera_id, name, is_running, pid

  Scenario: Stream status reports HLS URL for active streams
    Given a camera with an active stream
    When I GET /api/streams/status
    Then the stream entry should include hls_url path

  Scenario: HLS playlist is accessible for active stream
    Given a camera with an active stream
    When I GET the HLS playlist URL
    Then I should receive a valid m3u8 playlist
    And it should list available segments


Feature: Frontend Camera Form
  As a user
  I want a simple camera setup experience
  So that I can add cameras without knowing technical details

  Scenario: Simple setup mode probes camera
    Given I'm on the Add Camera modal in Simple mode
    When I enter IP address and credentials and click "Detect Camera"
    Then the system should probe the camera
    And display detected camera info
    And show available stream options

  Scenario: Simple setup pre-fills camera name from detection
    Given the camera probe succeeded with name "IPC-Model-123"
    Then the camera name field should be pre-filled with "IPC-Model-123"
    And I should be able to change it before saving

  Scenario: Simple setup saves with clean URL
    Given I completed simple setup with stream selection
    When I submit the form
    Then the created camera should have clean RTSP URL without credentials
    And credentials should be stored separately

  Scenario: Advanced mode allows manual configuration
    Given I'm on the Add Camera modal
    When I switch to Advanced tab
    Then I should see full manual configuration form
    And I should be able to enter RTSP URL directly

  Scenario: Edit camera uses advanced mode
    Given an existing camera
    When I click Edit on the camera
    Then the form should open in Advanced mode
    And be pre-filled with current camera settings
