"""Constants for the Bird Feeder Voice Portal integration."""

DOMAIN = "birdfeeder_portal"

# Configuration keys
CONF_PORT = "port"
CONF_FRIGATE_URL = "frigate_url"
CONF_CAMERA_NAME = "camera_name"
CONF_FRIGATE_USERNAME = "frigate_username"
CONF_FRIGATE_PASSWORD = "frigate_password"
CONF_CONVERSATION_AGENT = "conversation_agent"
CONF_TTS_ENGINE = "tts_engine"
CONF_TTS_VOICE = "tts_voice"

# Default configuration values
DEFAULT_PORT = 8195
DEFAULT_FRIGATE_URL = "http://ccab4aaf-frigate:5000"
DEFAULT_CAMERA_NAME = "feeder"
DEFAULT_CONVERSATION_AGENT = "conversation.google_ai_conversation"
DEFAULT_TTS_ENGINE = "tts.home_assistant_cloud"
DEFAULT_TTS_VOICE = "AmberNeural"

# Storage / state tracking keys
STORAGE_VERSION = 1
STORAGE_KEY = "birdfeeder_portal_stats"
