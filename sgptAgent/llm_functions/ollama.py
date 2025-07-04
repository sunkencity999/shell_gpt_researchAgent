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
        Maps system_prompt to 'system' and context_window to 'context_window' for the Ollama API.
        """
        model = model or self.model
        payload = {
            "model": model,
            "prompt": prompt,
        }
        # Map advanced kwargs to Ollama API
        if "system_prompt" in kwargs and kwargs["system_prompt"]:
            payload["system"] = kwargs["system_prompt"]
        if "context_window" in kwargs and kwargs["context_window"]:
            payload["context_window"] = kwargs["context_window"]
        if "temperature" in kwargs and kwargs["temperature"] is not None:
            payload["temperature"] = kwargs["temperature"]
        if "max_tokens" in kwargs and kwargs["max_tokens"]:
            payload["num_predict"] = kwargs["max_tokens"]
        # Forward any other kwargs
        for k, v in kwargs.items():
            if k not in ("system_prompt", "context_window", "temperature", "max_tokens"):
                payload[k] = v
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

    def chat(self, model: str, prompt: str, **kwargs) -> str:
        """
        Chat method that wraps generate() for compatibility with agent interface.
        Maps the expected chat parameters to generate parameters.
        """
        return self.generate(prompt, model=model, **kwargs)

# Example usage:
client = OllamaClient()
print(client.generate("What is the capital of France?", model="qwen3:8b"))
print(client.chat("qwen3:8b", "What is the capital of France?"))
