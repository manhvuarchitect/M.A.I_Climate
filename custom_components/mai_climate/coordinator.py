"""Coordinator for Smart Fan Manager - handles all logic."""
from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.helpers.event import async_track_state_change_event, async_call_later
from homeassistant.util.dt import utcnow

from .const import (
    DOMAIN,
    CONF_FAN_ENTITY,
    CONF_TEMP_SENSOR,
    CONF_HUMIDITY_SENSOR,
    CONF_AC_ENTITY,
    CONF_AC_SYNC_ENABLED,
    CONF_PRESENCE_SENSOR,
    CONF_AUTO_ON_THRESHOLD,
    CONF_AUTO_ON_ENABLED,
    DEFAULT_AUTO_ON_THRESHOLD,
    DEFAULT_SCAN_INTERVAL,
    MODE_TIMER,
    MODE_COOLDOWN,
    MODE_AUTO,
    MODE_AC_HANDOFF,
    MODE_ECO_COOLING,
)

_LOGGER = logging.getLogger(__name__)


class SmartFanCoordinator(DataUpdateCoordinator):
    """Quản lý toàn bộ logic cho một quạt."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Khởi tạo coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_{entry.entry_id}",
            update_interval=timedelta(seconds=DEFAULT_SCAN_INTERVAL),
        )
        self.entry = entry
        self.hass = hass

        # Config - Ưu tiên lấy từ options nếu đã chỉnh sửa
        config = {**entry.data, **entry.options}
        self.fan_entity: str = config[CONF_FAN_ENTITY]
        self.temp_sensor: str = config[CONF_TEMP_SENSOR]
        self.humidity_sensor: str = config.get(CONF_HUMIDITY_SENSOR, "")
        self.ac_entity: str = config.get(CONF_AC_ENTITY, "")
        self.presence_sensor: str = config.get(CONF_PRESENCE_SENSOR, "")
        self.ac_sync_enabled: bool = config.get(CONF_AC_SYNC_ENABLED, True)
        self.auto_on_enabled: bool = config.get(CONF_AUTO_ON_ENABLED, True)
        self.auto_on_threshold: float = config.get(
            CONF_AUTO_ON_THRESHOLD, DEFAULT_AUTO_ON_THRESHOLD
        )

        # State
        self.muggy_index: float = 0.0
        self.timer_end: datetime | None = None
        self.current_mode: str | None = None
        self.cooldown_active: bool = False
        self._timer_cancel = None
        self._unsub_listeners: list = []

    async def _async_update_data(self) -> dict[str, Any]:
        """Cập nhật dữ liệu định kỳ."""
        self._calculate_muggy_index()
        await self._check_auto_on()
        return self._build_state()

    def _calculate_muggy_index(self) -> None:
        """Tính chỉ số oi bức từ nhiệt độ và độ ẩm.

        Công thức Heat Index (Steadman 1979, đơn vị Celsius):
        HI = -8.78 + 1.61*T + 2.34*RH - 0.146*T*RH
             - 0.012*T² - 0.016*RH² + 0.00221*T²*RH
             + 0.00072*T*RH² - 0.000003583*T²*RH²
        """
        temp_state = self.hass.states.get(self.temp_sensor)
        if not temp_state or temp_state.state in ("unknown", "unavailable"):
            return

        try:
            T = float(temp_state.state)
        except ValueError:
            return

        # Nếu không có cảm biến độ ẩm, ước tính 70%
        RH = 70.0
        if self.humidity_sensor:
            hum_state = self.hass.states.get(self.humidity_sensor)
            if hum_state and hum_state.state not in ("unknown", "unavailable"):
                try:
                    RH = float(hum_state.state)
                except ValueError:
                    pass

        if T < 27:
            # Dưới ngưỡng này heat index không áp dụng, dùng trực tiếp
            self.muggy_index = T
            return

        HI = (
            -8.78
            + 1.61 * T
            + 2.34 * RH
            - 0.146 * T * RH
            - 0.012 * T**2
            - 0.016 * RH**2
            + 0.00221 * T**2 * RH
            + 0.00072 * T * RH**2
            - 0.000003583 * T**2 * RH**2
        )
        self.muggy_index = round(HI, 1)

    async def _check_auto_on(self) -> None:
        """Tự động bật/tắt quạt theo chỉ số oi bức và cảm biến hiện diện."""
        if not self.auto_on_enabled:
            return

        fan_state = self.hass.states.get(self.fan_entity)
        is_fan_on = fan_state is not None and fan_state.state != "off"

        # Kiểm tra cảm biến hiện diện
        presence = True
        if self.presence_sensor:
            p_state = self.hass.states.get(self.presence_sensor)
            if p_state and p_state.state == "off":
                presence = False

        if self.muggy_index >= self.auto_on_threshold and presence:
            if not is_fan_on:
                _LOGGER.info(
                    "Auto-on: Nhiệt độ %.1f >= %.1f và Có người -> Bật %s",
                    self.muggy_index,
                    self.auto_on_threshold,
                    self.fan_entity,
                )
                await self.hass.services.async_call(
                    "fan", "turn_on", {"entity_id": self.fan_entity}
                )
        elif not presence:
            if is_fan_on:
                _LOGGER.info(
                    "Auto-off: Không có người -> Tắt %s", self.fan_entity
                )
                # Xoá timer nếu có
                await self.async_cancel_timer()
                await self.hass.services.async_call(
                    "fan", "turn_off", {"entity_id": self.fan_entity}
                )

    def _build_state(self) -> dict[str, Any]:
        """Tổng hợp state hiện tại."""
        remaining = None
        if self.timer_end:
            delta = (self.timer_end - utcnow()).total_seconds()
            remaining = max(0, int(delta))
            if remaining == 0:
                self.timer_end = None
                self.current_mode = None

        return {
            "muggy_index": self.muggy_index,
            "timer_remaining": remaining,
            "current_mode": self.current_mode,
            "cooldown_active": self.cooldown_active,
            "auto_on_threshold": self.auto_on_threshold,
            "auto_on_enabled": self.auto_on_enabled,
            "ac_sync_enabled": self.ac_sync_enabled,
        }

    async def async_set_timer(self, minutes: int, mode: str = MODE_TIMER) -> None:
        """Bật quạt và đặt timer tắt sau N phút."""
        # Hủy timer cũ nếu có
        await self.async_cancel_timer()

        # Bật quạt
        await self.hass.services.async_call(
            "fan", "turn_on", {"entity_id": self.fan_entity}
        )

        self.timer_end = utcnow() + timedelta(minutes=minutes)
        self.current_mode = mode
        _LOGGER.info("Timer đặt: %d phút, mode: %s", minutes, mode)

        # Đặt callback tắt quạt sau đúng thời gian
        delay = minutes * 60

        @callback
        def _timer_expired(_now):
            self.hass.async_create_task(self._async_timer_expired())

        self._timer_cancel = async_call_later(self.hass, delay, _timer_expired)
        await self.async_refresh()

    async def _async_timer_expired(self) -> None:
        """Callback khi timer hết giờ."""
        _LOGGER.info("Timer hết giờ — tắt %s", self.fan_entity)
        await self.hass.services.async_call(
            "fan", "turn_off", {"entity_id": self.fan_entity}
        )
        self.timer_end = None
        self.current_mode = None
        self._timer_cancel = None
        await self.async_refresh()

    async def async_cancel_timer(self) -> None:
        """Hủy timer đang chạy."""
        if self._timer_cancel:
            self._timer_cancel()
            self._timer_cancel = None
        self.timer_end = None
        self.current_mode = None
        await self.async_refresh()

    async def async_set_cooldown_mode(self, active: bool) -> None:
        """Bật/tắt chế độ giải nhiệt vận động (30 phút)."""
        self.cooldown_active = active
        if active:
            await self.async_set_timer(minutes=30, mode=MODE_COOLDOWN)
        else:
            await self.async_cancel_timer()
            await self.hass.services.async_call(
                "fan", "turn_off", {"entity_id": self.fan_entity}
            )

    async def async_update_threshold(self, threshold: float) -> None:
        """Cập nhật ngưỡng auto-on."""
        self.auto_on_threshold = threshold
        # Lưu vào options để persist
        self.hass.config_entries.async_update_entry(
            self.entry,
            options={**self.entry.options, CONF_AUTO_ON_THRESHOLD: threshold},
        )
        await self.async_refresh()

    async def async_set_auto_on_enabled(self, enabled: bool) -> None:
        """Bật/tắt tính năng Auto-on."""
        self.auto_on_enabled = enabled
        self.hass.config_entries.async_update_entry(
            self.entry,
            options={**self.entry.options, CONF_AUTO_ON_ENABLED: enabled},
        )
        if enabled:
            # Check ngay lập tức
            await self._check_auto_on()
        await self.async_refresh()

    async def async_set_ac_sync_enabled(self, enabled: bool) -> None:
        """Bật/tắt tính năng đồng bộ điều hòa."""
        self.ac_sync_enabled = enabled
        self.hass.config_entries.async_update_entry(
            self.entry,
            options={**self.entry.options, CONF_AC_SYNC_ENABLED: enabled},
        )
        await self.async_refresh()

    async def async_setup(self) -> None:
        """Thiết lập listeners theo dõi thay đổi sensor."""

        @callback
        def _sensor_changed(event):
            self.hass.async_create_task(self.async_refresh())

        # Lắng nghe thay đổi từ sensor nhiệt độ & độ ẩm
        entities_to_watch = [self.temp_sensor]
        if self.humidity_sensor:
            entities_to_watch.append(self.humidity_sensor)

        self._unsub_listeners.append(
            async_track_state_change_event(
                self.hass, entities_to_watch, _sensor_changed
            )
        )

        # Lắng nghe thay đổi cảm biến hiện diện
        if self.presence_sensor:
            @callback
            def _presence_changed(event):
                # Trigger cập nhật ngay lập tức để xử lý bật/tắt
                self.hass.async_create_task(self.async_refresh())

            self._unsub_listeners.append(
                async_track_state_change_event(
                    self.hass, [self.presence_sensor], _presence_changed
                )
            )

        # Lắng nghe thay đổi từ điều hòa (nếu có)
        if self.ac_entity:
            @callback
            def _ac_state_changed(event):
                if not self.ac_sync_enabled:
                    return

                old_state = event.data.get("old_state")
                new_state = event.data.get("new_state")
                if not old_state or not new_state:
                    return

                old_val = old_state.state
                new_val = new_state.state

                if old_val == new_val:
                    return

                # AC Handoff: Điều hòa tắt
                if old_val != "off" and new_val == "off":
                    _LOGGER.info("AC turned off. Bật quạt luân chuyển gió (AC Handoff) 30 phút.")
                    self.hass.async_create_task(
                        self.async_set_timer(minutes=30, mode=MODE_AC_HANDOFF)
                    )

                # Eco-Cooling: Điều hòa bật
                elif old_val == "off" and new_val != "off":
                    _LOGGER.info("AC turned on. Bật quạt trộn khí (Eco-Cooling) 15 phút.")
                    self.hass.async_create_task(
                        self.async_set_timer(minutes=15, mode=MODE_ECO_COOLING)
                    )

            self._unsub_listeners.append(
                async_track_state_change_event(
                    self.hass, [self.ac_entity], _ac_state_changed
                )
            )

    async def async_unload(self) -> None:
        """Dọn dẹp khi unload entry."""
        for unsub in self._unsub_listeners:
            unsub()
        self._unsub_listeners.clear()
        if self._timer_cancel:
            self._timer_cancel()
