import requests
import subprocess
import time
import json
from typing import Optional, Dict, Any

class OllamaClient:
    def __init__(self, base_url: str = "http://localhost:11434"):
        self.base_url = base_url.rstrip("/")
        self.api_url = f"{self.base_url}/api/generate"
        self.model = "qwen3:8b"

    def generate(self, prompt: str, model: str = None, **kwargs) -> str:
        """
        Sends a prompt to the Ollama server and returns the completion.
        Handles streaming/multi-line JSON responses.
        """
        model = model or self.model
        payload = {
            "model": model,
            "prompt": prompt,
            **kwargs,
        }
        def stream_and_concat(resp):
            output = ""
            for line in resp.iter_lines():
                if not line:
                    continue
                try:
                    data = json.loads(line)
                    chunk = data.get("response", "")
                    
                    output += chunk
                except Exception as e:
                    print(f"[OLLAMA ERROR] Could not parse line: {line} | {e}")
            return output
        try:
            resp = requests.post(self.api_url, json=payload, timeout=60, stream=True)
            
            
            resp.raise_for_status()
            return stream_and_concat(resp)
        except requests.ConnectionError as e:
            print("[OLLAMA ERROR] Ollama server is not running. Attempting to start with 'ollama serve'...")
            try:
                subprocess.Popen(["ollama", "serve"])
                time.sleep(2)  # Give it a moment to start
                resp = requests.post(self.api_url, json=payload, timeout=60, stream=True)
                
                
                resp.raise_for_status()
                return stream_and_concat(resp)
            except Exception as e2:
                return f"[Ollama error: Could not start Ollama server: {e2}]"
        except requests.HTTPError as e:
            print(f"[OLLAMA ERROR] HTTP error: {e}")
            if e.response is not None and e.response.status_code == 404:
                return f"[Ollama HTTP 404: Model '{model}' not found at {self.api_url}]"
            return f"[Ollama HTTP error: {e}]"
        except Exception as e:
            print(f"[OLLAMA ERROR] Unexpected error: {e}")
            return f"[Ollama error: {e}]"

# Example usage:
client = OllamaClient()
print(client.generate("What is the capital of France?", model="qwen3:8b"))
