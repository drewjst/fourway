import tenacity


CORE = [
    "retry",
    "Retrying",
    "AsyncRetrying",
    "RetryError",
    "RetryCallState",
    "TryAgain",
    "stop_after_attempt",
    "wait_fixed",
    "wait_exponential",
    "wait_random_exponential",
    "wait_full_jitter",
    "retry_if_exception_type",
    "before_sleep_log",
]


def test_all_is_declared_and_resolvable():
    exported = tenacity.__all__
    assert isinstance(exported, (list, tuple))
    for name in CORE:
        assert name in exported, name
    for name in exported:
        assert hasattr(tenacity, name), name


def test_star_import_exposes_core_symbols():
    ns = {}
    exec("from tenacity import *", ns)
    for name in CORE:
        assert name in ns, name
        assert ns[name] is getattr(tenacity, name)
