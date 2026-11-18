"""Config flow for GloBird."""

from __future__ import annotations

import logging
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any

from homeassistant import config_entries
from homeassistant.config_entries import ConfigFlowResult
from homeassistant.helpers import selector

from .client import GloBirdAuthError, GloBirdCaptchaRequired, GloBirdClient, service_id
from .const import (
    CONF_DAILY_POLL_START_TIME,
    CONF_EMAIL,
    CONF_PASSWORD,
    CONF_REGISTER_RATES,
    DEFAULT_DAILY_POLL_START_TIME,
    DOMAIN,
)

if TYPE_CHECKING:
    import probatio as vol
else:
    # Core aliases this import to Probatio from 2026.9 onward.
    import voluptuous as vol

_LOGGER = logging.getLogger(__name__)


def _credentials_schema(default_email: str | None = None) -> vol.Schema:
    """Build the credentials form schema."""
    email_key = (
        vol.Required(CONF_EMAIL, default=default_email)
        if default_email
        else vol.Required(CONF_EMAIL)
    )
    return vol.Schema(
        {
            email_key: str,
            vol.Required(CONF_PASSWORD): selector.TextSelector(
                selector.TextSelectorConfig(type=selector.TextSelectorType.PASSWORD)
            ),
        }
    )


class GloBirdConfigFlow(  # pyright: ignore[reportGeneralTypeIssues, reportCallIssue]
    config_entries.ConfigFlow,
    domain=DOMAIN,
):
    """Handle a config flow for GloBird."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize the config flow."""
        super().__init__()
        self._reauth_entry: config_entries.ConfigEntry | None = None

    @staticmethod
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> GloBirdOptionsFlow:
        """Create the options flow."""
        return GloBirdOptionsFlow()

    async def _async_validate_credentials(
        self, email: str, password: str
    ) -> dict[str, str]:
        """Validate portal credentials and return any flow error mapping."""
        errors: dict[str, str] = {}
        client = GloBirdClient()
        try:
            await client.authenticate(email, password)
        except GloBirdCaptchaRequired:
            errors["base"] = "captcha_required"
        except GloBirdAuthError:
            errors["base"] = "invalid_auth"
        except Exception:
            _LOGGER.exception("Unexpected GloBird setup failure")
            errors["base"] = "cannot_connect"
        finally:
            await client.close()
        return errors

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial setup step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            email = str(user_input[CONF_EMAIL]).strip()
            password = str(user_input[CONF_PASSWORD])

            await self.async_set_unique_id(email.lower())
            self._abort_if_unique_id_configured()

            errors = await self._async_validate_credentials(email, password)
            if not errors:
                return self.async_create_entry(
                    title=email,
                    data={
                        CONF_EMAIL: email,
                        CONF_PASSWORD: password,
                    },
                )

        return self.async_show_form(
            step_id="user",
            data_schema=_credentials_schema(),
            errors=errors,
        )

    async def async_step_reauth(
        self, entry_data: Mapping[str, Any]
    ) -> ConfigFlowResult:
        """Handle initiation of re-authentication with GloBird."""
        if hasattr(self, "_get_reauth_entry"):
            self._reauth_entry = self._get_reauth_entry()
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Confirm re-authentication credentials."""
        reauth_entry = self._reauth_entry
        if reauth_entry is None and hasattr(self, "_get_reauth_entry"):
            reauth_entry = self._get_reauth_entry()
        default_email = (
            str(reauth_entry.data.get(CONF_EMAIL, ""))
            if reauth_entry is not None
            else ""
        )
        errors: dict[str, str] = {}

        if user_input is not None:
            email = str(user_input.get(CONF_EMAIL) or default_email).strip()
            password = str(user_input[CONF_PASSWORD])
            errors = await self._async_validate_credentials(email, password)
            if not errors:
                await self.async_set_unique_id(email.lower())
                if hasattr(self, "_abort_if_unique_id_mismatch"):
                    self._abort_if_unique_id_mismatch(reason="wrong_account")
                if reauth_entry is not None and hasattr(
                    self, "async_update_reload_and_abort"
                ):
                    return self.async_update_reload_and_abort(
                        reauth_entry,
                        data_updates={
                            CONF_EMAIL: email,
                            CONF_PASSWORD: password,
                        },
                    )
                return self.async_create_entry(
                    title=email,
                    data={
                        CONF_EMAIL: email,
                        CONF_PASSWORD: password,
                    },
                )

        return self.async_show_form(
            step_id="reauth_confirm",
            data_schema=_credentials_schema(default_email or None),
            errors=errors,
        )

    async def async_step_reconfigure(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle reconfiguration of an existing GloBird config entry."""
        reconfigure_entry = (
            self._get_reconfigure_entry()
            if hasattr(self, "_get_reconfigure_entry")
            else None
        )
        default_email = (
            str(reconfigure_entry.data.get(CONF_EMAIL, ""))
            if reconfigure_entry is not None
            else ""
        )
        errors: dict[str, str] = {}

        if user_input is not None:
            email = str(user_input.get(CONF_EMAIL) or default_email).strip()
            password = str(user_input[CONF_PASSWORD])
            errors = await self._async_validate_credentials(email, password)
            if not errors:
                await self.async_set_unique_id(email.lower())
                if hasattr(self, "_abort_if_unique_id_mismatch"):
                    self._abort_if_unique_id_mismatch(reason="wrong_account")
                if reconfigure_entry is not None and hasattr(
                    self, "async_update_reload_and_abort"
                ):
                    return self.async_update_reload_and_abort(
                        reconfigure_entry,
                        data_updates={
                            CONF_EMAIL: email,
                            CONF_PASSWORD: password,
                        },
                    )
                return self.async_create_entry(
                    title=email,
                    data={
                        CONF_EMAIL: email,
                        CONF_PASSWORD: password,
                    },
                )

        return self.async_show_form(
            step_id="reconfigure",
            data_schema=_credentials_schema(default_email or None),
            errors=errors,
        )


def _register_label(register: dict[str, Any]) -> str:
    """Return a readable label for a usage register."""
    parts = [
        str(register.get("suffix") or "").strip(),
        str(register.get("chargeType") or "").strip(),
    ]
    label = " ".join(part for part in parts if part)
    return label or str(register.get("slug") or "register")


RATE_FIELD_MIN = -100
RATE_FIELD_MAX = 1000
# Home Assistant's number selector rejects steps smaller than 0.001.
RATE_FIELD_STEP = 0.001


class GloBirdOptionsFlow(config_entries.OptionsFlowWithReload):
    """Handle GloBird options."""

    def __init__(self) -> None:
        """Initialize the options flow."""
        super().__init__()
        self._stored_rates: dict[str, float] = {}

    def _register_rate_fields(
        self, entry: config_entries.ConfigEntry
    ) -> dict[str, Any]:
        """Return per-register rate field configs keyed by ``service_id:slug``.

        Only electricity registers that get their own usage statistic
        (``register_sensor``) and are imported can be priced: the portal's
        cost rows have no register split, so their cost is computed from the
        register's daily usage and the configured rate.
        """
        coordinator = getattr(entry, "runtime_data", None)
        data = getattr(coordinator, "data", None)
        if not isinstance(data, dict):
            return {}
        service_data = data.get("service_data")
        if not isinstance(service_data, dict):
            return {}

        services = data.get("services")
        electricity = [
            service
            for service in (services if isinstance(services, list) else [])
            if isinstance(service, dict)
            and "gas" not in str(service.get("serviceType") or "").lower()
        ]
        show_sites = len(electricity) > 1
        fields: dict[str, Any] = {}
        for service in electricity:
            sid = service_id(service)
            detail = service_data.get(sid)
            if not isinstance(detail, dict):
                continue
            summary = detail.get("usage_summary")
            registers = (
                summary.get("registers") if isinstance(summary, dict) else None
            ) or []
            site = str(
                service.get("siteIdentifier") or service.get("accountServiceId") or ""
            ).strip()
            for register in registers:
                if not isinstance(register, dict):
                    continue
                if not register.get("register_sensor"):
                    continue
                if register.get("direction") != "import":
                    continue
                slug = str(register.get("slug") or "").strip()
                if not slug:
                    continue
                label = _register_label(register)
                if show_sites and site:
                    label = f"{label} ({site})"
                key = f"{sid}:{slug}"
                field: dict[str, Any] = {
                    "label": f"{label} rate (AUD/kWh)",
                    "selector": selector.NumberSelector(
                        selector.NumberSelectorConfig(
                            min=RATE_FIELD_MIN,
                            max=RATE_FIELD_MAX,
                            step=RATE_FIELD_STEP,
                            unit_of_measurement="AUD/kWh",
                            mode=selector.NumberSelectorMode.BOX,
                        )
                    ),
                    "required": False,
                }
                if key in self._stored_rates:
                    field["default"] = self._stored_rates[key]
                fields[key] = field
        return fields

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Manage integration options."""
        if user_input is not None:
            data = dict(user_input)
            submitted = data.get(CONF_REGISTER_RATES)
            if isinstance(submitted, dict):
                for key, value in submitted.items():
                    if not isinstance(key, str) or not key:
                        continue
                    try:
                        rate = float(value)
                    except (TypeError, ValueError):
                        continue
                    self._stored_rates[key] = rate
            data[CONF_REGISTER_RATES] = self._stored_rates
            return self.async_create_entry(title="", data=data)

        entry = self.config_entry
        current_time = entry.options.get(
            CONF_DAILY_POLL_START_TIME,
            DEFAULT_DAILY_POLL_START_TIME,
        )
        stored_rates = entry.options.get(CONF_REGISTER_RATES)
        self._stored_rates = (
            {
                str(key): float(value)
                for key, value in stored_rates.items()
                if isinstance(value, (int, float))
            }
            if isinstance(stored_rates, dict)
            else {}
        )

        schema: dict[Any, Any] = {
            vol.Required(
                CONF_DAILY_POLL_START_TIME,
                default=current_time,
            ): selector.TimeSelector(),
        }
        if rate_fields := self._register_rate_fields(entry):
            schema[vol.Optional(CONF_REGISTER_RATES)] = selector.ObjectSelector(
                selector.ObjectSelectorConfig(fields=rate_fields)
            )

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(schema),
        )
