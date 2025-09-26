# HANDOFF

## Current Status
- Flow: welcome -> entrevistador -> analista -> final -> memory, controlled by `router_node`. Interviewer stores conversation data, generates a structured profile JSON when `ready_for_analysis` (or `<<FIN_ENTREVISTA>>`) fires, and then triggers the analyst.
- Summaries persisted to `data/interviews/` with timestamped filenames and referenced by `interview_summary_path`; each file contains `conversation_history`, `user_profile`, and the new `structured_profile`.
- CLI prints only new assistant messages.
- Latest tests pass (`python -m pytest src/tests/test_conversation_flow.py`).

## Open Challenges / Next Steps
1. Validate end-to-end with real LLM responses to ensure the interviewer returns parseable `structured_profile` JSON and the analyst consumes it without errors.
2. Confirm environment variables (`LLM_API_KEY`, provider settings) are configured in `.env` before running CLI.
3. Extend automated tests to cover the new structured profile generation and the final/memory nodes (current test stops at analyst output).

## Key Paths & Artifacts
- `data/interviews/`: persisted interview summaries (JSON). Example: `data/interviews/user-test_test-flow_20250924204645.json`.
- `data/memory/`: long-term summary files written by final/memory nodes.
- Prompts: `src/agente_perfilamiento/agents/prompts/*.txt`
- LangGraph orchestrator: `src/agente_perfilamiento/application/orchestrator.py`

## Recent Test Results
- `python -m pytest src/tests/test_conversation_flow.py` → PASS (creates/interacts with summary file, cleaned afterward).

## Schemas / Contracts
- `ConversationState` (`src/agente_perfilamiento/domain/models/conversation_state.py`): includes `interview_summary`, `interview_summary_path`, `ready_for_analysis`, `evaluation_complete`.
- Interview summary payload stored in JSON with keys: `id_user`, `session_id`, `created_at`, `current_question_index`, `conversation_history`, `user_profile`, plus `structured_profile` when the LLM returns a valid object.
- Interviewer must emit `<<FIN_ENTREVISTA>>` (as plain text) when done; router uses `ready_for_analysis` flag.

## Environment Notes
- Virtualenv: `.venv` (Python 3.11.9). Avoid creating a new venv; reuse existing to keep identical package versions.
- Core packages (already installed):
  - langchain-core==0.3.76
  - langchain==0.3.27
  - langgraph (version per project requirements)
  - pytest==8.4.2
  - python-dotenv (for `.env` loading)
- Activate with `.\.venv\Scripts\Activate.ps1` (Windows PowerShell).
- `.env` must provide `LLM_API_KEY` and optionally overrides (provider/model). No upgrades performed.

## Examples
- Run CLI session:
  ```powershell
  .\.venv\Scripts\Activate.ps1
  py -m agente_perfilamiento.main
  ```
- Execute end-to-end test:
  ```powershell
  .\.venv\Scripts\Activate.ps1
  python -m pytest src/tests/test_conversation_flow.py
  ```

Ensure you stay within the existing environment and file structure when continuing work.
