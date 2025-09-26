# README_CODEX

## Purpose & Scope
This repository contains the Agente_Perfilamiento vocational assistant. The project now separates the conversation flow into welcome, interviewer, analyst, final, memory, and fallback nodes. The goal is to collect user context cleanly (interviewer), persist summaries, then pass control to a specialised analyst that produces the recommendation.

## Architecture Overview
- src/agente_perfilamiento/domain
  - models/: Typed state (`conversation_state.py`), short-term memory models
  - services/: Stateless services (`memory_service.py`, `long_term_memory_service.py`, `entity_memory_service.py`)
- src/agente_perfilamiento/ports: Abstract repository interfaces
- src/agente_perfilamiento/adapters: File/in-memory repositories for ports
- src/agente_perfilamiento/agents: LangGraph nodes and prompts
- src/agente_perfilamiento/application/orchestrator.py: LangGraph state graph (router entry point)
- src/agente_perfilamiento/infrastructure
  - config/settings.py: env & runtime configuration
  - persistence/provider.py: singleton provider for MemoryService
- src/tests/test_conversation_flow.py: End-to-end test of interviewer→analyst pipeline

## Stack
- Python 3.11.9 (venv: `.venv`)
- langchain-core 0.3.76, langchain 0.3.27 (already installed in venv)
- langgraph (version bundled in project requirements)
- pytest 8.4.2 (dev dependency)
- dotenv for config loading

## How to Run
### CLI (interactive)
```powershell
.\.venv\Scripts\Activate.ps1
py -m agente_perfilamiento.main
```
This starts the LangGraph flow (router→welcome→interviewer→analyst→final→memory). Interviewer now emits `<<FIN_ENTREVISTA>>` internally to hand control to the analyst.

### Tests
```powershell
.\.venv\Scripts\Activate.ps1
python -m pytest src/tests/test_conversation_flow.py
```
This test stubs the LLM, exercises the full flow, verifies interview summary persistence, and removes the temp file afterward.

## Recent Decisions / Changelog-lite
- **Structured Interview Output**: Interviewer now triggers a follow-up LLM call when `ready_for_analysis` activates, generating the full JSON profile (`dimensiones_mapeadas`, `tags_acumulados_vector`, `Resumen`). This payload is saved in `data/interviews/...` under `structured_profile` for the analyst.
- **Summary Persistence**: Each interview summary file stores `conversation_history`, `user_profile`, and the new `structured_profile`. The path is still recorded via `state["interview_summary_path"]`.
- **Router -> Analyst**: Router continues to route to `analista` when `ready_for_analysis` is `True`; the analyst receives the enriched summary and produces recommendations as before.
- **CLI Print Behaviour**: CLI keeps printing only new assistant turns, avoiding duplicate output.
