"""Number entity: điều chỉnh ngưỡng chỉ số oi bức để tự động bật quạt."""
from __future__ import annotations

from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import slugify

from .const import DOMAIN, ICON_THRESHOLD, SUFFIX_THRESHOLD_NUMBER
from .coordinator import SmartFanCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Tạo number entity ngưỡng auto-on."""
    coordinator: SmartFanCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([AutoOnThresholdNumber(coordinator, entry)])


class AutoOnThresholdNumber(CoordinatorEntity, NumberEntity):
    """Number entity để điều chỉnh ngưỡng Heat Index tự động bật quạt."""

    _attr_native_min_value = 25.0
    _attr_native_max_value = 60.0
    _attr_native_step = 0.5
    _attr_native_unit_of_measurement = "°C"
    _attr_mode = NumberMode.BOX
    _attr_icon = ICON_THRESHOLD

    def __init__(self, coordinator: SmartFanCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self.entry = entry
        self._attr_unique_id = f"{entry.entry_id}{SUFFIX_THRESHOLD_NUMBER}"
        self._attr_has_entity_name = True
        self._attr_translation_key = "auto_on_threshold"
        slug_name = slugify(entry.data.get("fan_name", "fan")).replace("_", "")
        self.entity_id = f"number.maic_{slug_name}_{self._attr_translation_key}"

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, self.entry.entry_id)},
            "name": self.entry.data.get("fan_name", "Smart Fan"),
            "manufacturer": "Smart Fan Manager",
            "model": "Fan Controller",
        }

    @property
    def native_value(self) -> float:
        """Ngưỡng hiện tại."""
        return self.coordinator.data.get("auto_on_threshold", 38.0)

    async def async_set_native_value(self, value: float) -> None:
        """Cập nhật ngưỡng mới."""
        await self.coordinator.async_update_threshold(value)

    @property
    def extra_state_attributes(self) -> dict:
        muggy = self.coordinator.data.get("muggy_index", 0)
        return {
            "chỉ_số_oi_bức_hiện_tại": muggy,
            "khoảng_cách_đến_ngưỡng": round(self.native_value - muggy, 1),
        }
