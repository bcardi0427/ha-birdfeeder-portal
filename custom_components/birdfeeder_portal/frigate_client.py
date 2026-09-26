"""Frigate REST API Client for Bird Feeder Portal."""

import logging
import time
from typing import Any, Dict, List, Optional
import aiohttp
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.util import dt as dt_util

_LOGGER = logging.getLogger(__name__)


class FrigateClient:
    """Async client to communicate with the external Frigate NVR REST API."""

    def __init__(self, hass: HomeAssistant, frigate_url: str, camera_name: str) -> None:
        self.hass = hass
        self.frigate_url = frigate_url.rstrip("/")
        self.camera_name = camera_name

    @property
    def session(self) -> aiohttp.ClientSession:
        return async_get_clientsession(self.hass)

    async def get_feeder_summary(self) -> Dict[str, Any]:
        """Fetch today's events and recent visits from Frigate REST API."""
        now = dt_util.now()
        start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)
        start_ts = int(start_of_day.timestamp())

        recent_birds: List[Dict[str, Any]] = []
        species_counts: Dict[str, int] = {}
        last_visit: Optional[Dict[str, Any]] = None

        url = f"{self.frigate_url}/api/events"
        params = {
            "camera": self.camera_name,
            "after": str(start_ts),
            "limit": "100",
        }

        events = []
        try:
            async with self.session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=6)) as resp:
                if resp.status == 200:
                    events = await resp.json()
                else:
                    _LOGGER.warning("Frigate API returned status %s: %s", resp.status, await resp.text())
        except Exception as err:
            _LOGGER.error("Failed to query Frigate events for today: %s", err)

        # If no events today yet, fetch the last 10 historical events
        if not events:
            try:
                fallback_params = {
                    "camera": self.camera_name,
                    "limit": "10",
                }
                async with self.session.get(url, params=fallback_params, timeout=aiohttp.ClientTimeout(total=6)) as resp:
                    if resp.status == 200:
                        events = await resp.json()
            except Exception as err:
                _LOGGER.error("Failed to query fallback Frigate events: %s", err)

        now_ts = time.time()
        for ev in events:
            eid = ev.get("id")
            sub_label = ev.get("sub_label")
            st = ev.get("start_time", 0)
            data = ev.get("data", {})
            desc = data.get("description", "") if isinstance(data, dict) else ""

            species_name = sub_label if sub_label else "Wild Bird"
            species_counts[species_name] = species_counts.get(species_name, 0) + 1

            visit_dt = dt_util.as_local(dt_util.utc_from_timestamp(st))
            mins_ago = max(0, int((now_ts - st) / 60))

            item = {
                "id": eid,
                "species": species_name,
                "time_str": visit_dt.strftime("%I:%M %p"),
                "mins_ago": mins_ago,
                "timestamp": st,
                "description": desc[:300] if desc else "",
            }
            recent_birds.append(item)

        if recent_birds:
            last_visit = recent_birds[0]

        return {
            "recent_birds": recent_birds[:8],
            "species_counts": species_counts,
            "total_visits_today": len(recent_birds),
            "last_visit": last_visit,
        }

    async def get_snapshot(self, event_id: str) -> Optional[bytes]:
        """Fetch snapshot image bytes for an event."""
        url = f"{self.frigate_url}/api/events/{event_id}/snapshot.jpg"
        try:
            async with self.session.get(url, timeout=aiohttp.ClientTimeout(total=8)) as resp:
                if resp.status == 200:
                    return await resp.read()
                _LOGGER.warning("Frigate snapshot error status %s for event %s", resp.status, event_id)
        except Exception as err:
            _LOGGER.error("Error fetching snapshot for event %s: %s", event_id, err)
        return None
