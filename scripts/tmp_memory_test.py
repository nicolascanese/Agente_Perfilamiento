import sys

sys.path.append('src')

from agente_perfilamiento.application.services.memory_service import MemoryService
from agente_perfilamiento.infrastructure.memory.in_memory_repository import (
    InMemoryMemoryRepository,
)


def main():
    repo = InMemoryMemoryRepository()
    svc = MemoryService(
        repository=repo, ttl_seconds=None, max_items_per_agent=5, window_limit=3
    )

    session = 'test-session-1'
    agent = 'perfilamiento_agent'

    for i in range(5):
        role = 'user' if i % 2 == 0 else 'assistant'
        svc.append_and_get_window(agent, session, role, f'msg-{i}')

    win_default = svc.get_window(agent, session)
    print('DEFAULT WINDOW SIZE:', len(win_default))
    print('DEFAULT WINDOW CONTENTS:', [w['content'] for w in win_default])

    win5 = svc.get_window(agent, session, limit=5)
    print('WINDOW(5) SIZE:', len(win5))
    print('WINDOW(5) CONTENTS:', [w['content'] for w in win5])

    svc.clear_session(session)
    print('AFTER CLEAR SIZE:', len(svc.get_window(agent, session)))


if __name__ == '__main__':
    main()
