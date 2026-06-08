"""M.A.I Climate — HACS Custom Integration.

Quản lý thiết bị khí hậu thông minh (quạt, điều hòa, máy lọc khí, quạt thông phòng): hẹn giờ, chỉ số oi bức, auto-on/off, giải nhiệt vận động.
Hỗ trợ quản lý nhiều thiết bị độc lập qua Config Flow.
"""
from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady

from .const import DOMAIN
from .coordinator import SmartFanCoordinator
from .services import async_setup_services, async_unload_services

_LOGGER = logging.getLogger(__name__)

# Các platform sẽ được load
PLATFORMS: list[Platform] = [
    Platform.SENSOR,
    Platform.SWITCH,
    Platform.NUMBER,
    Platform.SELECT,
]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Thiết lập integration từ một config entry (một quạt)."""
    hass.data.setdefault(DOMAIN, {})

    if not hass.data[DOMAIN]:
        try:
            # Register path tương thích với cả bản HA cũ và mới
            if hasattr(hass.http, "async_register_static_paths"):
                from homeassistant.components.http import StaticPathConfig
                hass.http.async_register_static_paths([
                    StaticPathConfig(
                        "/mai_climate_card",
                        hass.config.path("custom_components/mai_climate/www"),
                        cache_headers=True
                    )
                ])
            else:
                hass.http.register_static_path(
                    "/mai_climate_card",
                    hass.config.path("custom_components/mai_climate/www"),
                    True
                )
        except Exception as e:
            _LOGGER.debug("Path đã được đăng ký hoặc lỗi: %s", e)

    coordinator = SmartFanCoordinator(hass, entry)

    try:
        await coordinator.async_setup()
        await coordinator.async_config_entry_first_refresh()
    except Exception as err:
        raise ConfigEntryNotReady(f"Không thể khởi tạo coordinator: {err}") from err

    hass.data[DOMAIN][entry.entry_id] = coordinator

    # Load tất cả platform (sensor, switch, number, select)
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Đăng ký services (chỉ lần đầu)
    if len(hass.data[DOMAIN]) == 1:
        await async_setup_services(hass)

    # Lắng nghe thay đổi options (không reload, chỉ cập nhật biến trong bộ nhớ)
    entry.async_on_unload(entry.add_update_listener(async_update_options))

    _LOGGER.info("M.A.I Climate đã khởi tạo cho: %s", entry.data.get("fan_name"))
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Gỡ bỏ một config entry."""
    coordinator: SmartFanCoordinator = hass.data[DOMAIN].get(entry.entry_id)
    if coordinator:
        await coordinator.async_unload()

    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
        # Nếu không còn quạt nào, gỡ services
        if not hass.data[DOMAIN]:
            await async_unload_services(hass)

    return unload_ok


async def async_update_options(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Cập nhật options vào coordinator mà không reload toàn bộ integration nếu chỉ bật/tắt tính năng."""
    coordinator: SmartFanCoordinator = hass.data[DOMAIN].get(entry.entry_id)
    if coordinator:
        # Kiểm tra xem có thay đổi các entity lõi cần reload lại listeners không
        needs_reload = False
        old_options = coordinator.entry.options
        new_options = entry.options
        
        core_keys = [
            "fan_entity", "temp_sensor", "humidity_sensor", 
            "presence_sensor", "ac_entity"
        ]
        
        for key in core_keys:
            if old_options.get(key) != new_options.get(key):
                needs_reload = True
                break
                
        if needs_reload:
            _LOGGER.info("Cấu hình thiết bị thay đổi, đang tải lại integration...")
            await hass.config_entries.async_reload(entry.entry_id)
        else:
            _LOGGER.debug("Chỉ cập nhật tính năng thông minh, không cần reload")
            # Cập nhật entry.options cho coordinator
            coordinator.entry = entry
            coordinator.update_options(entry.options)
            await coordinator.async_refresh()
