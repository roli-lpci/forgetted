"""Tests for the forgetted package.

All file operations use /tmp/incognito-test/ as scratch space.
No writes to the real workspace (~/.openclaw/workspace/).
"""

import shutil
from pathlib import Path

import pytest

from forgetted.checkpoint import create_checkpoint, load_checkpoint
from forgetted.cleaner import delete_session_log, find_session_log
from forgetted.guard import ForgetGuard
from forgetted.trigger import TRIGGERS, is_forget_trigger

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

SCRATCH_ROOT = Path("/tmp/incognito-test/scratch")


@pytest.fixture(autouse=True)
def clean_scratch():
    """Create a fresh scratch workspace for each test."""
    if SCRATCH_ROOT.exists():
        shutil.rmtree(SCRATCH_ROOT)
    SCRATCH_ROOT.mkdir(parents=True, exist_ok=True)
    (SCRATCH_ROOT / "memory").mkdir()
    yield


# ---------------------------------------------------------------------------
# Trigger tests
# ---------------------------------------------------------------------------


class TestTriggerDetection:
    def test_slash_command(self):
        assert is_forget_trigger("/forgetted")

    def test_slash_forget(self):
        assert is_forget_trigger("/forget")

    def test_natural_language_forget_this(self):
        assert is_forget_trigger("hey can you forget this conversation")

    def test_natural_language_off_the_record(self):
        assert is_forget_trigger("let's go off the record")

    def test_forgetted_mode(self):
        assert is_forget_trigger("enable forgetted mode please")

    def test_case_insensitive(self):
        assert is_forget_trigger("FORGETTED MODE")
        assert is_forget_trigger("/FORGETTED")
        assert is_forget_trigger("Off The Record")

    def test_normal_message_not_triggered(self):
        assert not is_forget_trigger("hello how are you")
        assert not is_forget_trigger("what's the weather")
        assert not is_forget_trigger("tell me about memory")

    def test_empty_message(self):
        assert not is_forget_trigger("")

    def test_triggers_list_is_populated(self):
        assert len(TRIGGERS) >= 3


# ---------------------------------------------------------------------------
# Guard tests
# ---------------------------------------------------------------------------


class TestForgetGuard:
    def test_blocks_write_to_memory_dir(self):
        """Guard should silently discard writes to memory/ files."""
        target = SCRATCH_ROOT / "memory" / "2026-03-22.md"

        with ForgetGuard(str(SCRATCH_ROOT)), open(target, "w") as f:
            f.write("this should not persist")

        assert not target.exists()

    def test_blocks_write_to_deliverables(self):
        target = SCRATCH_ROOT / "DELIVERABLES.md"

        with ForgetGuard(str(SCRATCH_ROOT)), open(target, "w") as f:
            f.write("secret deliverable")

        assert not target.exists()

    def test_blocks_write_to_jsonl(self):
        target = SCRATCH_ROOT / "sessions" / "abc123.jsonl"
        target.parent.mkdir(parents=True, exist_ok=True)

        with ForgetGuard(str(SCRATCH_ROOT)), open(target, "w") as f:
            f.write('{"line": 1}')

        assert not target.exists()

    def test_blocks_append_mode(self):
        target = SCRATCH_ROOT / "memory" / "daily.md"

        with ForgetGuard(str(SCRATCH_ROOT)), open(target, "a") as f:
            f.write("appended content")

        assert not target.exists()

    def test_allows_reads(self):
        """Guard should never block read operations."""
        target = SCRATCH_ROOT / "memory" / "existing.md"
        target.write_text("readable content", encoding="utf-8")

        with ForgetGuard(str(SCRATCH_ROOT)), open(target) as f:
            content = f.read()

        assert content == "readable content"

    def test_allows_writes_outside_workspace(self):
        """Writes to paths outside the workspace should pass through."""
        outside = Path("/tmp/incognito-test/outside-workspace.txt")

        with ForgetGuard(str(SCRATCH_ROOT)), open(outside, "w") as f:
            f.write("this should work")

        assert outside.exists()
        assert outside.read_text() == "this should work"
        outside.unlink()

    def test_allows_writes_to_unprotected_workspace_files(self):
        """Non-protected files inside workspace should be writable."""
        target = SCRATCH_ROOT / "README.md"

        with ForgetGuard(str(SCRATCH_ROOT)), open(target, "w") as f:
            f.write("readme content")

        assert target.exists()
        assert target.read_text() == "readme content"

    def test_blocked_count_tracked(self):
        guard = ForgetGuard(str(SCRATCH_ROOT))
        guard.start()

        with open(SCRATCH_ROOT / "memory" / "a.md", "w") as f:
            f.write("blocked 1")
        with open(SCRATCH_ROOT / "memory" / "b.md", "w") as f:
            f.write("blocked 2")
        with open(SCRATCH_ROOT / "DELIVERABLES.md", "w") as f:
            f.write("blocked 3")

        guard.stop()
        assert guard.blocked_count == 3

    def test_guard_restores_open_after_stop(self):
        """After stop(), writes should work normally again."""
        target = SCRATCH_ROOT / "memory" / "post-guard.md"
        guard = ForgetGuard(str(SCRATCH_ROOT))

        guard.start()
        guard.stop()

        with open(target, "w") as f:
            f.write("this should persist now")

        assert target.exists()
        assert target.read_text() == "this should persist now"

    def test_double_start_is_safe(self):
        guard = ForgetGuard(str(SCRATCH_ROOT))
        guard.start()
        guard.start()  # should not error or double-patch
        guard.stop()

    def test_double_stop_is_safe(self):
        guard = ForgetGuard(str(SCRATCH_ROOT))
        guard.start()
        guard.stop()
        guard.stop()  # should not error


# ---------------------------------------------------------------------------
# Checkpoint tests
# ---------------------------------------------------------------------------


class TestCheckpoint:
    def test_checkpoint_created(self):
        summary = "Discussing API design for v2. Pending: endpoint naming decision."
        path = create_checkpoint(summary, str(SCRATCH_ROOT))

        assert path.exists()
        assert path.name == "forgetted-checkpoint.md"
        content = path.read_text()
        assert "Discussing API design" in content
        assert "endpoint naming decision" in content
        assert "Forgetted Checkpoint" in content

    def test_checkpoint_includes_timestamp(self):
        path = create_checkpoint("test summary", str(SCRATCH_ROOT))
        content = path.read_text()
        assert "UTC" in content

    def test_checkpoint_includes_resume_instructions(self):
        path = create_checkpoint("context here", str(SCRATCH_ROOT))
        content = path.read_text()
        assert "resume" in content.lower()
        assert "forgetted" in content.lower()

    def test_load_checkpoint_returns_content(self):
        create_checkpoint("important context", str(SCRATCH_ROOT))
        content = load_checkpoint(str(SCRATCH_ROOT))

        assert content is not None
        assert "important context" in content

    def test_load_checkpoint_deletes_file(self):
        path = create_checkpoint("will be consumed", str(SCRATCH_ROOT))
        assert path.exists()

        load_checkpoint(str(SCRATCH_ROOT))
        assert not path.exists()

    def test_load_checkpoint_returns_none_when_missing(self):
        result = load_checkpoint(str(SCRATCH_ROOT))
        assert result is None

    def test_checkpoint_creates_memory_dir_if_missing(self):
        workspace = SCRATCH_ROOT / "fresh-workspace"
        path = create_checkpoint("auto-create test", str(workspace))

        assert path.exists()
        assert (workspace / "memory").is_dir()


# ---------------------------------------------------------------------------
# Cleaner tests
# ---------------------------------------------------------------------------


class TestCleaner:
    def _make_session_log(self, session_id: str) -> Path:
        """Create a fake session log .jsonl file."""
        agents_dir = SCRATCH_ROOT / "agents" / "main" / "sessions"
        agents_dir.mkdir(parents=True, exist_ok=True)
        log_file = agents_dir / f"{session_id}.jsonl"
        log_file.write_text('{"msg": "test"}\n', encoding="utf-8")
        return log_file

    def test_find_session_log(self):
        self._make_session_log("session-abc123")
        agents_dir = str(SCRATCH_ROOT / "agents")

        found = find_session_log("session-abc123", agents_dir)
        assert found is not None
        assert found.name == "session-abc123.jsonl"

    def test_find_session_log_partial_match(self):
        self._make_session_log("agent-main-abc123-2026")
        agents_dir = str(SCRATCH_ROOT / "agents")

        found = find_session_log("abc123", agents_dir)
        assert found is not None

    def test_find_session_log_not_found(self):
        agents_dir = str(SCRATCH_ROOT / "agents")
        (Path(agents_dir)).mkdir(parents=True, exist_ok=True)

        found = find_session_log("nonexistent", agents_dir)
        assert found is None

    def test_find_session_log_missing_dir(self):
        found = find_session_log("anything", "/tmp/incognito-test/no-such-dir")
        assert found is None

    def test_delete_session_log_renames_to_deleted(self):
        log = self._make_session_log("session-to-delete")

        result = delete_session_log(log)
        assert result is True
        assert not log.exists()
        deleted = log.with_suffix(log.suffix + ".deleted")
        assert deleted.exists()

    def test_delete_session_log_missing_file(self):
        missing = Path("/tmp/incognito-test/no-such-file.jsonl")
        result = delete_session_log(missing)
        assert result is False

    def test_delete_session_log_idempotent(self):
        log = self._make_session_log("session-double-delete")
        delete_session_log(log)
        result = delete_session_log(log)
        assert result is False
