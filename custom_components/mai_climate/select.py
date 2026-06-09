"""Select entity: chọn preset timer và kích hoạt ngay."""
from __future__ import annotations

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import slugify

from .const import (
    DOMAIN,
    CONF_DEVICE_TYPE,
    DEVICE_TYPE_FAN,
    DEVICE_TYPE_AC,
    TIMER_PRESETS,
    ICON_TIMER,
    SUFFIX_TIMER_SELECT,
)
from .coordinator import SmartFanCoordinator
from .coordinator_ac import SmartACCoordinator

OPTION_NONE = "— Chọn thời gian —"


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Thiết lập platform select."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    device_type = entry.data.get(CONF_DEVICE_TYPE, DEVICE_TYPE_FAN)

    selects = []

    if device_type == DEVICE_TYPE_FAN:
        selects.append(TimerPresetSelect(coordinator, entry))
    elif device_type == DEVICE_TYPE_AC:
        pass

    if selects:
        async_add_entities(selects)


class TimerPresetSelect(CoordinatorEntity, SelectEntity):
    """Select entity: chọn thời gian hẹn giờ tắt quạt.

    Khi chọn một preset, quạt tự bật và timer được đặt.
    Sau khi timer hết, entity trở về trạng thái "chọn thời gian".
    """

    _attr_icon = ICON_TIMER

    def __init__(self, coordinator: SmartFanCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self.entry = entry
        self._attr_unique_id = f"{entry.entry_id}{SUFFIX_TIMER_SELECT}"
        self._attr_has_entity_name = True
        self._attr_translation_key = "timer_preset"
        slug_name = slugify(entry.data.get("fan_name", "fan")).replace("_", "")
        self.entity_id = f"select.maic_{slug_name}_{self._attr_translation_key}"
        self._attr_options = [OPTION_NONE] + list(TIMER_PRESETS.keys())

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, self.entry.entry_id)},
            "name": self.entry.data.get("fan_name", "Smart Fan"),
            "manufacturer": "Smart Fan Manager",
            "model": "Fan Controller",
        }

    @property
    def current_option(self) -> str:
        """Hiển thị preset đang chạy hoặc placeholder."""
        remaining = self.coordinator.data.get("timer_remaining")
        if remaining and remaining > 0:
            mode = self.coordinator.data.get("current_mode", "")
            # Tìm label phù hợp với số phút còn lại
            for label, minutes in TIMER_PRESETS.items():
                if self.coordinator.timer_end:
                    return label
        return OPTION_NONE

    async def async_select_option(self, option: str) -> None:
        """Kích hoạt timer khi chọn preset."""
        if option == OPTION_NONE:
            await self.coordinator.async_cancel_timer()
            return

        minutes = TIMER_PRESETS.get(option)
        if minutes:
            await self.coordinator.async_set_timer(minutes=minutes)

    @property
    def extra_state_attributes(self) -> dict:
        return {
            "các_preset": list(TIMER_PRESETS.keys()),
            "timer_đang_chạy": self.coordinator.data.get("timer_remaining") is not None,
        }
