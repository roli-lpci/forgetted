# forgetted — Intent

A selective memory governance primitive for AI agents. Intercepts an agent's persistence layer during a bounded session window so that writes to memory files, session logs, and vector DBs vanish silently while reads continue to work normally. On exit, the session self-cleans and the agent resumes from where it left off. Intended for developers who need context-without-consequence windows — sensitive conversations, client data, experiments — inside an otherwise persistent agent architecture.

## Accepts

- opens and closes a forgetted window via `ForgetSession` context manager or explicit `start()` / `stop()` calls
- blocks file writes to `memory/`, `DELIVERABLES.md`, and `*.jsonl` paths inside the workspace by monkey-patching `builtins.open`
- returns a no-op `StringIO` or `BytesIO` handle for blocked write attempts — agent code does not crash
- never blocks reads — the agent retains full read access to existing memory during the window
- saves a resumption checkpoint to `memory/forgetted-checkpoint.md` before going dark when `checkpoint_summary` is provided
- consumes the checkpoint on the next `load_checkpoint()` call and deletes it immediately after reading (single-use)
- blocks mem0 `add` and `update` calls during the window via `Mem0Adapter`
- runs a post-window cleanup sweep on each adapter to delete memories that leaked in during the session
- deletes the session log file after the window if `session_id` and `agents_dir` are provided
- supports additional custom adapters implementing the `PersistenceAdapter` base class
- raises `RuntimeError` if an adapter is added after `start()` has been called
- activates forgetted mode from natural-language trigger phrases (`/forget`, `off the record`, `don't remember this`, etc.) via `is_forget_trigger()`
- re-enables all adapters before running cleanup so cleanup code can write freely
- continues across all adapters if one adapter raises during disable, enable, or cleanup

## Does not

- intercept writes outside the declared workspace path
- block network calls, API calls, or external agent tool use
- guarantee erasure of data already written before the window opened
- protect against writes that bypass `builtins.open` (e.g., C extensions, subprocess)
- delete memories that existed before the forgetted window started
- function as a security boundary — it is a software convenience layer, not a containment primitive
- support concurrent forgetted sessions from multiple threads on the same workspace
