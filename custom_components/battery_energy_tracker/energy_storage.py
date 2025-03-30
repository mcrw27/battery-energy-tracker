"""Energy storage tracking for the Battery Energy Tracker integration."""
import logging

_LOGGER = logging.getLogger(__name__)

# Default battery capacity in kWh (5120Wh = 5.12kWh)
DEFAULT_BATTERY_CAPACITY = 5.12

# Note: These functions will be attached to a class, so we use 'self' parameter
async def update_stored_energy(self):
    """Update the stored energy values based on current state."""
    # This is called after processing counters, so we just need to update derived values
    
    # Calculate total stored energy across all batteries
    total_stored = sum(self.battery_stored_energy.values())
    self.total_stored_energy = total_stored
    
    # Calculate percentage of total capacity
    total_capacity = sum(self.battery_capacities.values())
    if total_capacity > 0:
        self.total_stored_energy_percent = (total_stored / total_capacity) * 100
    else:
        self.total_stored_energy_percent = 0
    
    # Log total
    _LOGGER.debug(f"Total stored energy: {total_stored:.2f} kWh ({self.total_stored_energy_percent:.1f}%)")
    
    # Log per-battery values
    for battery_num, energy in self.battery_stored_energy.items():
        capacity = self.battery_capacities.get(battery_num, DEFAULT_BATTERY_CAPACITY)
        percent = (energy / capacity) * 100 if capacity > 0 else 0
        _LOGGER.debug(f"Battery {battery_num} stored energy: {energy:.2f} kWh ({percent:.1f}%)")
    
    return self.battery_stored_energy

def process_energy_change(self, battery_num, entity_type, delta):
    """Update stored energy for a battery based on charge or discharge activity."""
    if battery_num not in self.battery_stored_energy:
        # Initialize if not already set
        self.battery_stored_energy[battery_num] = 0
        
    if battery_num not in self.battery_capacities:
        # Set default capacity if not already set
        self.battery_capacities[battery_num] = DEFAULT_BATTERY_CAPACITY
    
    # Convert counter delta to kWh (1 counter unit ≈ 1 Wh = 0.001 kWh)
    energy_delta_kwh = delta * 0.001
    
    if entity_type == "discharge":
        # Subtract discharge energy
        self.battery_stored_energy[battery_num] -= energy_delta_kwh
        # Ensure we don't go below zero
        self.battery_stored_energy[battery_num] = max(0, self.battery_stored_energy[battery_num])
        _LOGGER.debug(f"Battery {battery_num} discharged {energy_delta_kwh:.3f} kWh, remaining: {self.battery_stored_energy[battery_num]:.2f} kWh")
    
    elif entity_type == "charge":
        # Add charge energy
        self.battery_stored_energy[battery_num] += energy_delta_kwh
        # Ensure we don't exceed capacity
        max_capacity = self.battery_capacities.get(battery_num, DEFAULT_BATTERY_CAPACITY)
        self.battery_stored_energy[battery_num] = min(max_capacity, self.battery_stored_energy[battery_num])
        _LOGGER.debug(f"Battery {battery_num} charged {energy_delta_kwh:.3f} kWh, now at: {self.battery_stored_energy[battery_num]:.2f} kWh")

async def set_battery_stored_energy(self, battery_num, energy_kwh, capacity_kwh=None):
    """Set the stored energy for a specific battery."""
    if battery_num not in range(1, self.battery_count + 1):
        _LOGGER.error(f"Invalid battery number: {battery_num}")
        return False
        
    # Validate energy value
    try:
        energy_kwh = float(energy_kwh)
        if energy_kwh < 0:
            _LOGGER.error(f"Energy value cannot be negative: {energy_kwh}")
            return False
    except (ValueError, TypeError):
        _LOGGER.error(f"Invalid energy value: {energy_kwh}")
        return False
    
    # Update capacity if provided
    if capacity_kwh is not None:
        try:
            capacity_kwh = float(capacity_kwh)
            if capacity_kwh <= 0:
                _LOGGER.error(f"Capacity value must be positive: {capacity_kwh}")
                return False
            self.battery_capacities[battery_num] = capacity_kwh
        except (ValueError, TypeError):
            _LOGGER.error(f"Invalid capacity value: {capacity_kwh}")
            return False
    
    # Ensure we have a capacity value
    if battery_num not in self.battery_capacities:
        self.battery_capacities[battery_num] = DEFAULT_BATTERY_CAPACITY
    
    # Cap the energy to the battery capacity
    max_capacity = self.battery_capacities[battery_num]
    energy_kwh = min(energy_kwh, max_capacity)
    
    # Set the energy value
    self.battery_stored_energy[battery_num] = energy_kwh
    
    _LOGGER.info(
        f"Set battery {battery_num} stored energy to {energy_kwh:.2f} kWh "
        f"(capacity: {self.battery_capacities.get(battery_num, DEFAULT_BATTERY_CAPACITY):.2f} kWh)"
    )
    
    # Update derived values
    await self.update_stored_energy()
    await self.async_refresh()
    return True

async def set_battery_to_full(self, battery_num=None):
    """Set the stored energy to full capacity for one or all batteries."""
    if battery_num is not None:
        if battery_num not in range(1, self.battery_count + 1):
            _LOGGER.error(f"Invalid battery number: {battery_num}")
            return False
        
        # Ensure we have a capacity value
        if battery_num not in self.battery_capacities:
            self.battery_capacities[battery_num] = DEFAULT_BATTERY_CAPACITY
            
        capacity = self.battery_capacities[battery_num]
        self.battery_stored_energy[battery_num] = capacity
        _LOGGER.info(f"Set battery {battery_num} stored energy to full capacity ({capacity:.2f} kWh)")
    else:
        # Set all batteries to full
        for bnum in range(1, self.battery_count + 1):
            # Ensure we have a capacity value
            if bnum not in self.battery_capacities:
                self.battery_capacities[bnum] = DEFAULT_BATTERY_CAPACITY
                
            capacity = self.battery_capacities[bnum]
            self.battery_stored_energy[bnum] = capacity
            _LOGGER.info(f"Set battery {bnum} stored energy to full capacity ({capacity:.2f} kWh)")
    
    # Update derived values
    await self.update_stored_energy()
    await self.async_refresh()
    return True

async def set_battery_capacity(self, battery_num, capacity_kwh):
    """Set the maximum capacity for a specific battery."""
    if battery_num not in range(1, self.battery_count + 1):
        _LOGGER.error(f"Invalid battery number: {battery_num}")
        return False
        
    # Validate capacity value
    try:
        capacity_kwh = float(capacity_kwh)
        if capacity_kwh <= 0:
            _LOGGER.error(f"Capacity value must be positive: {capacity_kwh}")
            return False
    except (ValueError, TypeError):
        _LOGGER.error(f"Invalid capacity value: {capacity_kwh}")
        return False
    
    # Set the capacity
    self.battery_capacities[battery_num] = capacity_kwh
    
    # Ensure stored energy doesn't exceed new capacity
    if battery_num in self.battery_stored_energy:
        self.battery_stored_energy[battery_num] = min(
            self.battery_stored_energy[battery_num], 
            capacity_kwh
        )
    
    _LOGGER.info(f"Set battery {battery_num} capacity to {capacity_kwh:.2f} kWh")
    
    # Update derived values
    await self.update_stored_energy()
    await self.async_refresh()
    return True

async def initialize_all_batteries(self):
    """Initialize all batteries with default values if not already set."""
    for battery_num in range(1, self.battery_count + 1):
        # Initialize capacity if not set
        if battery_num not in self.battery_capacities:
            self.battery_capacities[battery_num] = DEFAULT_BATTERY_CAPACITY
            
        # Initialize stored energy if not set
        if battery_num not in self.battery_stored_energy:
            # Default to 50% for initial value
            self.battery_stored_energy[battery_num] = self.battery_capacities[battery_num] * 0.5
            
    _LOGGER.info(f"Initialized {self.battery_count} batteries with default values")
    
    # Update derived values
    await self.update_stored_energy()