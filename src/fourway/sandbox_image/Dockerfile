# The image fourway runs pytest in when it runs in the sandbox. See
# docs/decisions/0003. Changing this file or requirements.txt changes the
# image tag, so evidence recorded under the old image stops matching.
FROM python:3.12-slim@sha256:229a2c5bfa27522db7815ea81f9bed70af17ccb9de9fc7ad142b1877b5830d36

ENV PIP_DISABLE_PIP_VERSION_CHECK=1 PIP_NO_CACHE_DIR=1
COPY requirements.txt /tmp/requirements.txt
RUN pip install --require-hashes --no-deps -r /tmp/requirements.txt && rm /tmp/requirements.txt
