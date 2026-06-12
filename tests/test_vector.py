from enrichment.vector_resolver import (
    resolve_by_vector
)

result = resolve_by_vector(
    "cilantro leaves"
)

assert (
    result[
        "canonical_name"
    ]
    == "cilantro leaves"
)

print(
    "Vector tests passed"
)