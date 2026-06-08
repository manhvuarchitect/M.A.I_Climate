"""Các công tắc cấu hình riêng cho Điều hòa nhiệt độ."""
from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator_ac import SmartACCoordinator

class SmartSleepSwitch(CoordinatorEntity, SwitchEntity):
    def __init__(self, coordinator: SmartACCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self._attr_name = "Ngủ sâu thông minh (Smart Sleep)"
        self._attr_unique_id = f"{entry.entry_id}_ac_smart_sleep"
        self._attr_icon = "mdi:bed-temperature"

    @property
    def is_on(self) -> bool:
        return self.coordinator.smart_sleep_enabled

    async def async_turn_on(self, **kwargs) -> None:
        await self.coordinator.async_set_smart_sleep_enabled(True)

    async def async_turn_off(self, **kwargs) -> None:
        await self.coordinator.async_set_smart_sleep_enabled(False)


class WindowGuardSwitch(CoordinatorEntity, SwitchEntity):
    def __init__(self, coordinator: SmartACCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self._attr_name = "Chống thoát nhiệt (Window Guard)"
        self._attr_unique_id = f"{entry.entry_id}_ac_window_guard"
        self._attr_icon = "mdi:window-open-variant"

    @property
    def is_on(self) -> bool:
        return self.coordinator.window_guard_enabled

    async def async_turn_on(self, **kwargs) -> None:
        await self.coordinator.async_set_window_guard_enabled(True)

    async def async_turn_off(self, **kwargs) -> None:
        await self.coordinator.async_set_window_guard_enabled(False)


class EcoLeaveSwitch(CoordinatorEntity, SwitchEntity):
    def __init__(self, coordinator: SmartACCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self._attr_name = "Vắng mặt tiết kiệm điện (Eco Leave)"
        self._attr_unique_id = f"{entry.entry_id}_ac_eco_leave"
        self._attr_icon = "mdi:motion-sensor-off"

    @property
    def is_on(self) -> bool:
        return self.coordinator.eco_leave_enabled

    async def async_turn_on(self, **kwargs) -> None:
        await self.coordinator.async_set_eco_leave_enabled(True)

    async def async_turn_off(self, **kwargs) -> None:
        await self.coordinator.async_set_eco_leave_enabled(False)


class AutoDrySwitch(CoordinatorEntity, SwitchEntity):
    def __init__(self, coordinator: SmartACCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self._attr_name = "Hút ẩm thông minh (Auto Dry)"
        self._attr_unique_id = f"{entry.entry_id}_ac_auto_dry"
        self._attr_icon = "mdi:water-percent-alert"

    @property
    def is_on(self) -> bool:
        return self.coordinator.auto_dry_enabled

    async def async_turn_on(self, **kwargs) -> None:
        await self.coordinator.async_set_auto_dry_enabled(True)

    async def async_turn_off(self, **kwargs) -> None:
        await self.coordinator.async_set_auto_dry_enabled(False)
