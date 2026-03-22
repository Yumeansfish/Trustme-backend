#!/usr/bin/env python3
import sys
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from typing import Callable

from aw_core.models import Event

from aw_datastore import get_storage_methods
from aw_datastore.storages import AbstractStorage

td1s = timedelta(seconds=1)


def create_test_events(n):
    now = datetime.now(timezone.utc) - timedelta(days=1000)

    events = []
    for i in range(n):
        events.append(
            Event(timestamp=now + i * td1s, duration=td1s, data={"label": "asd"})
        )

    return events


@contextmanager
def temporary_bucket(ds):
    bucket_id = "test_bucket"
    try:
        ds.delete_bucket(bucket_id)
    except Exception:
        pass
    bucket = ds.create_bucket(bucket_id, "testingtype", "test-client", "testing-box")
    yield bucket
    ds.delete_bucket(bucket_id)


def benchmark(storage: Callable[..., AbstractStorage]):
    raise NotImplementedError(
        "No longer implemented as ttt/takethetime dependency is removed"
    )


if __name__ == "__main__":
    for storage in get_storage_methods().values():
        if len(sys.argv) <= 1 or storage.__name__ in sys.argv:
            benchmark(storage)
