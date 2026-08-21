import time
from typing import Optional

import redis.asyncio as aioredis
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

# Memory fallback jail for brute force: {ip: [fail_timestamps]}
_memory_jail: dict[str, list[float]] = {}


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response: Response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self' https:; "
            "script-src 'self' 'unsafe-inline' https://cdn.tailwindcss.com https://cdn.jsdelivr.net https://cdnjs.cloudflare.com https://pagead2.googlesyndication.com https://adservice.google.com; "
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com https://cdnjs.cloudflare.com; "
            "font-src 'self' https://fonts.gstatic.com https://cdnjs.cloudflare.com; "
            "frame-src 'self' https://googleads.g.doubleclick.net https://tpc.googlesyndication.com https://www.google.com; "
            "img-src 'self' data: https:;"
        )
        return response


class BruteForceGuard:
    @staticmethod
    async def is_ip_jailed(redis_cli: Optional[aioredis.Redis], ip: str) -> bool:
        if redis_cli:
            try:
                locked = await redis_cli.get(f"jail:login:{ip}")
                return bool(locked)
            except Exception:
                pass

        now = time.time()
        failures = [ts for ts in _memory_jail.get(ip, []) if now - ts < 900]  # 15 minutes
        return len(failures) >= 5

    @staticmethod
    async def record_failure(redis_cli: Optional[aioredis.Redis], ip: str) -> None:
        now = time.time()
        if redis_cli:
            try:
                key = f"jail:fails:{ip}"
                count = await redis_cli.incr(key)
                if count == 1:
                    await redis_cli.expire(key, 900)
                if count >= 5:
                    await redis_cli.set(f"jail:login:{ip}", "locked", ex=900)
                return
            except Exception:
                pass

        failures = [ts for ts in _memory_jail.get(ip, []) if now - ts < 900]
        failures.append(now)
        _memory_jail[ip] = failures

    @staticmethod
    async def record_success(redis_cli: Optional[aioredis.Redis], ip: str) -> None:
        if redis_cli:
            try:
                await redis_cli.delete(f"jail:fails:{ip}")
                await redis_cli.delete(f"jail:login:{ip}")
            except Exception:
                pass
        _memory_jail.pop(ip, None)
