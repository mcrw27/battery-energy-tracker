# Battery Energy Tracker

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/custom-components/hacs)
[![GitHub Release](https://img.shields.io/github/release/mcrw27/battery-energy-tracker/battery_energy_tracer/icon.svg)](https://github.com/mcrw27/battery-energy-tracker/releases)
[![GitHub License](https://img.shields.io/github/license/mcrw27/battery-energy-tracker/battery_energy_tracer/icon.svg)](https://github.com/mcrw27/battery-energy-tracker/blob/main/LICENSE)

A Home Assistant integration that tracks battery energy data, handling counter rollovers and providing accurate charge/discharge metrics.

## Features

- Accurate tracking of battery charge and discharge energy
- Persistent storage of energy data across restarts
- Handling of counter rollovers
- Estimation of charge time
- Automatic detection of battery entities
- Detailed battery energy storage tracking
- Diagnostic information
- Custom services for managing battery data

## Installation

### HACS (Recommended)

1. Make sure [HACS](https://hacs.xyz/) is installed in your Home Assistant instance
2. Add this repository as a custom repository in HACS:
   - Go to HACS → Integrations
   - Click the three dots in the top right corner
   - Select "Custom repositories"
   - Enter `https://github.com/mcrw27/battery-energy-tracker` in the repository field
   - Select "Integration" as the category
   - Click "Add"
3. Click on "Battery Energy Tracker" in the integration list
4. Click "Download"
5. Restart Home Assistant

### Manual Installation

1. Download the latest release from the [releases page](https://github.com/mcrw27/battery-energy-tracker/releases)
2. Unpack the release and copy the `custom_components/battery_energy_tracker` directory to your Home Assistant's `custom_components` directory
3. Restart Home Assistant

## Configuration

The integration can be configured through the Home Assistant UI:

1. Go to Settings → Devices & Services
2. Click the "+ Add Integration" button
3. Search for "Battery Energy Tracker"
4. Follow the configuration steps

### Configuration Parameters

- **battery_count**: Number of batteries to track (1-16)
  - Default: 4
  - This is the primary configuration parameter used throughout the system.

- **charge_rate**: Battery charging rate in Watts
  - Default: 1500
  - This is used as a fallback when calculating estimated charge time if real-time charge rates can't be determined from current and voltage readings.

- **scale_factor**: Scale factor for counter values
  - Default: 0.1
  - This parameter is maintained for backward compatibility but most calculations now use a fixed conversion factor of 0.001.

- **startup_delay**: Delay in seconds before starting tracking
  - Default: 0
  - Range: 0-300
  - This parameter is available in the configuration but may not be actively used in the current implementation.

### Entity Detection and Pattern Overrides

The integration tries to automatically find your battery entities using predefined patterns. By default, it looks for entities with these patterns:

- Discharge counters: `sensor.antra_battery_{}_total_discharge`
- Charge counters: `sensor.antra_battery_{}_total_charge`
- Current sensors: `sensor.antra_battery_{}_current`

Where `{}` is replaced with the battery number (1, 2, 3, etc.).

#### Custom Entity Patterns

If your entities don't match these patterns, you can specify custom patterns in your YAML configuration:

```yaml
battery_energy_tracker:
  battery_count: 4
  entity_patterns:
    discharge: "sensor.my_battery_{}_discharge_counter"
    charge: "sensor.my_battery_{}_charge_counter"
    current: "sensor.my_battery_{}_current_reading"
```

#### Manual Entity Specification

For complete control, you can manually specify exact entity IDs for each battery:

```yaml
battery_energy_tracker:
  battery_count: 4
  manual_entities:
    discharge:
      - "sensor.battery1_discharge"
      - "sensor.battery2_discharge"
      - "sensor.battery3_discharge"
      - "sensor.battery4_discharge"
    charge:
      - "sensor.battery1_charge"
      - "sensor.battery2_charge"
      - "sensor.battery3_charge"
      - "sensor.battery4_charge"
    current:
      - "sensor.battery1_current"
      - "sensor.battery2_current"
      - "sensor.battery3_current"
      - "sensor.battery4_current"
```

### Basic YAML Configuration

A simple configuration in `configuration.yaml`:

```yaml
battery_energy_tracker:
  battery_count: 4  # Number of batteries
  charge_rate: 1500  # Battery charging rate in Watts (fallback value)
```

## Services

The integration provides several services to manage your battery data:

- `battery_energy_tracker.reset_counters`: Reset all energy counters to zero
- `battery_energy_tracker.reset_energy_since_charge`: Reset only the energy since last charge counter
- `battery_energy_tracker.set_charge_state`: Manually set the charging state
- `battery_energy_tracker.adjust_counters`: Adjust counter values
- `battery_energy_tracker.set_battery_stored_energy`: Set the stored energy for a specific battery
- `battery_energy_tracker.set_battery_to_full`: Set one or all batteries to full capacity
- `battery_energy_tracker.set_battery_capacity`: Set the maximum capacity for a specific battery

## Sensors

The integration creates the following sensors:

- **Total Discharge Energy**: Total energy discharged from batteries
- **Total Charge Energy**: Total energy charged to batteries
- **Energy Since Last Charge**: Energy used since the last completed charge
- **Estimated Charge Time**: Estimated time needed to recharge
- **Charge Status**: Current charging status
- **Charge Rate**: Current charging rate when charging
- **Total Stored Energy**: Total energy stored across all batteries
- **Individual Battery Stored Energy**: Energy stored in each battery

## Dashboard Examples

### Energy Overview Card

![Energy Overview](https://raw.githubusercontent.com/mcrw27/battery-energy-tracker/main/battery-energy-tracker/battery_energy_tracer/icon.svg)

### Battery Status Card

![Battery Status](https://raw.githubusercontent.com/mcrw27/battery-energy-tracker/main/battery-energy-tracker/battery_energy_tracer/icon.svg)

## Troubleshooting

If the integration isn't detecting your battery entities correctly:

1. Check the logs for entity detection issues
2. Use the diagnostic sensor to see detected entities
3. Try using custom entity patterns or manual entity specification (see Configuration section)
4. Increase log level for better diagnostics:
   ```yaml
   logger:
     logs:
       custom_components.battery_energy_tracker: debug
   ```

If total discharge or charge values aren't updating:

1. Check if the entity detection found the correct entities
2. Verify the sensor values are numeric and increasing
3. Use the diagnostic sensor to check counter values

If metrics aren't persisting across restarts:

1. Check the Home Assistant logs for any storage-related errors
2. Ensure the integration has proper permissions to write to storage

## Support

- Report issues on [GitHub](https://github.com/mcrw27/battery-energy-tracker/issues)
- Ask questions in the [Home Assistant Community Forum](https://community.home-assistant.io/)

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.