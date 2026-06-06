"""Config Flow — giao diện UI để thêm/cấu hình quạt (4 Bước)."""
from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import selector
import homeassistant.helpers.config_validation as cv

from .const import (
    DOMAIN,
    CONF_FAN_NAME,
    CONF_FAN_ENTITY,
    CONF_SPEED_1_ENTITY,
    CONF_SPEED_2_ENTITY,
    CONF_SPEED_3_ENTITY,
    CONF_SPEED_4_ENTITY,
    CONF_TEMP_SENSOR,
    CONF_HUMIDITY_SENSOR,
    CONF_PRESENCE_SENSOR,
    CONF_AUTO_ON_ENABLED,
    CONF_AUTO_ON_THRESHOLD,
    DEFAULT_AUTO_ON_THRESHOLD,
    CONF_SMART_SPEED_ENABLED,
    CONF_SLEEP_MODE_ENABLED,
    CONF_NATURAL_WIND_ENABLED,
    CONF_QUIET_HOURS_ENABLED,
    CONF_QUIET_HOURS_START,
    CONF_QUIET_HOURS_END,
    CONF_AC_SYNC_ENABLED,
    CONF_AC_ENTITY,
)

# Helpers for schemas
def get_entity_selector(domain: str | list[str], device_class: str | None = None) -> selector.EntitySelector:
    config = {"domain": domain}
    if device_class:
        config["device_class"] = device_class
    return selector.EntitySelector(selector.EntitySelectorConfig(**config))

class SmartFanManagerConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Config Flow để thêm quạt mới vào Smart Fan Manager (4 bước)."""

    VERSION = 1

    def __init__(self):
        self._setup_data: dict[str, Any] = {}

    async def async_step_user(self, user_input=None):
        """Bước 1/4: Thiết lập quạt, tên, gán entity quạt và các nút tốc độ."""
        errors = {}

        if user_input is not None:
            # Kiểm tra entity tồn tại
            fan_state = self.hass.states.get(user_input[CONF_FAN_ENTITY])
            if fan_state is None:
                errors[CONF_FAN_ENTITY] = "entity_not_found"
            else:
                await self.async_set_unique_id(user_input[CONF_FAN_ENTITY])
                self._abort_if_unique_id_configured()

                self._setup_data.update(user_input)
                return await self.async_step_auto_on()

        schema = {
            vol.Required(CONF_FAN_NAME, default="Quạt phòng làm việc"): str,
            vol.Required(CONF_FAN_ENTITY): get_entity_selector("fan"),
            vol.Optional(CONF_SPEED_1_ENTITY): get_entity_selector(["button", "switch", "script", "scene", "input_boolean"]),
            vol.Optional(CONF_SPEED_2_ENTITY): get_entity_selector(["button", "switch", "script", "scene", "input_boolean"]),
            vol.Optional(CONF_SPEED_3_ENTITY): get_entity_selector(["button", "switch", "script", "scene", "input_boolean"]),
            vol.Optional(CONF_SPEED_4_ENTITY): get_entity_selector(["button", "switch", "script", "scene", "input_boolean"]),
        }

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(schema),
            errors=errors,
        )

    async def async_step_auto_on(self, user_input=None):
        """Bước 2/4: Tự động theo nhiệt độ."""
        errors = {}

        if user_input is not None:
            self._setup_data.update(user_input)
            return await self.async_step_advanced()

        schema = {
            vol.Required(CONF_TEMP_SENSOR): get_entity_selector("sensor", "temperature"),
            vol.Optional(CONF_HUMIDITY_SENSOR): get_entity_selector("sensor", "humidity"),
            vol.Optional(CONF_AUTO_ON_ENABLED, default=True): selector.BooleanSelector(),
            vol.Optional(CONF_PRESENCE_SENSOR): get_entity_selector("binary_sensor"),
            vol.Optional(CONF_AUTO_ON_THRESHOLD, default=DEFAULT_AUTO_ON_THRESHOLD): selector.NumberSelector(
                selector.NumberSelectorConfig(min=25, max=60, step=0.5, unit_of_measurement="°C (HI)")
            ),
        }

        return self.async_show_form(
            step_id="auto_on",
            data_schema=vol.Schema(schema),
            errors=errors,
        )

    async def async_step_advanced(self, user_input=None):
        """Bước 3/4: Tính năng thông minh."""
        errors = {}

        if user_input is not None:
            self._setup_data.update(user_input)
            return await self.async_step_ac_sync()

        schema = {
            vol.Optional(CONF_SMART_SPEED_ENABLED, default=False): selector.BooleanSelector(),
            vol.Optional(CONF_SLEEP_MODE_ENABLED, default=False): selector.BooleanSelector(),
            vol.Optional(CONF_NATURAL_WIND_ENABLED, default=False): selector.BooleanSelector(),
            vol.Optional(CONF_QUIET_HOURS_ENABLED, default=False): selector.BooleanSelector(),
            vol.Optional(CONF_QUIET_HOURS_START, default="23:00:00"): selector.TimeSelector(),
            vol.Optional(CONF_QUIET_HOURS_END, default="06:00:00"): selector.TimeSelector(),
        }

        return self.async_show_form(
            step_id="advanced",
            data_schema=vol.Schema(schema),
            errors=errors,
        )

    async def async_step_ac_sync(self, user_input=None):
        """Bước 4/4: Đồng bộ điều hòa."""
        errors = {}

        if user_input is not None:
            self._setup_data.update(user_input)
            return self.async_create_entry(
                title=self._setup_data[CONF_FAN_NAME],
                data=self._setup_data,
            )

        schema = {
            vol.Optional(CONF_AC_SYNC_ENABLED, default=True): selector.BooleanSelector(),
            vol.Optional(CONF_AC_ENTITY): get_entity_selector("climate"),
        }

        return self.async_show_form(
            step_id="ac_sync",
            data_schema=vol.Schema(schema),
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return SmartFanManagerOptionsFlow(config_entry)


class SmartFanManagerOptionsFlow(config_entries.OptionsFlow):
    """Options Flow — chỉnh sửa cấu hình quạt đã thêm (4 bước)."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        self.config_entry = config_entry
        self._options: dict[str, Any] = dict(config_entry.options)
        self._current_config = {**config_entry.data, **config_entry.options}

    async def async_step_init(self, user_input=None):
        """Khởi động Options Flow, chuyển tới Bước 1."""
        return await self.async_step_user()

    async def async_step_user(self, user_input=None):
        """Bước 1/4 (Options): Thiết lập quạt."""
        if user_input is not None:
            self._options.update(user_input)
            return await self.async_step_auto_on()

        defaults = self._current_config
        schema = {
            vol.Required(CONF_FAN_NAME, default=defaults.get(CONF_FAN_NAME, "Quạt phòng làm việc")): str,
        }

        fan_entity = defaults.get(CONF_FAN_ENTITY)
        schema[vol.Required(CONF_FAN_ENTITY, default=fan_entity)] = get_entity_selector("fan")

        for speed_conf in [CONF_SPEED_1_ENTITY, CONF_SPEED_2_ENTITY, CONF_SPEED_3_ENTITY, CONF_SPEED_4_ENTITY]:
            val = defaults.get(speed_conf)
            if val:
                schema[vol.Optional(speed_conf, default=val)] = get_entity_selector(["button", "switch", "script", "scene", "input_boolean"])
            else:
                schema[vol.Optional(speed_conf)] = get_entity_selector(["button", "switch", "script", "scene", "input_boolean"])

        return self.async_show_form(step_id="user", data_schema=vol.Schema(schema))

    async def async_step_auto_on(self, user_input=None):
        """Bước 2/4 (Options): Tự động theo nhiệt độ."""
        if user_input is not None:
            self._options.update(user_input)
            return await self.async_step_advanced()

        defaults = self._current_config
        schema = {}

        temp_sensor = defaults.get(CONF_TEMP_SENSOR)
        if temp_sensor:
            schema[vol.Required(CONF_TEMP_SENSOR, default=temp_sensor)] = get_entity_selector("sensor", "temperature")
        else:
            schema[vol.Required(CONF_TEMP_SENSOR)] = get_entity_selector("sensor", "temperature")

        for key, class_name in [(CONF_HUMIDITY_SENSOR, "humidity")]:
            val = defaults.get(key)
            if val:
                schema[vol.Optional(key, default=val)] = get_entity_selector("sensor", class_name)
            else:
                schema[vol.Optional(key)] = get_entity_selector("sensor", class_name)

        schema[vol.Optional(CONF_AUTO_ON_ENABLED, default=defaults.get(CONF_AUTO_ON_ENABLED, True))] = selector.BooleanSelector()

        p_sensor = defaults.get(CONF_PRESENCE_SENSOR)
        if p_sensor:
            schema[vol.Optional(CONF_PRESENCE_SENSOR, default=p_sensor)] = get_entity_selector("binary_sensor")
        else:
            schema[vol.Optional(CONF_PRESENCE_SENSOR)] = get_entity_selector("binary_sensor")

        schema[vol.Optional(CONF_AUTO_ON_THRESHOLD, default=defaults.get(CONF_AUTO_ON_THRESHOLD, DEFAULT_AUTO_ON_THRESHOLD))] = selector.NumberSelector(
            selector.NumberSelectorConfig(min=25, max=60, step=0.5, unit_of_measurement="°C (HI)")
        )

        return self.async_show_form(step_id="auto_on", data_schema=vol.Schema(schema))

    async def async_step_advanced(self, user_input=None):
        """Bước 3/4 (Options): Tính năng thông minh."""
        if user_input is not None:
            self._options.update(user_input)
            return await self.async_step_ac_sync()

        defaults = self._current_config
        schema = {
            vol.Optional(CONF_SMART_SPEED_ENABLED, default=defaults.get(CONF_SMART_SPEED_ENABLED, False)): selector.BooleanSelector(),
            vol.Optional(CONF_SLEEP_MODE_ENABLED, default=defaults.get(CONF_SLEEP_MODE_ENABLED, False)): selector.BooleanSelector(),
            vol.Optional(CONF_NATURAL_WIND_ENABLED, default=defaults.get(CONF_NATURAL_WIND_ENABLED, False)): selector.BooleanSelector(),
            vol.Optional(CONF_QUIET_HOURS_ENABLED, default=defaults.get(CONF_QUIET_HOURS_ENABLED, False)): selector.BooleanSelector(),
            vol.Optional(CONF_QUIET_HOURS_START, default=defaults.get(CONF_QUIET_HOURS_START, "23:00:00")): selector.TimeSelector(),
            vol.Optional(CONF_QUIET_HOURS_END, default=defaults.get(CONF_QUIET_HOURS_END, "06:00:00")): selector.TimeSelector(),
        }
        return self.async_show_form(step_id="advanced", data_schema=vol.Schema(schema))

    async def async_step_ac_sync(self, user_input=None):
        """Bước 4/4 (Options): Đồng bộ điều hòa."""
        if user_input is not None:
            self._options.update(user_input)
            return self.async_create_entry(title="", data=self._options)

        defaults = self._current_config
        schema = {
            vol.Optional(CONF_AC_SYNC_ENABLED, default=defaults.get(CONF_AC_SYNC_ENABLED, True)): selector.BooleanSelector(),
        }

        ac_entity = defaults.get(CONF_AC_ENTITY)
        if ac_entity:
            schema[vol.Optional(CONF_AC_ENTITY, default=ac_entity)] = get_entity_selector("climate")
        else:
            schema[vol.Optional(CONF_AC_ENTITY)] = get_entity_selector("climate")

        return self.async_show_form(step_id="ac_sync", data_schema=vol.Schema(schema))
