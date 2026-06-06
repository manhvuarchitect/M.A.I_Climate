"""Config Flow — giao diện UI để thêm/cấu hình quạt."""
from __future__ import annotations

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import selector
import homeassistant.helpers.config_validation as cv

from .const import (
    DOMAIN,
    CONF_FAN_ENTITY,
    CONF_TEMP_SENSOR,
    CONF_HUMIDITY_SENSOR,
    CONF_AC_ENTITY,
    CONF_AUTO_ON_THRESHOLD,
    CONF_FAN_NAME,
    DEFAULT_AUTO_ON_THRESHOLD,
)


def _fan_schema(defaults: dict = None) -> vol.Schema:
    """Tạo schema form cấu hình quạt."""
    if defaults is None:
        defaults = {}

    schema = {
        vol.Required(
            CONF_FAN_NAME,
            default=defaults.get(CONF_FAN_NAME, "Quạt phòng làm việc"),
        ): str,
    }

    fan_entity = defaults.get(CONF_FAN_ENTITY)
    if fan_entity:
        schema[vol.Required(CONF_FAN_ENTITY, default=fan_entity)] = selector.EntitySelector(
            selector.EntitySelectorConfig(domain="fan")
        )
    else:
        schema[vol.Required(CONF_FAN_ENTITY)] = selector.EntitySelector(
            selector.EntitySelectorConfig(domain="fan")
        )

    temp_sensor = defaults.get(CONF_TEMP_SENSOR)
    if temp_sensor:
        schema[vol.Required(CONF_TEMP_SENSOR, default=temp_sensor)] = selector.EntitySelector(
            selector.EntitySelectorConfig(domain="sensor", device_class="temperature")
        )
    else:
        schema[vol.Required(CONF_TEMP_SENSOR)] = selector.EntitySelector(
            selector.EntitySelectorConfig(domain="sensor", device_class="temperature")
        )

    humidity_sensor = defaults.get(CONF_HUMIDITY_SENSOR)
    if humidity_sensor:
        schema[vol.Optional(CONF_HUMIDITY_SENSOR, default=humidity_sensor)] = selector.EntitySelector(
            selector.EntitySelectorConfig(domain="sensor", device_class="humidity")
        )
    else:
        schema[vol.Optional(CONF_HUMIDITY_SENSOR)] = selector.EntitySelector(
            selector.EntitySelectorConfig(domain="sensor", device_class="humidity")
        )

    ac_entity = defaults.get(CONF_AC_ENTITY)
    if ac_entity:
        schema[vol.Optional(CONF_AC_ENTITY, default=ac_entity)] = selector.EntitySelector(
            selector.EntitySelectorConfig(domain="climate")
        )
    else:
        schema[vol.Optional(CONF_AC_ENTITY)] = selector.EntitySelector(
            selector.EntitySelectorConfig(domain="climate")
        )

    auto_on_threshold = defaults.get(CONF_AUTO_ON_THRESHOLD, DEFAULT_AUTO_ON_THRESHOLD)
    schema[vol.Optional(CONF_AUTO_ON_THRESHOLD, default=auto_on_threshold)] = selector.NumberSelector(
        selector.NumberSelectorConfig(min=25, max=60, step=0.5, unit_of_measurement="°C (HI)")
    )

    return vol.Schema(schema)


class SmartFanManagerConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Config Flow để thêm quạt mới vào Smart Fan Manager."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Bước đầu: người dùng điền thông tin quạt."""
        errors = {}

        if user_input is not None:
            # Kiểm tra entity tồn tại
            fan_state = self.hass.states.get(user_input[CONF_FAN_ENTITY])
            if fan_state is None:
                errors[CONF_FAN_ENTITY] = "entity_not_found"
            else:
                # Tạo unique_id từ fan entity để tránh thêm trùng
                await self.async_set_unique_id(user_input[CONF_FAN_ENTITY])
                self._abort_if_unique_id_configured()

                return self.async_create_entry(
                    title=user_input[CONF_FAN_NAME],
                    data=user_input,
                )

        return self.async_show_form(
            step_id="user",
            data_schema=_fan_schema(),
            errors=errors,
            description_placeholders={
                "docs_url": "https://github.com/yourusername/smart_fan_manager"
            },
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Trả về options flow để chỉnh sửa sau khi cài đặt."""
        return SmartFanManagerOptionsFlow()


class SmartFanManagerOptionsFlow(config_entries.OptionsFlow):
    """Options Flow — chỉnh sửa cấu hình quạt đã thêm."""

    def __init__(self) -> None:
        """Khởi tạo."""
        pass

    async def async_step_init(self, user_input=None):
        """Hiển thị form chỉnh sửa."""
        errors = {}

        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        # Lấy dữ liệu hiện tại (ưu tiên options nếu đã từng sửa, nếu không dùng data ban đầu)
        current_config = {**self.config_entry.data, **self.config_entry.options}

        return self.async_show_form(
            step_id="init",
            data_schema=_fan_schema(defaults=current_config),
            errors=errors,
        )
