"""Switch entity: bật/tắt chế độ Giải nhiệt vận động."""
from __future__ import annotations

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import slugify

from .const import (
    DOMAIN,
    CONF_SPEED_1_ENTITY,
    CONF_SPEED_2_ENTITY,
    CONF_SPEED_3_ENTITY,
    CONF_SPEED_4_ENTITY,
    CONF_AC_ENTITY,
    CONF_DEVICE_TYPE,
    DEVICE_TYPE_FAN,
    DEVICE_TYPE_AC,
    ICON_COOLDOWN, 
    SUFFIX_COOLDOWN_SWITCH, 
    SUFFIX_AUTO_ON_SWITCH,
    SUFFIX_SMART_SPEED_SWITCH,
    SUFFIX_SLEEP_MODE_SWITCH,
    SUFFIX_NATURAL_WIND_SWITCH,
    SUFFIX_QUIET_HOURS_SWITCH,
    SUFFIX_AC_SYNC_SWITCH,
    SUFFIX_AUTO_OFF_SWITCH,
)
from .coordinator import SmartFanCoordinator
from .coordinator_ac import SmartACCoordinator


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Thiết lập platform switch."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    device_type = entry.data.get(CONF_DEVICE_TYPE, DEVICE_TYPE_FAN)

    switches = []

    if device_type == DEVICE_TYPE_FAN:
        switches.extend([
            CooldownModeSwitch(coordinator, entry),
            AutoOnSwitch(coordinator, entry),
            SmartSpeedSwitch(coordinator, entry),
            SleepModeSwitch(coordinator, entry),
            NaturalWindSwitch(coordinator, entry),
            QuietHoursSwitch(coordinator, entry),
            AutoOffSwitch(coordinator, entry),
        ])
        if entry.data.get(CONF_AC_ENTITY) or entry.options.get(CONF_AC_ENTITY):
            switches.append(ACSyncSwitch(coordinator, entry))
    elif device_type == DEVICE_TYPE_AC:
        from .switch_ac import (
            SmartSleepSwitch,
            WindowGuardSwitch,
            EcoLeaveSwitch,
            AutoDrySwitch,
        )
        switches.extend([
            SmartSleepSwitch(coordinator, entry),
            WindowGuardSwitch(coordinator, entry),
            EcoLeaveSwitch(coordinator, entry),
            AutoDrySwitch(coordinator, entry),
        ])

    if switches:
        async_add_entities(switches)


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

class AutoOffSwitch(CoordinatorEntity, SwitchEntity):
    """Switch bật/tắt tính năng tự động tắt quạt theo nhiệt độ."""

    _attr_icon = "mdi:fan-off"

    def __init__(self, coordinator: SmartFanCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self.entry = entry
        self._attr_unique_id = f"{entry.entry_id}{SUFFIX_AUTO_OFF_SWITCH}"
        self._attr_has_entity_name = True
        self._attr_translation_key = "auto_off_enabled"
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
        return self.coordinator.data.get("auto_off_enabled", False)

    async def async_turn_on(self, **kwargs) -> None:
        await self.coordinator.async_set_auto_off_enabled(True)

    async def async_turn_off(self, **kwargs) -> None:
        await self.coordinator.async_set_auto_off_enabled(False)

    @property
    def extra_state_attributes(self) -> dict:
        return {
            "mô_tả": "Tự động tắt quạt khi nhiệt độ giảm xuống thấp",
        }

class SmartSpeedSwitch(CoordinatorEntity, SwitchEntity):
    _attr_icon = "mdi:fan-speed-3"

    def __init__(self, coordinator: SmartFanCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self.entry = entry
        self._attr_unique_id = f"{entry.entry_id}{SUFFIX_SMART_SPEED_SWITCH}"
        self._attr_has_entity_name = True
        self._attr_translation_key = "smart_speed_enabled"
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
        return self.coordinator.data.get("smart_speed_enabled", False)

    async def async_turn_on(self, **kwargs) -> None:
        await self.coordinator.async_set_smart_speed_enabled(True)

    async def async_turn_off(self, **kwargs) -> None:
        await self.coordinator.async_set_smart_speed_enabled(False)

class SleepModeSwitch(CoordinatorEntity, SwitchEntity):
    _attr_icon = "mdi:sleep"

    def __init__(self, coordinator: SmartFanCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self.entry = entry
        self._attr_unique_id = f"{entry.entry_id}{SUFFIX_SLEEP_MODE_SWITCH}"
        self._attr_has_entity_name = True
        self._attr_translation_key = "sleep_mode_enabled"
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
        return self.coordinator.data.get("sleep_mode_enabled", False)

    async def async_turn_on(self, **kwargs) -> None:
        await self.coordinator.async_set_sleep_mode_enabled(True)

    async def async_turn_off(self, **kwargs) -> None:
        await self.coordinator.async_set_sleep_mode_enabled(False)

class NaturalWindSwitch(CoordinatorEntity, SwitchEntity):
    _attr_icon = "mdi:weather-windy"

    def __init__(self, coordinator: SmartFanCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self.entry = entry
        self._attr_unique_id = f"{entry.entry_id}{SUFFIX_NATURAL_WIND_SWITCH}"
        self._attr_has_entity_name = True
        self._attr_translation_key = "natural_wind_enabled"
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
        return self.coordinator.data.get("natural_wind_enabled", False)

    async def async_turn_on(self, **kwargs) -> None:
        await self.coordinator.async_set_natural_wind_enabled(True)

    async def async_turn_off(self, **kwargs) -> None:
        await self.coordinator.async_set_natural_wind_enabled(False)

class QuietHoursSwitch(CoordinatorEntity, SwitchEntity):
    _attr_icon = "mdi:volume-off"

    def __init__(self, coordinator: SmartFanCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self.entry = entry
        self._attr_unique_id = f"{entry.entry_id}{SUFFIX_QUIET_HOURS_SWITCH}"
        self._attr_has_entity_name = True
        self._attr_translation_key = "quiet_hours_enabled"
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
        return self.coordinator.data.get("quiet_hours_enabled", False)

    async def async_turn_on(self, **kwargs) -> None:
        await self.coordinator.async_set_quiet_hours_enabled(True)

    async def async_turn_off(self, **kwargs) -> None:
        await self.coordinator.async_set_quiet_hours_enabled(False)

class ACSyncSwitch(CoordinatorEntity, SwitchEntity):
    """Switch bật/tắt đồng bộ điều hòa."""

    _attr_icon = "mdi:air-conditioner"

    def __init__(self, coordinator: SmartFanCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self.entry = entry
        self._attr_unique_id = f"{entry.entry_id}{SUFFIX_AC_SYNC_SWITCH}"
        self._attr_has_entity_name = True
        self._attr_translation_key = "ac_sync_enabled"
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
        """Trạng thái hiện tại của nút."""
        return self.coordinator.data.get("ac_sync_enabled", True)

    async def async_turn_on(self, **kwargs) -> None:
        """Bật tính năng."""
        await self.coordinator.async_set_ac_sync_enabled(True)

    async def async_turn_off(self, **kwargs) -> None:
        """Tắt tính năng."""
        await self.coordinator.async_set_ac_sync_enabled(False)

    @property
    def extra_state_attributes(self) -> dict:
        return {
            "mô_tả": "Bật/Tắt tính năng đồng bộ thông minh với Điều hòa",
        }
