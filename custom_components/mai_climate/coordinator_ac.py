"""Coordinator cho thiết bị Điều hòa nhiệt độ."""
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
    CONF_AC_ENTITY,
    CONF_TEMP_SENSOR,
    CONF_HUMIDITY_SENSOR,
    CONF_PRESENCE_SENSOR,
    CONF_WINDOW_SENSOR,
    CONF_SMART_SLEEP_ENABLED,
    CONF_WINDOW_GUARD_ENABLED,
    CONF_ECO_LEAVE_ENABLED,
    CONF_AUTO_DRY_ENABLED,
    CONF_AUTO_ON_ENABLED,
    CONF_AUTO_ON_THRESHOLD,
    CONF_AUTO_OFF_ENABLED,
    CONF_AUTO_OFF_THRESHOLD,
    DEFAULT_SCAN_INTERVAL,
)

_LOGGER = logging.getLogger(__name__)

class SmartACCoordinator(DataUpdateCoordinator):
    """Lớp quản lý trạng thái trung tâm cho Điều hòa nhiệt độ."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Khởi tạo."""
        config = {**entry.data, **entry.options}
        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_ac_{entry.entry_id}",
            update_interval=timedelta(seconds=DEFAULT_SCAN_INTERVAL),
        )
        self.entry = entry
        self.hass = hass
        self._unsub_listeners: list = []

        # Thiết lập các biến cấu hình
        self.ac_entity = config.get(CONF_AC_ENTITY)
        self.temp_sensor = config.get(CONF_TEMP_SENSOR)
        self.humidity_sensor = config.get(CONF_HUMIDITY_SENSOR)
        self.presence_sensor = config.get(CONF_PRESENCE_SENSOR)
        self.window_sensor = config.get(CONF_WINDOW_SENSOR)

        self.smart_sleep_enabled = config.get(CONF_SMART_SLEEP_ENABLED, True)
        self.window_guard_enabled = config.get(CONF_WINDOW_GUARD_ENABLED, False)
        self.eco_leave_enabled = config.get(CONF_ECO_LEAVE_ENABLED, True)
        self.auto_dry_enabled = config.get(CONF_AUTO_DRY_ENABLED, False)
        self.auto_on_enabled = config.get(CONF_AUTO_ON_ENABLED, False)
        self.auto_off_enabled = config.get(CONF_AUTO_OFF_ENABLED, False)
        
        self.auto_on_threshold = config.get(CONF_AUTO_ON_THRESHOLD, 32.0)
        self.auto_off_threshold = config.get(CONF_AUTO_OFF_THRESHOLD, 25.0)

        # State theo dõi
        self._window_open_since: datetime | None = None
        self._presence_off_since: datetime | None = None
        self._sleep_mode_start_time: datetime | None = None
        self._sleep_temp_increased: int = 0
        self._last_ac_state: str | None = None

    def update_options(self, options: dict[str, Any]) -> None:
        """Cập nhật tùy chọn."""
        self.ac_entity = options.get(CONF_AC_ENTITY, self.ac_entity)
        self.temp_sensor = options.get(CONF_TEMP_SENSOR, self.temp_sensor)
        self.humidity_sensor = options.get(CONF_HUMIDITY_SENSOR, self.humidity_sensor)
        self.presence_sensor = options.get(CONF_PRESENCE_SENSOR, self.presence_sensor)
        self.window_sensor = options.get(CONF_WINDOW_SENSOR, self.window_sensor)

        self.smart_sleep_enabled = options.get(CONF_SMART_SLEEP_ENABLED, self.smart_sleep_enabled)
        self.window_guard_enabled = options.get(CONF_WINDOW_GUARD_ENABLED, self.window_guard_enabled)
        self.eco_leave_enabled = options.get(CONF_ECO_LEAVE_ENABLED, self.eco_leave_enabled)
        self.auto_dry_enabled = options.get(CONF_AUTO_DRY_ENABLED, self.auto_dry_enabled)
        self.auto_on_enabled = options.get(CONF_AUTO_ON_ENABLED, self.auto_on_enabled)
        self.auto_off_enabled = options.get(CONF_AUTO_OFF_ENABLED, self.auto_off_enabled)

    async def _async_update_data(self) -> dict[str, Any]:
        """Cập nhật dữ liệu và chạy logic."""
        if not self.ac_entity:
            return self._build_state()

        try:
            ac_state = self.hass.states.get(self.ac_entity)
            is_ac_on = ac_state is not None and ac_state.state != "off"

            # Reset sleep tracking if AC is turned off
            if not is_ac_on:
                self._sleep_mode_start_time = None
                self._sleep_temp_increased = 0

            await self._check_window_guard(is_ac_on)
            await self._check_eco_leave(is_ac_on)
            await self._check_auto_dry(is_ac_on, ac_state)
            await self._check_smart_sleep(is_ac_on, ac_state)
            await self._check_auto_on_off(is_ac_on)

        except Exception as e:
            _LOGGER.error("Lỗi khi cập nhật dữ liệu SmartACCoordinator: %s", e)

        return self._build_state()

    def _build_state(self) -> dict[str, Any]:
        return {
            "smart_sleep_enabled": self.smart_sleep_enabled,
            "window_guard_enabled": self.window_guard_enabled,
            "eco_leave_enabled": self.eco_leave_enabled,
            "auto_dry_enabled": self.auto_dry_enabled,
            "auto_on_enabled": self.auto_on_enabled,
            "auto_off_enabled": self.auto_off_enabled,
        }

    async def _check_window_guard(self, is_ac_on: bool) -> None:
        """Kiểm tra Window Guard (cửa sổ mở > 3 phút tắt ĐH)."""
        if not self.window_guard_enabled or not self.window_sensor or not is_ac_on:
            self._window_open_since = None
            return

        w_state = self.hass.states.get(self.window_sensor)
        if w_state and w_state.state == "on":  # on usually means open for window sensors
            if self._window_open_since is None:
                self._window_open_since = utcnow()
            else:
                elapsed = (utcnow() - self._window_open_since).total_seconds()
                if elapsed > 180:  # 3 minutes
                    _LOGGER.info("Window Guard: Cửa mở quá 3 phút, tự động tắt AC %s", self.ac_entity)
                    await self.hass.services.async_call("climate", "turn_off", {"entity_id": self.ac_entity})
                    self._window_open_since = None # Reset
        else:
            self._window_open_since = None

    async def _check_eco_leave(self, is_ac_on: bool) -> None:
        """Kiểm tra Eco Leave (vắng mặt > 15 phút tắt ĐH)."""
        if not self.eco_leave_enabled or not self.presence_sensor or not is_ac_on:
            self._presence_off_since = None
            return

        p_state = self.hass.states.get(self.presence_sensor)
        if p_state and p_state.state == "off":
            if self._presence_off_since is None:
                self._presence_off_since = utcnow()
            else:
                elapsed = (utcnow() - self._presence_off_since).total_seconds()
                if elapsed > 900:  # 15 minutes
                    _LOGGER.info("Eco Leave: Không có người quá 15 phút, tự động tắt AC %s", self.ac_entity)
                    await self.hass.services.async_call("climate", "turn_off", {"entity_id": self.ac_entity})
                    self._presence_off_since = None
        else:
            self._presence_off_since = None

    async def _check_auto_dry(self, is_ac_on: bool, ac_state) -> None:
        """Kiểm tra Auto Dry (độ ẩm > 80% chuyển Dry)."""
        if not self.auto_dry_enabled or not self.humidity_sensor or not is_ac_on:
            return

        h_state = self.hass.states.get(self.humidity_sensor)
        if not h_state or h_state.state in ("unknown", "unavailable"):
            return

        try:
            humidity = float(h_state.state)
        except ValueError:
            return

        current_hvac_mode = ac_state.state
        if humidity > 80.0 and current_hvac_mode != "dry":
            _LOGGER.info("Auto Dry: Độ ẩm %.1f%% > 80%%, chuyển AC %s sang chế độ Hút ẩm (Dry)", humidity, self.ac_entity)
            await self.hass.services.async_call("climate", "set_hvac_mode", {"entity_id": self.ac_entity, "hvac_mode": "dry"})
        elif humidity < 70.0 and current_hvac_mode == "dry":
            _LOGGER.info("Auto Dry: Độ ẩm %.1f%% < 70%%, trả AC %s về chế độ Cool", humidity, self.ac_entity)
            await self.hass.services.async_call("climate", "set_hvac_mode", {"entity_id": self.ac_entity, "hvac_mode": "cool"})

    async def _check_smart_sleep(self, is_ac_on: bool, ac_state) -> None:
        """Kiểm tra Smart Sleep (tăng 1 độ mỗi 2 tiếng từ 22h - 6h)."""
        if not self.smart_sleep_enabled or not is_ac_on:
            return

        now = datetime.now().time()
        start = datetime.strptime("22:00:00", "%H:%M:%S").time()
        end = datetime.strptime("06:00:00", "%H:%M:%S").time()
        
        is_sleeping_hours = False
        if start <= end:
            is_sleeping_hours = start <= now <= end
        else:
            is_sleeping_hours = start <= now or now <= end

        if not is_sleeping_hours:
            self._sleep_mode_start_time = None
            self._sleep_temp_increased = 0
            return

        if self._sleep_mode_start_time is None:
            self._sleep_mode_start_time = utcnow()
            return

        elapsed_hours = (utcnow() - self._sleep_mode_start_time).total_seconds() / 3600
        expected_increases = min(2, int(elapsed_hours / 2.0))  # Tăng tối đa 2 lần, mỗi 2 tiếng 1 lần

        if expected_increases > self._sleep_temp_increased:
            current_temp = ac_state.attributes.get("temperature")
            if current_temp:
                new_temp = current_temp + 1
                _LOGGER.info("Smart Sleep: Đã ngủ %.1f giờ, tăng nhiệt độ AC lên %.1f", elapsed_hours, new_temp)
                await self.hass.services.async_call("climate", "set_temperature", {"entity_id": self.ac_entity, "temperature": new_temp})
                self._sleep_temp_increased += 1

    async def _check_auto_on_off(self, is_ac_on: bool) -> None:
        """Tự động bật tắt theo nhiệt độ."""
        if not self.temp_sensor:
            return

        t_state = self.hass.states.get(self.temp_sensor)
        if not t_state or t_state.state in ("unknown", "unavailable"):
            return

        try:
            temp = float(t_state.state)
        except ValueError:
            return

        presence_on = True
        if self.presence_sensor:
            p_state = self.hass.states.get(self.presence_sensor)
            if p_state and p_state.state == "off":
                presence_on = False

        if self.auto_on_enabled and not is_ac_on and temp >= self.auto_on_threshold and presence_on:
            _LOGGER.info("AC Auto-on: Nhiệt độ %.1f >= %.1f, bật AC %s", temp, self.auto_on_threshold, self.ac_entity)
            await self.hass.services.async_call("climate", "turn_on", {"entity_id": self.ac_entity})
        
        if self.auto_off_enabled and is_ac_on and temp <= self.auto_off_threshold:
            _LOGGER.info("AC Auto-off: Nhiệt độ %.1f <= %.1f, tắt AC %s", temp, self.auto_off_threshold, self.ac_entity)
            await self.hass.services.async_call("climate", "turn_off", {"entity_id": self.ac_entity})

    async def async_setup(self) -> None:
        """Thiết lập listeners."""
        @callback
        def _sensor_changed(event):
            self.hass.async_create_task(self.async_refresh())

        entities_to_watch = []
        if self.temp_sensor: entities_to_watch.append(self.temp_sensor)
        if self.humidity_sensor: entities_to_watch.append(self.humidity_sensor)
        if self.presence_sensor: entities_to_watch.append(self.presence_sensor)
        if self.window_sensor: entities_to_watch.append(self.window_sensor)
        if self.ac_entity: entities_to_watch.append(self.ac_entity)

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
    async def async_set_smart_sleep_enabled(self, enabled: bool) -> None:
        self.smart_sleep_enabled = enabled
        self.hass.config_entries.async_update_entry(self.entry, options={**self.entry.options, CONF_SMART_SLEEP_ENABLED: enabled})
        await self.async_refresh()

    async def async_set_window_guard_enabled(self, enabled: bool) -> None:
        self.window_guard_enabled = enabled
        self.hass.config_entries.async_update_entry(self.entry, options={**self.entry.options, CONF_WINDOW_GUARD_ENABLED: enabled})
        await self.async_refresh()

    async def async_set_eco_leave_enabled(self, enabled: bool) -> None:
        self.eco_leave_enabled = enabled
        self.hass.config_entries.async_update_entry(self.entry, options={**self.entry.options, CONF_ECO_LEAVE_ENABLED: enabled})
        await self.async_refresh()

    async def async_set_auto_dry_enabled(self, enabled: bool) -> None:
        self.auto_dry_enabled = enabled
        self.hass.config_entries.async_update_entry(self.entry, options={**self.entry.options, CONF_AUTO_DRY_ENABLED: enabled})
        await self.async_refresh()
