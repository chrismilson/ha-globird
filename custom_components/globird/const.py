"""Constants for the GloBird integration."""

from __future__ import annotations

from datetime import timedelta

DOMAIN = "globird"

CONF_EMAIL = "email"
CONF_PASSWORD = "password"  # nosec B105 - configuration key name, not a secret
CONF_DAILY_POLL_START_TIME = "daily_poll_start_time"
DEFAULT_DAILY_POLL_START_TIME = "00:05"

# Options key holding {f"{service_id}:{register_slug}": rate} AUD/kWh rates for
# registers that get their own usage statistic. Configured rates let the
# integration import a per-register (and usage-total) daily cost statistic for
# the Energy Dashboard, which cannot price external statistics itself. The
# options form shows and takes the rates in AUD-cents per kWh, the unit the
# GloBird bill uses, and stores them converted to AUD/kWh.
CONF_REGISTER_RATES = "register_rates"

BASE_URL = "https://myaccount.globirdenergy.com.au"

DEFAULT_USAGE_DAYS = 31
DEFAULT_GAS_READING_DAYS = 365
DEFAULT_INVOICE_LIMIT = 20
DEFAULT_INVOICE_MONTHS = 12

ACCOUNT_UPDATE_INTERVAL = timedelta(minutes=30)

STORAGE_VERSION = 1

SENSITIVE_KEYS = {
    "accessToken",
    "accountAddress",
    "accountName",
    "accountNumber",
    "address",
    "concessionAddress",
    "documentId",
    "email",
    "emailAddress",
    "identifier",
    "invoiceNumber",
    "nmi",
    "password",
    "serial",
    "serialNumber",
    "siteAddress",
    "siteIdentifier",
    "streetAddress",
}
