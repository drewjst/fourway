import ast
import inspect
import sys
import typing

import pytest

import tenacity


def _type_checking_block():
    tree = ast.parse(inspect.getsource(tenacity))
    for node in tree.body:
        if isinstance(node, ast.If):
            test = node.test
            if isinstance(test, ast.Attribute) and test.attr == "TYPE_CHECKING":
                return node
            if isinstance(test, ast.Name) and test.id == "TYPE_CHECKING":
                return node
    raise AssertionError("no TYPE_CHECKING block found in tenacity/__init__.py")


def _imports_self(stmt):
    for sub in ast.walk(stmt):
        if isinstance(sub, ast.ImportFrom):
            for alias in sub.names:
                if (alias.asname or alias.name) == "Self":
                    return True
    return False


def _self_import_code():
    block = _type_checking_block()
    stmts = [s for s in block.body if _imports_self(s)]
    assert stmts, "TYPE_CHECKING block does not import Self"
    mod = ast.Module(body=stmts, type_ignores=[])
    ast.fix_missing_locations(mod)
    return compile(mod, "<tenacity-type-checking>", "exec")


@pytest.mark.skipif(sys.version_info < (3, 11), reason="typing.Self requires 3.11+")
def test_self_resolves_from_stdlib_without_typing_extensions(monkeypatch):
    code = _self_import_code()
    # Block typing_extensions entirely: on 3.11+ it must not be needed.
    monkeypatch.setitem(sys.modules, "typing_extensions", None)
    ns = {"sys": sys, "t": typing}
    exec(code, ns)
    assert ns["Self"] is typing.Self
