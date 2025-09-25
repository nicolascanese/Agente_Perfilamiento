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
- **Conversation Flow Split**: Interviewer and analyst are now separate nodes. Interviewer collects data, analyst generates recommendations.
- **Interview Summary**: interviewer writes JSON to `data/interviews/<user>_<session>_<timestamp>.json`, stored in state (`interview_summary`, `interview_summary_path`).
- **Router Logic**: router checks welcome memory before re-routing; uses `ready_for_analysis` and `evaluation_complete` flags to branch to analyst/final.
- **CLI Print Behaviour**: only new assistant messages are printed each turn, preventing repeated output.
- **Prompt Update**: interviewer prompt reverted to original detailed version, but instruction now states to output only `<<FIN_ENTREVISTA>>` when done.
