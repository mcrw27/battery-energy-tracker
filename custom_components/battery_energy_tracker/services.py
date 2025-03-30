"""Service methods for the Battery Energy Tracker integration."""
import logging
from typing import Optional
from homeassistant.util import dt as dt_util
import voluptuous as vol
from homeassistant.helpers import config_validation as cv

from .const import (
    DOMAIN,
    SERVICE_RESET_COUNTERS,
    SERVICE_RESET_ENERGY_SINCE_CHARGE,
    SERVICE_SET_CHARGE_STATE,
    SERVICE_ADJUST_COUNTERS,
    ATTR_IS_CHARGING,
    ATTR_DISCHARGE_ADJUSTMENT,
    ATTR_CHARGE_ADJUSTMENT,
)

_LOGGER = logging.getLogger(__name__)

# Service schema definitions
SET_BATTERY_STORED_ENERGY_SCHEMA = vol.Schema({
    vol.Required("battery_num"): cv.positive_int,
    vol.Required("energy_kwh"): vol.Coerce(float),
    vol.Optional("capacity_kwh"): vol.Coerce(float),
})

SET_BATTERY_TO_FULL_SCHEMA = vol.Schema({
    vol.Optional("battery_num"): cv.positive_int,
})

SET_BATTERY_CAPACITY_SCHEMA = vol.Schema({
    vol.Required("battery_num"): cv.positive_int,
    vol.Required("capacity_kwh"): vol.Coerce(float),
})

# Note: These functions will be attached to a class, so we use 'self' parameter
async def reset_counters(self):
    """Reset all counters to zero."""
    _LOGGER.info("Resetting all energy counters")
    self.total_discharge_counter = 0
    self.total_charge_counter = 0
    self.energy_since_last_charge_counter = 0
    self.total_discharge_kwh = 0.0
    self.total_charge_kwh = 0.0
    self.energy_since_last_charge = 0.0
    await self.async_refresh()
    
async def reset_energy_since_charge(self):
    """Reset energy since last charge counter."""
    _LOGGER.info("Resetting energy since last charge counter")
    self.energy_since_last_charge_counter = 0
    self.energy_since_last_charge = 0.0
    await self.async_refresh()
    
async def set_charge_state(self, is_charging: bool):
    """Manually set the charging state."""
    _LOGGER.info(f"Manually setting charge state to: {is_charging}")
    
    was_charging = self.is_charging
    self.is_charging = is_charging
    
    # Handle state transitions
    if is_charging and not was_charging:
        # Charging just started
        self.charge_start_time = dt_util.utcnow()
        _LOGGER.info("Charging started (manual) at %s", self.charge_start_time)
        
    elif not is_charging and was_charging:
        # Charging just ended
        charge_end_time = dt_util.utcnow()
        self.last_charge_completed = charge_end_time
        
        # Calculate charge duration
        if self.charge_start_time:
            self.last_charge_duration = (charge_end_time - self.charge_start_time).total_seconds() / 3600  # hours
            _LOGGER.info("Charging completed (manual). Duration: %.2f hours", self.last_charge_duration)
        
        self.charge_start_time = None
        
async def adjust_counters(self, discharge_adjustment: Optional[float] = None, charge_adjustment: Optional[float] = None):
    """Adjust the counter values."""
    if discharge_adjustment is not None:
        self.total_discharge_counter += discharge_adjustment
        # Recalculate kWh value
        self.total_discharge_kwh = self.total_discharge_counter * 0.001
        _LOGGER.info(f"Adjusted total discharge counter to {self.total_discharge_counter} ({self.total_discharge_kwh:.2f} kWh)")
        
    if charge_adjustment is not None:
        self.total_charge_counter += charge_adjustment
        # Recalculate kWh value
        self.total_charge_kwh = self.total_charge_counter * 0.001
        _LOGGER.info(f"Adjusted total charge counter to {self.total_charge_counter} ({self.total_charge_kwh:.2f} kWh)")
        
    await self.async_refresh()

# Service registration function
def register_services(hass):
    """Register services for the integration."""
    
    # Get the coordinator
    def get_coordinator():
        """Get the coordinator from hass data."""
        if not hass.data.get(DOMAIN):
            _LOGGER.error(f"Integration {DOMAIN} not initialized")
            return None
        return next(iter(hass.data[DOMAIN].values()))
    
    # Service handlers
    async def async_handle_reset_counters(service):
        """Handle reset_counters service."""
        coordinator = get_coordinator()
        if coordinator:
            await coordinator.reset_counters()
    
    async def async_handle_reset_energy_since_charge(service):
        """Handle reset_energy_since_charge service."""
        coordinator = get_coordinator()
        if coordinator:
            await coordinator.reset_energy_since_charge()
    
    async def async_handle_set_charge_state(service):
        """Handle set_charge_state service."""
        coordinator = get_coordinator()
        if coordinator:
            is_charging = service.data.get(ATTR_IS_CHARGING)
            await coordinator.set_charge_state(is_charging)
    
    async def async_handle_adjust_counters(service):
        """Handle adjust_counters service."""
        coordinator = get_coordinator()
        if coordinator:
            discharge_adjustment = service.data.get(ATTR_DISCHARGE_ADJUSTMENT)
            charge_adjustment = service.data.get(ATTR_CHARGE_ADJUSTMENT)
            await coordinator.adjust_counters(discharge_adjustment, charge_adjustment)
    
    async def async_handle_set_battery_stored_energy(service):
        """Handle the set_battery_stored_energy service call."""
        coordinator = get_coordinator()
        if coordinator:
            battery_num = service.data.get("battery_num")
            energy_kwh = service.data.get("energy_kwh")
            capacity_kwh = service.data.get("capacity_kwh")
            await coordinator.set_battery_stored_energy(battery_num, energy_kwh, capacity_kwh)

    async def async_handle_set_battery_to_full(service):
        """Handle the set_battery_to_full service call."""
        coordinator = get_coordinator()
        if coordinator:
            battery_num = service.data.get("battery_num")
            await coordinator.set_battery_to_full(battery_num)

    async def async_handle_set_battery_capacity(service):
        """Handle the set_battery_capacity service call."""
        coordinator = get_coordinator()
        if coordinator:
            battery_num = service.data.get("battery_num")
            capacity_kwh = service.data.get("capacity_kwh")
            await coordinator.set_battery_capacity(battery_num, capacity_kwh)
    
    # Register services
    hass.services.async_register(DOMAIN, SERVICE_RESET_COUNTERS, async_handle_reset_counters)
    hass.services.async_register(DOMAIN, SERVICE_RESET_ENERGY_SINCE_CHARGE, async_handle_reset_energy_since_charge)
    hass.services.async_register(DOMAIN, SERVICE_SET_CHARGE_STATE, async_handle_set_charge_state)
    hass.services.async_register(DOMAIN, SERVICE_ADJUST_COUNTERS, async_handle_adjust_counters)
    
    # Register services for energy storage tracking
    hass.services.async_register(
        DOMAIN, "set_battery_stored_energy", 
        async_handle_set_battery_stored_energy,
        schema=SET_BATTERY_STORED_ENERGY_SCHEMA
    )
    
    hass.services.async_register(
        DOMAIN, "set_battery_to_full", 
        async_handle_set_battery_to_full,
        schema=SET_BATTERY_TO_FULL_SCHEMA
    )
    
    hass.services.async_register(
        DOMAIN, "set_battery_capacity", 
        async_handle_set_battery_capacity,
        schema=SET_BATTERY_CAPACITY_SCHEMA
    )
    
    _LOGGER.info("Battery Energy Tracker services registered")