"""Các công tắc cấu hình riêng cho Máy lọc không khí."""
from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import slugify

from .const import DOMAIN
from .coordinator_purifier import SmartPurifierCoordinator

class AutoBoostSwitch(CoordinatorEntity, SwitchEntity):
    def __init__(self, coordinator: SmartPurifierCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self._attr_name = "Tăng tốc tự động (Auto Boost)"
        self._attr_unique_id = f"{entry.entry_id}_purifier_auto_boost"
        slug_name = slugify(entry.data.get("purifier_name", "purifier")).replace("_", "")
        self.entity_id = f"switch.maic_{slug_name}_purifier_auto_boost"
        self._attr_icon = "mdi:air-filter"

    @property
    def is_on(self) -> bool:
        return self.coordinator.auto_boost_enabled

    async def async_turn_on(self, **kwargs) -> None:
        await self.coordinator.async_set_auto_boost_enabled(True)

    async def async_turn_off(self, **kwargs) -> None:
        await self.coordinator.async_set_auto_boost_enabled(False)


class KitchenSyncSwitch(CoordinatorEntity, SwitchEntity):
    def __init__(self, coordinator: SmartPurifierCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self._attr_name = "Đồng bộ Bếp (Kitchen Sync)"
        self._attr_unique_id = f"{entry.entry_id}_purifier_kitchen_sync"
        slug_name = slugify(entry.data.get("purifier_name", "purifier")).replace("_", "")
        self.entity_id = f"switch.maic_{slug_name}_purifier_kitchen_sync"
        self._attr_icon = "mdi:pot-steam"

    @property
    def is_on(self) -> bool:
        return self.coordinator.kitchen_sync_enabled

    async def async_turn_on(self, **kwargs) -> None:
        await self.coordinator.async_set_kitchen_sync_enabled(True)

    async def async_turn_off(self, **kwargs) -> None:
        await self.coordinator.async_set_kitchen_sync_enabled(False)


class StrictQuietHoursSwitch(CoordinatorEntity, SwitchEntity):
    def __init__(self, coordinator: SmartPurifierCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self._attr_name = "Giờ yên tĩnh tuyệt đối (Strict Quiet)"
        self._attr_unique_id = f"{entry.entry_id}_purifier_strict_quiet"
        slug_name = slugify(entry.data.get("purifier_name", "purifier")).replace("_", "")
        self.entity_id = f"switch.maic_{slug_name}_purifier_strict_quiet"
        self._attr_icon = "mdi:volume-off"

    @property
    def is_on(self) -> bool:
        return self.coordinator.strict_quiet_hours_enabled

    async def async_turn_on(self, **kwargs) -> None:
        await self.coordinator.async_set_strict_quiet_hours_enabled(True)

    async def async_turn_off(self, **kwargs) -> None:
        await self.coordinator.async_set_strict_quiet_hours_enabled(False)
