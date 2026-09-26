"""Dedicated aiohttp web server for the Bird Feeder Voice Portal."""

import json
import logging
import os
import time
import urllib.parse
from typing import Any, Dict, Optional
from aiohttp import web
import aiohttp

from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.storage import Store
from homeassistant.util import dt as dt_util

from .const import (
    DOMAIN,
    STORAGE_KEY,
    STORAGE_VERSION,
)
from .frigate_client import FrigateClient

_LOGGER = logging.getLogger(__name__)


class BirdFeederPortalServer:
    """Manages the standalone HTTP server on the dedicated port."""

    def __init__(
        self,
        hass: HomeAssistant,
        host: str,
        port: int,
        frigate_client: FrigateClient,
        conversation_agent: str,
        tts_engine: str,
        tts_voice: str,
    ) -> None:
        self.hass = hass
        self.host = host
        self.port = port
        self.frigate_client = frigate_client
        self.conversation_agent = conversation_agent
        self.tts_engine = tts_engine
        self.tts_voice = tts_voice

        self._store = Store(hass, STORAGE_VERSION, STORAGE_KEY)
        self.stats: Dict[str, Any] = {
            "total_page_views": 0,
            "total_questions_asked": 0,
            "today_views": 0,
            "today_questions": 0,
            "yesterday_views": 0,
            "yesterday_questions": 0,
            "referrers": {},
            "today_referrers": {},
            "history": {},
            "last_date": "",
        }

        self.app = web.Application()
        self.runner: Optional[web.AppRunner] = None
        self.site: Optional[web.TCPSite] = None
        self._frontend_dir = os.path.join(os.path.dirname(__file__), "frontend")
        self._setup_routes()

    def _setup_routes(self) -> None:
        """Register routes on the dedicated web application."""
        self.app.router.add_get("/", self.handle_index)
        self.app.router.add_get("/index.html", self.handle_index)
        self.app.router.add_get("/feeder_preview.jpg", self.handle_preview_image)
        self.app.router.add_get("/api/stats", self.handle_stats)
        self.app.router.add_get("/api/status", self.handle_status)
        self.app.router.add_get("/api/snapshot", self.handle_snapshot)
        self.app.router.add_get("/api/audio", self.handle_audio)
        self.app.router.add_post("/api/ask", self.handle_ask)

    async def async_load_stats(self) -> None:
        """Load persisted visitor statistics."""
        data = await self._store.async_load()
        if data and isinstance(data, dict):
            self.stats.update(data)
        self._check_date_rollover()

    def _check_date_rollover(self) -> bool:
        """Roll over daily metrics when the calendar date changes."""
        now = dt_util.now()
        today_str = now.strftime("%Y-%m-%d")
        if self.stats.get("last_date") != today_str:
            old_date = self.stats.get("last_date")
            if old_date:
                if "history" not in self.stats:
                    self.stats["history"] = {}
                self.stats["history"][old_date] = {
                    "views": self.stats.get("today_views", 0),
                    "questions": self.stats.get("today_questions", 0),
                }
                self.stats["yesterday_views"] = self.stats.get("today_views", 0)
                self.stats["yesterday_questions"] = self.stats.get("today_questions", 0)
            self.stats["last_date"] = today_str
            self.stats["today_views"] = 0
            self.stats["today_questions"] = 0
            self.stats["today_referrers"] = {}
            return True
        return False

    @staticmethod
    def _clean_referrer(referer: Optional[str]) -> str:
        """Extract a clean source name from an HTTP Referer header."""
        if not referer:
            return "Direct / None"
        try:
            parsed = urllib.parse.urlparse(referer)
            host = parsed.netloc.lower()
            if not host:
                return "Direct / None"
            if ":" in host:
                host = host.split(":")[0]
            if "reddit.com" in host or "redd.it" in host:
                return "reddit.com"
            if "home-assistant.io" in host:
                return "community.home-assistant.io"
            if "discord" in host:
                return "discord.com"
            if "github.com" in host:
                return "github.com"
            if "google." in host:
                return "google.com"
            if "facebook.com" in host or "fb.com" in host:
                return "facebook.com"
            if "t.co" in host or "twitter.com" in host or "x.com" in host:
                return "x.com"
            if host in ("bf.bcardi.org", "birdfeeder.bcardi.org", "127.0.0.1", "localhost"):
                return "Direct / Refresh"
            return host
        except Exception:
            return "Direct / None"

    async def _record_stat(self, metric: str, request: Optional[web.Request] = None) -> None:
        """Increment view or question counters and save."""
        self._check_date_rollover()
        if metric == "view":
            self.stats["total_page_views"] = self.stats.get("total_page_views", 0) + 1
            self.stats["today_views"] = self.stats.get("today_views", 0) + 1

            if request is not None:
                referer = request.headers.get("Referer")
                source = self._clean_referrer(referer)
                if "referrers" not in self.stats or not isinstance(self.stats["referrers"], dict):
                    self.stats["referrers"] = {}
                if "today_referrers" not in self.stats or not isinstance(self.stats["today_referrers"], dict):
                    self.stats["today_referrers"] = {}
                self.stats["referrers"][source] = self.stats["referrers"].get(source, 0) + 1
                self.stats["today_referrers"][source] = self.stats["today_referrers"].get(source, 0) + 1

        elif metric == "question":
            self.stats["total_questions_asked"] = self.stats.get("total_questions_asked", 0) + 1
            self.stats["today_questions"] = self.stats.get("today_questions", 0) + 1

        await self._store.async_save(self.stats)

        # Notify sensor update listeners if registered
        dispatcher = self.hass.data.get(DOMAIN, {}).get("sensor_update_cb")
        if dispatcher and callable(dispatcher):
            dispatcher()

    async def handle_index(self, request: web.Request) -> web.Response:
        """Serve the portal single-page application."""
        await self._record_stat("view", request=request)
        index_path = os.path.join(self._frontend_dir, "index.html")
        if os.path.exists(index_path):
            with open(index_path, "r", encoding="utf-8") as f:
                content = f.read()
            return web.Response(text=content, content_type="text/html", charset="utf-8")
        return web.Response(text="Bird Feeder Portal Frontend not found.", status=404)

    async def handle_preview_image(self, request: web.Request) -> web.Response:
        """Serve the preview/og image."""
        img_path = os.path.join(self._frontend_dir, "feeder_preview.jpg")
        if os.path.exists(img_path):
            with open(img_path, "rb") as f:
                img_bytes = f.read()
            return web.Response(
                body=img_bytes,
                content_type="image/jpeg",
                headers={"Cache-Control": "public, max-age=86400"},
            )
        return web.Response(status=404, text="Preview image not found")

    async def handle_stats(self, request: web.Request) -> web.Response:
        """Return visitor and question metrics."""
        self._check_date_rollover()
        return web.json_response(self.stats)

    async def handle_status(self, request: web.Request) -> web.Response:
        """Return real-time feeder visit summary."""
        summary = await self.frigate_client.get_feeder_summary()
        return web.json_response(summary)

    async def handle_snapshot(self, request: web.Request) -> web.Response:
        """Proxy snapshot image from Frigate LXC."""
        event_id = request.query.get("id")
        if not event_id:
            return web.Response(status=400, text="Missing event id query parameter")

        img_bytes = await self.frigate_client.get_snapshot(event_id)
        if img_bytes:
            return web.Response(
                body=img_bytes,
                content_type="image/jpeg",
                headers={"Cache-Control": "public, max-age=3600"},
            )
        return web.Response(status=404, text="Snapshot not found")

    async def handle_audio(self, request: web.Request) -> web.Response:
        """Proxy or stream TTS audio file."""
        audio_path = request.query.get("path")
        if not audio_path:
            return web.Response(status=400, text="Missing path parameter")

        session = async_get_clientsession(self.hass)
        ha_port = self.hass.config.http.server_port if hasattr(self.hass.config, "http") else 8123

        if audio_path.startswith("http://") or audio_path.startswith("https://"):
            full_url = audio_path
        elif audio_path.startswith("/"):
            full_url = f"http://127.0.0.1:{ha_port}{audio_path}"
        else:
            full_url = f"http://127.0.0.1:{ha_port}/{audio_path}"

        try:
            async with session.get(full_url, timeout=aiohttp.ClientTimeout(total=12)) as resp:
                if resp.status == 200:
                    content = await resp.read()
                    content_type = resp.headers.get("Content-Type", "audio/mpeg")
                    return web.Response(body=content, content_type=content_type)
                return web.Response(status=resp.status, text=f"Upstream audio returned status {resp.status}")
        except Exception as err:
            _LOGGER.error("Error fetching audio from %s: %s", full_url, err)
            return web.Response(status=500, text=f"Error fetching audio: {err}")

    async def handle_ask(self, request: web.Request) -> web.Response:
        """Handle voice assistant question, invoke Gemini & TTS."""
        await self._record_stat("question")
        try:
            payload = await request.json()
        except Exception:
            payload = {}

        prompt_text = payload.get("prompt", "Who was the last bird at the feeder?")
        conversation_id = payload.get("conversation_id")

        # 1. Fetch live feeder summary
        summary = await self.frigate_client.get_feeder_summary()
        counts_str = ", ".join([f"{count} {sp}" for sp, count in summary["species_counts"].items()]) or "No visits recorded yet today"
        last_str = "None yet"
        if summary.get("last_visit"):
            lv = summary["last_visit"]
            ago_text = f"{lv['mins_ago']} minutes ago" if lv["mins_ago"] > 0 else "just seconds ago"
            last_str = f"{lv['species']} ({ago_text} at {lv['time_str']})"
            if lv.get("description"):
                last_str += f". Details: {lv['description']}"

        grounded_prompt = (
            f"You are the friendly Voice Assistant for Jerry's bird feeder in Fruitland Park, Central Florida. "
            f"Answer clearly, naturally, and concisely in 2 to 3 sentences suitable for spoken voice output.\n"
            f"Current Feeder Status:\n"
            f"- Last visitor: {last_str}\n"
            f"- Today's recorded visits: {summary['total_visits_today']} total ({counts_str})\n\n"
            f"User question: {prompt_text}"
        )

        # 2. Invoke Home Assistant conversation agent (Gemini)
        speech_text = ""
        new_conv_id = None
        try:
            # Modern HA conversation API
            from homeassistant.components import conversation
            conv_response = await conversation.async_converse(
                hass=self.hass,
                text=grounded_prompt,
                conversation_id=conversation_id,
                agent_id=self.conversation_agent,
            )
            response_dict = conv_response.as_dict()
            speech_text = (
                response_dict.get("response", {})
                .get("speech", {})
                .get("plain", {})
                .get("speech", "")
            )
            new_conv_id = response_dict.get("conversation_id")
        except Exception as err:
            _LOGGER.warning("Direct conversation.async_converse call failed, trying service call: %s", err)
            try:
                svc_res = await self.hass.services.async_call(
                    "conversation",
                    "process",
                    {
                        "text": grounded_prompt,
                        "agent_id": self.conversation_agent,
                        "conversation_id": conversation_id,
                    },
                    blocking=True,
                    return_response=True,
                )
                if svc_res and isinstance(svc_res, dict):
                    speech_text = (
                        svc_res.get("response", {})
                        .get("speech", {})
                        .get("plain", {})
                        .get("speech", "")
                    )
                    new_conv_id = svc_res.get("conversation_id")
            except Exception as svc_err:
                _LOGGER.error("Failed to process conversation: %s", svc_err)

        if not speech_text:
            if "last" in prompt_text.lower():
                speech_text = f"The last visitor at the feeder was a {last_str}."
            elif "today" in prompt_text.lower():
                speech_text = f"We have had {summary['total_visits_today']} visits today, including {counts_str}."
            else:
                speech_text = f"The feeder is active in Fruitland Park with {summary['total_visits_today']} visits recorded today."

        # 3. Generate Cloud TTS Audio using modern HA media_source API
        audio_proxy_url = ""
        try:
            from homeassistant.components.media_source import async_resolve_media
            from homeassistant.components.tts.media_source import generate_media_source_id

            media_id = generate_media_source_id(
                self.hass,
                speech_text,
                engine=self.tts_engine,
                language="en-US",
                options={"voice": self.tts_voice} if self.tts_voice else None,
            )
            item = await async_resolve_media(self.hass, media_id, None)
            if item and item.url:
                audio_proxy_url = item.url
        except Exception as err:
            _LOGGER.debug("Modern media_source TTS resolution failed, trying fallback: %s", err)

        if not audio_proxy_url:
            try:
                tts_manager = self.hass.data.get("tts")
                if tts_manager and hasattr(tts_manager, "async_get_url"):
                    audio_proxy_url = await tts_manager.async_get_url(
                        self.tts_engine,
                        speech_text,
                        language="en-US",
                        options={"voice": self.tts_voice},
                    )
            except Exception as err:
                _LOGGER.debug("Direct TTS manager call exception: %s", err)

        # Fallback to internal HTTP request to HA /api/tts_get_url
        if not audio_proxy_url:
            try:
                ha_port = self.hass.config.http.server_port if hasattr(self.hass.config, "http") else 8123
                session = async_get_clientsession(self.hass)
                tts_payload = {
                    "engine_id": self.tts_engine,
                    "message": speech_text,
                    "language": "en-US",
                    "options": {"voice": self.tts_voice},
                }
                async with session.post(
                    f"http://127.0.0.1:{ha_port}/api/tts_get_url",
                    json=tts_payload,
                    timeout=aiohttp.ClientTimeout(total=8),
                ) as resp:
                    if resp.status == 200:
                        tts_data = await resp.json()
                        audio_proxy_url = tts_data.get("path") or tts_data.get("url", "")
            except Exception as err:
                _LOGGER.error("Fallback TTS HTTP request failed: %s", err)

        return web.json_response({
            "text": speech_text,
            "audio_path": audio_proxy_url,
            "conversation_id": new_conv_id,
            "summary": summary,
        })

    async def async_start(self) -> None:
        """Start the aiohttp web server."""
        await self.async_load_stats()
        self.runner = web.AppRunner(self.app)
        await self.runner.setup()
        self.site = web.TCPSite(self.runner, self.host, self.port)
        await self.site.start()
        _LOGGER.info("Bird Feeder Portal web server started on http://%s:%s", self.host, self.port)

    async def async_stop(self) -> None:
        """Stop the aiohttp web server."""
        if self.site:
            await self.site.stop()
            self.site = None
        if self.runner:
            await self.runner.cleanup()
            self.runner = None
        _LOGGER.info("Bird Feeder Portal web server stopped")
