"""Sensor platform for Bird Feeder Voice Portal."""

from typing import Any, Dict, List, Optional
from homeassistant.components.sensor import (
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
)

from .const import DOMAIN
from .server import BirdFeederPortalServer


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Bird Feeder Portal sensors based on a config entry."""
    data = hass.data[DOMAIN][entry.entry_id]
    server: BirdFeederPortalServer = data["server"]
    coordinator: DataUpdateCoordinator = data["coordinator"]

    entities: List[SensorEntity] = [
        BirdFeederTodayViewsSensor(server, entry),
        BirdFeederTodayQuestionsSensor(server, entry),
        BirdFeederTotalViewsSensor(server, entry),
        BirdFeederTotalQuestionsSensor(server, entry),
        BirdFeederLastVisitorSensor(coordinator, entry),
        BirdFeederVisitsTodaySensor(coordinator, entry),
    ]

    async_add_entities(entities)


class BirdFeederBaseSensor(SensorEntity):
    """Base class for Bird Feeder statistics sensors."""

    def __init__(self, server: BirdFeederPortalServer, entry: ConfigEntry) -> None:
        self._server = server
        self._entry = entry

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(
            identifiers={(DOMAIN, self._entry.entry_id)},
            name="Bird Feeder Voice Portal",
            manufacturer="Jerry's Feeder",
            model="Voice Portal",
            sw_version="1.0.0",
        )

    async def async_added_to_hass(self) -> None:
        """Register update callback."""
        self.async_on_remove(
            self.hass.helpers.dispatcher.async_dispatcher_connect(
                f"{DOMAIN}_stats_updated", self._handle_stats_update
            )
        )

    @callback
    def _handle_stats_update(self) -> None:
        """Handle updated stats."""
        self.async_write_ha_state()


class BirdFeederTodayViewsSensor(BirdFeederBaseSensor):
    """Sensor for today's web portal page views."""

    _attr_has_entity_name = True
    _attr_translation_key = "today_views"
    _attr_icon = "mdi:eye"
    _attr_state_class = SensorStateClass.TOTAL_INCREASING

    def __init__(self, server: BirdFeederPortalServer, entry: ConfigEntry) -> None:
        super().__init__(server, entry)
        self._attr_unique_id = f"{entry.entry_id}_today_views"
        self._attr_name = "Today Views"

    @property
    def native_value(self) -> int:
        return self._server.stats.get("today_views", 0)


class BirdFeederTodayQuestionsSensor(BirdFeederBaseSensor):
    """Sensor for today's voice questions asked."""

    _attr_has_entity_name = True
    _attr_translation_key = "today_questions"
    _attr_icon = "mdi:comment-question-outline"
    _attr_state_class = SensorStateClass.TOTAL_INCREASING

    def __init__(self, server: BirdFeederPortalServer, entry: ConfigEntry) -> None:
        super().__init__(server, entry)
        self._attr_unique_id = f"{entry.entry_id}_today_questions"
        self._attr_name = "Today Questions"

    @property
    def native_value(self) -> int:
        return self._server.stats.get("today_questions", 0)


class BirdFeederTotalViewsSensor(BirdFeederBaseSensor):
    """Sensor for all-time page views."""

    _attr_has_entity_name = True
    _attr_translation_key = "total_views"
    _attr_icon = "mdi:chart-timeline-variant"
    _attr_state_class = SensorStateClass.TOTAL_INCREASING

    def __init__(self, server: BirdFeederPortalServer, entry: ConfigEntry) -> None:
        super().__init__(server, entry)
        self._attr_unique_id = f"{entry.entry_id}_total_views"
        self._attr_name = "Total Views"

    @property
    def native_value(self) -> int:
        return self._server.stats.get("total_page_views", 0)


class BirdFeederTotalQuestionsSensor(BirdFeederBaseSensor):
    """Sensor for all-time questions asked."""

    _attr_has_entity_name = True
    _attr_translation_key = "total_questions"
    _attr_icon = "mdi:forum"
    _attr_state_class = SensorStateClass.TOTAL_INCREASING

    def __init__(self, server: BirdFeederPortalServer, entry: ConfigEntry) -> None:
        super().__init__(server, entry)
        self._attr_unique_id = f"{entry.entry_id}_total_questions"
        self._attr_name = "Total Questions"

    @property
    def native_value(self) -> int:
        return self._server.stats.get("total_questions_asked", 0)


class BirdFeederLastVisitorSensor(CoordinatorEntity, SensorEntity):
    """Sensor representing the last bird visitor species."""

    _attr_has_entity_name = True
    _attr_translation_key = "last_visitor"
    _attr_icon = "mdi:bird"

    def __init__(self, coordinator: DataUpdateCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_last_visitor"
        self._attr_name = "Last Visitor Species"

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(
            identifiers={(DOMAIN, self._entry.entry_id)},
            name="Bird Feeder Voice Portal",
            manufacturer="Jerry's Feeder",
            model="Voice Portal",
            sw_version="1.0.0",
        )

    @property
    def native_value(self) -> Optional[str]:
        if self.coordinator.data and self.coordinator.data.get("last_visit"):
            return self.coordinator.data["last_visit"].get("species")
        return "None"

    @property
    def extra_state_attributes(self) -> Dict[str, Any]:
        if self.coordinator.data and self.coordinator.data.get("last_visit"):
            lv = self.coordinator.data["last_visit"]
            return {
                "time": lv.get("time_str"),
                "mins_ago": lv.get("mins_ago"),
                "event_id": lv.get("id"),
                "description": lv.get("description"),
            }
        return {}


class BirdFeederVisitsTodaySensor(CoordinatorEntity, SensorEntity):
    """Sensor representing the total number of bird visits today."""

    _attr_has_entity_name = True
    _attr_translation_key = "visits_today"
    _attr_icon = "mdi:counter"
    _attr_state_class = SensorStateClass.TOTAL

    def __init__(self, coordinator: DataUpdateCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_visits_today"
        self._attr_name = "Bird Visits Today"

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(
            identifiers={(DOMAIN, self._entry.entry_id)},
            name="Bird Feeder Voice Portal",
            manufacturer="Jerry's Feeder",
            model="Voice Portal",
            sw_version="1.0.0",
        )

    @property
    def native_value(self) -> int:
        if self.coordinator.data:
            return self.coordinator.data.get("total_visits_today", 0)
        return 0

    @property
    def extra_state_attributes(self) -> Dict[str, Any]:
        if self.coordinator.data:
            return {
                "species_counts": self.coordinator.data.get("species_counts", {})
            }
        return {}
