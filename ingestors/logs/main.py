import os
import json
import logging
import time
import httpx
from typing import List
from hanabi.utils.queue import DockerLogQueue

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("LogsIngestor")

FALCO_CONTAINER = os.getenv("FALCO_CONTAINER", "43039infrasecurity-falco")
API_URL = os.getenv("API_URL", "http://43039infrasecurity-api:8000/infrasecurity/api/logs/internal/ingest")
BATCH_SIZE = 100 # Reduced batch size for lower latency streaming
FLUSH_INTERVAL = 3.0  # seconds

def flush_buffer(client: httpx.Client, buffer: List[dict]):
    if not buffer:
        return
    try:
        resp = client.post(API_URL, json=buffer)
        if resp.status_code != 200:
            logger.error(f"Failed to push logs to API: {resp.text}")
    except Exception as e:
        logger.error(f"Failed to push logs to API: {e}")

def run():
    q = DockerLogQueue(container_name=FALCO_CONTAINER, max_queue_size=100000)
    q.start()
    
    buffer: List[dict] = []
    last_flush_time = time.time()
    
    logger.info(f"LogsIngestor started. Streaming to {API_URL}")

    with httpx.Client(timeout=5.0) as client:
        try:
            while True:
                try:
                    # Use a small timeout to allow checking time-based flush
                    obj = q.get(timeout=0.1)
                    if obj:
                        buffer.append(obj)
                except Exception:
                    # Queue empty or other error
                    pass

                now = time.time()
                time_since_flush = now - last_flush_time
                
                # Check flush conditions
                if len(buffer) >= BATCH_SIZE or (len(buffer) > 0 and time_since_flush >= FLUSH_INTERVAL):
                    flush_buffer(client, buffer)
                    buffer.clear()
                    last_flush_time = now

        except KeyboardInterrupt:
            logger.info("Stopping LogsIngestor...")
            # Final flush
            flush_buffer(client, buffer)
        finally:
            q.stop()

if __name__ == "__main__":
    run()
