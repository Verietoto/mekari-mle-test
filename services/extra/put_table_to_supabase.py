import pandas as pd
import requests
from datetime import datetime
import math
import time
import json

# ============================================================
# CONFIG
# ============================================================
API_URL = "http://localhost:8000/fraud/v1/transactions"  # adjust if needed
CSV_PATH = "../raw_dataset/fraudTest.csv"
CHUNK_SIZE = 10000               # adjust (start small)
TIMEOUT = 120                # seconds
RETRY_LIMIT = 3              # how many times to retry if failure
SLEEP_BETWEEN_CHUNKS = 1.0   # seconds between chunks


# ============================================================
# LOAD DATA
# ============================================================
print(f"📂 Loading CSV from {CSV_PATH}...")
df = pd.read_csv(CSV_PATH)

# Fix column names
df = df.rename(columns={
    "first": "first_name",
    "last": "last_name"
})
df = df.drop(columns=["Unnamed: 0"], errors="ignore")

# Fix datetime fields
if "trans_date_trans_time" in df.columns:
    df["trans_date_trans_time"] = pd.to_datetime(
        df["trans_date_trans_time"], errors="coerce"
    ).dt.strftime("%Y-%m-%dT%H:%M:%S")

if "dob" in df.columns:
    df["dob"] = pd.to_datetime(df["dob"], errors="coerce").dt.strftime("%Y-%m-%d")

total_records = len(df)
total_chunks = math.ceil(total_records / CHUNK_SIZE)
print(f"🚀 Starting bulk upload: {total_records} records, {total_chunks} chunks of {CHUNK_SIZE}\n")

# ============================================================
# BULK INSERT LOOP
# ============================================================
for i in range(total_chunks):
    start_idx = i * CHUNK_SIZE
    end_idx = min((i + 1) * CHUNK_SIZE, total_records)
    chunk = df.iloc[start_idx:end_idx]

    payload = chunk.to_dict(orient="records")

    print(f"📦 Sending chunk {i+1}/{total_chunks} ({len(payload)} records)...")

    # Retry logic
    for attempt in range(1, RETRY_LIMIT + 1):
        try:
            start_time = time.time()
            response = requests.post(API_URL, json=payload, timeout=TIMEOUT)
            duration_ms = (time.time() - start_time) * 1000

            if response.status_code in [200, 201]:
                try:
                    result = response.json()
                    data = result.get("data", {})
                    rows = data.get("rows_affected", len(payload))
                    print(f"✅ Chunk {i+1} OK — {rows} rows ({duration_ms:.2f} ms)")
                except json.JSONDecodeError:
                    print(f"✅ Chunk {i+1} OK — response not JSON ({duration_ms:.2f} ms)")
                break

            else:
                # Avoid printing huge input dumps
                try:
                    err_json = response.json()
                    detail = err_json.get("detail", [])
                    msg = json.dumps(detail, indent=2)[:500] + "..." if detail else response.text
                except Exception:
                    msg = response.text[:500]
                print(f"❌ Chunk {i+1} failed (status {response.status_code}): {msg}")
                if attempt < RETRY_LIMIT:
                    print("🔁 Retrying...")
                    time.sleep(2)
                else:
                    print("🚨 Giving up on this chunk after multiple retries.")
        except requests.exceptions.RequestException as e:
            print(f"⚠️ Request failed: {e}")
            if attempt < RETRY_LIMIT:
                print("🔁 Retrying...")
                time.sleep(2)
            else:
                print("🚨 Giving up on this chunk after multiple retries.")

    time.sleep(SLEEP_BETWEEN_CHUNKS)

print("\n✅ All done!")
