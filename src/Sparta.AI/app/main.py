"""FastAPI application for Sparta AI service."""
from datetime import datetime, timedelta, timezone
from typing import Literal

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field

from . import analytics, channels, db
from .config import get_settings

app = FastAPI(
    title="Sparta AI Service",
    description="Local AI analytics for Rapid SCADA PostgreSQL archive.",
    version="0.1.0",
)


class AnalyzeRequest(BaseModel):
    cnl_num: int | None = None
    tag_code: str | None = None
    from_time: datetime | None = Field(None, alias="from")
    to_time: datetime | None = Field(None, alias="to")
    method: Literal["zscore", "ewma"] = "zscore"
    threshold: float = 3.0
    ewma_span: int = 10
    limit: int = 1000


class PredictRequest(BaseModel):
    cnl_num: int | None = None
    tag_code: str | None = None
    from_time: datetime | None = Field(None, alias="from")
    to_time: datetime | None = Field(None, alias="to")
    steps: int = 10
    limit: int = 500


@app.get("/health")
def health() -> dict:
    db_ok = db.check_connection()
    return {
        "status": "ok" if db_ok else "degraded",
        "database": "connected" if db_ok else "unavailable",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@app.get("/tags")
def get_tags() -> list[dict]:
    rows = db.list_current_values()
    return channels.enrich_current_values(rows)


@app.get("/history")
def get_history(
    cnl_num: int | None = Query(None),
    tag_code: str | None = Query(None),
    dt_from: datetime | None = Query(None, alias="from"),
    dt_to: datetime | None = Query(None, alias="to"),
    limit: int = Query(1000, ge=1, le=100000),
) -> list[dict]:
    resolved = _resolve_channel(cnl_num, tag_code)
    rows = db.get_history(resolved, dt_from, dt_to, limit)
    return rows


@app.post("/analyze")
def analyze(req: AnalyzeRequest) -> dict:
    resolved = _resolve_channel(req.cnl_num, req.tag_code)
    dt_to = req.to_time or datetime.now(timezone.utc)
    dt_from = req.from_time or dt_to - timedelta(hours=1)

    rows = db.get_history(resolved, dt_from, dt_to, req.limit)
    if not rows:
        raise HTTPException(status_code=404, detail="No historical data found for the channel")

    # Chronological order for analysis.
    rows = list(reversed(rows))
    values = [row["val"] for row in rows]
    timestamps = [row["time_stamp"] for row in rows]

    stats = analytics.compute_stats(values)
    if req.method == "zscore":
        anomalies = analytics.zscore_anomalies(values, req.threshold)
    else:
        anomalies = analytics.ewma_anomalies(values, req.ewma_span, req.threshold)

    return {
        "cnl_num": resolved,
        "from": dt_from.isoformat(),
        "to": dt_to.isoformat(),
        "method": req.method,
        "threshold": req.threshold,
        "stats": {
            "count": stats.count,
            "mean": stats.mean,
            "std": stats.std,
            "min": stats.min,
            "max": stats.max,
        },
        "anomalies": [
            {
                "index": a.index,
                "time_stamp": timestamps[a.index].isoformat(),
                "value": a.value,
                "score": a.score,
            }
            for a in anomalies
        ],
    }


@app.post("/predict")
def predict(req: PredictRequest) -> dict:
    resolved = _resolve_channel(req.cnl_num, req.tag_code)
    dt_to = req.to_time or datetime.now(timezone.utc)
    dt_from = req.from_time or dt_to - timedelta(hours=1)

    rows = db.get_history(resolved, dt_from, dt_to, req.limit)
    if len(rows) < 2:
        raise HTTPException(status_code=400, detail="Not enough historical data for prediction")

    rows = list(reversed(rows))
    timestamps = [row["time_stamp"].timestamp() for row in rows]
    values = [row["val"] for row in rows]

    forecast = analytics.linear_forecast(timestamps, values, req.steps)
    return {
        "cnl_num": resolved,
        "steps": req.steps,
        "forecast": [
            {
                "time_stamp": datetime.fromtimestamp(ts, tz=timezone.utc).isoformat(),
                "value": val,
            }
            for ts, val in forecast
        ],
    }


def _resolve_channel(cnl_num: int | None, tag_code: str | None) -> int:
    if cnl_num is not None:
        return cnl_num
    if tag_code:
        resolved = channels.resolve_cnl_num(tag_code)
        if resolved is not None:
            return resolved
        raise HTTPException(status_code=404, detail=f"Channel with tag_code '{tag_code}' not found")
    raise HTTPException(status_code=400, detail="Either cnl_num or tag_code must be provided")
