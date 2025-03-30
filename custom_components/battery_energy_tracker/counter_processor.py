"""Counter processing for the Battery Energy Tracker integration."""
import logging
from .const import MAX_COUNTER_VALUE, COUNTER_THRESHOLD

_LOGGER = logging.getLogger(__name__)

# Note: These functions will be attached to a class, so we use 'self' parameter
async def _update_counters(self):
    """Update discharge and charge counters from current state."""
    _LOGGER.info("==== COUNTER PROCESSING DEBUG ====")
    _LOGGER.info(f"Starting counter update with detected entities: discharge={len(self.detected_entities.get('discharge', []))}, charge={len(self.detected_entities.get('charge', []))}")
    
    # Process discharge counters
    for battery_num, entity_id in self.detected_entities.get('discharge', []):
        _LOGGER.info(f"Processing discharge entity for battery {battery_num}: {entity_id}")
        result = self._process_counter_value("discharge", battery_num, entity_id)
        _LOGGER.info(f"Result of discharge processing for battery {battery_num}: {result}")
    
    # Process charge counters
    for battery_num, entity_id in self.detected_entities.get('charge', []):
        _LOGGER.info(f"Processing charge entity for battery {battery_num}: {entity_id}")
        result = self._process_counter_value("charge", battery_num, entity_id)
        _LOGGER.info(f"Result of charge processing for battery {battery_num}: {result}")
    
    _LOGGER.info(f"After processing - total_discharge_counter: {self.total_discharge_counter}, total_charge_counter: {self.total_charge_counter}")
    _LOGGER.info(f"After processing - energy_since_last_charge_counter: {self.energy_since_last_charge_counter}")

def _process_counter_value(self, entity_type, battery_num, entity_id):
    """Process a counter value and update totals with error handling."""
    state = self.hass.states.get(entity_id)
    if not state or not state.state or state.state == "unknown" or state.state == "unavailable":
        _LOGGER.debug(f"Entity {entity_id} not available for processing")
        return False
    
    try:
        counter_value = float(state.state)
        _LOGGER.info(f"Counter value for {entity_type} on battery {battery_num}: {counter_value}")
        
        if entity_type == "discharge":
            prev_values = self._last_discharge_values
        else:  # charge
            prev_values = self._last_charge_values
            
        if battery_num not in prev_values or prev_values[battery_num] is None:
            # First time seeing this counter
            _LOGGER.info(f"First time seeing {entity_type} counter for battery {battery_num}: {counter_value}")
            prev_values[battery_num] = counter_value
            return True
            
        prev_value = prev_values[battery_num]
        
        # Check for rollover
        _LOGGER.info(f"Previous {entity_type} value for battery {battery_num}: {prev_value}, Current value: {counter_value}")
        
        if prev_value > COUNTER_THRESHOLD and counter_value < 1000:
            # Counter rolled over
            delta = (MAX_COUNTER_VALUE - prev_value) + counter_value
            _LOGGER.info(f"Detected counter rollover for {entity_type} on battery {battery_num}! Previous: {prev_value}, Current: {counter_value}, Calculated delta: {delta}")
        else:
            delta = counter_value - prev_value
            _LOGGER.info(f"Regular delta calculation for {entity_type} on battery {battery_num}: {delta}")
            
        # Only count positive deltas - store raw counter values without scaling
        if delta > 0:
            _LOGGER.info(f"Processing positive delta ({delta}) for {entity_type} on battery {battery_num}")
            # Store raw counter values
            if entity_type == "discharge":
                self.total_discharge_counter += delta
                self.energy_since_last_charge_counter += delta
                _LOGGER.info(f"Updated total discharge counter: {self.total_discharge_counter}")
                _LOGGER.info(f"Updated energy since last charge counter: {self.energy_since_last_charge_counter}")
        
                # Update stored energy for this battery
                _LOGGER.info(f"Calling process_energy_change for battery {battery_num} (discharge) with delta {delta}")
                self.process_energy_change(battery_num, "discharge", delta)
        
            else:  # charge
                self.total_charge_counter += delta
                _LOGGER.info(f"Updated total charge counter: {self.total_charge_counter}")
        
                # Update stored energy for this battery
                _LOGGER.info(f"Calling process_energy_change for battery {battery_num} (charge) with delta {delta}")
                self.process_energy_change(battery_num, "charge", delta)
        elif delta < 0:
            # Negative delta - could be a counter reset or error
            _LOGGER.warning(f"Negative delta detected for {entity_type} on battery {battery_num}: {delta}. This could indicate a counter reset or error.")
        else:
            _LOGGER.info(f"No change in counter value for {entity_type} on battery {battery_num}")
        
        # Always update the stored value
        prev_values[battery_num] = counter_value
        return True
        
    except (ValueError, TypeError) as err:
        _LOGGER.error(f"Error processing {entity_type} counter for battery {battery_num}: {err}")
        return False