import requests
import subprocess
import time
import json
from typing import Optional, Dict, Any
import ollama

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

    def embeddings(self, model: str, prompt: str) -> list:
        """
        Gets embeddings for a given prompt using the specified model.
        """
        try:
            return ollama.embeddings(model=model, prompt=prompt)['embedding']
        except Exception as e:
            # Check if the model is available, if not, prompt the user to pull it.
            if "not found" in str(e):
                print(f"Embedding model '{model}' not found.")
                print(f"Please pull the model using: ollama pull {model}")
            else:
                print(f"[OLLAMA ERROR] Could not get embeddings: {e}")
            return []

    def chat_with_image(self, model: str, prompt: str, image_path: str, **kwargs) -> str:
        """
        Sends a prompt and an image to the Ollama server and returns the completion.
        """
        import base64

        with open(image_path, "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read()).decode('utf-8')

        payload = {
            "model": model,
            "prompt": prompt,
            "images": [encoded_string]
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

    def list_models(self) -> list:
        """
        Lists available Ollama models.
        """
        try:
            result = subprocess.run(['ollama', 'list'], capture_output=True, text=True, check=True)
            output = result.stdout.strip()
            
            if not output:
                return []
            
            lines = output.split('\n')[1:]  # Skip "NAME ID MODIFIED SIZE" header
            models = []
            for line in lines:
                if line.strip():
                    model_name = line.split()[0]
                    if model_name and not model_name.startswith('NAME'):
                        # Filter out embedding models that don't support text generation
                        if not any(embed_keyword in model_name.lower() for embed_keyword in ['embed', 'embedding', 'nomic-embed']):
                            models.append(model_name)
            return models
        except subprocess.CalledProcessError as e:
            print(f"[OLLAMA ERROR] Could not list Ollama models: {e}")
            return []
        except Exception as e:
            print(f"[OLLAMA ERROR] Unexpected error listing models: {e}")
            return []

# Example usage:
client = OllamaClient()
print(client.generate("What is the capital of France?", model="qwen3:8b"))
print(client.chat("qwen3:8b", "What is the capital of France?"))