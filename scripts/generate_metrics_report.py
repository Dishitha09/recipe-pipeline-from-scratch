from enrichment.metrics import (
    get_metrics
)

import os

os.makedirs(
    "reports",
    exist_ok=True,
)

metrics = get_metrics()

with open(
    "reports/ps3_report.txt",
    "w",
    encoding="utf-8",
) as f:

    f.write(
        "PS3 METRICS REPORT\n\n"
    )

    for k, v in metrics.items():

        f.write(
            f"{k}: {v}\n"
        )

print(
    "Saved reports/ps3_report.txt"
)