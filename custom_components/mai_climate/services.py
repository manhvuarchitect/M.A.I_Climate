"""Services cho Smart Fan Manager — gọi được từ automation và script."""
from __future__ import annotations

import logging
import voluptuous as vol

from homeassistant.core import HomeAssistant, ServiceCall
import homeassistant.helpers.config_validation as cv

from .const import (
    DOMAIN,
    SERVICE_SET_TIMER,
    SERVICE_CANCEL_TIMER,
    SERVICE_SET_MODE,
    ATTR_MINUTES,
    ATTR_MODE,
    MODE_TIMER,
    MODE_COOLDOWN,
    TIMER_PRESETS,
)

_LOGGER = logging.getLogger(__name__)

# Schema validation cho service calls
SET_TIMER_SCHEMA = vol.Schema(
    {
        vol.Required("entry_id"): str,
        vol.Required(ATTR_MINUTES): vol.All(
            vol.Coerce(int), vol.Range(min=1, max=480)
        ),
        vol.Optional(ATTR_MODE, default=MODE_TIMER): vol.In(
            [MODE_TIMER, MODE_COOLDOWN]
        ),
    }
)

CANCEL_TIMER_SCHEMA = vol.Schema(
    {
        vol.Required("entry_id"): str,
    }
)

SET_MODE_SCHEMA = vol.Schema(
    {
        vol.Required("entry_id"): str,
        vol.Required(ATTR_MODE): vol.In([MODE_TIMER, MODE_COOLDOWN]),
        vol.Optional(ATTR_MINUTES, default=30): vol.All(
            vol.Coerce(int), vol.Range(min=1, max=480)
        ),
    }
)


def _get_coordinator(hass: HomeAssistant, entry_id: str):
    """Tìm coordinator theo entry_id."""
    coordinators = hass.data.get(DOMAIN, {})
    coordinator = coordinators.get(entry_id)
    if not coordinator:
        raise ValueError(
            f"Không tìm thấy Smart Fan với entry_id: {entry_id}. "
            f"Các entry hợp lệ: {list(coordinators.keys())}"
        )
    return coordinator


async def async_setup_services(hass: HomeAssistant) -> None:
    """Đăng ký tất cả services của integration."""

    async def handle_set_timer(call: ServiceCall) -> None:
        """Service: đặt timer tắt quạt sau N phút."""
        coordinator = _get_coordinator(hass, call.data["entry_id"])
        await coordinator.async_set_timer(
            minutes=call.data[ATTR_MINUTES],
            mode=call.data.get(ATTR_MODE, MODE_TIMER),
        )
        _LOGGER.info(
            "Service set_timer: %d phút cho %s",
            call.data[ATTR_MINUTES],
            coordinator.fan_entity,
        )

    async def handle_cancel_timer(call: ServiceCall) -> None:
        """Service: hủy timer đang chạy."""
        coordinator = _get_coordinator(hass, call.data["entry_id"])
        await coordinator.async_cancel_timer()

    async def handle_set_mode(call: ServiceCall) -> None:
        """Service: chuyển chế độ hoạt động."""
        coordinator = _get_coordinator(hass, call.data["entry_id"])
        mode = call.data[ATTR_MODE]
        if mode == MODE_COOLDOWN:
            await coordinator.async_set_cooldown_mode(True)
        else:
            await coordinator.async_set_timer(
                minutes=call.data.get(ATTR_MINUTES, 30),
                mode=mode,
            )

    hass.services.async_register(
        DOMAIN, SERVICE_SET_TIMER, handle_set_timer, schema=SET_TIMER_SCHEMA
    )
    hass.services.async_register(
        DOMAIN, SERVICE_CANCEL_TIMER, handle_cancel_timer, schema=CANCEL_TIMER_SCHEMA
    )
    hass.services.async_register(
        DOMAIN, SERVICE_SET_MODE, handle_set_mode, schema=SET_MODE_SCHEMA
    )

    _LOGGER.info("Smart Fan Manager services đã đăng ký")


async def async_unload_services(hass: HomeAssistant) -> None:
    """Gỡ bỏ services khi không còn quạt nào."""
    for service in [SERVICE_SET_TIMER, SERVICE_CANCEL_TIMER, SERVICE_SET_MODE]:
        hass.services.async_remove(DOMAIN, service)
