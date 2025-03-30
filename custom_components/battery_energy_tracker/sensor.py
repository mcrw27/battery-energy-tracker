"""Battery Energy Tracker sensor platform."""
import logging
from datetime import timedelta

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.const import (
    UnitOfEnergy,
    UnitOfPower,
    UnitOfTime
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import dt as dt_util

from .const import (
    DOMAIN,
    ATTR_TOTAL_DISCHARGE,
    ATTR_TOTAL_CHARGE,
    ATTR_ESTIMATED_CHARGE_TIME,
    ATTR_LAST_RESET,
    ATTR_LAST_CHARGE_STARTED,
    ATTR_LAST_CHARGE_COMPLETED,
    ATTR_CHARGE_DURATION,
    ATTR_ENERGY_SINCE_LAST_CHARGE,
)

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the battery tracker sensors from config entry."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id]
    
    # Initialize batteries with default values
    await coordinator.initialize_all_batteries()
    
    entities = [
        TotalDischargeEnergySensor(coordinator),
        TotalChargeEnergySensor(coordinator),
        EnergySinceLastChargeSensor(coordinator),
        EstimatedChargeTimeSensor(coordinator),
        ChargeStatusSensor(coordinator),
        ChargeRateSensor(coordinator),
        DiagnosticSensor(coordinator),
        TotalStoredEnergySensor(coordinator),
    ]
    
    # Add individual battery storage sensors
    for battery_num in range(1, coordinator.battery_count + 1):
        entities.append(BatteryStoredEnergySensor(coordinator, battery_num))
    
    async_add_entities(entities)
class BatteryEnergySensor(CoordinatorEntity, SensorEntity):
    """Base class for battery energy sensors."""
    
    def __init__(self, coordinator):
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._attr_has_entity_name = True
        
    @property
    def device_info(self):
        """Return device information."""
        return {
            "identifiers": {(DOMAIN, "battery_energy_tracker")},
            "name": "Battery Energy Tracker",
            "manufacturer": "Custom",
            "model": "Battery Energy Monitor",
        }


class TotalDischargeEnergySensor(BatteryEnergySensor):
    """Sensor to track total discharged energy with rollover handling."""
    
    _attr_name = "Total Discharge Energy"
    _attr_native_unit_of_measurement = UnitOfEnergy.KILO_WATT_HOUR
    _attr_device_class = SensorDeviceClass.ENERGY
    _attr_state_class = SensorStateClass.TOTAL_INCREASING
    _attr_icon = "mdi:battery-minus-outline"
    
    @property
    def unique_id(self):
        """Return unique ID for the sensor."""
        return f"{DOMAIN}_total_discharge_energy"
        
    @property
    def native_value(self):
        """Return the total discharge energy."""
        if self.coordinator.data and "total_discharge_kwh" in self.coordinator.data:
            return round(self.coordinator.data["total_discharge_kwh"], 2)
        return 0


class TotalChargeEnergySensor(BatteryEnergySensor):
    """Sensor to track total charged energy with rollover handling."""
    
    _attr_name = "Total Charge Energy"
    _attr_native_unit_of_measurement = UnitOfEnergy.KILO_WATT_HOUR
    _attr_device_class = SensorDeviceClass.ENERGY
    _attr_state_class = SensorStateClass.TOTAL_INCREASING
    _attr_icon = "mdi:battery-plus-outline"
    
    @property
    def unique_id(self):
        """Return unique ID for the sensor."""
        return f"{DOMAIN}_total_charge_energy"
        
    @property
    def native_value(self):
        """Return the total charge energy."""
        if self.coordinator.data and "total_charge_kwh" in self.coordinator.data:
            return round(self.coordinator.data["total_charge_kwh"], 2)
        return 0


class EnergySinceLastChargeSensor(BatteryEnergySensor):
    """Sensor to track energy used since last charge."""
    
    _attr_name = "Energy Since Last Charge"
    _attr_native_unit_of_measurement = UnitOfEnergy.KILO_WATT_HOUR
    _attr_device_class = SensorDeviceClass.ENERGY
    _attr_state_class = SensorStateClass.TOTAL
    _attr_icon = "mdi:battery-charging-low"
    
    @property
    def unique_id(self):
        """Return unique ID for the sensor."""
        return f"{DOMAIN}_energy_since_last_charge"
        
    @property
    def native_value(self):
        """Return energy used since last charge."""
        if self.coordinator.data and "energy_since_last_charge" in self.coordinator.data:
            return round(self.coordinator.data["energy_since_last_charge"], 2)
        return 0
    
    @property
    def extra_state_attributes(self):
        """Return additional attributes."""
        if not self.coordinator.data:
            return {}
            
        return {
            ATTR_LAST_CHARGE_COMPLETED: self.coordinator.data.get("last_charge_completed"),
            ATTR_CHARGE_DURATION: round(self.coordinator.data.get("last_charge_duration", 0), 2) if self.coordinator.data.get("last_charge_duration") else None,
        }


class EstimatedChargeTimeSensor(BatteryEnergySensor):
    """Sensor to estimate charge time needed."""
    
    _attr_name = "Estimated Charge Time"
    _attr_native_unit_of_measurement = UnitOfTime.HOURS
    _attr_device_class = None  # No suitable device class
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_icon = "mdi:clock-outline"
    
    @property
    def unique_id(self):
        """Return unique ID for the sensor."""
        return f"{DOMAIN}_estimated_charge_time"
        
    @property
    def native_value(self):
        """Return estimated time to recharge."""
        if self.coordinator.data and "estimated_charge_time" in self.coordinator.data:
            estimate = self.coordinator.data.get("estimated_charge_time")
            if estimate is not None:
                return round(estimate, 2)
        return None
    
    @property
    def extra_state_attributes(self):
        """Return additional attributes."""
        if not self.coordinator.data or "estimated_charge_time" not in self.coordinator.data:
            return {ATTR_ENERGY_SINCE_LAST_CHARGE: 0}
            
        estimate = self.coordinator.data.get("estimated_charge_time")
        if estimate is not None:
            hours = int(estimate)
            minutes = int((estimate - hours) * 60)
            
            return {
                "hours": hours,
                "minutes": minutes,
                "friendly_format": f"{hours}h {minutes}m" if hours > 0 else f"{minutes}m",
                ATTR_ENERGY_SINCE_LAST_CHARGE: round(self.coordinator.data.get("energy_since_last_charge", 0), 2),
            }
        return {ATTR_ENERGY_SINCE_LAST_CHARGE: 0}


class ChargeStatusSensor(BatteryEnergySensor):
    """Sensor to track battery charging status."""
    
    _attr_name = "Charge Status"
    _attr_icon = "mdi:battery-charging"
    
    @property
    def unique_id(self):
        """Return unique ID for the sensor."""
        return f"{DOMAIN}_charge_status"
        
    @property
    def native_value(self):
        """Return charging status."""
        if not self.coordinator.data:
            return "Unknown"
        return self.coordinator.get_charge_status()
    
    @property
    def extra_state_attributes(self):
        """Return additional attributes."""
        if not self.coordinator.data:
            return {"is_charging": False}
            
        attrs = {
            "is_charging": self.coordinator.data.get("is_charging", False),
        }
        
        charge_start_time = self.coordinator.data.get("charge_start_time")
        if charge_start_time:
            attrs["charge_start_time"] = charge_start_time
            
            # Calculate elapsed time
            elapsed_seconds = (dt_util.utcnow() - charge_start_time).total_seconds()
            attrs["elapsed_minutes"] = round(elapsed_seconds / 60, 1)
            
        if self.coordinator.data.get("last_charge_completed"):
            attrs["last_charge_completed"] = self.coordinator.data.get("last_charge_completed")
            
        return attrs


class ChargeRateSensor(BatteryEnergySensor):
    """Sensor to track the current charge rate."""
    
    _attr_name = "Charge Rate"
    _attr_native_unit_of_measurement = UnitOfPower.WATT
    _attr_device_class = SensorDeviceClass.POWER
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_icon = "mdi:flash"
    
    @property
    def unique_id(self):
        """Return unique ID for the sensor."""
        return f"{DOMAIN}_charge_rate"
        
    @property
    def native_value(self):
        """Return the current charge rate."""
        if not self.coordinator.data:
            return 0
            
        # Only show a rate when we're actually charging
        if not self.coordinator.data.get("is_charging", False):
            return 0
            
        return round(self.coordinator.data.get("total_charge_rate", 0), 1)
    
    @property
    def extra_state_attributes(self):
        """Return additional attributes."""
        if not self.coordinator.data or not self.coordinator.data.get("is_charging", False):
            return {"status": "Not charging"}
            
        charge_rate_data = self.coordinator.data.get("charge_rate_data", {})
        
        return {
            "instantaneous_total": round(charge_rate_data.get("instantaneous_total", 0), 1),
            "weighted_average": round(charge_rate_data.get("weighted_average", 0), 1),
            "counter_based": round(charge_rate_data.get("counter_based", 0), 1) if charge_rate_data.get("counter_based") else None,
            "active_charging_batteries": charge_rate_data.get("active_charging_batteries", 0),
            "per_battery": {
                f"battery_{bnum}": round(bdata.get("instantaneous_rate", 0), 1)
                for bnum, bdata in charge_rate_data.get("battery_rates", {}).items()
            }
        }


class DiagnosticSensor(BatteryEnergySensor):
    """Sensor that provides diagnostic information about the battery tracker."""
    
    _attr_name = "Energy Tracker Diagnostics"
    _attr_icon = "mdi:alert-circle-check"
    
    @property
    def unique_id(self):
        """Return unique ID for the sensor."""
        return f"{DOMAIN}_diagnostics"
        
    @property
    def native_value(self):
        """Return a simple status."""
        if not self.coordinator.data or "diagnostics" not in self.coordinator.data:
            return "Initializing"
            
        diagnostics = self.coordinator.data.get("diagnostics", {})
        battery_entities = diagnostics.get("battery_entities", {})
        
        # Count how many battery entities are found
        count = len(battery_entities)
        
        if count == 0:
            return "No battery entities found"
        elif count < self.coordinator.battery_count:
            return f"Found {count}/{self.coordinator.battery_count} batteries"
        else:
            # Check if all entities are available
            all_available = True
            for battery_data in battery_entities.values():
                for entity_data in battery_data.values():
                    if not entity_data.get("available", False):
                        all_available = False
                        break
                if not all_available:
                    break
                    
            if all_available:
                return "All battery entities found and available"
            else:
                return "All battery entities found but some unavailable"
    
    @property
    def extra_state_attributes(self):
        """Return diagnostic information."""
        if not self.coordinator.data or "diagnostics" not in self.coordinator.data:
            return {"status": "Initializing"}
            
        diagnostics = self.coordinator.data.get("diagnostics", {})
        tracker_state = diagnostics.get("tracker_state", {})
        
        attrs = {
            "total_discharge_kwh": round(tracker_state.get("total_discharge_kwh", 0), 2),
            "total_charge_kwh": round(tracker_state.get("total_charge_kwh", 0), 2),
            "energy_since_last_charge": round(tracker_state.get("energy_since_last_charge", 0), 2),
            "is_charging": tracker_state.get("is_charging", False),
            "battery_count": self.coordinator.battery_count,
            "detected_entities": diagnostics.get("battery_entities", {}),
            "retry_count": diagnostics.get("retry_count", 0),
        }
        
        # Add charge rate data if available
        if self.coordinator.data.get("charge_rate_data"):
            attrs["charge_rate_data"] = self.coordinator.data.get("charge_rate_data")
            
        return attrs
    
class BatteryStoredEnergySensor(BatteryEnergySensor):
    """Sensor to track net energy stored in a specific battery."""
    
    def __init__(self, coordinator, battery_num):
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.battery_num = battery_num
        self._attr_name = f"Battery {battery_num} Stored Energy"
        self._attr_native_unit_of_measurement = UnitOfEnergy.KILO_WATT_HOUR
        self._attr_device_class = SensorDeviceClass.ENERGY
        # Changed from MEASUREMENT to TOTAL to comply with HA requirements
        self._attr_state_class = SensorStateClass.TOTAL
        self._attr_icon = "mdi:battery-charging-medium"
        
    @property
    def unique_id(self):
        """Return unique ID for the sensor."""
        return f"{DOMAIN}_battery_{self.battery_num}_stored_energy"
        
    @property
    def native_value(self):
        """Return the stored energy value."""
        if not self.coordinator.data:
            return 0
            
        stored_energy = self.coordinator.data.get("battery_stored_energy", {})
        return round(stored_energy.get(self.battery_num, 0), 2)
        
    @property
    def extra_state_attributes(self):
        """Return additional attributes."""
        if not self.coordinator.data:
            return {}
            
        capacities = self.coordinator.data.get("battery_capacities", {})
        capacity = capacities.get(self.battery_num, 5.12)
        
        stored_energy = self.coordinator.data.get("battery_stored_energy", {})
        energy = stored_energy.get(self.battery_num, 0)
        
        # Calculate percentage
        percentage = (energy / capacity) * 100 if capacity > 0 else 0
        
        return {
            "capacity_kwh": round(capacity, 2),
            "percentage": round(percentage, 1),
        }


class TotalStoredEnergySensor(BatteryEnergySensor):
    """Sensor to track total energy stored across all batteries."""

    _attr_name = "Total Stored Energy"
    _attr_native_unit_of_measurement = UnitOfEnergy.KILO_WATT_HOUR
    _attr_device_class = SensorDeviceClass.ENERGY
    # Changed from MEASUREMENT to TOTAL to comply with HA requirements
    _attr_state_class = SensorStateClass.TOTAL
    _attr_icon = "mdi:battery-charging"

    @property
    def unique_id(self):
        """Return unique ID for the sensor."""
        return f"{DOMAIN}_total_stored_energy"
    
    @property
    def native_value(self):
        """Return the total stored energy value."""
        if not self.coordinator.data:
            return 0
        
        return round(self.coordinator.data.get("total_stored_energy", 0), 2)
    
    @property
    def extra_state_attributes(self):
        """Return additional attributes."""
        if not self.coordinator.data:
            return {}
        
        # Get the percentage
        percentage = self.coordinator.data.get("total_stored_energy_percent", 0)
    
        # Get the individual battery values
        stored_energy = self.coordinator.data.get("battery_stored_energy", {})
        per_battery = {f"battery_{bnum}": round(energy, 2) for bnum, energy in stored_energy.items()}
    
        return {
            "percentage": round(percentage, 1),
            "per_battery": per_battery,
        }