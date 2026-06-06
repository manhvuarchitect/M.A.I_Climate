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

SET_TIMER_SCHEMA = vol.Schema(
    {
        vol.Required("entity_id"): cv.entity_ids,
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
        vol.Required("entity_id"): cv.entity_ids,
    }
)

SET_MODE_SCHEMA = vol.Schema(
    {
        vol.Required("entity_id"): cv.entity_ids,
        vol.Required(ATTR_MODE): vol.In([MODE_TIMER, MODE_COOLDOWN]),
        vol.Optional(ATTR_MINUTES, default=30): vol.All(
            vol.Coerce(int), vol.Range(min=1, max=480)
        ),
    }
)


def _get_coordinators_by_entities(hass: HomeAssistant, entity_ids: list[str]):
    """Tìm coordinator theo danh sách fan entity_id."""
    matched = []
    coordinators = hass.data.get(DOMAIN, {})
    for entity_id in entity_ids:
        found = False
        for coordinator in coordinators.values():
            if coordinator.fan_entity == entity_id:
                matched.append(coordinator)
                found = True
                break
        if not found:
            _LOGGER.warning("Không tìm thấy cấu hình M.A.I Climate cho quạt: %s", entity_id)
            raise ValueError(f"Quạt '{entity_id}' chưa được cấu hình trong M.A.I Climate. Vui lòng vào Thiết bị & Dịch vụ để thêm quạt này!")
    return matched


async def async_setup_services(hass: HomeAssistant) -> None:
    """Đăng ký tất cả services của integration."""

    async def handle_set_timer(call: ServiceCall) -> None:
        """Service: đặt timer tắt quạt sau N phút."""
        coordinators = _get_coordinators_by_entities(hass, call.data["entity_id"])
        for coordinator in coordinators:
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
        coordinators = _get_coordinators_by_entities(hass, call.data["entity_id"])
        for coordinator in coordinators:
            await coordinator.async_cancel_timer()

    async def handle_set_mode(call: ServiceCall) -> None:
        """Service: chuyển chế độ hoạt động."""
        coordinators = _get_coordinators_by_entities(hass, call.data["entity_id"])
        mode = call.data[ATTR_MODE]
        for coordinator in coordinators:
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
