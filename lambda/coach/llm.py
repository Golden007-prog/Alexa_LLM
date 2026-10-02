# -*- coding: utf-8 -*-
"""Tiny dependency-free LLM client (Gemini or Claude) with a hard deadline.

Alexa gives a skill about 8 seconds to answer, so every call has a timeout
and the caller falls back to rule-based feedback when it expires.

Config is read, first match wins, from:
  1. environment variables  LLM_PROVIDER, LLM_API_KEY, LLM_MODEL, ...
  2. lambda/config.json      (create it in the Alexa console Code tab)
  3. Media/llm_config.json   in the Alexa-hosted S3 bucket
Never commit a real key to a public repository.
"""

import json
import logging
import os
import time
import urllib.error
import urllib.request

logger = logging.getLogger(__name__)

MAX_TIMEOUT_SECONDS = 5.5  # hard cap, whatever the config says
MIN_USEFUL_SECONDS = 1.0   # less time than this left: skip the call

DEFAULTS = {
    "provider": "none",             # "gemini", "anthropic" or "none"
    "api_key": "",
    "model": "",                    # blank = provider default below
    "timeout_seconds": 5.5,
    "gemini_thinking_level": "",    # optional, e.g. "minimal" or "low"
}
DEFAULT_MODELS = {
    "gemini": "gemini-3.5-flash-lite",   # fast; minimal thinking by default
    "anthropic": "claude-haiku-4-5",
}

_cache = {}


def _from_s3():
    bucket = os.environ.get("S3_PERSISTENCE_BUCKET")
    if not bucket:
        return {}
    try:
        import boto3  # available in the Lambda runtime
        from botocore.config import Config
        # botocore defaults are 60 s per attempt with retries: far past
        # Alexa's 8 s reply window.
        client = boto3.client("s3", config=Config(
            connect_timeout=1, read_timeout=1, retries={"max_attempts": 0}))
        obj = client.get_object(Bucket=bucket, Key="Media/llm_config.json")
        return json.loads(obj["Body"].read().decode("utf-8"))
    except Exception as exc:  # missing file is normal
        logger.info("No S3 LLM config: %s", exc)
        return {}


def _from_file():
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    path = os.path.join(here, "config.json")
    if os.path.exists(path):
        try:
            with open(path, encoding="utf-8") as fh:
                return json.load(fh)
        except Exception as exc:
            logger.warning("Bad config.json: %s", exc)
    return {}


def get_config():
    if _cache:
        return _cache
    cfg = dict(DEFAULTS)
    for source in (_from_s3(), _from_file()):
        for k, v in source.items():
            if v not in (None, ""):
                cfg[k] = v
    env = {
        "provider": os.environ.get("LLM_PROVIDER"),
        "api_key": os.environ.get("LLM_API_KEY"),
        "model": os.environ.get("LLM_MODEL"),
        "timeout_seconds": os.environ.get("LLM_TIMEOUT_SECONDS"),
        "gemini_thinking_level": os.environ.get("GEMINI_THINKING_LEVEL"),
    }
    for k, v in env.items():
        if v:
            cfg[k] = v
    cfg["provider"] = str(cfg["provider"]).lower().strip()
    cfg["timeout_seconds"] = min(float(cfg["timeout_seconds"]),
                                 MAX_TIMEOUT_SECONDS)
    if not cfg["model"]:
        cfg["model"] = DEFAULT_MODELS.get(cfg["provider"], "")
    _cache.update(cfg)
    return _cache


def enabled():
    cfg = get_config()
    return cfg["provider"] in DEFAULT_MODELS and bool(cfg["api_key"])


def _post(url, headers, body, timeout):
    req = urllib.request.Request(url, data=json.dumps(body).encode("utf-8"),
                                 headers=headers, method="POST")
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _gemini(cfg, system, prompt, max_tokens, timeout):
    url = ("https://generativelanguage.googleapis.com/v1beta/models/%s:generateContent"
           % cfg["model"])
    gen = {"maxOutputTokens": max_tokens, "temperature": 0.4}
    if cfg.get("gemini_thinking_level"):
        gen["thinkingConfig"] = {"thinkingLevel": cfg["gemini_thinking_level"]}
    body = {
        "systemInstruction": {"parts": [{"text": system}]},
        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
        "generationConfig": gen,
    }
    data = _post(url, {"Content-Type": "application/json",
                       "x-goog-api-key": cfg["api_key"]},
                 body, timeout)
    parts = data["candidates"][0]["content"]["parts"]
    return "".join(p.get("text", "") for p in parts if not p.get("thought"))


def _anthropic(cfg, system, prompt, max_tokens, timeout):
    body = {"model": cfg["model"], "max_tokens": max_tokens, "system": system,
            "messages": [{"role": "user", "content": prompt}]}
    data = _post("https://api.anthropic.com/v1/messages",
                 {"Content-Type": "application/json",
                  "x-api-key": cfg["api_key"],
                  "anthropic-version": "2023-06-01"},
                 body, timeout)
    return "".join(b.get("text", "") for b in data.get("content", [])
                   if b.get("type") == "text")


def generate(system, prompt, max_tokens=700, deadline=None):
    """Return model text, or None on any failure or timeout.
    deadline: time.monotonic() value the reply must be ready by."""
    if not enabled():
        return None
    cfg = get_config()
    timeout = cfg["timeout_seconds"]
    if deadline is not None:
        timeout = min(timeout, deadline - time.monotonic())
    if timeout < MIN_USEFUL_SECONDS:
        logger.warning("LLM skipped: only %.1f s left", timeout)
        return None
    try:
        if cfg["provider"] == "gemini":
            text = _gemini(cfg, system, prompt, max_tokens, timeout)
        else:
            text = _anthropic(cfg, system, prompt, max_tokens, timeout)
        return text.strip() or None
    except urllib.error.HTTPError as exc:
        try:
            detail = exc.read().decode("utf-8")[:300]
        except Exception:
            detail = ""
        logger.warning("LLM HTTP %s: %s", exc.code, detail)
    except Exception as exc:
        logger.warning("LLM call failed: %s", exc)
    return None
