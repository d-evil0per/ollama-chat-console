import requests
import json
from typing import List, Dict, Generator, Optional


class OllamaClient:
    def __init__(self, base_url: str = "http://localhost:11434"):
        self.base_url = base_url.rstrip("/")

    def check_server(self) -> bool:
        """Check if Ollama server is reachable."""
        try:
            r = requests.get(self.base_url, timeout=2)
            return r.status_code == 200
        except Exception:
            return False

    def list_models(self) -> List[Dict]:
        """List local models using common endpoints."""
        endpoints = ["/api/tags", "/api/models", "/api/list"]
        for ep in endpoints:
            try:
                r = requests.get(self.base_url + ep, timeout=3)
                if r.status_code == 200:
                    data = r.json()
                    if isinstance(data, dict) and "tags" in data:
                        return data["tags"]
                    if isinstance(data, dict) and "models" in data:
                        return data["models"]
                    if isinstance(data, list):
                        return data
                    return [data]
            except Exception:
                continue
        return []

    def generate_non_stream(
        self,
        model: str,
        prompt: str,
        temperature: float = 0.2,
        max_tokens: int = 1024,
    ) -> Dict:
        """Generate text (non-streaming)."""
        payload = {
            "model": model,
            "prompt": prompt,
            "temperature": float(temperature),
            "max_tokens": int(max_tokens),
            "stream": False,
        }
        r = requests.post(self.base_url + "/api/generate", json=payload, timeout=120)
        r.raise_for_status()
        try:
            return r.json()
        except Exception:
            return {"error": "non-json response", "text": r.text}

    def generate_stream(self, model, prompt, temperature=0.2, max_tokens=512):
        """
        Stream responses from Ollama /api/generate.
        Yields text chunks as they arrive.
        """
        payload = {
            "model": model,
            "prompt": prompt,
            "temperature": float(temperature),
            "max_tokens": int(max_tokens),
            "stream": True,
        }

        with requests.post(f"{self.base_url}/api/generate", json=payload, stream=True, timeout=300) as r:
            r.raise_for_status()
            for raw_line in r.iter_lines(decode_unicode=True):
                if not raw_line:
                    continue
                try:
                    parsed = json.loads(raw_line)
                    if "response" in parsed:
                        yield parsed["response"]
                    elif "text" in parsed:  # some models return "text"
                        yield parsed["text"]
                except json.JSONDecodeError:
                    # fallback: raw text
                    yield raw_line