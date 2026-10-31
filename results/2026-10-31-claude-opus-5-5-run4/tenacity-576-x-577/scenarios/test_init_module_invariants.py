import ast
import inspect
import sys
import types
import typing

import tenacity
from tenacity import after, before, before_sleep, nap, stop, wait
from tenacity import retry as retry_mod


def test_public_reexports_intact():
    for name in tenacity.__all__:
        assert hasattr(tenacity, name), name
    assert tenacity.wait_full_jitter is wait.wait_random_exponential
    assert tenacity.sleep is nap.sleep
    assert tenacity.sleep_using_event is nap.sleep_using_event
    assert tenacity.after_log is after.after_log
    assert tenacity.before_nothing is before.before_nothing
    assert tenacity.before_sleep_log is before_sleep.before_sleep_log
    assert tenacity.retry_never is retry_mod.retry_never
    assert tenacity.stop_when_event_set is stop.stop_when_event_set
    assert tenacity.wait_exception is wait.wait_exception
    ns = {}
    exec("from tenacity import *", ns)
    for name in tenacity.__all__:
        assert name in ns, name


def test_copy_preserves_subclass_and_runs():
    class MyRetrying(tenacity.Retrying):
        pass

    slept = []
    r = MyRetrying(sleep=slept.append, stop=tenacity.stop_after_attempt(5),
                   wait=tenacity.wait_fixed(2))
    c = r.copy(stop=tenacity.stop_after_attempt(3))
    assert type(c) is MyRetrying
    assert c.sleep is r.sleep
    assert c.wait is r.wait

    calls = []

    def f():
        calls.append(1)
        raise ValueError("boom")

    try:
        c(f)
    except tenacity.RetryError as e:
        assert e.last_attempt.attempt_number == 3
    else:
        raise AssertionError("expected RetryError")
    assert len(calls) == 3
    assert slept == [2.0, 2.0]
    assert c.statistics["attempt_number"] == 3

    wrapped = r.wraps(f)
    faster = wrapped.retry_with(stop=tenacity.stop_after_attempt(2))
    calls.clear()
    try:
        faster()
    except tenacity.RetryError:
        pass
    assert len(calls) == 2


def test_iter_annotation_mentions_actions():
    ann = tenacity.BaseRetrying.iter.__annotations__["return"]
    args = set(typing.get_args(ann))
    assert tenacity.DoAttempt in args
    assert tenacity.DoSleep in args


def test_self_fallback_on_old_python(monkeypatch):
    tree = ast.parse(inspect.getsource(tenacity))
    block = None
    for node in tree.body:
        if isinstance(node, ast.If) and isinstance(node.test, ast.Attribute) \
                and node.test.attr == "TYPE_CHECKING":
            block = node
            break
    assert block is not None

    def imports_self(stmt):
        for sub in ast.walk(stmt):
            if isinstance(sub, ast.ImportFrom):
                if any((a.asname or a.name) == "Self" for a in sub.names):
                    return True
        return False

    stmts = [s for s in block.body if imports_self(s)]
    assert stmts
    mod = ast.Module(body=stmts, type_ignores=[])
    ast.fix_missing_locations(mod)
    code = compile(mod, "<tc>", "exec")

    sentinel = object()
    stub = types.ModuleType("typing_extensions")
    stub.Self = sentinel
    monkeypatch.setitem(sys.modules, "typing_extensions", stub)
    fake_sys = types.SimpleNamespace(version_info=(3, 10, 0))
    ns = {"sys": fake_sys, "t": typing}
    exec(code, ns)
    assert ns["Self"] is sentinel
