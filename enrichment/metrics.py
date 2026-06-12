RESOLVED_EXACT = 0
RESOLVED_VECTOR = 0
RESOLVED_LLM = 0
UNRESOLVED = 0


def increment_exact():
    global RESOLVED_EXACT
    RESOLVED_EXACT += 1


def increment_vector():
    global RESOLVED_VECTOR
    RESOLVED_VECTOR += 1


def increment_llm():
    global RESOLVED_LLM
    RESOLVED_LLM += 1


def increment_unresolved():
    global UNRESOLVED
    UNRESOLVED += 1


def get_metrics():

    total = (
        RESOLVED_EXACT +
        RESOLVED_VECTOR +
        RESOLVED_LLM +
        UNRESOLVED
    )

    if total == 0:
        resolution_rate = 0
    else:
        resolution_rate = round(
            (
                (
                    RESOLVED_EXACT +
                    RESOLVED_VECTOR +
                    RESOLVED_LLM
                )
                / total
            ) * 100,
            2,
        )

    return {
        "resolved_exact":
            RESOLVED_EXACT,

        "resolved_vector":
            RESOLVED_VECTOR,

        "resolved_llm":
            RESOLVED_LLM,

        "unresolved":
            UNRESOLVED,

        "resolution_rate":
            resolution_rate,
    }