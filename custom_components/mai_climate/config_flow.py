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
    CONF_AUTO_OFF_ENABLED,
    CONF_AUTO_OFF_THRESHOLD,
    CONF_AUTO_OFF_CONSTRAINT,
    DEFAULT_AUTO_OFF_THRESHOLD,
    CONF_AC_NAME,
    CONF_WINDOW_SENSOR,
    CONF_SMART_SLEEP_ENABLED,
    CONF_WINDOW_GUARD_ENABLED,
    CONF_ECO_LEAVE_ENABLED,
    CONF_AUTO_DRY_ENABLED,
    CONF_PURIFIER_NAME,
    CONF_PURIFIER_ENTITY,
    CONF_PM25_SENSOR,
    CONF_VOC_SENSOR,
    CONF_KITCHEN_SENSOR,
    CONF_AUTO_BOOST_ENABLED,
    CONF_KITCHEN_SYNC_ENABLED,
    CONF_STRICT_QUIET_HOURS_ENABLED,
    DEVICE_TYPE_FAN,
    DEVICE_TYPE_AC,
    DEVICE_TYPE_PURIFIER,
    DEVICE_TYPE_VENTILATOR,
    CONF_DEVICE_TYPE,
)

# Helpers for schemas
def get_entity_selector(domain: str | None = None, device_class: str | None = None) -> selector.EntitySelector:
    config = {}
    if domain:
        config["domain"] = domain
    if device_class:
        config["device_class"] = device_class
    return selector.EntitySelector(selector.EntitySelectorConfig(**config))

class SmartFanManagerConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Config Flow để thêm quạt mới vào Smart Fan Manager (4 bước)."""

    VERSION = 1

    def __init__(self):
        self._setup_data: dict[str, Any] = {}

    async def async_step_user(self, user_input=None):
        """Bước 0: Chọn loại thiết bị để thiết lập."""
        from .const import DEVICE_TYPE_FAN, DEVICE_TYPE_AC, DEVICE_TYPE_PURIFIER, DEVICE_TYPE_VENTILATOR, CONF_DEVICE_TYPE

        errors = {}
        if user_input is not None:
            self._setup_data[CONF_DEVICE_TYPE] = user_input[CONF_DEVICE_TYPE]
            
            if user_input[CONF_DEVICE_TYPE] == DEVICE_TYPE_FAN:
                return await self.async_step_fan_setup()
            elif user_input[CONF_DEVICE_TYPE] == DEVICE_TYPE_AC:
                return await self.async_step_ac_setup()
            elif user_input[CONF_DEVICE_TYPE] == DEVICE_TYPE_PURIFIER:
                return await self.async_step_purifier_setup()
            elif user_input[CONF_DEVICE_TYPE] == DEVICE_TYPE_VENTILATOR:
                errors["base"] = "not_implemented_yet"

            if not errors:
                return await self.async_step_fan_setup()

        schema = {
            vol.Required(CONF_DEVICE_TYPE, default=DEVICE_TYPE_FAN): selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=[
                        {"value": DEVICE_TYPE_FAN, "label": "Quạt thông minh"},
                        {"value": DEVICE_TYPE_AC, "label": "Điều hòa nhiệt độ"},
                        {"value": DEVICE_TYPE_PURIFIER, "label": "Máy lọc không khí"},
                        {"value": DEVICE_TYPE_VENTILATOR, "label": "Quạt thông gió"},
                    ],
                    mode=selector.SelectSelectorMode.DROPDOWN,
                )
            )
        }

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(schema),
            errors=errors,
        )

    async def async_step_fan_setup(self, user_input=None):
        """Bước 1/4 (Quạt): Thiết lập quạt, tên, gán entity quạt và các nút tốc độ."""
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
            vol.Optional(CONF_SPEED_1_ENTITY): get_entity_selector(),
            vol.Optional(CONF_SPEED_2_ENTITY): get_entity_selector(),
            vol.Optional(CONF_SPEED_3_ENTITY): get_entity_selector(),
            vol.Optional(CONF_SPEED_4_ENTITY): get_entity_selector(),
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
            vol.Optional(CONF_AUTO_ON_THRESHOLD, default=DEFAULT_AUTO_ON_THRESHOLD): selector.NumberSelector(
                selector.NumberSelectorConfig(min=25, max=60, step=0.5, unit_of_measurement="°C (HI)")
            ),
            vol.Optional(CONF_PRESENCE_SENSOR): get_entity_selector("binary_sensor"),
            vol.Optional(CONF_AUTO_OFF_ENABLED, default=False): selector.BooleanSelector(),
            vol.Optional(CONF_AUTO_OFF_THRESHOLD, default=DEFAULT_AUTO_OFF_THRESHOLD): selector.NumberSelector(
                selector.NumberSelectorConfig(min=25, max=60, step=0.5, unit_of_measurement="°C (HI)")
            ),
            vol.Optional(CONF_AUTO_OFF_CONSTRAINT): get_entity_selector("binary_sensor"),
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

    async def async_step_ac_setup(self, user_input=None):
        """Bước 1/3 (Điều hòa): Chọn thiết bị và Đặt tên."""
        errors = {}

        if user_input is not None:
            ac_state = self.hass.states.get(user_input[CONF_AC_ENTITY])
            if ac_state is None:
                errors[CONF_AC_ENTITY] = "entity_not_found"
            else:
                await self.async_set_unique_id(user_input[CONF_AC_ENTITY])
                self._abort_if_unique_id_configured()

                self._setup_data.update(user_input)
                return await self.async_step_ac_auto_on()

        schema = {
            vol.Required(CONF_AC_NAME, default="Điều hòa phòng khách"): str,
            vol.Required(CONF_AC_ENTITY): get_entity_selector("climate"),
        }

        return self.async_show_form(
            step_id="ac_setup",
            data_schema=vol.Schema(schema),
            errors=errors,
        )

    async def async_step_ac_auto_on(self, user_input=None):
        """Bước 2/3 (Điều hòa): Tự động bật/tắt."""
        errors = {}

        if user_input is not None:
            self._setup_data.update(user_input)
            return await self.async_step_ac_advanced()

        schema = {
            vol.Required(CONF_TEMP_SENSOR): get_entity_selector("sensor", "temperature"),
            vol.Optional(CONF_HUMIDITY_SENSOR): get_entity_selector("sensor", "humidity"),
            vol.Optional(CONF_PRESENCE_SENSOR): get_entity_selector("binary_sensor", "occupancy"),
            vol.Optional(CONF_AUTO_ON_ENABLED, default=False): selector.BooleanSelector(),
            vol.Optional(CONF_AUTO_ON_THRESHOLD, default=32.0): selector.NumberSelector(
                selector.NumberSelectorConfig(min=20, max=40, step=0.5, unit_of_measurement="°C")
            ),
            vol.Optional(CONF_AUTO_OFF_ENABLED, default=False): selector.BooleanSelector(),
            vol.Optional(CONF_AUTO_OFF_THRESHOLD, default=25.0): selector.NumberSelector(
                selector.NumberSelectorConfig(min=16, max=30, step=0.5, unit_of_measurement="°C")
            ),
        }

        return self.async_show_form(
            step_id="ac_auto_on",
            data_schema=vol.Schema(schema),
            errors=errors,
        )

    async def async_step_ac_advanced(self, user_input=None):
        """Bước 3/3 (Điều hòa): Tính năng thông minh."""
        errors = {}

        if user_input is not None:
            self._setup_data.update(user_input)
            return self.async_create_entry(
                title=self._setup_data[CONF_AC_NAME],
                data=self._setup_data,
            )

        schema = {
            vol.Optional(CONF_SMART_SLEEP_ENABLED, default=True): selector.BooleanSelector(),
            vol.Optional(CONF_ECO_LEAVE_ENABLED, default=True): selector.BooleanSelector(),
            vol.Optional(CONF_AUTO_DRY_ENABLED, default=False): selector.BooleanSelector(),
            vol.Optional(CONF_WINDOW_GUARD_ENABLED, default=False): selector.BooleanSelector(),
            vol.Optional(CONF_WINDOW_SENSOR): get_entity_selector("binary_sensor", "window"),
        }

        return self.async_show_form(
            step_id="ac_advanced",
            data_schema=vol.Schema(schema),
            errors=errors,
        )

    # --- SETUP FLOW CHO MÁY LỌC KHÔNG KHÍ (PURIFIER) ---
    async def async_step_purifier_setup(self, user_input=None):
        """Bước 1/2 (Máy lọc): Thiết lập cơ bản & Cảm biến."""
        errors = {}

        if user_input is not None:
            purifier_state = self.hass.states.get(user_input[CONF_PURIFIER_ENTITY])
            if purifier_state is None:
                errors[CONF_PURIFIER_ENTITY] = "entity_not_found"
            else:
                await self.async_set_unique_id(user_input[CONF_PURIFIER_ENTITY])
                self._abort_if_unique_id_configured()

                self._setup_data.update(user_input)
                return await self.async_step_purifier_advanced()

        schema = {
            vol.Required(CONF_PURIFIER_NAME, default="Máy lọc không khí"): str,
            vol.Required(CONF_PURIFIER_ENTITY): get_entity_selector("fan"),
            vol.Optional(CONF_PM25_SENSOR): get_entity_selector("sensor", "pm25"),
            vol.Optional(CONF_VOC_SENSOR): get_entity_selector("sensor", "volatile_organic_compounds"),
        }

        return self.async_show_form(
            step_id="purifier_setup",
            data_schema=vol.Schema(schema),
            errors=errors,
        )

    async def async_step_purifier_advanced(self, user_input=None):
        """Bước 2/2 (Máy lọc): Tính năng thông minh."""
        errors = {}

        if user_input is not None:
            self._setup_data.update(user_input)
            return self.async_create_entry(
                title=self._setup_data[CONF_PURIFIER_NAME],
                data=self._setup_data,
            )

        schema = {
            vol.Optional(CONF_AUTO_BOOST_ENABLED, default=True): selector.BooleanSelector(),
            vol.Optional(CONF_KITCHEN_SYNC_ENABLED, default=False): selector.BooleanSelector(),
            vol.Optional(CONF_KITCHEN_SENSOR): get_entity_selector("switch"),
            vol.Optional(CONF_STRICT_QUIET_HOURS_ENABLED, default=False): selector.BooleanSelector(),
            vol.Optional(CONF_QUIET_HOURS_START, default="23:00:00"): selector.TimeSelector(),
            vol.Optional(CONF_QUIET_HOURS_END, default="06:00:00"): selector.TimeSelector(),
        }

        return self.async_show_form(
            step_id="purifier_advanced",
            data_schema=vol.Schema(schema),
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return SmartFanManagerOptionsFlow()


class SmartFanManagerOptionsFlow(config_entries.OptionsFlow):
    """Options Flow — chỉnh sửa cấu hình quạt đã thêm (4 bước)."""

    async def async_step_init(self, user_input=None):
        """Khởi động Options Flow, chuyển tới Bước 1 tương ứng thiết bị."""
        self._options = dict(self.config_entry.options)
        self._current_config = {**self.config_entry.data, **self.config_entry.options}
        
        device_type = self._current_config.get(CONF_DEVICE_TYPE, DEVICE_TYPE_FAN)
        if device_type == DEVICE_TYPE_AC:
            return await self.async_step_ac_setup()
        elif device_type == DEVICE_TYPE_PURIFIER:
            return await self.async_step_purifier_setup()
        return await self.async_step_user()

    # --- OPTIONS FLOW CHO QUẠT (FAN) ---
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
                schema[vol.Optional(speed_conf, default=val)] = get_entity_selector()
            else:
                schema[vol.Optional(speed_conf)] = get_entity_selector()

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

        schema[vol.Optional(CONF_AUTO_ON_THRESHOLD, default=defaults.get(CONF_AUTO_ON_THRESHOLD, DEFAULT_AUTO_ON_THRESHOLD))] = selector.NumberSelector(
            selector.NumberSelectorConfig(min=25, max=60, step=0.5, unit_of_measurement="°C (HI)")
        )

        p_sensor = defaults.get(CONF_PRESENCE_SENSOR)
        if p_sensor:
            schema[vol.Optional(CONF_PRESENCE_SENSOR, default=p_sensor)] = get_entity_selector("binary_sensor")
        else:
            schema[vol.Optional(CONF_PRESENCE_SENSOR)] = get_entity_selector("binary_sensor")

        schema[vol.Optional(CONF_AUTO_OFF_ENABLED, default=defaults.get(CONF_AUTO_OFF_ENABLED, False))] = selector.BooleanSelector()

        schema[vol.Optional(CONF_AUTO_OFF_THRESHOLD, default=defaults.get(CONF_AUTO_OFF_THRESHOLD, DEFAULT_AUTO_OFF_THRESHOLD))] = selector.NumberSelector(
            selector.NumberSelectorConfig(min=25, max=60, step=0.5, unit_of_measurement="°C (HI)")
        )

        off_constraint = defaults.get(CONF_AUTO_OFF_CONSTRAINT)
        if off_constraint:
            schema[vol.Optional(CONF_AUTO_OFF_CONSTRAINT, default=off_constraint)] = get_entity_selector("binary_sensor")
        else:
            schema[vol.Optional(CONF_AUTO_OFF_CONSTRAINT)] = get_entity_selector("binary_sensor")

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

    # --- OPTIONS FLOW CHO ĐIỀU HÒA (AC) ---
    async def async_step_ac_setup(self, user_input=None):
        """Bước 1/3 (Options AC): Thiết lập cơ bản."""
        if user_input is not None:
            self._options.update(user_input)
            return await self.async_step_ac_auto_on()

        defaults = self._current_config
        schema = {
            vol.Required(CONF_AC_NAME, default=defaults.get(CONF_AC_NAME, "Điều hòa phòng khách")): str,
        }

        ac_entity = defaults.get(CONF_AC_ENTITY)
        schema[vol.Required(CONF_AC_ENTITY, default=ac_entity)] = get_entity_selector("climate")

        return self.async_show_form(step_id="ac_setup", data_schema=vol.Schema(schema))

    async def async_step_ac_auto_on(self, user_input=None):
        """Bước 2/3 (Options AC): Tự động bật/tắt."""
        if user_input is not None:
            self._options.update(user_input)
            return await self.async_step_ac_advanced()

        defaults = self._current_config
        schema = {}

        temp_sensor = defaults.get(CONF_TEMP_SENSOR)
        if temp_sensor:
            schema[vol.Required(CONF_TEMP_SENSOR, default=temp_sensor)] = get_entity_selector("sensor", "temperature")
        else:
            schema[vol.Required(CONF_TEMP_SENSOR)] = get_entity_selector("sensor", "temperature")

        hum_sensor = defaults.get(CONF_HUMIDITY_SENSOR)
        if hum_sensor:
            schema[vol.Optional(CONF_HUMIDITY_SENSOR, default=hum_sensor)] = get_entity_selector("sensor", "humidity")
        else:
            schema[vol.Optional(CONF_HUMIDITY_SENSOR)] = get_entity_selector("sensor", "humidity")

        p_sensor = defaults.get(CONF_PRESENCE_SENSOR)
        if p_sensor:
            schema[vol.Optional(CONF_PRESENCE_SENSOR, default=p_sensor)] = get_entity_selector("binary_sensor", "occupancy")
        else:
            schema[vol.Optional(CONF_PRESENCE_SENSOR)] = get_entity_selector("binary_sensor", "occupancy")

        schema[vol.Optional(CONF_AUTO_ON_ENABLED, default=defaults.get(CONF_AUTO_ON_ENABLED, False))] = selector.BooleanSelector()
        schema[vol.Optional(CONF_AUTO_ON_THRESHOLD, default=defaults.get(CONF_AUTO_ON_THRESHOLD, 32.0))] = selector.NumberSelector(
            selector.NumberSelectorConfig(min=20, max=40, step=0.5, unit_of_measurement="°C")
        )
        schema[vol.Optional(CONF_AUTO_OFF_ENABLED, default=defaults.get(CONF_AUTO_OFF_ENABLED, False))] = selector.BooleanSelector()
        schema[vol.Optional(CONF_AUTO_OFF_THRESHOLD, default=defaults.get(CONF_AUTO_OFF_THRESHOLD, 25.0))] = selector.NumberSelector(
            selector.NumberSelectorConfig(min=16, max=30, step=0.5, unit_of_measurement="°C")
        )

        return self.async_show_form(step_id="ac_auto_on", data_schema=vol.Schema(schema))

    async def async_step_ac_advanced(self, user_input=None):
        """Bước 3/3 (Options AC): Tính năng thông minh."""
        if user_input is not None:
            self._options.update(user_input)
            return self.async_create_entry(title="", data=self._options)

        defaults = self._current_config
        schema = {
            vol.Optional(CONF_SMART_SLEEP_ENABLED, default=defaults.get(CONF_SMART_SLEEP_ENABLED, True)): selector.BooleanSelector(),
            vol.Optional(CONF_ECO_LEAVE_ENABLED, default=defaults.get(CONF_ECO_LEAVE_ENABLED, True)): selector.BooleanSelector(),
            vol.Optional(CONF_AUTO_DRY_ENABLED, default=defaults.get(CONF_AUTO_DRY_ENABLED, False)): selector.BooleanSelector(),
            vol.Optional(CONF_WINDOW_GUARD_ENABLED, default=defaults.get(CONF_WINDOW_GUARD_ENABLED, False)): selector.BooleanSelector(),
        }

        w_sensor = defaults.get(CONF_WINDOW_SENSOR)
        if w_sensor:
            schema[vol.Optional(CONF_WINDOW_SENSOR, default=w_sensor)] = get_entity_selector("binary_sensor", "window")
        else:
            schema[vol.Optional(CONF_WINDOW_SENSOR)] = get_entity_selector("binary_sensor", "window")

        return self.async_show_form(step_id="ac_advanced", data_schema=vol.Schema(schema))

    # --- OPTIONS FLOW CHO MÁY LỌC KHÔNG KHÍ (PURIFIER) ---
    async def async_step_purifier_setup(self, user_input=None):
        """Bước 1/2 (Options Máy lọc): Thiết lập cơ bản."""
        if user_input is not None:
            self._options.update(user_input)
            return await self.async_step_purifier_advanced()

        defaults = self._current_config
        schema = {
            vol.Required(CONF_PURIFIER_NAME, default=defaults.get(CONF_PURIFIER_NAME, "Máy lọc không khí")): str,
        }
        
        entity = defaults.get(CONF_PURIFIER_ENTITY)
        schema[vol.Required(CONF_PURIFIER_ENTITY, default=entity)] = get_entity_selector("fan")

        pm25 = defaults.get(CONF_PM25_SENSOR)
        if pm25:
            schema[vol.Optional(CONF_PM25_SENSOR, default=pm25)] = get_entity_selector("sensor", "pm25")
        else:
            schema[vol.Optional(CONF_PM25_SENSOR)] = get_entity_selector("sensor", "pm25")

        voc = defaults.get(CONF_VOC_SENSOR)
        if voc:
            schema[vol.Optional(CONF_VOC_SENSOR, default=voc)] = get_entity_selector("sensor", "volatile_organic_compounds")
        else:
            schema[vol.Optional(CONF_VOC_SENSOR)] = get_entity_selector("sensor", "volatile_organic_compounds")

        return self.async_show_form(step_id="purifier_setup", data_schema=vol.Schema(schema))

    async def async_step_purifier_advanced(self, user_input=None):
        """Bước 2/2 (Options Máy lọc): Tính năng thông minh."""
        if user_input is not None:
            self._options.update(user_input)
            return self.async_create_entry(title="", data=self._options)

        defaults = self._current_config
        schema = {
            vol.Optional(CONF_AUTO_BOOST_ENABLED, default=defaults.get(CONF_AUTO_BOOST_ENABLED, True)): selector.BooleanSelector(),
            vol.Optional(CONF_KITCHEN_SYNC_ENABLED, default=defaults.get(CONF_KITCHEN_SYNC_ENABLED, False)): selector.BooleanSelector(),
        }

        kitchen = defaults.get(CONF_KITCHEN_SENSOR)
        if kitchen:
            schema[vol.Optional(CONF_KITCHEN_SENSOR, default=kitchen)] = get_entity_selector("switch")
        else:
            schema[vol.Optional(CONF_KITCHEN_SENSOR)] = get_entity_selector("switch")

        schema.update({
            vol.Optional(CONF_STRICT_QUIET_HOURS_ENABLED, default=defaults.get(CONF_STRICT_QUIET_HOURS_ENABLED, False)): selector.BooleanSelector(),
            vol.Optional(CONF_QUIET_HOURS_START, default=defaults.get(CONF_QUIET_HOURS_START, "23:00:00")): selector.TimeSelector(),
            vol.Optional(CONF_QUIET_HOURS_END, default=defaults.get(CONF_QUIET_HOURS_END, "06:00:00")): selector.TimeSelector(),
        })

        return self.async_show_form(step_id="purifier_advanced", data_schema=vol.Schema(schema))
