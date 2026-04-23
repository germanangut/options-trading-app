from pathlib import Path

from backend.repositories.sqlite_lifecycle_repository import SQLiteLifecycleRepository


def test_lifecycle_repository_upsert_get_and_list(tmp_path: Path):
    repository = SQLiteLifecycleRepository(tmp_path / "scan_store.sqlite")

    repository.upsert_trade_lifecycle(
        trade_id="trade_1",
        lifecycle_state="saved",
        state_updated_at="2026-04-22T10:00:00Z",
        note="Watch for tighter credit.",
        tags=["swing", "earnings_week"],
        source_scan_id="scan_123",
        created_at="2026-04-22T10:00:00Z",
        updated_at="2026-04-22T10:00:00Z",
        user_id="user_a",
    )

    loaded = repository.get_trade_lifecycle("trade_1", user_id="user_a")
    assert loaded is not None
    assert loaded.trade_id == "trade_1"
    assert loaded.lifecycle_state == "saved"
    assert loaded.note == "Watch for tighter credit."
    assert loaded.tags == ["swing", "earnings_week"]
    assert loaded.source_scan_id == "scan_123"

    rows = repository.list_trade_lifecycles(user_id="user_a")
    assert len(rows) == 1
    assert rows[0].trade_id == "trade_1"


def test_lifecycle_repository_is_user_scoped(tmp_path: Path):
    repository = SQLiteLifecycleRepository(tmp_path / "scan_store.sqlite")

    repository.upsert_trade_lifecycle(
        trade_id="trade_shared",
        lifecycle_state="watching",
        state_updated_at="2026-04-22T10:00:00Z",
        note=None,
        tags=[],
        source_scan_id=None,
        created_at="2026-04-22T10:00:00Z",
        updated_at="2026-04-22T10:00:00Z",
        user_id="user_a",
    )
    repository.upsert_trade_lifecycle(
        trade_id="trade_shared",
        lifecycle_state="dismissed",
        state_updated_at="2026-04-22T10:01:00Z",
        note=None,
        tags=[],
        source_scan_id=None,
        created_at="2026-04-22T10:01:00Z",
        updated_at="2026-04-22T10:01:00Z",
        user_id="user_b",
    )

    loaded_a = repository.get_trade_lifecycle("trade_shared", user_id="user_a")
    loaded_b = repository.get_trade_lifecycle("trade_shared", user_id="user_b")
    assert loaded_a is not None
    assert loaded_b is not None
    assert loaded_a.lifecycle_state == "watching"
    assert loaded_b.lifecycle_state == "dismissed"
