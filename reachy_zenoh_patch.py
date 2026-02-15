"""Zenoh configuration patching for restricted/sandboxed environments.

On some macOS setups (and in sandboxed runners) Zenoh's shared memory transport
can fail to initialize with a POSIX shm permission error. The Reachy Mini SDK
constructs Zenoh configs programmatically, so the most robust workaround is to
inject `transport/shared_memory/enabled=false` into all configs.
"""

from __future__ import annotations

import os


def disable_zenoh_shared_memory() -> None:
    """Disable Zenoh shared memory transport globally for this Python process."""
    import zenoh

    # Also set the override env var so any subprocesses or native layers that
    # consult it will inherit the setting.
    os.environ.setdefault("ZENOH_CONFIG_OVERRIDE", "transport/shared_memory/enabled=false")

    if getattr(zenoh, "_reachy_shm_disabled", False):
        return

    orig_from_json5 = zenoh.Config.from_json5

    def _from_json5_patched(*args, **kwargs):  # type: ignore[no-untyped-def]
        cfg = orig_from_json5(*args, **kwargs)
        try:
            # Zenoh expects JSON pointers for nested fields.
            cfg.insert_json5("transport/shared_memory/enabled", "false")
        except Exception:
            # If the schema changes, fail open (better than breaking all configs).
            pass
        return cfg

    zenoh.Config.from_json5 = _from_json5_patched  # type: ignore[method-assign]
    setattr(zenoh, "_reachy_shm_disabled", True)
