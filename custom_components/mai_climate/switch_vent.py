"""Các công tắc cấu hình riêng cho Quạt thông gió."""
from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator_vent import SmartVentCoordinator

class OdorControlSwitch(CoordinatorEntity, SwitchEntity):
    def __init__(self, coordinator: SmartVentCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self._attr_name = "Khử mùi phòng tắm (Odor Control)"
        self._attr_unique_id = f"{entry.entry_id}_vent_odor_control"
        self._attr_icon = "mdi:air-purifier"

    @property
    def is_on(self) -> bool:
        return self.coordinator.odor_control_enabled

    async def async_turn_on(self, **kwargs) -> None:
        await self.coordinator.async_set_odor_control_enabled(True)

    async def async_turn_off(self, **kwargs) -> None:
        await self.coordinator.async_set_odor_control_enabled(False)


class VentAutoDrySwitch(CoordinatorEntity, SwitchEntity):
    def __init__(self, coordinator: SmartVentCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self._attr_name = "Hút ẩm tự động (Auto Dry)"
        self._attr_unique_id = f"{entry.entry_id}_vent_auto_dry"
        self._attr_icon = "mdi:water-percent"

    @property
    def is_on(self) -> bool:
        return self.coordinator.vent_auto_dry_enabled

    async def async_turn_on(self, **kwargs) -> None:
        await self.coordinator.async_set_vent_auto_dry_enabled(True)

    async def async_turn_off(self, **kwargs) -> None:
        await self.coordinator.async_set_vent_auto_dry_enabled(False)


class RoutineAirSyncSwitch(CoordinatorEntity, SwitchEntity):
    def __init__(self, coordinator: SmartVentCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self._attr_name = "Lưu thông khí định kỳ (Routine Sync)"
        self._attr_unique_id = f"{entry.entry_id}_vent_routine_sync"
        self._attr_icon = "mdi:clock-outline"

    @property
    def is_on(self) -> bool:
        return self.coordinator.routine_air_sync_enabled

    async def async_turn_on(self, **kwargs) -> None:
        await self.coordinator.async_set_routine_air_sync_enabled(True)

    async def async_turn_off(self, **kwargs) -> None:
        await self.coordinator.async_set_routine_air_sync_enabled(False)
