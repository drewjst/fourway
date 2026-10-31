import ast
import os

import tomlkit


def test_register_encoder_docstring_uses_literal_block() -> None:
    doc = tomlkit.register_encoder.__doc__ or ""
    assert "Example::" in doc
    # the code example follows the literal-block marker after a blank line
    after = doc.split("Example::", 1)[1]
    assert after.lstrip(" ").startswith("\n")
    assert "@register_encoder" in after


def test_docs_conf_disables_docstring_signature_parsing() -> None:
    path = os.path.join(os.getcwd(), "docs", "conf.py")
    with open(path, encoding="utf-8") as f:
        tree = ast.parse(f.read())
    values = {}
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    values[target.id] = node.value
    assert "autodoc_docstring_signature" in values
    node = values["autodoc_docstring_signature"]
    assert isinstance(node, ast.Constant) and node.value is False
    assert "nitpick_ignore" in values
