import json
import urllib.error
import urllib.request


class OllamaProvider:
    def __init__(
        self,
        model: str = "qwen2.5:1.5b",
        base_url: str = "http://127.0.0.1:11434",
        timeout: float = 15.0,
    ):
        self.model = model
        self.base_url = base_url
        self.timeout = timeout

    def generate_json(
        self,
        prompt: str,
    ) -> dict:

        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "format": "json",
            "options": {
                "temperature": 0.55,
                "top_p": 0.85,
                "repeat_penalty": 1.15,
                "num_predict": 140,
            },
        }

        request = urllib.request.Request(
            f"{self.base_url}/api/generate",
            data=json.dumps(
                payload
            ).encode("utf-8"),
            headers={
                "Content-Type":
                    "application/json",
            },
            method="POST",
        )

        try:
            with urllib.request.urlopen(
                request,
                timeout=self.timeout,
            ) as response:

                body = json.loads(
                    response.read().decode(
                        "utf-8"
                    )
                )

        except urllib.error.URLError as error:
            raise RuntimeError(
                f"Ollama unavailable: {error}"
            )

        except TimeoutError:
            raise RuntimeError(
                "Ollama request timed out"
            )

        raw_response = body.get(
            "response"
        )

        if not raw_response:
            raise RuntimeError(
                "Ollama returned empty response"
            )

        try:
            result = json.loads(
                raw_response
            )

        except json.JSONDecodeError:
            raise RuntimeError(
                "Ollama returned invalid JSON"
            )

        if not isinstance(
            result,
            dict,
        ):
            raise RuntimeError(
                "Ollama JSON response must be an object"
            )

        if not result:
            raise RuntimeError(
                "Ollama returned empty JSON object"
            )

        return result
