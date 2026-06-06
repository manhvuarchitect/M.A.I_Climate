"""Sensor entities: chỉ số oi bức & thời gian còn lại của timer."""
from __future__ import annotations

from homeassistant.components.sensor import SensorEntity, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    DOMAIN,
    ICON_MUGGY,
    ICON_TIMER,
    MUGGY_LOW,
    MUGGY_MEDIUM,
    MUGGY_HIGH,
    SUFFIX_MUGGY_SENSOR,
    SUFFIX_TIMER_SENSOR,
)
from .coordinator import SmartFanCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Tạo sensor entities cho entry này."""
    coordinator: SmartFanCoordinator = hass.data[DOMAIN][entry.entry_id]

    async_add_entities([
        MuggyIndexSensor(coordinator, entry),
        TimerRemainingSensor(coordinator, entry),
    ])


class SmartFanSensorBase(CoordinatorEntity, SensorEntity):
    """Base class cho tất cả sensor của Smart Fan Manager."""

    def __init__(self, coordinator: SmartFanCoordinator, entry: ConfigEntry) -> None:
        """Khởi tạo."""
        super().__init__(coordinator)
        self.entry = entry
        self._fan_id = entry.data["fan_entity"].replace("fan.", "")

    @property
    def device_info(self):
        """Gom tất cả entity vào cùng một device."""
        return {
            "identifiers": {(DOMAIN, self.entry.entry_id)},
            "name": self.entry.data.get("fan_name", "Smart Fan"),
            "manufacturer": "Smart Fan Manager",
            "model": "Fan Controller",
        }


class MuggyIndexSensor(SmartFanSensorBase):
    """Sensor hiển thị chỉ số oi bức (Heat Index)."""

    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = "°C"
    _attr_icon = ICON_MUGGY

    def __init__(self, coordinator: SmartFanCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}{SUFFIX_MUGGY_SENSOR}"
        self._attr_has_entity_name = True
        self._attr_translation_key = "muggy_index"

    @property
    def native_value(self) -> float | None:
        """Trả về chỉ số oi bức hiện tại."""
        return self.coordinator.data.get("muggy_index")

    @property
    def extra_state_attributes(self) -> dict:
        """Thuộc tính bổ sung: mức độ và màu sắc."""
        val = self.native_value or 0
        if val < MUGGY_LOW:
            level = "Dễ chịu"
            color = "#4CAF50"
        elif val < MUGGY_MEDIUM:
            level = "Hơi oi"
            color = "#FF9800"
        elif val < MUGGY_HIGH:
            level = "Oi bức"
            color = "#FF5722"
        else:
            level = "Rất oi bức"
            color = "#F44336"

        return {
            "mức_độ": level,
            "màu_sắc": color,
            "ngưỡng_auto_on": self.coordinator.auto_on_threshold,
        }


class TimerRemainingSensor(SmartFanSensorBase):
    """Sensor hiển thị số giây còn lại của timer."""

    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = "s"
    _attr_icon = ICON_TIMER

    def __init__(self, coordinator: SmartFanCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}{SUFFIX_TIMER_SENSOR}"
        self._attr_has_entity_name = True
        self._attr_translation_key = "timer_remaining"

    @property
    def native_value(self) -> int | None:
        """Trả về số giây còn lại, None nếu không có timer."""
        return self.coordinator.data.get("timer_remaining")

    @property
    def extra_state_attributes(self) -> dict:
        remaining = self.native_value
        if remaining is None:
            return {"trạng_thái": "Không có timer", "chế_độ": None}

        minutes = remaining // 60
        seconds = remaining % 60
        return {
            "trạng_thái": f"Còn {minutes} phút {seconds} giây",
            "chế_độ": self.coordinator.data.get("current_mode"),
            "thời_gian_kết_thúc": str(self.coordinator.timer_end),
        }
