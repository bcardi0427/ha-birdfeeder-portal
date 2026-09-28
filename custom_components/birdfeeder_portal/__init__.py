"""Bird Feeder Voice Portal Integration for Home Assistant."""

from datetime import timedelta
import logging
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from aiohttp import web
from homeassistant.components.http import HomeAssistantView
from homeassistant.helpers.dispatcher import async_dispatcher_send
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    CONF_CAMERA_NAME,
    CONF_CONVERSATION_AGENT,
    CONF_FRIGATE_PASSWORD,
    CONF_FRIGATE_URL,
    CONF_FRIGATE_USERNAME,
    CONF_PORT,
    CONF_TTS_ENGINE,
    CONF_TTS_VOICE,
    DEFAULT_CAMERA_NAME,
    DEFAULT_CONVERSATION_AGENT,
    DEFAULT_FRIGATE_URL,
    DEFAULT_PORT,
    DEFAULT_TTS_ENGINE,
    DEFAULT_TTS_VOICE,
    DOMAIN,
)
from .frigate_client import FrigateClient
from .server import BirdFeederPortalServer

_LOGGER = logging.getLogger(__name__)
PLATFORMS = [Platform.SENSOR]


class BirdFeederRedirectView(HomeAssistantView):
    """View to redirect sidebar iframe to the dedicated portal port."""

    url = "/api/birdfeeder_portal/redirect"
    name = "api:birdfeeder_portal:redirect"
    requires_auth = False

    def __init__(self, port: int) -> None:
        self.port = port

    async def get(self, request: web.Request) -> web.Response:
        host_header = request.headers.get("X-Forwarded-Host") or request.headers.get("Host") or "localhost"
        host_name = host_header.split(":")[0]

        if host_name.endswith("bcardi.org"):
            primary_url = "https://bf.bcardi.org/?ha=1"
            secondary_url = f"http://{host_name}:{self.port}/?ha=1"
            secondary_label = f"Or open via local network ({secondary_url}) →"
        else:
            primary_url = f"http://{host_name}:{self.port}/?ha=1"
            secondary_url = "https://bf.bcardi.org/?ha=1"
            secondary_label = "Or open via External Domain (bf.bcardi.org) →"

        html = f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Bird Feeder Portal</title>
  <style>
    body {{
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
      background: #0d1117;
      color: #c9d1d9;
      display: flex;
      justify-content: center;
      align-items: center;
      min-height: 80vh;
      margin: 0;
      padding: 1.5rem;
    }}
    .card {{
      max-width: 480px;
      width: 100%;
      background: #161b22;
      border: 1px solid #30363d;
      border-radius: 12px;
      padding: 2rem 1.5rem;
      text-align: center;
      box-shadow: 0 8px 24px rgba(0,0,0,0.4);
    }}
    h2 {{ color: #ffffff; margin-top: 0; font-size: 1.4rem; }}
    p {{ color: #8b949e; line-height: 1.5; font-size: 0.95rem; margin: 0.8rem 0; }}
    .btn {{
      display: inline-block;
      background: #238636;
      color: white !important;
      padding: 0.85rem 1.75rem;
      border-radius: 8px;
      margin-top: 1rem;
      margin-bottom: 0.75rem;
      text-decoration: none;
      font-weight: 600;
      font-size: 1.05rem;
      transition: background 0.2s;
    }}
    .btn:hover {{ background: #2ea043; }}
    .url-display {{
      margin-top: 0.75rem;
      font-family: monospace;
      font-size: 0.85rem;
      word-break: break-all;
    }}
    .url-display a {{ color: #58a6ff; text-decoration: none; }}
    .url-display a:hover {{ text-decoration: underline; }}
    .external-link {{
      display: block;
      margin-top: 1.5rem;
      color: #58a6ff;
      font-size: 0.9rem;
      text-decoration: none;
    }}
    .external-link:hover {{ text-decoration: underline; }}
  </style>
</head>
<body>
  <div class="card">
    <h2>🐦 Bird Feeder Portal</h2>
    <p>Connecting to Bird Feeder Portal...</p>
    <a id="open-link" class="btn" target="_blank" rel="noopener noreferrer" href="{primary_url}">Open Portal in New Tab</a>
    <div class="url-display"><a id="url-text" href="{primary_url}" target="_blank" rel="noopener noreferrer">{primary_url}</a></div>
    <a class="external-link" id="alt-link" href="{secondary_url}" target="_blank" rel="noopener noreferrer">{secondary_label}</a>
  </div>
  <script>
    const port = {self.port};
    const hostname = window.location.hostname || "{host_name}";
    let targetUrl;
    if (hostname.endsWith("bcardi.org")) {{
      targetUrl = "https://bf.bcardi.org/?ha=1";
    }} else {{
      targetUrl = "http://" + hostname + ":" + port + "/?ha=1";
    }}
    const link = document.getElementById("open-link");
    const urlText = document.getElementById("url-text");
    if (link) link.href = targetUrl;
    if (urlText) {{
      urlText.href = targetUrl;
      urlText.textContent = targetUrl;
    }}
    // Automatically redirect inside the iframe if possible
    try {{
      window.location.replace(targetUrl);
    }} catch (e) {{}}
  </script>
</body>
</html>"""
        return web.Response(text=html, content_type="text/html", charset="utf-8")


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Set up the Bird Feeder Portal component."""
    hass.data.setdefault(DOMAIN, {})
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Bird Feeder Portal from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    config = {**entry.data, **entry.options}
    frigate_url = config.get(CONF_FRIGATE_URL, DEFAULT_FRIGATE_URL)
    camera_name = config.get(CONF_CAMERA_NAME, DEFAULT_CAMERA_NAME)
    frigate_username = config.get(CONF_FRIGATE_USERNAME)
    frigate_password = config.get(CONF_FRIGATE_PASSWORD)
    port = config.get(CONF_PORT, DEFAULT_PORT)
    conversation_agent = config.get(CONF_CONVERSATION_AGENT, DEFAULT_CONVERSATION_AGENT)
    tts_engine = config.get(CONF_TTS_ENGINE, DEFAULT_TTS_ENGINE)
    tts_voice = config.get(CONF_TTS_VOICE, DEFAULT_TTS_VOICE)

    # 1. Initialize Frigate Client
    frigate_client = FrigateClient(
        hass=hass,
        frigate_url=frigate_url,
        camera_name=camera_name,
        username=frigate_username,
        password=frigate_password,
    )

    # 2. Coordinator for periodic status polling (sensors)
    async def async_update_data():
        try:
            return await frigate_client.get_feeder_summary()
        except Exception as err:
            raise UpdateFailed(f"Error fetching feeder summary: {err}") from err

    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name="Bird Feeder Portal Coordinator",
        update_method=async_update_data,
        update_interval=timedelta(seconds=60),
    )
    await coordinator.async_config_entry_first_refresh()

    # 3. Initialize & Start dedicated aiohttp Web Server
    server = BirdFeederPortalServer(
        hass=hass,
        host="0.0.0.0",
        port=port,
        frigate_client=frigate_client,
        conversation_agent=conversation_agent,
        tts_engine=tts_engine,
        tts_voice=tts_voice,
    )

    try:
        await server.async_start()
    except Exception as err:
        _LOGGER.error("Failed to start Bird Feeder Portal server on port %s: %s", port, err)
        return False

    # Dispatcher callback to update sensors immediately on portal events
    def notify_stats_updated():
        async_dispatcher_send(hass, f"{DOMAIN}_stats_updated")

    hass.data[DOMAIN]["sensor_update_cb"] = notify_stats_updated
    hass.data[DOMAIN][entry.entry_id] = {
        "server": server,
        "coordinator": coordinator,
        "frigate_client": frigate_client,
    }

    # 4. Set up platform entities (sensors)
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # 5. Register HTTP redirect view & sidebar panel
    try:
        view = hass.data[DOMAIN].get("redirect_view")
        if not view:
            view = BirdFeederRedirectView(port)
            hass.http.register_view(view)
            hass.data[DOMAIN]["redirect_view"] = view
        else:
            view.port = port

        from homeassistant.components.frontend import async_register_built_in_panel
        async_register_built_in_panel(
            hass,
            component_name="iframe",
            sidebar_title="Bird Feeder",
            sidebar_icon="mdi:bird",
            frontend_url_path="birdfeeder_portal",
            config={"url": "/api/birdfeeder_portal/redirect"},
            require_admin=False,
        )
    except Exception as err:
        _LOGGER.debug("Note: Could not register sidebar iframe panel: %s", err)

    entry.async_on_unload(entry.add_update_listener(async_reload_entry))
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    data = hass.data[DOMAIN].get(entry.entry_id)
    if data:
        server: BirdFeederPortalServer = data.get("server")
        if server:
            await server.async_stop()

    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)

    try:
        from homeassistant.components.frontend import async_remove_panel
        async_remove_panel(hass, "birdfeeder_portal")
    except Exception:
        pass

    return unload_ok


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload config entry after options change."""
    await async_unload_entry(hass, entry)
    await async_setup_entry(hass, entry)
