"""The Battery Energy Tracker integration."""
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.const import Platform
from homeassistant.helpers import config_validation as cv
import voluptuous as vol

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

# Define the platforms we support
PLATFORMS = [Platform.SENSOR]

# Define CONFIG_SCHEMA since we're using config_entries
CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Set up the Battery Energy Tracker component."""
    hass.data.setdefault(DOMAIN, {})
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Battery Energy Tracker from a config entry."""
    # Import coordinator to ensure methods are attached
    from .coordinator_base import BatteryEnergyCoordinator
    from . import coordinator
    from . import storage  # Import the storage module
    
    # Get configuration
    config = entry.data
    
    # Create coordinator instance
    battery_tracker = BatteryEnergyCoordinator(
        hass,
        config.get("battery_count", 4),
        config.get("charge_rate", 1500),
        config.get("entity_patterns"),
        config.get("scale_factor", 0.1),
        config.get("manual_entities"),
    )
    
    # Attach storage methods to coordinator
    battery_tracker.save_data = storage.save_data.__get__(battery_tracker)
    battery_tracker.load_data = storage.load_data.__get__(battery_tracker)
    battery_tracker._convert_string_keys = storage._convert_string_keys.__get__(battery_tracker)
    battery_tracker.init_storage = storage.init_storage.__get__(battery_tracker)
    battery_tracker._clean_up_storage = storage._clean_up_storage.__get__(battery_tracker)
    
    # Initialize storage and load saved data
    await battery_tracker.init_storage(entry)
    
    # Initialize coordinator
    await battery_tracker.async_config_entry_first_refresh()
    
    # Store for later use
    hass.data[DOMAIN][entry.entry_id] = battery_tracker
    
    # Set up all supported platforms
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    
    # Register services
    from .services import register_services
    register_services(hass)  # Call directly instead of using async_add_executor_job
    
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    
    if unload_ok:
        # Clean up storage before removing
        coordinator = hass.data[DOMAIN][entry.entry_id]
        await coordinator._clean_up_storage()
        
        # Remove the coordinator
        hass.data[DOMAIN].pop(entry.entry_id)
    
    return unload_ok