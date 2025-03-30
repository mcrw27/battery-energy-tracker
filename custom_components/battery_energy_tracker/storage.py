"""Storage implementation for the Battery Energy Tracker integration."""
import logging
import json
import os
from datetime import timedelta
from homeassistant.helpers.storage import Store
from homeassistant.util import dt as dt_util

_LOGGER = logging.getLogger(__name__)

# Storage version and key
STORAGE_VERSION = 1
STORAGE_KEY = "battery_energy_tracker.{entry_id}"

# Helper methods to be attached to the coordinator class
async def save_data(self):
    """Save energy tracker data to persistent storage."""
    data = {
        "discharge_counter": self.total_discharge_counter,
        "charge_counter": self.total_charge_counter,
        "discharge_kwh": self.total_discharge_kwh,
        "charge_kwh": self.total_charge_kwh,
        "energy_since_last_charge_counter": self.energy_since_last_charge_counter,
        "energy_since_last_charge": self.energy_since_last_charge,
        "is_charging": self.is_charging,
        "last_charge_completed": self.last_charge_completed.isoformat() if self.last_charge_completed else None,
        "last_charge_duration": self.last_charge_duration,
        "charge_start_time": self.charge_start_time.isoformat() if self.charge_start_time else None,
        "battery_stored_energy": self.battery_stored_energy,
        "battery_capacities": self.battery_capacities,
        "total_stored_energy": self.total_stored_energy,
        "total_stored_energy_percent": self.total_stored_energy_percent,
        "last_discharge_values": self._last_discharge_values,
        "last_charge_values": self._last_charge_values,
        "save_time": dt_util.utcnow().isoformat(),
    }
    
    try:
        _LOGGER.debug("Saving energy tracker data to storage")
        await self._store.async_save(data)
        _LOGGER.info("Energy tracker data saved successfully")
    except Exception as ex:
        _LOGGER.error(f"Error saving energy tracker data: {ex}")

async def load_data(self):
    """Load energy tracker data from persistent storage."""
    try:
        stored_data = await self._store.async_load()
        
        if not stored_data:
            _LOGGER.info("No stored energy tracker data found")
            return False
            
        _LOGGER.info(f"Loading stored energy tracker data (saved at {stored_data.get('save_time')})")
        
        # Restore counters and energy values
        self.total_discharge_counter = stored_data.get("discharge_counter", 0)
        self.total_charge_counter = stored_data.get("charge_counter", 0)
        self.total_discharge_kwh = stored_data.get("discharge_kwh", 0)
        self.total_charge_kwh = stored_data.get("charge_kwh", 0)
        
        # Restore charge status
        self.energy_since_last_charge_counter = stored_data.get("energy_since_last_charge_counter", 0)
        self.energy_since_last_charge = stored_data.get("energy_since_last_charge", 0)
        self.is_charging = stored_data.get("is_charging", False)
        
        # Restore timestamps with proper conversion
        last_charge_completed = stored_data.get("last_charge_completed")
        self.last_charge_completed = dt_util.parse_datetime(last_charge_completed) if last_charge_completed else None
        
        charge_start_time = stored_data.get("charge_start_time")
        self.charge_start_time = dt_util.parse_datetime(charge_start_time) if charge_start_time else None
        
        self.last_charge_duration = stored_data.get("last_charge_duration")
        
        # Restore battery energy storage data
        self.battery_stored_energy = stored_data.get("battery_stored_energy", {})
        self.battery_capacities = stored_data.get("battery_capacities", {})
        self.total_stored_energy = stored_data.get("total_stored_energy", 0)
        self.total_stored_energy_percent = stored_data.get("total_stored_energy_percent", 0)
        
        # Restore last known counter values for detecting rollovers
        self._last_discharge_values = stored_data.get("last_discharge_values", {})
        self._last_charge_values = stored_data.get("last_charge_values", {})
        
        # Convert string keys back to integers for dictionaries
        self._convert_string_keys(self.battery_stored_energy)
        self._convert_string_keys(self.battery_capacities)
        self._convert_string_keys(self._last_discharge_values)
        self._convert_string_keys(self._last_charge_values)
        
        _LOGGER.info(
            f"Restored state: total_discharge={self.total_discharge_kwh:.2f}kWh, "
            f"total_charge={self.total_charge_kwh:.2f}kWh, "
            f"energy_since_last_charge={self.energy_since_last_charge:.2f}kWh"
        )
        
        return True
    except Exception as ex:
        _LOGGER.error(f"Error loading energy tracker data: {ex}")
        return False
        
def _convert_string_keys(self, dict_obj):
    """Convert string keys to integers in a dictionary."""
    if not dict_obj or not isinstance(dict_obj, dict):
        return
        
    # Create a list of keys to avoid modifying dictionary during iteration
    keys = list(dict_obj.keys())
    
    for key in keys:
        if isinstance(key, str) and key.isdigit():
            # Convert string key to integer
            dict_obj[int(key)] = dict_obj.pop(key)

# Function to initialize storage in coordinator
async def init_storage(self, config_entry):
    """Initialize the storage system."""
    # Create a unique storage key based on the config entry ID
    storage_key = STORAGE_KEY.format(entry_id=config_entry.entry_id)
    
    # Create the store instance
    self._store = Store(self.hass, STORAGE_VERSION, storage_key)
    
    # Load existing data from storage
    loaded = await self.load_data()
    
    # Set up periodic saving
    _LOGGER.info("Setting up periodic data saving every 15 minutes")
    
    async def _save_data_handler(now=None):
        """Handle periodic data saving."""
        await self.save_data()
        
    # Schedule periodic saving
    from homeassistant.helpers.event import async_track_time_interval
    self._unsub_save_data = async_track_time_interval(
        self.hass, _save_data_handler, timedelta(minutes=15)
    )
    
    return loaded

# Update the async_unload_entry function to clean up storage
async def _clean_up_storage(self):
    """Clean up storage related resources."""
    # Save data one last time before unloading
    await self.save_data()
    
    # Unsubscribe from the periodic saving interval
    if hasattr(self, "_unsub_save_data") and self._unsub_save_data:
        self._unsub_save_data()
        self._unsub_save_data = None