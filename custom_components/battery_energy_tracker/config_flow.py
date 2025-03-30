"""Config flow for Battery Energy Tracker integration."""
from __future__ import annotations

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant, callback
from homeassistant.data_entry_flow import FlowResult

from .const import (
    DOMAIN,
    CONF_BATTERY_COUNT,
    CONF_CHARGE_RATE,
    CONF_SCALE_FACTOR,
    CONF_STARTUP_DELAY,
    DEFAULT_CHARGE_RATE,
    DEFAULT_SCALE_FACTOR,
)

CONFIG_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_BATTERY_COUNT, default=4): vol.All(
            vol.Coerce(int), vol.Range(min=1, max=16)
        ),
        vol.Required(CONF_CHARGE_RATE, default=DEFAULT_CHARGE_RATE): vol.All(
            vol.Coerce(float), vol.Range(min=100, max=10000)
        ),
        vol.Optional(CONF_STARTUP_DELAY, default=0): vol.All(
            vol.Coerce(int), vol.Range(min=0, max=300)
        ),
        vol.Optional(CONF_SCALE_FACTOR, default=DEFAULT_SCALE_FACTOR): vol.All(
            vol.Coerce(float), vol.Range(min=0.001, max=10)
        ),
    }
)


class BatteryEnergyTrackerConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Battery Energy Tracker."""

    VERSION = 1

    async def async_step_user(self, user_input=None) -> FlowResult:
        """Handle the initial step."""
        if user_input is None:
            return self.async_show_form(
                step_id="user", data_schema=CONFIG_SCHEMA
            )

        await self.async_set_unique_id(DOMAIN)
        self._abort_if_unique_id_configured()

        return self.async_create_entry(
            title="Battery Energy Tracker",
            data=user_input,
        )