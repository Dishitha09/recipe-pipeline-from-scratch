
from enrichment.ingredient_resolver import resolve_ingredient
from enrichment.vector_resolver import resolve_by_vector
from enrichment.llm_resolver import (
    resolve_by_llm,
    get_llm_metrics,
)


class ResolutionMetrics:

    def __init__(self):

        self.resolved_exact = 0
        self.resolved_vector = 0
        self.resolved_llm = 0
        self.unresolved = 0

    def record(self, resolution_type: str):

        if resolution_type == "exact":
            self.resolved_exact += 1

        elif resolution_type == "vector":
            self.resolved_vector += 1

        elif resolution_type == "llm":
            self.resolved_llm += 1

        else:
            self.unresolved += 1

    def summary(self):

        total = (
            self.resolved_exact
            + self.resolved_vector
            + self.resolved_llm
            + self.unresolved
        )

        if total == 0:
            resolution_rate = 0.0
        else:
            resolution_rate = round(
                (
                    (
                        self.resolved_exact
                        + self.resolved_vector
                        + self.resolved_llm
                    )
                    / total
                )
                * 100,
                2,
            )

        return {
            "resolved_exact": self.resolved_exact,
            "resolved_vector": self.resolved_vector,
            "resolved_llm": self.resolved_llm,
            "unresolved": self.unresolved,
            "resolution_rate": resolution_rate,
        }


metrics = ResolutionMetrics()


def resolve_ingredient_v2(name: str):

    exact_result = resolve_ingredient(name)

    if exact_result["resolution_type"] == "exact":

        metrics.record("exact")

        return exact_result

    vector_result = resolve_by_vector(name)

    if vector_result:

        metrics.record("vector")

        return vector_result

    llm_result = resolve_by_llm(name)

    if llm_result:

        metrics.record("llm")

        return llm_result

    metrics.record("unresolved")

    return {
        "raw_name": name,
        "canonical_name": None,
        "resolution_type": "unresolved",
    }


def get_metrics():

    return {
        **metrics.summary(),
        **get_llm_metrics(),
    }


if __name__ == "__main__":

    test_ingredients = [
        "haldi",
        "jeera powder",
        "cilantro leaves",
        "ghee",
        "random_unknown_ingredient",
    ]

    for ingredient in test_ingredients:

        print(
            resolve_ingredient_v2(
                ingredient
            )
        )

    print("\nMETRICS\n")

    print(
        get_metrics()
    )
