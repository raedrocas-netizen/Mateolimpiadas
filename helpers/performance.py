import contextvars
import functools
import os
import time
from contextlib import contextmanager


_current_context = contextvars.ContextVar("performance_context", default=None)
_serialization_depth = contextvars.ContextVar("serialization_depth", default=0)


def performance_enabled():
    return os.getenv("PERFORMANCE_LOGS", "1").lower() not in {"0", "false", "no"}


class PerformanceContext:

    def __init__(self, label, kind="general"):
        self.label = label
        self.kind = kind
        self.started_at = time.perf_counter()
        self.metrics = {
            "SQL": 0.0,
            "DB connection": 0.0,
            "SocketIO": 0.0,
            "Serializacion": 0.0,
        }
        self.counts = {
            "SQL": 0,
            "DB connection": 0,
            "SocketIO": 0,
            "Serializacion": 0,
        }
        self.slow_sql = []
        self.finished = False

    def add(self, category, elapsed):
        if elapsed < 0:
            return

        self.metrics[category] = self.metrics.get(category, 0.0) + elapsed
        self.counts[category] = self.counts.get(category, 0) + 1

    def add_sql(self, statement, elapsed):
        self.add("SQL", elapsed)

        if elapsed >= 0.05:
            clean_statement = " ".join(str(statement).split())
            self.slow_sql.append((elapsed, clean_statement[:180]))

    def finish(self, status=None):
        if self.finished:
            return

        self.finished = True

        if not performance_enabled():
            return

        total = time.perf_counter() - self.started_at
        remaining = total - sum(self.metrics.values())
        slow_sql = sorted(self.slow_sql, reverse=True)[:3]

        print("[PERFORMANCE]", flush=True)
        print(self.label, flush=True)

        if status is not None:
            print(f"Estado: {status}", flush=True)

        print(f"Tiempo total: {total:.3f} s", flush=True)
        print(
            f"DB connection: {self.metrics.get('DB connection', 0.0):.3f} s "
            f"({self.counts.get('DB connection', 0)})",
            flush=True
        )
        print(
            f"SQL: {self.metrics.get('SQL', 0.0):.3f} s "
            f"({self.counts.get('SQL', 0)})",
            flush=True
        )
        print(
            f"SocketIO: {self.metrics.get('SocketIO', 0.0):.3f} s "
            f"({self.counts.get('SocketIO', 0)})",
            flush=True
        )
        print(
            f"Serializacion: {self.metrics.get('Serializacion', 0.0):.3f} s "
            f"({self.counts.get('Serializacion', 0)})",
            flush=True
        )
        print(f"Negocio/otros: {max(remaining, 0.0):.3f} s", flush=True)

        if slow_sql:
            print("SQL lento:", flush=True)
            for elapsed, statement in slow_sql:
                print(f"- {elapsed:.3f} s | {statement}", flush=True)


def current_context():
    return _current_context.get()


def begin_operation(label, kind="general"):
    context = PerformanceContext(label, kind=kind)
    token = _current_context.set(context)
    return context, token


def finish_operation(context, token, status=None):
    if context is not None:
        context.finish(status=status)

    if token is not None:
        _current_context.reset(token)


@contextmanager
def performance_operation(label, kind="general", status=None):
    context, token = begin_operation(label, kind=kind)

    try:
        yield context
    finally:
        finish_operation(context, token, status=status)


def record_metric(category, elapsed):
    context = current_context()

    if context is not None:
        context.add(category, elapsed)


def record_sql(statement, elapsed):
    context = current_context()

    if context is not None:
        context.add_sql(statement, elapsed)


@contextmanager
def measure(category):
    started_at = time.perf_counter()

    try:
        yield
    finally:
        record_metric(category, time.perf_counter() - started_at)


@contextmanager
def measure_serialization():
    depth = _serialization_depth.get()
    token = _serialization_depth.set(depth + 1)
    started_at = time.perf_counter() if depth == 0 else None

    try:
        yield
    finally:
        if depth == 0 and started_at is not None:
            record_metric("Serializacion", time.perf_counter() - started_at)

        _serialization_depth.reset(token)


def socket_event_performance(event_name):
    def decorator(function):
        @functools.wraps(function)
        def wrapper(*args, **kwargs):
            with performance_operation(f"SocketIO {event_name}", kind="socket"):
                return function(*args, **kwargs)

        return wrapper

    return decorator
