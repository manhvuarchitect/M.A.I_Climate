"""Coordinator cho thiết bị Quạt thông gió."""
import logging
from datetime import datetime, timedelta
from typing import Any

from homeassistant.core import HomeAssistant, callback
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.helpers.event import async_track_state_change_event
from homeassistant.util.dt import utcnow

from .const import (
    DOMAIN,
    CONF_VENT_ENTITY,
    CONF_BATHROOM_SENSOR,
    CONF_VENT_HUMIDITY_SENSOR,
    CONF_ODOR_CONTROL_ENABLED,
    CONF_VENT_AUTO_DRY_ENABLED,
    CONF_ROUTINE_AIR_SYNC_ENABLED,
    DEFAULT_SCAN_INTERVAL,
)

_LOGGER = logging.getLogger(__name__)

class SmartVentCoordinator(DataUpdateCoordinator):
    """Lớp quản lý trạng thái trung tâm cho Quạt thông gió."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Khởi tạo."""
        config = {**entry.data, **entry.options}
        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_vent_{entry.entry_id}",
            update_interval=timedelta(seconds=DEFAULT_SCAN_INTERVAL),
        )
        self.entry = entry
        self.hass = hass
        self._unsub_listeners: list = []

        self.vent_entity = config.get(CONF_VENT_ENTITY)
        self.bathroom_sensor = config.get(CONF_BATHROOM_SENSOR)
        self.vent_humidity_sensor = config.get(CONF_VENT_HUMIDITY_SENSOR)

        self.odor_control_enabled = config.get(CONF_ODOR_CONTROL_ENABLED, True)
        self.vent_auto_dry_enabled = config.get(CONF_VENT_AUTO_DRY_ENABLED, True)
        self.routine_air_sync_enabled = config.get(CONF_ROUTINE_AIR_SYNC_ENABLED, False)

        self._presence_off_since: datetime | None = None

    def update_options(self, options: dict[str, Any]) -> None:
        """Cập nhật tùy chọn."""
        self.vent_entity = options.get(CONF_VENT_ENTITY, self.vent_entity)
        self.bathroom_sensor = options.get(CONF_BATHROOM_SENSOR, self.bathroom_sensor)
        self.vent_humidity_sensor = options.get(CONF_VENT_HUMIDITY_SENSOR, self.vent_humidity_sensor)

        self.odor_control_enabled = options.get(CONF_ODOR_CONTROL_ENABLED, self.odor_control_enabled)
        self.vent_auto_dry_enabled = options.get(CONF_VENT_AUTO_DRY_ENABLED, self.vent_auto_dry_enabled)
        self.routine_air_sync_enabled = options.get(CONF_ROUTINE_AIR_SYNC_ENABLED, self.routine_air_sync_enabled)

    async def _async_update_data(self) -> dict[str, Any]:
        """Cập nhật dữ liệu định kỳ."""
        if not self.vent_entity:
            return self._build_state()

        try:
            await self._apply_vent_logic()
        except Exception as e:
            _LOGGER.error("Lỗi khi cập nhật dữ liệu SmartVentCoordinator: %s", e)

        return self._build_state()

    def _build_state(self) -> dict[str, Any]:
        return {
            "odor_control_enabled": self.odor_control_enabled,
            "vent_auto_dry_enabled": self.vent_auto_dry_enabled,
            "routine_air_sync_enabled": self.routine_air_sync_enabled,
        }

    async def _apply_vent_logic(self) -> None:
        """Thực thi logic cho quạt thông gió."""
        should_be_on = False

        # 1. Odor Control (Khử mùi phòng tắm)
        if self.odor_control_enabled and self.bathroom_sensor:
            p_state = self.hass.states.get(self.bathroom_sensor)
            if p_state and p_state.state == "on":
                should_be_on = True
                self._presence_off_since = None
            elif p_state and p_state.state == "off":
                if self._presence_off_since is None:
                    self._presence_off_since = utcnow()
                else:
                    elapsed = (utcnow() - self._presence_off_since).total_seconds()
                    if elapsed <= 300: # Chạy thêm 5 phút sau khi rời đi
                        should_be_on = True

        # 2. Auto Dry (Hút ẩm)
        if not should_be_on and self.vent_auto_dry_enabled and self.vent_humidity_sensor:
            h_state = self.hass.states.get(self.vent_humidity_sensor)
            if h_state and h_state.state not in ("unknown", "unavailable"):
                try:
                    humidity = float(h_state.state)
                    if humidity > 80.0:
                        should_be_on = True
                    # Nếu độ ẩm < 70, để nó tự tắt trừ khi các đk khác yêu cầu bật
                    # Hiện tại logic nếu không ai yêu cầu bật thì sẽ tắt, nên < 80 sẽ có khả năng tắt nếu đk khác không giữ
                except ValueError:
                    pass

        # 3. Routine Air Sync (Lưu thông khí định kỳ)
        if not should_be_on and self.routine_air_sync_enabled:
            # Chạy 10 phút đầu mỗi giờ
            current_minute = datetime.now().minute
            if 0 <= current_minute < 10:
                should_be_on = True

        # Thực thi lệnh
        vent_state = self.hass.states.get(self.vent_entity)
        is_on = vent_state is not None and vent_state.state != "off"

        if should_be_on and not is_on:
            _LOGGER.info("Bật quạt thông gió %s", self.vent_entity)
            await self.hass.services.async_call("fan", "turn_on", {"entity_id": self.vent_entity})
        elif not should_be_on and is_on:
            _LOGGER.info("Tắt quạt thông gió %s", self.vent_entity)
            await self.hass.services.async_call("fan", "turn_off", {"entity_id": self.vent_entity})

    async def async_setup(self) -> None:
        """Thiết lập listeners."""
        @callback
        def _sensor_changed(event):
            self.hass.async_create_task(self.async_refresh())

        entities_to_watch = []
        if self.bathroom_sensor: entities_to_watch.append(self.bathroom_sensor)
        if self.vent_humidity_sensor: entities_to_watch.append(self.vent_humidity_sensor)

        if entities_to_watch:
            self._unsub_listeners.append(
                async_track_state_change_event(self.hass, entities_to_watch, _sensor_changed)
            )

    async def async_unload(self) -> None:
        """Hủy bỏ."""
        for unsub in self._unsub_listeners:
            unsub()
        self._unsub_listeners.clear()

    # --- Phương thức cho Switch Entities ---
    async def async_set_odor_control_enabled(self, enabled: bool) -> None:
        self.odor_control_enabled = enabled
        self.hass.config_entries.async_update_entry(self.entry, options={**self.entry.options, CONF_ODOR_CONTROL_ENABLED: enabled})
        await self.async_refresh()

    async def async_set_vent_auto_dry_enabled(self, enabled: bool) -> None:
        self.vent_auto_dry_enabled = enabled
        self.hass.config_entries.async_update_entry(self.entry, options={**self.entry.options, CONF_VENT_AUTO_DRY_ENABLED: enabled})
        await self.async_refresh()

    async def async_set_routine_air_sync_enabled(self, enabled: bool) -> None:
        self.routine_air_sync_enabled = enabled
        self.hass.config_entries.async_update_entry(self.entry, options={**self.entry.options, CONF_ROUTINE_AIR_SYNC_ENABLED: enabled})
        await self.async_refresh()
