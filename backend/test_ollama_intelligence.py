from backend.llm_provider import OllamaProvider


llm = OllamaProvider(
    model="qwen2.5:1.5b"
)

result = llm.generate_json(
    """
You are Cypher's reasoning engine.

Choose ONE intent.

Allowed intents:
NONE
IDLE
PRESENCE
DARK
ALERT
SUCCESS
THINKING

Rules:
- An object entering interaction range means PRESENCE.
- Return JSON only.
- Do not add extra keys.

Situation:
An object entered interaction range.
Distance: 42 cm.

Return:
{
  "intent": "<allowed intent>",
  "reason": "<short reason>",
  "confidence": <number from 0 to 1>
}
"""
)

print("RAW RESULT:")
print(result)

print()
print("TYPE:")
print(type(result))