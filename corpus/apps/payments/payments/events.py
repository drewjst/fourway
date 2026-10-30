"""In-process event bus. Handlers run synchronously, in subscription order."""

from collections import defaultdict


class EventBus:
    def __init__(self):
        self._handlers = defaultdict(list)

    def subscribe(self, name, handler):
        self._handlers[name].append(handler)

    def publish(self, name, payload):
        for handler in self._handlers[name]:
            handler(payload)
