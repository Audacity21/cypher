import json
import urllib.request


class OllamaProvider:
    def __init__(
        self,
        model: str = "deepseek-r1:1.5b",
        base_url: str = "http://127.0.0.1:11434",
    ):
        self.model = model
        self.base_url = base_url

    def generate_json(
        self,
        prompt: str,
    ) -> dict:
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "format": "json",
        }

        request = urllib.request.Request(
            f"{self.base_url}/api/generate",
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
            },
            method="POST",
        )

        with urllib.request.urlopen(
            request,
            timeout=60,
        ) as response:
            body = json.loads(
                response.read().decode("utf-8")
            )

        return json.loads(body["response"])