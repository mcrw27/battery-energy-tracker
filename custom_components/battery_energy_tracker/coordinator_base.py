"""Base coordinator for the Battery Energy Tracker integration."""
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple

from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.util import dt as dt_util
# Import event helpers directly as per deprecation warning
from homeassistant.helpers.event import async_call_later

from .const import (
    DOMAIN,
    MAX_COUNTER_VALUE,
    COUNTER_THRESHOLD,
    DEFAULT_SCALE_FACTOR,
)

_LOGGER = logging.getLogger(__name__)

class BatteryEnergyCoordinator(DataUpdateCoordinator):
    """Class to coordinate battery energy data."""
    
    def __init__(
        self, 
        hass: HomeAssistant, 
        battery_count: int, 
        charge_rate: float, 
        entity_patterns: Optional[Dict[str, str]] = None,
        scale_factor: float = DEFAULT_SCALE_FACTOR,
        manual_entities: Optional[Dict[str, List[str]]] = None,
    ):
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name="Battery Energy",
            update_interval=timedelta(seconds=60),  # Update every minute
        )
        
        self.hass = hass
        self.battery_count = battery_count
        self.charge_rate = charge_rate
        self.entity_patterns = entity_patterns or {}
        self.scale_factor = scale_factor  # Kept for backward compatibility
        self.manual_entities = manual_entities
        
        # Raw counter values - we'll store these without scaling
        self._discharge_counters = {}  # For discharge counters
        self._charge_counters = {}     # For charge counters
        
        # Total accumulated values (raw counter units)
        self.total_discharge_counter = 0
        self.total_charge_counter = 0
        
        # Computed energy values (for display and calculations)
        self.total_discharge_kwh = 0.0
        self.total_charge_kwh = 0.0
        
        # Status tracking
        self.is_charging = False
        self.charge_start_time = None
        self.last_charge_completed = None
        self.last_charge_duration = None
        self.energy_since_last_charge_counter = 0  # Raw counter units
        self.energy_since_last_charge = 0.0        # Computed kWh
        
        # Last known counter values for detecting rollovers
        self._last_discharge_values = {}
        self._last_charge_values = {}
        
        # For persistent storage
        self._store = None  # Will be initialized by init_storage
        self._last_saved_values = None  # To track changes for saving
        self._unsub_save_data = None  # For periodic saving
        
        # For charge rate tracking
        self.battery_charge_rates = {}  # Store charge rates for each battery
        self.historic_charge_rates = []  # For time-weighted average
        self.total_charge_rate = 0  # Total charge rate across all batteries
        self.charge_rate_data = {}  # For diagnostics
        self.last_counter_check = None  # For counter-based rate calculation
        
        # Store detected entity mappings
        self.detected_entities = {
            'discharge': [],
            'charge': [],
            'current': []
        }
        
        # Track first run and retry count
        self._first_run = True
        self._retry_count = 0
        self._max_retries = 10
        
        # For energy storage tracking
        self.battery_stored_energy = {}  # Dict to store energy level for each battery
        self.battery_capacities = {}     # Dict to store capacity for each battery
        self.total_stored_energy = 0.0   # Total energy stored across all batteries
        self.total_stored_energy_percent = 0.0  # Percentage of total capacity

        # Log initialization
        _LOGGER.info(
            f"Initializing battery energy coordinator with {battery_count} batteries, "
            f"charge rate {charge_rate}W"
        )
        
    async def _async_update_data(self):
        """Fetch latest data from the battery system."""
        _LOGGER.debug("Updating battery energy data")
        
        # Calculate derived values from raw counters
        # A conversion factor of 0.001 is approximately 1 counter unit = 1 Wh
        # We can adjust this if needed
        conversion_factor = 0.001
        
        # Calculate kWh values for display
        self.total_discharge_kwh = self.total_discharge_counter * conversion_factor
        self.total_charge_kwh = self.total_charge_counter * conversion_factor
        self.energy_since_last_charge = self.energy_since_last_charge_counter * conversion_factor
        
        data = {
            "total_discharge_counter": self.total_discharge_counter,
            "total_charge_counter": self.total_charge_counter,
            "total_discharge_kwh": self.total_discharge_kwh,
            "total_charge_kwh": self.total_charge_kwh,
            "energy_since_last_charge_counter": self.energy_since_last_charge_counter,
            "energy_since_last_charge": self.energy_since_last_charge,
            "is_charging": self.is_charging,
            "charge_start_time": self.charge_start_time,
            "last_charge_completed": self.last_charge_completed,
            "last_charge_duration": self.last_charge_duration,
            "estimated_charge_time": self.get_estimated_charge_time(),
            "total_charge_rate": self.total_charge_rate,
            "charge_rate_data": self.charge_rate_data,
            "battery_stored_energy": self.battery_stored_energy,
            "battery_capacities": self.battery_capacities,
            "total_stored_energy": self.total_stored_energy,
            "total_stored_energy_percent": self.total_stored_energy_percent,
        }
        
        # First, ensure we have detected entities
        if not any(self.detected_entities.values()):
            _LOGGER.info("No entities detected yet, running auto-detection")
            self.detected_entities = await self.auto_detect_entities()
        
        # Next, check if entities are available in state machine
        available_entities = await self._check_entities_available()
        if not available_entities and self._retry_count < self._max_retries:
            _LOGGER.warning(f"Entities not yet available in state machine (retry {self._retry_count+1}/{self._max_retries})")
            self._retry_count += 1
            
            # Schedule a retry in 30 seconds
            async def retry_update(now=None):
                _LOGGER.info("Attempting entity refresh...")
                await self.async_refresh()
            
            # Fixed: use imported async_call_later instead of self.hass.helpers.event.async_call_later
            async_call_later(self.hass, 30, retry_update)
        elif not available_entities:
            _LOGGER.error(f"Entities still not available after {self._max_retries} retries")
        else:
            self._retry_count = 0  # Reset retry count on success
        
        # Update discharge/charge counters based on current state
        await self._update_counters()
        
        # Update charging status
        await self._update_charging_status()
        
        # Update charge rates
        if self.is_charging:
            await self._update_charge_rates()
            
        # Update stored energy calculations
        await self.update_stored_energy()
        
        # Diagnostics
        data["diagnostics"] = await self.diagnostic_check()
        
        # Save data if significant changes
        if hasattr(self, "save_data") and self._store is not None:
            if self._changes_since_last_save():
                await self.save_data()
        
        # Log summary of current state
        _LOGGER.debug(
            f"Updated state: total_discharge_counter={self.total_discharge_counter}, "
            f"total_charge_counter={self.total_charge_counter}, "
            f"total_discharge={self.total_discharge_kwh:.2f}kWh, "
            f"total_charge={self.total_charge_kwh:.2f}kWh, "
            f"is_charging={self.is_charging}, "
            f"energy_since_last_charge={self.energy_since_last_charge:.2f}kWh"
        )
        
        return data
    
    def _changes_since_last_save(self):
        """Check if there have been significant changes since last save."""
        if not self._last_saved_values:
            self._last_saved_values = {
                "discharge": self.total_discharge_counter,
                "charge": self.total_charge_counter
            }
            return True
            
        # Check if counters have changed significantly
        discharge_change = abs(self.total_discharge_counter - self._last_saved_values["discharge"])
        charge_change = abs(self.total_charge_counter - self._last_saved_values["charge"])
        
        # Update last saved values
        self._last_saved_values = {
            "discharge": self.total_discharge_counter,
            "charge": self.total_charge_counter
        }
        
        # Save if there's been a significant change (more than 10 counter units)
        return discharge_change > 10 or charge_change > 10
    
    async def _check_entities_available(self):
        """Check if entities are available in state machine."""
        all_available = True
        
        for entity_type, entities in self.detected_entities.items():
            for battery_num, entity_id in entities:
                state = self.hass.states.get(entity_id)
                if state is None or state.state == "unavailable":
                    _LOGGER.debug(f"{entity_type} entity {entity_id} for battery {battery_num} not available in state machine")
                    all_available = False
                else:
                    _LOGGER.debug(f"{entity_type} entity {entity_id} for battery {battery_num} is available with state {state.state}")
        
        return all_available
    
    async def _async_save_state(self, now=None):
        """Save current state to persistent storage."""
        self._last_stored_totals = {
            'discharge_counter': self.total_discharge_counter,
            'charge_counter': self.total_charge_counter,
            'last_charge_completed': self.last_charge_completed,
            'last_charge_duration': self.last_charge_duration,
        }
        # This would use Home Assistant's storage system
    
    async def _restore_state(self):
        """Restore previous tracker state from storage."""
        # This would use Home Assistant's RestoreEntity mechanism
        # For now, simplified implementation
        self.total_discharge_counter = self._last_stored_totals['discharge_counter']
        self.total_charge_counter = self._last_stored_totals['charge_counter']
        self.last_charge_completed = self._last_stored_totals['last_charge_completed']
        self.last_charge_duration = self._last_stored_totals['last_charge_duration']
        
    def get_estimated_charge_time(self) -> Optional[float]:
        """Estimate time needed to recharge battery based on energy discharged."""
        # Convert counter units to kWh for calculation
        # Using approximate conversion factor of 0.001 (1 unit ≈ 1 Wh)
        energy_kwh = self.energy_since_last_charge_counter * 0.001
        
        if energy_kwh <= 0:
            return 0
            
        # Use calculated charge rate if available and we're charging,
        # otherwise use configured rate
        if self.is_charging and self.total_charge_rate > 100:
            charge_rate_watts = self.total_charge_rate
            _LOGGER.debug(f"Using calculated charge rate for estimate: {charge_rate_watts:.2f}W")
        else:
            charge_rate_watts = self.charge_rate
            _LOGGER.debug(f"Using configured charge rate for estimate: {charge_rate_watts:.2f}W")
        
        # Calculate time in hours
        estimated_hours = energy_kwh * 1000 / charge_rate_watts
        
        # Apply some real-world adjustment factor (batteries charge slower as they fill)
        adjustment_factor = 1.2  # 20% buffer for real-world charging
        return estimated_hours * adjustment_factor

    def is_currently_charging(self) -> bool:
        """Return whether the battery is currently charging."""
        return self.is_charging

    def get_charge_status(self) -> str:
        """Get the current charging status with details."""
        if self.is_charging:
            if self.charge_start_time:
                elapsed = (dt_util.utcnow() - self.charge_start_time).total_seconds() / 60  # minutes
                return f"Charging (elapsed: {elapsed:.0f} min)"
            return "Charging"
        return "Not Charging"
    
    def get_energy_since_last_charge(self) -> float:
        """Get energy used since last completed charge in kWh."""
        # Convert counter to kWh using approximate conversion factor
        return self.energy_since_last_charge_counter * 0.001