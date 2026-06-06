"""Switch entity: bật/tắt chế độ Giải nhiệt vận động."""
from __future__ import annotations

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import slugify

from .const import DOMAIN, ICON_COOLDOWN, SUFFIX_COOLDOWN_SWITCH, SUFFIX_AUTO_ON_SWITCH
from .coordinator import SmartFanCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: SmartFanCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([
        CooldownModeSwitch(coordinator, entry),
        AutoOnSwitch(coordinator, entry)
    ])


class CooldownModeSwitch(CoordinatorEntity, SwitchEntity):
    """Switch bật/tắt chế độ Giải nhiệt vận động (tự tắt sau 30 phút)."""

    _attr_icon = ICON_COOLDOWN

    def __init__(self, coordinator: SmartFanCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self.entry = entry
        self._attr_unique_id = f"{entry.entry_id}{SUFFIX_COOLDOWN_SWITCH}"
        self._attr_has_entity_name = True
        self._attr_translation_key = "cooldown_mode"
        slug_name = slugify(entry.data.get("fan_name", "fan")).replace("_", "")
        self.entity_id = f"switch.maic_{slug_name}_{self._attr_translation_key}"

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, self.entry.entry_id)},
            "name": self.entry.data.get("fan_name", "Smart Fan"),
            "manufacturer": "Smart Fan Manager",
            "model": "Fan Controller",
        }

    @property
    def is_on(self) -> bool:
        """Trả về True nếu chế độ giải nhiệt đang bật."""
        return self.coordinator.data.get("cooldown_active", False)

    async def async_turn_on(self, **kwargs) -> None:
        """Bật chế độ giải nhiệt — bật quạt 30 phút."""
        await self.coordinator.async_set_cooldown_mode(True)

    async def async_turn_off(self, **kwargs) -> None:
        """Tắt chế độ giải nhiệt — hủy timer và tắt quạt."""
        await self.coordinator.async_set_cooldown_mode(False)

    @property
    def extra_state_attributes(self) -> dict:
        return {
            "mô_tả": "Bật quạt 30 phút để giải nhiệt sau khi vận động",
            "chế_độ_hiện_tại": self.coordinator.data.get("current_mode"),
        }


class AutoOnSwitch(CoordinatorEntity, SwitchEntity):
    """Switch bật/tắt tính năng tự động bật quạt theo nhiệt độ/hiện diện."""

    _attr_icon = "mdi:fan-auto"

    def __init__(self, coordinator: SmartFanCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self.entry = entry
        self._attr_unique_id = f"{entry.entry_id}{SUFFIX_AUTO_ON_SWITCH}"
        self._attr_has_entity_name = True
        self._attr_translation_key = "auto_on_enabled"
        slug_name = slugify(entry.data.get("fan_name", "fan")).replace("_", "")
        self.entity_id = f"switch.maic_{slug_name}_{self._attr_translation_key}"

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, self.entry.entry_id)},
            "name": self.entry.data.get("fan_name", "Smart Fan"),
            "manufacturer": "Smart Fan Manager",
            "model": "Fan Controller",
        }

    @property
    def is_on(self) -> bool:
        """Trả về True nếu tính năng tự động bật đang hoạt động."""
        return self.coordinator.data.get("auto_on_enabled", True)

    async def async_turn_on(self, **kwargs) -> None:
        """Bật tính năng Auto-on."""
        await self.coordinator.async_set_auto_on_enabled(True)

    async def async_turn_off(self, **kwargs) -> None:
        """Tắt tính năng Auto-on."""
        await self.coordinator.async_set_auto_on_enabled(False)

    @property
    def extra_state_attributes(self) -> dict:
        return {
            "mô_tả": "Bật/Tắt chế độ tự động bật quạt khi quá nóng hoặc có người",
        }
