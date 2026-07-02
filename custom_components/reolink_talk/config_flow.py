from __future__ import annotations

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers import selector

from .const import CONF_CHANNEL, CONF_REOLINK_ENTRY_IDS, DEFAULT_CHANNEL, DOMAIN


class ReolinkTalkConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        # One-click setup: we don't ask for credentials; we piggyback on the official
        # Reolink integration config entries.
        if self._async_current_entries():
            return self.async_abort(reason="single_instance_allowed")
        return self.async_create_entry(title="Reolink Talk", data={})

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: config_entries.ConfigEntry):
        return ReolinkTalkOptionsFlowHandler(config_entry)


class ReolinkTalkOptionsFlowHandler(config_entries.OptionsFlow):
    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        self._config_entry = config_entry

    async def async_step_init(self, user_input=None):
        hass = self.hass
        reolink_entries = hass.config_entries.async_entries("reolink")
        entry_map = {e.entry_id: e.title for e in reolink_entries}

        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        schema = vol.Schema(
            {
                vol.Optional(
                    CONF_REOLINK_ENTRY_IDS,
                    default=self._config_entry.options.get(CONF_REOLINK_ENTRY_IDS, list(entry_map.keys())),
                ): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=[selector.SelectOptionDict(value=eid, label=title) for eid, title in entry_map.items()],
                        multiple=True,
                        mode=selector.SelectSelectorMode.DROPDOWN,
                    )
                ),
                vol.Optional(
                    CONF_CHANNEL,
                    default=self._config_entry.options.get(CONF_CHANNEL, DEFAULT_CHANNEL),
                ): vol.Coerce(int),
            }
        )

        return self.async_show_form(step_id="init", data_schema=schema)
