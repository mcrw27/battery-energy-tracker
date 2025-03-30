"""Coordinator for the Battery Energy Tracker integration."""
import logging

# Import the main coordinator class
from .coordinator_base import BatteryEnergyCoordinator

# Import methods to attach
from . import charge_state, counter_processor, diagnostics, entity_detector, services
from . import charge_rate_tracker, energy_storage, storage

_LOGGER = logging.getLogger(__name__)

# Attach methods to the BatteryEnergyCoordinator class
BatteryEnergyCoordinator.auto_detect_entities = entity_detector.auto_detect_entities
BatteryEnergyCoordinator._update_counters = counter_processor._update_counters
BatteryEnergyCoordinator._process_counter_value = counter_processor._process_counter_value
BatteryEnergyCoordinator._update_charging_status = charge_state._update_charging_status
BatteryEnergyCoordinator.diagnostic_check = diagnostics.diagnostic_check
BatteryEnergyCoordinator.reset_counters = services.reset_counters
BatteryEnergyCoordinator.reset_energy_since_charge = services.reset_energy_since_charge
BatteryEnergyCoordinator.set_charge_state = services.set_charge_state
BatteryEnergyCoordinator.adjust_counters = services.adjust_counters

# Attach the charge rate tracking methods
BatteryEnergyCoordinator._update_charge_rates = charge_rate_tracker._update_charge_rates
BatteryEnergyCoordinator._calculate_weighted_average_rate = charge_rate_tracker._calculate_weighted_average_rate
BatteryEnergyCoordinator._calculate_counter_based_rate = charge_rate_tracker._calculate_counter_based_rate

# Attach the energy storage tracking methods
BatteryEnergyCoordinator.update_stored_energy = energy_storage.update_stored_energy
BatteryEnergyCoordinator.process_energy_change = energy_storage.process_energy_change
BatteryEnergyCoordinator.set_battery_stored_energy = energy_storage.set_battery_stored_energy
BatteryEnergyCoordinator.set_battery_to_full = energy_storage.set_battery_to_full
BatteryEnergyCoordinator.set_battery_capacity = energy_storage.set_battery_capacity
BatteryEnergyCoordinator.initialize_all_batteries = energy_storage.initialize_all_batteries

# Note: Storage methods are now attached in __init__.py when setting up the entry
# BatteryEnergyCoordinator.save_data = storage.save_data
# BatteryEnergyCoordinator.load_data = storage.load_data
# BatteryEnergyCoordinator._convert_string_keys = storage._convert_string_keys
# BatteryEnergyCoordinator.init_storage = storage.init_storage
# BatteryEnergyCoordinator._clean_up_storage = storage._clean_up_storage