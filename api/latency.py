from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import json
import os

app = FastAPI()

# Enable CORS for POST
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["POST"],
    allow_headers=["*"],
)

# Load telemetry
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_PATH = os.path.join(BASE_DIR, "telemetry.json")

with open(DATA_PATH, "r") as f:
    telemetry_data = json.load(f)


def mean(values):
    return sum(values) / len(values) if values else 0


def percentile(values, p):
    if not values:
        return 0
    values = sorted(values)
    k = (len(values) - 1) * (p / 100)
    f = int(k)
    c = f + 1
    if c >= len(values):
        return values[f]
    return values[f] + (values[c] - values[f]) * (k - f)


@app.post("/")
async def compute_latency(request: Request):
    body = await request.json()
    regions = body.get("regions", [])
    threshold = body.get("threshold_ms", 0)

    results = {}

    for region in regions:
        records = [r for r in telemetry_data if r["region"] == region]

        if not records:
            continue

        latencies = [r["latency_ms"] for r in records]
        uptimes = [r["uptime"] for r in records]

        results[region] = {
            "avg_latency": mean(latencies),
            "p95_latency": percentile(latencies, 95),
            "avg_uptime": mean(uptimes),
            "breaches": sum(1 for l in latencies if l > threshold)
        }

    return results