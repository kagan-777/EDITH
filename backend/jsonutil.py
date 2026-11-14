import json


def extract_json(text: str, expect=None):
    """Find the first valid JSON object/array in an LLM reply.

    Handles ```json fences and chatter before/after the JSON.
    `expect` may be `list` or `dict` to only accept that type.
    """
    decoder = json.JSONDecoder()
    text = (text or "").replace("```json", "").replace("```", "")
    for i, ch in enumerate(text):
        if ch in "[{":
            try:
                obj, _ = decoder.raw_decode(text[i:])
            except ValueError:
                continue
            if expect is None or isinstance(obj, expect):
                return obj
    raise ValueError("No valid JSON found in the AI response.")
