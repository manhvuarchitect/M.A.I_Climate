"""Coordinator cho thiết bị Máy lọc không khí."""
import logging
from datetime import datetime, timedelta
from typing import Any

from homeassistant.core import HomeAssistant, callback
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.helpers.event import async_track_state_change_event

from .const import (
    DOMAIN,
    CONF_PURIFIER_ENTITY,
    CONF_PM25_SENSOR,
    CONF_VOC_SENSOR,
    CONF_KITCHEN_SENSOR,
    CONF_AUTO_BOOST_ENABLED,
    CONF_KITCHEN_SYNC_ENABLED,
    CONF_STRICT_QUIET_HOURS_ENABLED,
    CONF_QUIET_HOURS_START,
    CONF_QUIET_HOURS_END,
    DEFAULT_SCAN_INTERVAL,
)

_LOGGER = logging.getLogger(__name__)

class SmartPurifierCoordinator(DataUpdateCoordinator):
    """Lớp quản lý trạng thái trung tâm cho Máy lọc không khí."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Khởi tạo."""
        config = {**entry.data, **entry.options}
        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_purifier_{entry.entry_id}",
            update_interval=timedelta(seconds=DEFAULT_SCAN_INTERVAL),
        )
        self.entry = entry
        self.hass = hass
        self._unsub_listeners: list = []

        self.purifier_entity = config.get(CONF_PURIFIER_ENTITY)
        self.pm25_sensor = config.get(CONF_PM25_SENSOR)
        self.voc_sensor = config.get(CONF_VOC_SENSOR)
        self.kitchen_sensor = config.get(CONF_KITCHEN_SENSOR)

        self.auto_boost_enabled = config.get(CONF_AUTO_BOOST_ENABLED, True)
        self.kitchen_sync_enabled = config.get(CONF_KITCHEN_SYNC_ENABLED, False)
        self.strict_quiet_hours_enabled = config.get(CONF_STRICT_QUIET_HOURS_ENABLED, False)
        self.quiet_hours_start = config.get(CONF_QUIET_HOURS_START, "23:00:00")
        self.quiet_hours_end = config.get(CONF_QUIET_HOURS_END, "06:00:00")

    def update_options(self, options: dict[str, Any]) -> None:
        """Cập nhật tùy chọn."""
        self.purifier_entity = options.get(CONF_PURIFIER_ENTITY, self.purifier_entity)
        self.pm25_sensor = options.get(CONF_PM25_SENSOR, self.pm25_sensor)
        self.voc_sensor = options.get(CONF_VOC_SENSOR, self.voc_sensor)
        self.kitchen_sensor = options.get(CONF_KITCHEN_SENSOR, self.kitchen_sensor)

        self.auto_boost_enabled = options.get(CONF_AUTO_BOOST_ENABLED, self.auto_boost_enabled)
        self.kitchen_sync_enabled = options.get(CONF_KITCHEN_SYNC_ENABLED, self.kitchen_sync_enabled)
        self.strict_quiet_hours_enabled = options.get(CONF_STRICT_QUIET_HOURS_ENABLED, self.strict_quiet_hours_enabled)
        self.quiet_hours_start = options.get(CONF_QUIET_HOURS_START, self.quiet_hours_start)
        self.quiet_hours_end = options.get(CONF_QUIET_HOURS_END, self.quiet_hours_end)

    def _is_quiet_hours(self) -> bool:
        """Kiểm tra xem có đang trong giờ yên tĩnh không."""
        try:
            now = datetime.now().time()
            start = datetime.strptime(self.quiet_hours_start, "%H:%M:%S").time()
            end = datetime.strptime(self.quiet_hours_end, "%H:%M:%S").time()
            if start <= end:
                return start <= now <= end
            else:
                return start <= now or now <= end
        except Exception:
            return False

    async def _async_update_data(self) -> dict[str, Any]:
        """Cập nhật dữ liệu định kỳ."""
        if not self.purifier_entity:
            return self._build_state()

        try:
            await self._apply_purifier_logic()
        except Exception as e:
            _LOGGER.error("Lỗi khi cập nhật dữ liệu SmartPurifierCoordinator: %s", e)

        return self._build_state()

    def _build_state(self) -> dict[str, Any]:
        return {
            "auto_boost_enabled": self.auto_boost_enabled,
            "kitchen_sync_enabled": self.kitchen_sync_enabled,
            "strict_quiet_hours_enabled": self.strict_quiet_hours_enabled,
        }

    async def _apply_purifier_logic(self) -> None:
        """Thực thi logic cho máy lọc không khí."""
        target_pct = None
        should_turn_on = False

        # 1. Kiểm tra Kitchen Sync (Ưu tiên)
        if self.kitchen_sync_enabled and self.kitchen_sensor:
            k_state = self.hass.states.get(self.kitchen_sensor)
            if k_state and k_state.state == "on":
                should_turn_on = True
                target_pct = 100  # Nấu ăn -> Chạy mức cao nhất

        # 2. Kiểm tra Auto Boost dựa vào chất lượng không khí
        if self.auto_boost_enabled and target_pct is None:
            pm25_val = 0.0
            voc_val = 0.0

            if self.pm25_sensor:
                p_state = self.hass.states.get(self.pm25_sensor)
                if p_state and p_state.state not in ("unknown", "unavailable"):
                    try:
                        pm25_val = float(p_state.state)
                    except ValueError:
                        pass

            if self.voc_sensor:
                v_state = self.hass.states.get(self.voc_sensor)
                if v_state and v_state.state not in ("unknown", "unavailable"):
                    try:
                        voc_val = float(v_state.state)
                    except ValueError:
                        pass

            if pm25_val > 50 or voc_val > 500:
                should_turn_on = True
                target_pct = 100
            elif pm25_val > 25 or voc_val > 200:
                should_turn_on = True
                target_pct = 66
            elif pm25_val > 10 or voc_val > 100:
                should_turn_on = True
                target_pct = 33
            else:
                # Không khí sạch, nếu đang chạy bằng Auto Boost thì có thể tắt hoặc giảm về mức thấp nhất
                target_pct = 10

        # 3. Chế độ Quiet Hours nghiêm ngặt (ghi đè tất cả)
        if self.strict_quiet_hours_enabled and self._is_quiet_hours():
            if target_pct is not None and target_pct > 33:
                target_pct = 33  # Ép tốc độ xuống mức thấp trong giờ yên tĩnh

        # 4. Áp dụng trạng thái
        purifier_state = self.hass.states.get(self.purifier_entity)
        is_on = purifier_state is not None and purifier_state.state != "off"

        if should_turn_on and not is_on:
            _LOGGER.info("Bật máy lọc không khí %s", self.purifier_entity)
            await self.hass.services.async_call("fan", "turn_on", {"entity_id": self.purifier_entity})
        
        if target_pct is not None:
            current_pct = purifier_state.attributes.get("percentage") if is_on else None
            if current_pct != target_pct:
                _LOGGER.info("Set tốc độ %s -> %d%%", self.purifier_entity, target_pct)
                # Ensure it's on before setting percentage
                if not is_on:
                    await self.hass.services.async_call("fan", "turn_on", {"entity_id": self.purifier_entity})
                await self.hass.services.async_call("fan", "set_percentage", {"entity_id": self.purifier_entity, "percentage": target_pct})

    async def async_setup(self) -> None:
        """Thiết lập listeners."""
        @callback
        def _sensor_changed(event):
            self.hass.async_create_task(self.async_refresh())

        entities_to_watch = []
        if self.pm25_sensor: entities_to_watch.append(self.pm25_sensor)
        if self.voc_sensor: entities_to_watch.append(self.voc_sensor)
        if self.kitchen_sensor: entities_to_watch.append(self.kitchen_sensor)

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
    async def async_set_auto_boost_enabled(self, enabled: bool) -> None:
        self.auto_boost_enabled = enabled
        self.hass.config_entries.async_update_entry(self.entry, options={**self.entry.options, CONF_AUTO_BOOST_ENABLED: enabled})
        await self.async_refresh()

    async def async_set_kitchen_sync_enabled(self, enabled: bool) -> None:
        self.kitchen_sync_enabled = enabled
        self.hass.config_entries.async_update_entry(self.entry, options={**self.entry.options, CONF_KITCHEN_SYNC_ENABLED: enabled})
        await self.async_refresh()

    async def async_set_strict_quiet_hours_enabled(self, enabled: bool) -> None:
        self.strict_quiet_hours_enabled = enabled
        self.hass.config_entries.async_update_entry(self.entry, options={**self.entry.options, CONF_STRICT_QUIET_HOURS_ENABLED: enabled})
        await self.async_refresh()
