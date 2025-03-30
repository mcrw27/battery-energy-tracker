"""Charge rate tracking for the Battery Energy Tracker integration."""
import logging
from datetime import timedelta
from typing import Dict, Any, List, Optional
from homeassistant.util import dt as dt_util

_LOGGER = logging.getLogger(__name__)

# Note: This function will be attached to a class, so we use 'self' parameter
async def _update_charge_rates(self):
    """Update charge rates based on current and voltage readings."""
    total_instantaneous_rate = 0
    active_charging_batteries = 0
    
    for battery_num in range(1, self.battery_count + 1):
        # Get current sensor
        current_entity_id = f"sensor.antra_battery_{battery_num}_current"
        current_state = self.hass.states.get(current_entity_id)
        
        # Get voltage sensor
        voltage_entity_id = f"sensor.antra_battery_{battery_num}_pack_voltage"
        voltage_state = self.hass.states.get(voltage_entity_id)
        
        if current_state and voltage_state and current_state.state not in ('unknown', 'unavailable') and voltage_state.state not in ('unknown', 'unavailable'):
            try:
                current = float(current_state.state)
                voltage = float(voltage_state.state)
                
                # Only consider positive current (charging)
                if current > 0:
                    instantaneous_rate = current * voltage  # Watts
                    total_instantaneous_rate += instantaneous_rate
                    active_charging_batteries += 1
                    
                    if battery_num not in self.battery_charge_rates:
                        self.battery_charge_rates[battery_num] = {}
                    
                    self.battery_charge_rates[battery_num] = {
                        'current': current,
                        'voltage': voltage,
                        'instantaneous_rate': instantaneous_rate,
                        'timestamp': dt_util.utcnow()
                    }
                    
                    _LOGGER.debug(f"Battery {battery_num} charging at {instantaneous_rate:.2f}W (current: {current:.2f}A, voltage: {voltage:.2f}V)")
            except (ValueError, TypeError) as err:
                _LOGGER.error(f"Error calculating charge rate for battery {battery_num}: {err}")
    
    # Store the total instantaneous rate with timestamp
    now = dt_util.utcnow()
    self.historic_charge_rates.append({
        'rate': total_instantaneous_rate,
        'timestamp': now,
        'active_batteries': active_charging_batteries
    })
    
    # Keep only last 10 minutes of data
    cutoff_time = now - timedelta(minutes=10)
    self.historic_charge_rates = [r for r in self.historic_charge_rates if r['timestamp'] >= cutoff_time]
    
    # Calculate a time-weighted average of charge rate
    weighted_avg_rate = self._calculate_weighted_average_rate()
    
    # If we have counter-based data, use it for comparison
    counter_based_rate = self._calculate_counter_based_rate()
    
    # Blend the rates, favoring counter-based when available
    if counter_based_rate and counter_based_rate > 0:
        # Counter-based rate is generally more accurate for long-term measurements
        blend_factor = 0.7  # 70% weight to counter-based rate
        blended_rate = (counter_based_rate * blend_factor) + (weighted_avg_rate * (1 - blend_factor))
        _LOGGER.debug(f"Blended charge rate: {blended_rate:.2f}W (counter: {counter_based_rate:.2f}W, instant: {weighted_avg_rate:.2f}W)")
    else:
        # If counter-based rate is not available, use only the instantaneous measurements
        blended_rate = weighted_avg_rate
        _LOGGER.debug(f"Using instant charge rate: {blended_rate:.2f}W (no counter data available)")
    
    self.total_charge_rate = blended_rate
    
    # Store for diagnostics
    self.charge_rate_data = {
        'instantaneous_total': total_instantaneous_rate,
        'weighted_average': weighted_avg_rate,
        'counter_based': counter_based_rate,
        'blended_rate': blended_rate,
        'battery_rates': self.battery_charge_rates,
        'active_charging_batteries': active_charging_batteries
    }
    
    return blended_rate

def _calculate_weighted_average_rate(self) -> float:
    """Calculate time-weighted average of charge rates."""
    if len(self.historic_charge_rates) <= 1:
        return self.historic_charge_rates[0]['rate'] if self.historic_charge_rates else 0
    
    total_weighted_rate = 0
    total_time = 0
    
    for i in range(1, len(self.historic_charge_rates)):
        current = self.historic_charge_rates[i]
        previous = self.historic_charge_rates[i-1]
        
        time_diff = (current['timestamp'] - previous['timestamp']).total_seconds()
        avg_rate = (current['rate'] + previous['rate']) / 2
        
        total_weighted_rate += avg_rate * time_diff
        total_time += time_diff
    
    if total_time > 0:
        return total_weighted_rate / total_time
    
    return self.historic_charge_rates[-1]['rate']

def _calculate_counter_based_rate(self) -> Optional[float]:
    """Calculate charge rate based on counter changes over time."""
    # Need at least 2 minutes of data for meaningful calculation
    if not hasattr(self, 'last_counter_check') or not self.last_counter_check:
        self.last_counter_check = {
            'timestamp': dt_util.utcnow(),
            'total_charge_counter': self.total_charge_counter
        }
        return None
    
    # Check if we're actually charging
    if not self.is_charging:
        return None
    
    now = dt_util.utcnow()
    time_diff = (now - self.last_counter_check['timestamp']).total_seconds()
    
    # Need at least 2 minutes of data, but not more than 30 minutes
    if time_diff < 120 or time_diff > 1800:
        # If too much time has passed, reset the reference point
        if time_diff > 1800:
            self.last_counter_check = {
                'timestamp': now,
                'total_charge_counter': self.total_charge_counter
            }
        return None
    
    # Calculate change in counter
    counter_diff = self.total_charge_counter - self.last_counter_check['total_charge_counter']
    
    # If there's no meaningful change, return None
    if counter_diff <= 0:
        return None
    
    # Convert counter units to Wh and calculate rate in Watts
    # 1 counter unit ≈ 1 Wh
    energy_wh = counter_diff * 1  # Using the 1Wh per counter unit conversion
    
    # Calculate rate in Watts
    rate = energy_wh * 3600 / time_diff
    
    _LOGGER.debug(
        f"Counter-based charge rate: {rate:.2f}W "
        f"(counter diff: {counter_diff}, time: {time_diff:.1f}s, energy: {energy_wh:.2f}Wh)"
    )
    
    # Update the reference point if we have a valid rate
    if counter_diff > 10:  # Only update if there's a meaningful change
        self.last_counter_check = {
            'timestamp': now,
            'total_charge_counter': self.total_charge_counter
        }
    
    return rate