import logging

import structlog

SENSITIVE_KEY_SUBSTRINGS = (
    "password",
    "secret",
    "token",
    "authorization",
    "cookie",
    "api_key",
    "apikey",
    "private_key",
)


def mask_email(email_str: str) -> str:
    """Masks email address for KVKK / GDPR compliance (e.g. user@domain.com -> u***@domain.com)."""
    if "@" in email_str:
        user, domain = email_str.split("@", 1)
        if len(user) <= 1:
            masked_user = user + "***"
        else:
            masked_user = user[0] + "***"
        return f"{masked_user}@{domain}"
    return email_str


def mask_sensitive_data(logger, method_name, event_dict):
    """
    Structlog processor that sanitizes PII and sensitive credentials in-place.
    Protects against inadvertent leakage of tokens, passwords, cookies, and personal emails
    in compliance with KVKK (Law No. 6698) and GDPR.
    """
    for key in list(event_dict.keys()):
        key_lower = key.lower()

        # 1. Redact credentials & tokens
        if any(substr in key_lower for substr in SENSITIVE_KEY_SUBSTRINGS):
            event_dict[key] = "[REDACTED]"
            continue

        val = event_dict[key]

        # 2. Mask personal emails
        if isinstance(val, str) and ("email" in key_lower or "reporter" in key_lower):
            event_dict[key] = mask_email(val)

    return event_dict


class HealthCheckAccessLogFilter(logging.Filter):
    """
    Filters out noisy automated liveness probe logs (/healtalive, /healthz) from uvicorn access logs.
    Preserves logs if status code indicates failure (>= 400) to ensure outages remain visible.
    """

    def filter(self, record: logging.LogRecord) -> bool:
        msg = record.getMessage()
        if "/healtalive" in msg or "/healthz" in msg:
            # If the probe failed with 4xx or 5xx, do NOT filter it out
            if any(f" {status} " in msg for status in ("500", "502", "503", "504", "400", "404")):
                return True
            return False
        return True


def setup_logging(debug: bool = False) -> None:
    log_level = logging.DEBUG if debug else logging.INFO
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            mask_sensitive_data,
            structlog.dev.ConsoleRenderer() if debug else structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(log_level),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )

    # Filter out recurring healthcheck access log lines to keep Render logs clean and save bandwidth
    access_logger = logging.getLogger("uvicorn.access")
    if not any(isinstance(f, HealthCheckAccessLogFilter) for f in access_logger.filters):
        access_logger.addFilter(HealthCheckAccessLogFilter())
