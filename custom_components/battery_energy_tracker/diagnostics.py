"""Diagnostic functions for the Battery Energy Tracker integration."""
import logging

_LOGGER = logging.getLogger(__name__)

# Note: This function will be attached to a class, so we use 'self' parameter
async def diagnostic_check(self):
    """Run a diagnostic check to verify entity availability and readings."""
    _LOGGER.debug("Running diagnostic check...")
    
    diagnostic_data = {
        "battery_entities": {},
        "tracker_state": {
            "total_discharge_counter": self.total_discharge_counter,
            "total_charge_counter": self.total_charge_counter,
            "total_discharge_kwh": self.total_discharge_kwh,
            "total_charge_kwh": self.total_charge_kwh,
            "energy_since_last_charge_counter": self.energy_since_last_charge_counter,
            "energy_since_last_charge": self.energy_since_last_charge,
            "is_charging": self.is_charging,
            "last_charge_completed": self.last_charge_completed,
            "charge_start_time": self.charge_start_time,
            "total_charge_rate": self.total_charge_rate,
            "charge_rate_data": self.charge_rate_data,
        }
    }
    
    # Check detected entities
    for entity_type, entities in self.detected_entities.items():
        for battery_num, entity_id in entities:
            if battery_num not in diagnostic_data["battery_entities"]:
                diagnostic_data["battery_entities"][battery_num] = {}
            
            state = self.hass.states.get(entity_id)
            status = "FOUND" if state else "NOT FOUND"
            _LOGGER.debug(f"Battery {battery_num} {entity_type} entity: {entity_id} - {status}")
            
            diagnostic_data["battery_entities"][battery_num][entity_type] = {
                "entity_id": entity_id,
                "available": state is not None,
                "value": state.state if state else None,
            }
    
    # Check for missing entities
    missing_entities = []
    for battery_num in range(1, self.battery_count + 1):
        for entity_type in ["discharge", "charge", "current"]:
            # Check if this battery number exists for this entity type
            found = False
            for bn, _ in self.detected_entities.get(entity_type, []):
                if bn == battery_num:
                    found = True
                    break
            
            if not found:
                missing_entities.append(f"Battery {battery_num} {entity_type}")
    
    if missing_entities:
        diagnostic_data["missing_entities"] = missing_entities
        _LOGGER.warning(f"Missing entities: {', '.join(missing_entities)}")
    
    # Check for abnormal values
    abnormal_values = []
    for battery_num, entities in diagnostic_data["battery_entities"].items():
        for entity_type, entity_info in entities.items():
            if not entity_info["available"]:
                continue
                
            try:
                value = float(entity_info["value"])
                
                # Check for abnormal values based on entity type
                if entity_type == "discharge" or entity_type == "charge":
                    if value < 0:
                        abnormal_values.append(f"Battery {battery_num} {entity_type}: {value} (negative)")
                elif entity_type == "current":
                    if abs(value) > 100:  # Unlikely to have >100A current
                        abnormal_values.append(f"Battery {battery_num} {entity_type}: {value}A (excessive)")
            except (ValueError, TypeError):
                # Non-numeric value
                abnormal_values.append(f"Battery {battery_num} {entity_type}: {entity_info['value']} (non-numeric)")
    
    if abnormal_values:
        diagnostic_data["abnormal_values"] = abnormal_values
        _LOGGER.warning(f"Abnormal values detected: {', '.join(abnormal_values)}")
    
    # Check for recent counter changes
    counter_activity = {}
    for entity_type in ["discharge", "charge"]:
        for battery_num, entity_id in self.detected_entities.get(entity_type, []):
            if battery_num not in counter_activity:
                counter_activity[battery_num] = {}
                
            if entity_type == "discharge":
                prev_value = self._last_discharge_values.get(battery_num)
            else:
                prev_value = self._last_charge_values.get(battery_num)
                
            state = self.hass.states.get(entity_id)
            if state and prev_value is not None:
                try:
                    current_value = float(state.state)
                    delta = current_value - prev_value
                    
                    counter_activity[battery_num][entity_type] = {
                        "previous": prev_value,
                        "current": current_value,
                        "delta": delta
                    }
                    
                    if delta > 0:
                        _LOGGER.debug(f"Battery {battery_num} {entity_type} counter active: +{delta}")
                except (ValueError, TypeError):
                    pass
    
    diagnostic_data["counter_activity"] = counter_activity
    
    # Include retry count
    diagnostic_data["retry_count"] = self._retry_count
    
    return diagnostic_data