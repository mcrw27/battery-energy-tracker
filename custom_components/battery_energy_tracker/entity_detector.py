"""Entity detection for the Battery Energy Tracker integration."""
import logging

_LOGGER = logging.getLogger(__name__)

# Note: This function is going to be attached to a class, so we use 'self' parameter
async def auto_detect_entities(self):
    """Automatically detect entity IDs for Antra batteries with enhanced debugging."""
    detected_entities = {
        'discharge': [],
        'charge': [],
        'current': []
    }
    
    _LOGGER.info("==== ENTITY DETECTION DEBUG ====")
    _LOGGER.info(f"Starting entity detection for {self.battery_count} batteries")
    
    # Use manually configured entities if provided
    if self.manual_entities:
        _LOGGER.info("Using manually configured entities")
        for battery_num in range(1, self.battery_count + 1):
            idx = battery_num - 1  # Convert to 0-based index for list access
            
            if idx < len(self.manual_entities.get("discharge", [])):
                entity_id = self.manual_entities["discharge"][idx]
                detected_entities["discharge"].append((battery_num, entity_id))
                _LOGGER.info(f"Using manual discharge entity for battery {battery_num}: {entity_id}")
                
            if idx < len(self.manual_entities.get("charge", [])):
                entity_id = self.manual_entities["charge"][idx]
                detected_entities["charge"].append((battery_num, entity_id))
                _LOGGER.info(f"Using manual charge entity for battery {battery_num}: {entity_id}")
                
            if idx < len(self.manual_entities.get("current", [])):
                entity_id = self.manual_entities["current"][idx]
                detected_entities["current"].append((battery_num, entity_id))
                _LOGGER.info(f"Using manual current entity for battery {battery_num}: {entity_id}")
        
        return detected_entities
    
    # First, let's log ALL entities to see what's available
    _LOGGER.debug("BEGIN: Full entity list dump ======")
    all_entities = self.hass.states.async_all()
    _LOGGER.info(f"Total entities in Home Assistant: {len(all_entities)}")
    
    # Count entities starting with 'sensor.'
    sensor_entities = [e for e in all_entities if e.entity_id.startswith('sensor.')]
    _LOGGER.info(f"Total sensor entities: {len(sensor_entities)}")
    
    # Filter for Antra
    antra_entities = [e for e in sensor_entities if 'antra' in e.entity_id.lower()]
    _LOGGER.info(f"Total Antra sensor entities: {len(antra_entities)}")
    
    # Enhanced logging - log ALL antra entities
    _LOGGER.info("All detected Antra entities:")
    for i, entity in enumerate(antra_entities):
        _LOGGER.info(f"  {i+1}: {entity.entity_id} = {entity.state}")
    
    _LOGGER.debug("END: Full entity list dump ======")
    
    # Let's specifically check for our exact entity
    test_entity_id = "sensor.antra_battery_1_total_discharge"
    test_state = self.hass.states.get(test_entity_id)
    
    if test_state is None:
        _LOGGER.warning(f"TEST FAILED: Could not find entity '{test_entity_id}' in state machine")
    else:
        _LOGGER.info(f"TEST PASSED: Found entity '{test_entity_id}' with state '{test_state.state}'")
    
    # Now let's try using the entity registry the modern way
    _LOGGER.debug("BEGIN: Entity Registry lookup ======")
    try:
        # Import the entity registry module properly
        from homeassistant.helpers import entity_registry as er
        
        # Get the registry without passing hass as an argument
        registry = er.async_get(self.hass)
        
        # Get all entities from the registry
        registry_entities = list(registry.entities.keys())
        _LOGGER.info(f"Total entities in registry: {len(registry_entities)}")
        
        # Count sensor entities in registry
        registry_sensors = [e for e in registry_entities if e.startswith('sensor.')]
        _LOGGER.info(f"Sensor entities in registry: {len(registry_sensors)}")
        
        # Filter for Antra in registry
        registry_antra = [e for e in registry_sensors if 'antra' in e.lower()]
        _LOGGER.info(f"Antra sensor entities in registry: {len(registry_antra)}")
        
        # Enhanced logging - log ALL antra entities from registry
        _LOGGER.info("All Antra entities in registry:")
        for i, entity_id in enumerate(registry_antra):
            _LOGGER.info(f"  {i+1}: {entity_id}")
            
        # Check for our test entity in registry
        if test_entity_id in registry_entities:
            _LOGGER.info(f"TEST PASSED: Found entity '{test_entity_id}' in registry")
        else:
            _LOGGER.warning(f"TEST FAILED: Could not find entity '{test_entity_id}' in registry")
            
        # Log all Battery-related entities
        battery_entities = [e for e in registry_entities if 'battery' in e.lower()]
        _LOGGER.info(f"Found {len(battery_entities)} battery-related entities in registry")
        for entity_id in battery_entities[:20]:  # Show more entities
            _LOGGER.info(f"  - {entity_id}")
            
    except Exception as e:
        _LOGGER.error(f"Error accessing entity registry: {e}")
        registry = None
        registry_entities = []
    _LOGGER.debug("END: Entity Registry lookup ======")
    
    # Common patterns to check
    patterns = {
        'discharge': [
            "sensor.antra_battery_{}_total_discharge",
        ],
        'charge': [
            "sensor.antra_battery_{}_total_charge",
        ],
        'current': [
            "sensor.antra_battery_{}_current",
        ]
    }
    
    # User-provided entity patterns override defaults
    if self.entity_patterns:
        _LOGGER.info(f"Using user-provided entity patterns: {self.entity_patterns}")
        for key, pattern in self.entity_patterns.items():
            if key in patterns and pattern:
                patterns[key] = [pattern]  # Replace with user pattern
                _LOGGER.info(f"Overriding pattern for {key}: {pattern}")
    else:
        _LOGGER.info(f"Using default entity patterns: {patterns}")
    
    # Try to find entities in registry for each battery
    if registry is not None:
        for battery_num in range(1, self.battery_count + 1):
            _LOGGER.info(f"Checking registry for entities for battery {battery_num}")
            
            for entity_type, entity_patterns in patterns.items():
                for pattern in entity_patterns:
                    entity_id = pattern.format(battery_num)
                    _LOGGER.info(f"Checking registry for {entity_type}: {entity_id}")
                    
                    if entity_id in registry_entities:
                        _LOGGER.info(f"Found {entity_type} entity in registry for battery {battery_num}: {entity_id}")
                        detected_entities[entity_type].append((battery_num, entity_id))
                    else:
                        # Try case-insensitive matching
                        found = False
                        for reg_entity in registry_entities:
                            if reg_entity.lower() == entity_id.lower():
                                _LOGGER.info(f"Found {entity_type} entity in registry with case-insensitive match: {reg_entity}")
                                detected_entities[entity_type].append((battery_num, reg_entity))
                                found = True
                                break
                        
                        if not found:
                            # Try any pattern that looks close
                            _LOGGER.info(f"Trying partial matching for {entity_type} on battery {battery_num}")
                            for reg_entity in registry_entities:
                                if all(part.lower() in reg_entity.lower() for part in ["antra", f"{battery_num}", "discharge"]):
                                    if (entity_type == 'discharge' in reg_entity) or \
                                        (entity_type == 'charge' not in reg_entity):
                                        _LOGGER.info(f"Found potential {entity_type} entity with partial match: {reg_entity}")
                                        detected_entities[entity_type].append((battery_num, reg_entity))
                                        found = True
                                        break
                                elif entity_type == 'current' and all(part.lower() in reg_entity.lower() for part in ["antra", f"{battery_num}", "current"]):
                                    _LOGGER.info(f"Found potential current entity with partial match: {reg_entity}")
                                    detected_entities[entity_type].append((battery_num, reg_entity))
                                    found = True
                                    break
                            
                            if not found:
                                _LOGGER.warning(f"Not found in registry: {entity_id}")
    
    # If we didn't find any entities, check if this is the first run
    if not any(detected_entities.values()) and self._first_run:
        _LOGGER.warning("No entities found on first run - scheduling retry in 60 seconds")
        self._first_run = False
        
        # Schedule a delayed entity check
        async def check_later(now=None):
            _LOGGER.info("Running delayed entity detection...")
            await self.async_refresh()
        
        # Use imported async_call_later instead of self.hass.helpers.event.async_call_later
        from homeassistant.helpers.event import async_call_later
        async_call_later(self.hass, 60, check_later)
    
    # Also try original state-based lookup as fallback
    for battery_num in range(1, self.battery_count + 1):
        _LOGGER.info(f"Looking for entities in state machine for battery {battery_num}")
        
        for entity_type, entity_patterns in patterns.items():
            # Skip if we already found this entity type and battery number
            already_found = False
            for (bn, _) in detected_entities[entity_type]:
                if bn == battery_num:
                    already_found = True
                    break
                    
            if already_found:
                continue
                
            for pattern in entity_patterns:
                entity_id = pattern.format(battery_num)
                _LOGGER.info(f"Checking state machine for {entity_type}: {entity_id}")
                
                state = self.hass.states.get(entity_id)
                if state is not None:
                    _LOGGER.info(f"Found {entity_type} entity in state machine for battery {battery_num}: {entity_id}")
                    detected_entities[entity_type].append((battery_num, entity_id))
                    break
                else:
                    _LOGGER.warning(f"Not found in state machine: {entity_id}")
    
    # Log what we found
    _LOGGER.info("==== DETECTION RESULTS ====")
    for entity_type, entities in detected_entities.items():
        if entities:
            _LOGGER.info(f"Found {entity_type} entities:")
            for battery_num, entity_id in entities:
                _LOGGER.info(f"  - Battery {battery_num}: {entity_id}")
        else:
            _LOGGER.warning(f"No {entity_type} entities found")
    
    return detected_entities