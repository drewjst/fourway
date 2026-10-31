from importlib import import_module

import toolz
import toolz.curried


def _should_curry(func):
    if not callable(func) or isinstance(func, toolz.curry):
        return False
    nargs = toolz.functoolz.num_required_args(func)
    if nargs is None or nargs > 1:
        return True
    return nargs == 1 and toolz.functoolz.has_keywords(func)


def _curry_namespace(ns):
    return {
        name: toolz.curry(f) if _should_curry(f) else f
        for name, f in ns.items() if '__' not in name
    }


def test_curried_namespace_matches_toolz():
    exceptions = import_module('toolz.curried.exceptions')
    namespace = {}
    namespace.update(toolz.merge(_curry_namespace(vars(toolz)),
                                 _curry_namespace(vars(exceptions))))
    namespace = toolz.valfilter(callable, namespace)
    curried_namespace = toolz.valfilter(callable, toolz.curried.__dict__)
    missing = set(namespace) - set(curried_namespace)
    extra = set(curried_namespace) - set(namespace)
    assert not missing, missing
    assert not extra, extra
    unequal = sorted(k for k in namespace
                     if namespace[k] != curried_namespace[k])
    assert not unequal, unequal


def test_all_public_toolz_callables_introspectable():
    for mod in (toolz.functoolz, toolz.itertoolz):
        for name in mod.__all__:
            func = getattr(mod, name)
            assert toolz.functoolz.is_partial_args(func, (), {}) is True, name
