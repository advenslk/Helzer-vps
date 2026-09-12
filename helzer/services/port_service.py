from __future__ import annotations


class PortService:
    def __init__(self, start: int = 20000, end: int = 40000):
        if not (1 <= start <= end <= 65535):
            raise ValueError("invalid port range")
        self.start = start
        self.end = end
        self._allocated: set[int] = set()

    def allocate(self) -> int:
        for port in range(self.start, self.end + 1):
            if port not in self._allocated:
                self._allocated.add(port)
                return port
        raise RuntimeError("no ports available")

    def reserve(self, port: int) -> None:
        if not self.start <= port <= self.end:
            raise ValueError("port outside managed range")
        self._allocated.add(port)

    def release(self, port: int) -> None:
        self._allocated.discard(port)

    def is_allocated(self, port: int) -> bool:
        return port in self._allocated
