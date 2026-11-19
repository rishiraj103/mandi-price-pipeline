"""The only module that talks to the language model: a local Ollama server (free, no API key)."""
import logging
import os
import time

import requests

OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434")
MODEL = os.environ.get("OLLAMA_MODEL", "qwen2.5:7b")

log = logging.getLogger(__name__)


def generate(prompt, temperature=0.1):
    """Return (text, meta) where meta has the model, token counts and response time."""
    start = time.time()
    resp = requests.post(f"{OLLAMA_URL}/api/generate", timeout=300, json={
        "model": MODEL, "prompt": prompt, "stream": False, "options": {"temperature": temperature}})
    resp.raise_for_status()
    body = resp.json()
    meta = {"model": MODEL, "prompt_tokens": body.get("prompt_eval_count"),
            "output_tokens": body.get("eval_count"), "seconds": round(time.time() - start, 1)}
    log.info("llm call %s", meta)
    return body["response"].strip(), meta
