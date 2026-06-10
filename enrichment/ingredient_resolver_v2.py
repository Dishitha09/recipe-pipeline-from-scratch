import enrichment.llm_resolver as llm_resolver

from enrichment.ingredient_resolver import (
    resolve_ingredient,
)

from enrichment.vector_resolver import (
    resolve_by_vector,
)

from enrichment.llm_resolver import (
    resolve_by_llm,
)


METRICS = {
    "resolved_exact": 0,
    "resolved_vector": 0,
    "resolved_llm": 0,
    "unresolved": 0,
}


def resolve_ingredient_v2(raw_name):

    # STEP 1
    # Exact / Alias

    exact_result = resolve_ingredient(
        raw_name
    )

    if exact_result is not None:

        if exact_result[
            "resolution_type"
        ] in [
            "exact",
            "alias",
        ]:

            METRICS[
                "resolved_exact"
            ] += 1

            return exact_result

    # STEP 2
    # Vector Search

    vector_result = resolve_by_vector(
        raw_name
    )

    if vector_result is not None:

        score = vector_result.get(
            "score",
            0,
        )

        # Only accept vector matches
        # above confidence threshold

        if score >= 0.70:

            METRICS[
                "resolved_vector"
            ] += 1

            return {
                "raw_name": raw_name,
                **vector_result,
            }

    # STEP 3
    # LLM Fallback

    llm_result = resolve_by_llm(
        raw_name
    )

    if llm_result is not None:

        METRICS[
            "resolved_llm"
        ] += 1

        return {
            "raw_name": raw_name,
            **llm_result,
        }

    # STEP 4
    # Unresolved

    METRICS[
        "unresolved"
    ] += 1

    return {
        "raw_name": raw_name,
        "canonical_name": None,
        "resolution_type": "unresolved",
    }


def get_metrics():

    total = (
        METRICS["resolved_exact"]
        + METRICS["resolved_vector"]
        + METRICS["resolved_llm"]
        + METRICS["unresolved"]
    )

    resolution_rate = 0

    if total > 0:

        resolution_rate = round(
            (
                (
                    METRICS["resolved_exact"]
                    + METRICS["resolved_vector"]
                    + METRICS["resolved_llm"]
                )
                / total
            )
            * 100,
            2,
        )

    return {
        **METRICS,
        "resolution_rate": resolution_rate,

        "llm_calls_made":
            llm_resolver.LLM_CALLS_MADE,

        "llm_calls_succeeded":
            llm_resolver.LLM_CALLS_SUCCEEDED,

        "llm_cost_usd":
            llm_resolver.LLM_COST_USD,
    }


if __name__ == "__main__":

    tests = [
        "haldi powder",
        "jeera powder",
        "gehun atta",
        "curd",
        "ghee",
        "totally_unknown_ingredient_xyz",
    ]

    for test in tests:

        print(
            resolve_ingredient_v2(
                test
            )
        )

    print("\nMETRICS\n")

    print(
        get_metrics()
    )