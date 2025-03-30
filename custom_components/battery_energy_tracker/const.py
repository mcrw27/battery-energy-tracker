"""Constants for the Battery Energy Tracker integration."""

DOMAIN = "battery_energy_tracker"

# Configuration constants
CONF_BATTERY_COUNT = "battery_count"
CONF_CHARGE_RATE = "charge_rate"
CONF_ENTITY_PATTERNS = "entity_patterns"
CONF_SCALE_FACTOR = "scale_factor"
CONF_MANUAL_ENTITIES = "manual_entities"
CONF_STARTUP_DELAY = "startup_delay"
DEFAULT_CHARGE_RATE = 1500  # Watts (typical for Antra battery charging)
DEFAULT_SCALE_FACTOR = 0.1

# Counter limits
MAX_COUNTER_VALUE = 65535  # 16-bit counter limit
COUNTER_THRESHOLD = 65000  # Value close to rollover to watch for

# Sensor attributes
ATTR_TOTAL_DISCHARGE = "total_discharge"
ATTR_TOTAL_CHARGE = "total_charge"
ATTR_ESTIMATED_CHARGE_TIME = "estimated_charge_time"
ATTR_LAST_RESET = "last_reset"
ATTR_LAST_CHARGE_STARTED = "last_charge_started"
ATTR_LAST_CHARGE_COMPLETED = "last_charge_completed"
ATTR_CHARGE_DURATION = "last_charge_duration"
ATTR_ENERGY_SINCE_LAST_CHARGE = "energy_since_last_charge"

# Service constants
SERVICE_RESET_COUNTERS = "reset_counters"
SERVICE_RESET_ENERGY_SINCE_CHARGE = "reset_energy_since_charge"
SERVICE_SET_CHARGE_STATE = "set_charge_state"
SERVICE_ADJUST_COUNTERS = "adjust_counters"

# Service attributes
ATTR_IS_CHARGING = "is_charging"
ATTR_DISCHARGE_ADJUSTMENT = "discharge_adjustment"
ATTR_CHARGE_ADJUSTMENT = "charge_adjustment"