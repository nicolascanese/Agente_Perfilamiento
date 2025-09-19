# Agente_Perfilamiento

Un agente vocacional que guía a personas de 14 a 25 años a elegir un área de IT para educarse.

## Overview

This project was generated from a cookiecutter template and implements a LangGraph-based chat agent following hexagonal architecture principles. The architecture separates business logic from infrastructure concerns, making the codebase maintainable, testable, and extensible.

## Architecture

The project follows **Hexagonal Architecture** (Ports & Adapters) pattern:

```
Agente_Perfilamiento/
├── src/
│   └── agente_perfilamiento/
│       ├── domain/              # Business entities and rules
│       │   ├── models/          # Domain entities
│       │   ├── services/        # Business services
│       │   └── events/          # Domain events
│       │
│       ├── application/         # Use cases and orchestration
│       │   ├── orchestrator.py  # LangGraph orchestrator
│       │   └── use_cases/       # Application use cases
│       │
│       ├── ports/               # Abstract interfaces
│       │   └── conversation_repository.py
│       │
│       ├── adapters/            # Concrete implementations
│       │   ├── memory_repository.py
│       │   ├── file_repository.py
│       │   └── __init__.py
│       │
│       ├── infrastructure/      # External integrations
│       │   ├── config/          # Settings and configuration
│       │   ├── logging/         # Logging setup
│       │   └── persistence/     # Database connections
│       │
│       ├── agents/              # LangGraph nodes and tools
│       │   ├── welcome_node.py  # Welcome node
│       │   ├── final_node.py    # Final node
│       │   ├── memory_node.py   # Memory node
│       │   ├── tools/           # Agent tools
│       │   └── __init__.py
│       │
│       └── main.py              # Entry point
├── pyproject.toml
├── README.md
├── .env.example
└── .pre-commit-config.yaml
```

## Quick Start

### Prerequisites

- Python 3.11.9+
- UV package manager (recommended) or pip

### Installation

1. Clone or download this generated project
2. Navigate to the project directory:
   ```bash
   cd Agente_Perfilamiento
   ```

3. Create and activate a virtual environment:
   ```bash
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

### Configuration

1. Copy the environment template:
   ```bash
   cp .env.example .env
   ```

2. Edit `.env` and add your configuration:
   ```env
   LLM_API_KEY=your_llm_api_key_here
   LLM_MODEL=gpt-4o-mini
   LOG_LEVEL=INFO
   ```

3. Ensure required directories exist:
   ```bash
   mkdir -p data/conversations data/memory logs
   ```
   ```PowerShell
   New-Item -ItemType Directory -Force -Path data\conversations, data\memory, logs
   ```
## Usage

### Command Line Interface

Run the agent directly from the command line:

```bash
python src/agente_perfilamiento/main.py
```

Or using the installed package:

```bash
agente_perfilamiento
```

### Programmatic Usage

```python
from agente_perfilamiento.main import process_conversation

# Process a single conversation turn
result = process_conversation(
    user_id="user123",
    user_input="Hello, I need help with my finances",
    conversation_id=None  # Will create new conversation
)

# Access the response
for message in result["mensajes_previos"]:
    if message["role"] == "assistant":
        print(message["content"])
```

### Streamlit Integration (Optional)

If you installed with Streamlit support:

```bash
uv pip install -e ".[streamlit]"
```

Create a `streamlit_app.py`:

```python
import streamlit as st
from agente_perfilamiento.main import process_conversation

st.title("Agente_Perfilamiento")

if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Chat input
if prompt := st.chat_input("What can I help you with?"):
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})

    # Process through agent
    result = process_conversation("streamlit_user", prompt)

    # Add assistant response
    for msg in result["mensajes_previos"]:
        if msg["role"] == "assistant":
            st.session_state.messages.append(msg)
            with st.chat_message("assistant"):
                st.markdown(msg["content"])
```

Run with: `streamlit run streamlit_app.py`

## Development

### Setup Development Environment

1. Install development dependencies:
   ```bash
   uv pip install -e ".[dev]"
   ```

2. Install pre-commit hooks:
   ```bash
   pre-commit install
   ```

3. Run tests:
   ```bash
   pytest
   ```

### Code Quality Tools

This project includes comprehensive code quality tools:

- **Black**: Code formatting
- **Flake8**: Linting and style checking
- **Pylint**: Static analysis
- **Bandit**: Security vulnerability scanning
- **MyPy**: Type checking

Run all checks:
```bash
pre-commit run --all-files
```

### Testing

Run the test suite:
```bash
pytest tests/
```

With coverage:
```bash
pytest --cov=src/agente_perfilamiento tests/
```

## Customization

### Adding New Agents/Nodes

1. Create a new node in `src/agente_perfilamiento/agents/`:
   ```python
   def my_custom_node(state: ConversationState) -> ConversationState:
       # Your node logic here
       return state
   ```

2. Register the node in `application/orchestrator.py`:
   ```python
   builder.add_node("my_custom", RunnableLambda(my_custom_node))
   ```

3. Add routing logic as needed.

### Adding New Tools

1. Create tools in `src/agente_perfilamiento/agents/tools/`:
   ```python
   from langchain_core.tools import tool

   @tool
   def my_custom_tool(query: str) -> str:
       """Tool description."""
       return "Tool response"
   ```

2. Import and use in relevant nodes.

### Extending Persistence

1. Create new repository implementations in `adapters/`
2. Implement the repository interface from `ports/`
3. Configure in `infrastructure/config/settings.py`

## Environment Variables

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `LLM_API_KEY` | LLM API key | Yes | - |
| `LLM_MODEL` | LLM model to use | No | gpt-4o-mini |
| `LOG_LEVEL` | Logging level | No | INFO |
| `ENVIRONMENT` | Environment (dev/prod) | No | development |
| `DATA_DIR` | Data storage directory | No | data |

## Project Structure Details

### Domain Layer
- **Models**: Core business entities and value objects
- **Services**: Business logic and domain rules
- **Events**: Domain events for decoupled communication

### Application Layer
- **Orchestrator**: LangGraph workflow coordination
- **Use Cases**: Application-specific business logic

### Infrastructure Layer
- **Config**: Environment and settings management
- **Logging**: Centralized logging configuration
- **Persistence**: Database and file system adapters

### Agents Layer
- **Nodes**: LangGraph conversation nodes
- **Tools**: LangChain tools for agent capabilities

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests and quality checks
5. Submit a pull request
