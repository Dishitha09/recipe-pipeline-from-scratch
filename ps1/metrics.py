from collections import defaultdict


_METRICS = defaultdict(int)


def increment(metric_name: str, amount: int = 1):
    _METRICS[metric_name] += amount


def get_metrics():
    return dict(_METRICS)


def reset_metrics():
    _METRICS.clear()
