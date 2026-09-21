#!/usr/bin/env python3
"""Verify Stage 2: Sparta.AI service reads SCADA data from PostgreSQL."""
import json
import os
import sys
import urllib.request
from datetime import datetime, timezone

BASE_URL = os.getenv("AI_SERVICE_URL", "http://localhost:8000")
EXPECTED_CHANNELS = {101, 102, 103, 104, 105, 106}
MAX_AGE_SECONDS = 120


def fetch_json(path: str, method: str = "GET", body: dict | None = None) -> dict | list:
    url = f"{BASE_URL}{path}"
    data = None
    headers = {}
    if body is not None:
        data = json.dumps(body).encode("utf-8")
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    with urllib.request.urlopen(req, timeout=10) as resp:
        return json.loads(resp.read().decode("utf-8"))


def main() -> int:
    try:
        health = fetch_json("/health")
        print(f"Health: {health}")
        if health.get("database") != "connected":
            print("Database is not connected")
            return 1

        tags = fetch_json("/tags")
        print(f"Tags count: {len(tags)}")
        found_channels = {tag["cnl_num"] for tag in tags}
        missing = EXPECTED_CHANNELS - found_channels
        if missing:
            print(f"Missing channels: {missing}")
            return 1

        latest_ts = max(
            datetime.fromisoformat(tag["time_stamp"].replace("Z", "+00:00"))
            for tag in tags
        )
        age = (datetime.now(timezone.utc) - latest_ts).total_seconds()
        print(f"Latest data age: {age:.1f} seconds")
        if age > MAX_AGE_SECONDS:
            print("Data is stale")
            return 1

        history = fetch_json("/history?cnl_num=104&limit=5")
        print(f"History rows for cnl 104: {len(history)}")
        if not history:
            print("No history returned")
            return 1

        analysis = fetch_json(
            "/analyze",
            method="POST",
            body={"tag_code": "SpikeData", "method": "zscore", "threshold": 3.0},
        )
        print(f"Anomalies found: {len(analysis['anomalies'])}")

        print("\nStage 2 verification passed: Sparta.AI service is reading SCADA data.")
        return 0
    except Exception as e:
        print(f"Verification failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
