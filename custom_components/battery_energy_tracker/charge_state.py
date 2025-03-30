"""Charge state tracking for the Battery Energy Tracker integration."""
import logging
from datetime import timedelta
from homeassistant.util import dt as dt_util

_LOGGER = logging.getLogger(__name__)

# Note: This function will be attached to a class, so we use 'self' parameter
async def _update_charging_status(self):
    """Update charging status based on current state."""
    was_charging = self.is_charging
    is_now_charging = False
    
    # Check if any battery is charging
    for battery_num, entity_id in self.detected_entities.get('current', []):
        state = self.hass.states.get(entity_id)
        if not state or not state.state or state.state == "unknown" or state.state == "unavailable":
            continue
            
        try:
            current = float(state.state)
            
            # Positive current means charging
            if current > 0.5:  # Small threshold to avoid flickering
                is_now_charging = True
                _LOGGER.debug(f"Battery {battery_num} is charging with current {current}A")
                break
                
        except (ValueError, TypeError) as err:
            _LOGGER.error(f"Error processing current for battery {battery_num}: {err}")
    
    # Handle state transitions
    if is_now_charging and not was_charging:
        # Charging just started
        self.is_charging = True
        self.charge_start_time = dt_util.utcnow()
        _LOGGER.info("Charging started at %s", self.charge_start_time)
        
        # Reset energy since last charge if needed
        # (don't reset if we're just continuing a charge that was interrupted)
        if self.last_charge_completed and (dt_util.utcnow() - self.last_charge_completed) > timedelta(hours=1):
            _LOGGER.info("Resetting energy since last charge")
            self.energy_since_last_charge_counter = 0
            self.energy_since_last_charge = 0.0
            
    elif not is_now_charging and was_charging:
        # Charging just ended
        self.is_charging = False
        charge_end_time = dt_util.utcnow()
        self.last_charge_completed = charge_end_time
        
        # Calculate charge duration
        if self.charge_start_time:
            self.last_charge_duration = (charge_end_time - self.charge_start_time).total_seconds() / 3600  # hours
            _LOGGER.info("Charging completed. Duration: %.2f hours", self.last_charge_duration)
        
        self.charge_start_time = None
    
    # Update the is_charging property
    self.is_charging = is_now_charging