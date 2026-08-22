from unittest.mock import AsyncMock

import dns.resolver
import pytest

from pulseroute.common.email_validator import email_domain_accepts_mail


@pytest.mark.asyncio
async def test_accepts_domain_with_mx_record(monkeypatch):
    monkeypatch.setattr("dns.asyncresolver.Resolver.resolve", AsyncMock(return_value=["mx.example.com"]))
    assert await email_domain_accepts_mail("user@example.com") is True


@pytest.mark.asyncio
async def test_falls_back_to_a_record_when_no_mx(monkeypatch):
    async def fake_resolve(self, domain, record_type):
        if record_type == "MX":
            raise dns.resolver.NoAnswer()
        return ["1.2.3.4"]

    monkeypatch.setattr("dns.asyncresolver.Resolver.resolve", fake_resolve)
    assert await email_domain_accepts_mail("user@a-record-only.example") is True


@pytest.mark.asyncio
async def test_rejects_nonexistent_domain(monkeypatch):
    monkeypatch.setattr("dns.asyncresolver.Resolver.resolve", AsyncMock(side_effect=dns.resolver.NXDOMAIN()))
    assert await email_domain_accepts_mail("user@asdkjhaskjdh-not-real.invalid") is False


@pytest.mark.asyncio
async def test_fails_open_on_resolver_error(monkeypatch):
    monkeypatch.setattr("dns.asyncresolver.Resolver.resolve", AsyncMock(side_effect=TimeoutError()))
    assert await email_domain_accepts_mail("user@example.com") is True
