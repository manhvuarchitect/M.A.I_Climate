"""Constants for Smart Fan Manager."""

DOMAIN = "mai_climate"

# Config entry keys
CONF_FAN_ENTITY = "fan_entity"
CONF_TEMP_SENSOR = "temp_sensor"
CONF_HUMIDITY_SENSOR = "humidity_sensor"
CONF_AC_ENTITY = "ac_entity"
CONF_PRESENCE_SENSOR = "presence_sensor"
CONF_AUTO_ON_THRESHOLD = "auto_on_threshold"
CONF_AUTO_ON_ENABLED = "auto_on_enabled"
CONF_FAN_NAME = "fan_name"
CONF_SMART_SPEED_ENABLED = "smart_speed_enabled"
CONF_SLEEP_MODE_ENABLED = "sleep_mode_enabled"
CONF_NATURAL_WIND_ENABLED = "natural_wind_enabled"
CONF_QUIET_HOURS_ENABLED = "quiet_hours_enabled"
CONF_QUIET_HOURS_START = "quiet_hours_start"
CONF_QUIET_HOURS_END = "quiet_hours_end"

# Default values
DEFAULT_AUTO_ON_THRESHOLD = 38  # Chỉ số oi bức tự động bật quạt
DEFAULT_SCAN_INTERVAL = 30       # Giây

# Timer presets (phút)
TIMER_PRESETS = {
    "15 minutes": 15,
    "30 minutes": 30,
    "45 minutes": 45,
    "60 minutes": 60,
    "90 minutes": 90,
    "120 minutes": 120,
}

# Muggy index thresholds
MUGGY_LOW = 30       # Dễ chịu
MUGGY_MEDIUM = 43    # Hơi oi
MUGGY_HIGH = 48      # Rất oi bức

# Service names
SERVICE_SET_TIMER = "set_timer"
SERVICE_CANCEL_TIMER = "cancel_timer"
SERVICE_SET_MODE = "set_mode"

# Modes
MODE_TIMER = "timer"
MODE_COOLDOWN = "cooldown"   # Giải nhiệt vận động
MODE_AUTO = "auto"
MODE_AC_HANDOFF = "ac_handoff" # Quạt luân chuyển khí khi tắt điều hòa
MODE_ECO_COOLING = "eco_cooling" # Trộn gió 15p khi bật điều hòa

# Entity suffixes
SUFFIX_MUGGY_SENSOR = "_muggy_index"
SUFFIX_TIMER_SENSOR = "_timer_remaining"
SUFFIX_COOLDOWN_SWITCH = "_cooldown_mode"
SUFFIX_AUTO_ON_SWITCH = "_auto_on_mode"
SUFFIX_THRESHOLD_NUMBER = "_auto_on_threshold"
SUFFIX_TIMER_SELECT = "_timer_preset"
SUFFIX_SMART_SPEED_SWITCH = "_smart_speed"
SUFFIX_SLEEP_MODE_SWITCH = "_sleep_mode"
SUFFIX_NATURAL_WIND_SWITCH = "_natural_wind"
SUFFIX_QUIET_HOURS_SWITCH = "_quiet_hours"

# Attributes
ATTR_MINUTES = "minutes"
ATTR_MODE = "mode"
ATTR_TARGET_FAN = "target_fan"
ATTR_MUGGY_INDEX = "muggy_index"
ATTR_TIMER_END = "timer_end"

# Icons
ICON_FAN = "mdi:fan"
ICON_TIMER = "mdi:fan-clock"
ICON_MUGGY = "mdi:thermometer-alert"
ICON_COOLDOWN = "mdi:run-fast"
ICON_THRESHOLD = "mdi:thermometer-chevron-up"
