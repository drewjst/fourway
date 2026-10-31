# The image fourway-sandbox runs pytest in. Build it from the repository root:
#
#   docker build -f sandbox/Dockerfile -t fourway-sandbox .
#
# Its Python minor version and test dependencies match uv.lock, so a sandboxed
# run and a local run of the same tree differ only in where they run;
# tests/test_sandbox.py checks the pins. Rebuild after changing uv.lock or the
# pytest plugin: the image carries a copy of the plugin, and its ID is part of
# each evidence record's environment guard.
FROM python:3.12-slim@sha256:229a2c5bfa27522db7815ea81f9bed70af17ccb9de9fc7ad142b1877b5830d36

COPY sandbox/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir --no-deps --require-hashes -r /tmp/requirements.txt \
    && rm /tmp/requirements.txt

COPY src/fourway/__init__.py src/fourway/pytest_plugin.py /usr/local/lib/python3.12/site-packages/fourway/
