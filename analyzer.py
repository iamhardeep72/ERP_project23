# ============================================================
# analyzer.py — AI Medical Report Analysis via Claude API
# ============================================================
# Sends extracted report text to Anthropic's Claude model and
# parses the structured JSON response into:
#   { high_values, low_values, normal_values }
# ============================================================

import os
import json
import logging
import anthropic

log = logging.getLogger(__name__)

# ── Anthropic client ──────────────────────────────────────────
# Reads ANTHROPIC_API_KEY from environment automatically.
# Set it in your .env or shell before running.
client = anthropic.Anthropic()

# ── System prompt ─────────────────────────────────────────────
SYSTEM_PROMPT = """You are a medical report analysis assistant.
Your job is to read extracted text from a medical lab report and identify
all measurable test values. For each value, classify it as:
  - HIGH   → above the reference/normal range
  - LOW    → below the reference/normal range
  - NORMAL → within the reference/normal range

Return ONLY a valid JSON object — no explanation, no markdown, no extra text.
Use this exact schema:

{
  "high_values": [
    {
      "name": "Test name (e.g. Glucose)",
      "value": "Measured value with unit (e.g. 130 mg/dL)",
      "unit": "unit string (e.g. mg/dL)",
      "normal_range": "Reference range (e.g. 70–99 mg/dL)"
    }
  ],
  "low_values": [ ... same structure ... ],
  "normal_values": [ ... same structure ... ]
}

Rules:
- Include every lab value you can identify.
- If a reference range is not listed in the report, use standard medical reference ranges.
- If you cannot determine the status confidently, classify as normal.
- Always return all three arrays (use empty arrays if no values in that category).
- Do NOT include diagnoses, advice, or any text outside the JSON.
"""


def analyze_report(extracted_text: str) -> dict:
    """
    Send extracted report text to Claude for analysis.

    Args:
        extracted_text: Plain text from the medical report.

    Returns:
        dict with keys: high_values, low_values, normal_values
    """

    user_message = f"""Please analyze the following medical report text and return the structured JSON:

---
{extracted_text}
---
"""

    log.info("Sending text to Claude API for analysis…")

    response = client.messages.create(
        model="claude-opus-4-5",          # Use the most capable model for accuracy
        max_tokens=4096,
        system=SYSTEM_PROMPT,
        messages=[
            {"role": "user", "content": user_message}
        ],
    )

    # Extract the response text
    raw_content = response.content[0].text.strip()
    log.info(f"Claude response received ({len(raw_content)} chars).")

    # Strip markdown code fences if present (Claude sometimes adds them)
    if raw_content.startswith("```"):
        lines = raw_content.splitlines()
        # Remove first line (```json or ```) and last line (```)
        raw_content = "\n".join(lines[1:-1]).strip()

    # Parse JSON
    try:
        result = json.loads(raw_content)
    except json.JSONDecodeError as e:
        log.error(f"Failed to parse Claude JSON: {e}\nRaw: {raw_content[:500]}")
        raise ValueError(
            "AI returned an unexpected format. "
            f"Parse error: {e}. Raw: {raw_content[:200]}"
        )

    # Ensure all required keys exist
    result.setdefault("high_values",   [])
    result.setdefault("low_values",    [])
    result.setdefault("normal_values", [])

    return result
