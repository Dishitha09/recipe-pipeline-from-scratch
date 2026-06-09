import os

LLM_CALLS_MADE = 0
LLM_CALLS_SUCCEEDED = 0
LLM_COST_USD = 0.0


def resolve_by_llm(name: str):

    global LLM_CALLS_MADE
    global LLM_CALLS_SUCCEEDED
    global LLM_COST_USD

    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        return None

    LLM_CALLS_MADE += 1

    try:

        import google.generativeai as genai

        genai.configure(api_key=api_key)

        model = genai.GenerativeModel(
            "gemini-1.5-flash"
        )

        prompt = f"""
Resolve this ingredient name to a canonical ingredient.

Ingredient:
{name}

Return only the canonical ingredient name.
"""

        response = model.generate_content(
            prompt
        )

        canonical_name = (
            response.text.strip()
        )

        LLM_CALLS_SUCCEEDED += 1

        LLM_COST_USD += 0.0001

        return {
            "canonical_name": canonical_name,
            "resolution_type": "llm",
        }

    except Exception:
        return None


def get_llm_metrics():

    return {
        "llm_calls_made":
            LLM_CALLS_MADE,
        "llm_calls_succeeded":
            LLM_CALLS_SUCCEEDED,
        "llm_cost_usd":
            round(
                LLM_COST_USD,
                6,
            ),
    }