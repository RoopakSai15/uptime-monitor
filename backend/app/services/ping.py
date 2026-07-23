import time
import httpx


async def check_url(url: str):
    start = time.perf_counter()
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(url)

        elapsed = (time.perf_counter() - start) * 100
        return {
            "status_code": response.status_code,
            "response_time_ms": round(elapsed),
            "is_up": response.status_code < 400,
        }
    except Exception:
        return {"status_code": None, "response_time_ms": None, "is_up": False}
