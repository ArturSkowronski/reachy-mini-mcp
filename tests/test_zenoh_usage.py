import sys
import types


class _FakeConfig:
    def __init__(self) -> None:
        self.inserted: list[tuple[str, str]] = []

    def insert_json5(self, path: str, value: str) -> None:
        self.inserted.append((path, value))

    def get_json(self, path: str) -> str:
        for p, v in reversed(self.inserted):
            if p == path:
                return v
        raise KeyError(path)


def _install_fake_zenoh(monkeypatch) -> types.ModuleType:
    mod = types.ModuleType("zenoh")

    class Config:
        @staticmethod
        def from_json5(_: str) -> _FakeConfig:
            return _FakeConfig()

    mod.Config = Config  # type: ignore[attr-defined]
    mod._reachy_shm_disabled = False  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "zenoh", mod)
    return mod


def test_disable_zenoh_shared_memory_is_idempotent(monkeypatch):
    _install_fake_zenoh(monkeypatch)

    import reachy_zenoh_patch

    reachy_zenoh_patch.disable_zenoh_shared_memory()
    reachy_zenoh_patch.disable_zenoh_shared_memory()

    import zenoh  # type: ignore

    assert getattr(zenoh, "_reachy_shm_disabled", False) is True
    cfg = zenoh.Config.from_json5("{}")
    assert cfg.get_json("transport/shared_memory/enabled") == "false"


def test_disable_zenoh_shared_memory_no_zenoh_installed(monkeypatch):
    # Simulate missing zenoh even if it's installed in the dev environment.
    orig_import = __import__

    def _import(name, *args, **kwargs):  # type: ignore[no-untyped-def]
        if name == "zenoh":
            raise ImportError("no zenoh")
        return orig_import(name, *args, **kwargs)

    monkeypatch.setattr("builtins.__import__", _import)

    import reachy_zenoh_patch

    reachy_zenoh_patch.disable_zenoh_shared_memory()


def test_reachy_import_calls_disable_zenoh_shared_memory(monkeypatch):
    z = _install_fake_zenoh(monkeypatch)

    # Force a clean import so module-level initialization runs.
    sys.modules.pop("reachy", None)
    import reachy  # noqa: F401

    # If reachy called disable_zenoh_shared_memory at import-time, the shim
    # should have patched Config.from_json5.
    cfg = z.Config.from_json5("{}")  # type: ignore[attr-defined]
    assert cfg.get_json("transport/shared_memory/enabled") == "false"
