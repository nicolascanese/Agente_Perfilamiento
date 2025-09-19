import sys
sys.path.append('src')

from datetime import datetime

from agente_perfilamiento.application.services.long_term_memory_service import LongTermMemoryService
from agente_perfilamiento.infrastructure.memory.file_long_term_repository import FileLongTermMemoryRepository
from agente_perfilamiento.application.services.entity_memory_service import EntityMemoryService
from agente_perfilamiento.infrastructure.memory.file_entity_repository import FileEntityMemoryRepository


def main():
    # Long-term memory
    ltm = LongTermMemoryService(FileLongTermMemoryRepository())
    rec_path = ltm.save_summary({
        'id_user': 'u1',
        'id_conversacion': 'sess-123',
        'fecha_inicio': datetime.now().isoformat(),
        'resumen': 'Usuario u1 habló sobre objetivos y ahorro.',
    })
    print('Saved LTM at:', rec_path)
    print('Summaries text:\n', ltm.get_user_summaries_text('u1'))

    # Entity memory
    ems = EntityMemoryService(FileEntityMemoryRepository())
    ems.upsert('u1', {'nombre': 'Nico', 'edad': 33, 'intereses': ['finanzas', 'IA']})
    print('Entity get 1:', ems.get('u1'))
    ems.upsert('u1', {'hoja_ruta': ['Paso 1', 'Paso 2']})
    print('Entity get 2:', ems.get('u1'))


if __name__ == '__main__':
    main()

