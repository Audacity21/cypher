from backend.llm_provider import OllamaProvider


llm = OllamaProvider()

result = llm.generate_json(
    """
You are Cypher's reasoning engine.

Your job is to choose ONE intent based on the situation.

Allowed intents:
NONE
IDLE
PRESENCE
DARK
ALERT
SUCCESS
THINKING

Rules:
- If something enters interaction range, choose PRESENCE.
- If the environment becomes dark, choose DARK.
- If nothing requires a reaction, choose NONE.
- Do not copy example values.
- Return JSON only.
- confidence must be between 0 and 1.

Situation:
An object entered Cypher's interaction range.
Distance: 42 cm.

Return exactly these fields:
{
  "intent": "<allowed intent>",
  "reason": "<one short sentence explaining the choice>",
  "confidence": <number between 0 and 1>
}
"""
)

print(result)