from pathlib import Path
import shutil
import uuid

import pytest

from backend.repositories.factory import get_lifecycle_repository
from backend.services.lifecycle_service import (
    get_trade_lifecycle,
    list_trade_lifecycles,
    upsert_trade_lifecycle,
)


def _configure_tmp_db(monkeypatch, workspace_tmp_dir: Path):
    monkeypatch.setenv(
        "SCAN_DATABASE_PATH",
        str(workspace_tmp_dir / "history" / "scan_store.sqlite"),
    )


def test_default_state_is_new_when_record_missing(monkeypatch):
    workspace_tmp_dir = Path("tmp_test_lifecycle_service") / str(uuid.uuid4())
    workspace_tmp_dir.mkdir(parents=True, exist_ok=True)
    _configure_tmp_db(monkeypatch, workspace_tmp_dir)
    get_lifecycle_repository().clear()

    try:
        lifecycle = get_trade_lifecycle("trade_missing", user_id="user_demo")
        assert lifecycle["trade_id"] == "trade_missing"
        assert lifecycle["lifecycle_state"] == "new"
        assert lifecycle["is_default"] is True
    finally:
        shutil.rmtree(workspace_tmp_dir, ignore_errors=True)


def test_lifecycle_transitions_and_note_persistence(monkeypatch):
    workspace_tmp_dir = Path("tmp_test_lifecycle_service") / str(uuid.uuid4())
    workspace_tmp_dir.mkdir(parents=True, exist_ok=True)
    _configure_tmp_db(monkeypatch, workspace_tmp_dir)
    get_lifecycle_repository().clear()

    try:
        first = upsert_trade_lifecycle(
            "trade_1",
            user_id="user_demo",
            lifecycle_state="saved",
            source_scan_id="scan_1",
        )
        assert first["lifecycle_state"] == "saved"
        assert first["is_default"] is False

        second = upsert_trade_lifecycle(
            "trade_1",
            user_id="user_demo",
            lifecycle_state="execution_ready",
            note="Approved for next review window.",
            tags=["high_conviction", "credit"],
        )
        assert second["lifecycle_state"] == "execution_ready"
        assert second["note"] == "Approved for next review window."
        assert second["tags"] == ["high_conviction", "credit"]

        listed = list_trade_lifecycles(user_id="user_demo")
        assert len(listed) == 1
        assert listed[0]["trade_id"] == "trade_1"
        assert listed[0]["lifecycle_state"] == "execution_ready"

        with pytest.raises(ValueError, match="Invalid lifecycle transition"):
            upsert_trade_lifecycle(
                "trade_1",
                user_id="user_demo",
                lifecycle_state="new",
            )
    finally:
        shutil.rmtree(workspace_tmp_dir, ignore_errors=True)
