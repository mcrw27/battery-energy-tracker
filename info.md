# Battery Energy Tracker

Track energy usage and charge status for your battery system with accurate metrics and detailed insights.

[![GitHub Release](https://img.shields.io/github/release/mcrw27/battery-energy-tracker.svg)](https://github.com/mcrw27/battery-energy-tracker/releases)
[![GitHub License](https://img.shields.io/github/license/mcrw27/battery-energy-tracker.svg)](LICENSE)

## Features

- 📊 Track charge/discharge energy with counter rollover handling
- 🔋 Monitor stored energy levels for multiple batteries
- ⚡ Calculate real-time charge rates based on current and voltage
- 🕒 Estimate remaining charge time based on usage patterns
- 💾 Persist energy data across Home Assistant restarts
- 🔍 Diagnostic tools for troubleshooting battery issues

## Quick Setup

1. Install the integration
2. Configure the number of batteries and charging rate
3. The integration will automatically detect your battery entities
4. Use the sensors in your dashboards and automations

## Available Sensors

- Total Discharge Energy
- Total Charge Energy
- Energy Since Last Charge
- Estimated Charge Time
- Charge Status
- Charge Rate
- Total Stored Energy
- Individual Battery Stored Energy

## Useful Services

- `reset_counters`: Reset all energy counters
- `set_battery_stored_energy`: Set the current energy level for a battery
- `set_battery_to_full`: Mark one or all batteries as fully charged

## Need Help?

- [Full Documentation](https://github.com/mcrw27/battery-energy-tracker)
- [Report an Issue](https://github.com/mcrw27/battery-energy-tracker/issues)