"""Analytics utilities: anomaly detection and simple forecasting."""
from dataclasses import dataclass
from typing import Sequence

import numpy as np


@dataclass
class SeriesStats:
    count: int
    mean: float
    std: float
    min: float
    max: float


@dataclass
class Anomaly:
    index: int
    value: float
    score: float


def compute_stats(values: Sequence[float]) -> SeriesStats:
    arr = np.asarray(values, dtype=float)
    return SeriesStats(
        count=int(arr.size),
        mean=float(arr.mean()),
        std=float(arr.std()),
        min=float(arr.min()),
        max=float(arr.max()),
    )


def zscore_anomalies(values: Sequence[float], threshold: float = 3.0) -> list[Anomaly]:
    arr = np.asarray(values, dtype=float)
    if arr.size < 2:
        return []
    mean = arr.mean()
    std = arr.std()
    if std == 0:
        return []
    scores = np.abs((arr - mean) / std)
    indices = np.where(scores > threshold)[0]
    return [
        Anomaly(index=int(i), value=float(arr[i]), score=float(scores[i]))
        for i in indices
    ]


def ewma_anomalies(values: Sequence[float], span: int = 10, threshold: float = 3.0) -> list[Anomaly]:
    arr = np.asarray(values, dtype=float)
    if arr.size < 2:
        return []
    alpha = 2.0 / (span + 1.0)
    ewma = np.empty_like(arr)
    ewma[0] = arr[0]
    for i in range(1, arr.size):
        ewma[i] = alpha * arr[i] + (1 - alpha) * ewma[i - 1]

    residuals = arr - ewma
    std_res = residuals.std()
    if std_res == 0:
        return []
    scores = np.abs(residuals) / std_res
    indices = np.where(scores > threshold)[0]
    return [
        Anomaly(index=int(i), value=float(arr[i]), score=float(scores[i]))
        for i in indices
    ]


def linear_forecast(
    timestamps: Sequence[float],
    values: Sequence[float],
    steps: int = 10,
) -> list[tuple[float, float]]:
    """Simple linear regression forecast. Returns (timestamp, value) pairs."""
    x = np.asarray(timestamps, dtype=float)
    y = np.asarray(values, dtype=float)
    if x.size < 2 or y.size != x.size:
        return []

    coeffs = np.polyfit(x, y, 1)
    poly = np.poly1d(coeffs)

    intervals = np.diff(x)
    median_interval = float(np.median(intervals)) if intervals.size else 1.0
    if median_interval <= 0:
        median_interval = 1.0

    last_ts = float(x[-1])
    result = []
    for i in range(1, steps + 1):
        ts = last_ts + median_interval * i
        result.append((ts, float(poly(ts))))
    return result
