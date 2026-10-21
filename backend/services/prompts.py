"""
Prompts del asistente de servicios (POST /api/v1/ai/suggest-service).

Tres tecnicas de prompting comparten el mismo prompt de sistema y el mismo
contexto recuperado (RAG); solo cambia la forma de pedir la respuesta:

- zero_shot: instrucciones + contexto, sin ejemplos.
- few_shot:  lo mismo + 3 ejemplos resueltos (sintoma -> JSON).
- cot:       chain-of-thought: el modelo escribe primero su analisis paso a
             paso en "reasoning" y despues elige los servicios.

El modelo SOLO devuelve service_id del contexto; el backend agrega nombre,
precio y duracion desde la base de datos, asi el LLM no puede inventarlos.
Los textos van en ingles (requisito de la guia); el cliente escribe en
espanol y el modelo responde "reason"/"notes" en el idioma del cliente.
"""

import json

TECHNIQUES = ('zero_shot', 'few_shot', 'cot')
DEFAULT_TECHNIQUE = 'few_shot'
MAX_SUGGESTIONS = 3

SYSTEM_PROMPT = """You are the service advisor of MecaTrack, a car repair workshop in Colombia.
A customer describes a problem with their vehicle in their own words, usually in Spanish.
Your job is to recommend which services from the workshop catalog they should book.

Rules:
1. Recommend ONLY services listed in the CATALOG CONTEXT, identified by their exact service_id.
2. Never invent services, prices or durations. Do not write prices or durations at all:
   the system adds them from the database.
3. Recommend at most 3 services, the most likely first. If no listed service fits,
   return an empty "suggestions" list and explain why in "notes".
4. If the description suggests a safety risk (brakes, steering, overheating), say so in "notes".
5. Write "reason" and "notes" in the same language as the customer's description.
6. Answer with one JSON object and nothing else."""

SUGGESTION_FORMAT = """{"service_id": <integer from the CATALOG CONTEXT>, "confidence": "high" | "medium" | "low", "reason": "<one short sentence>"}"""

OUTPUT_FORMAT = """Answer with this JSON shape:
{"suggestions": [""" + SUGGESTION_FORMAT + """], "notes": "<short note, or empty string>"}"""

COT_OUTPUT_FORMAT = """Think step by step before choosing. First write your analysis in "reasoning":
(1) which vehicle system is most likely affected, (2) the possible causes,
(3) which services of the CATALOG CONTEXT address those causes. Then give the suggestions.
Answer with this JSON shape:
{"reasoning": "<your step-by-step analysis>", "suggestions": [""" + SUGGESTION_FORMAT + """], "notes": "<short note, or empty string>"}"""

# Los ejemplos usan ids 101-106 de un catalogo ficticio a proposito: asi el
# modelo no copia ids de los ejemplos en vez de leer el CATALOG CONTEXT real.
FEW_SHOT_EXAMPLES = [
    {
        'catalog': [
            (101, 'Cambio de pastillas de freno', 'Reemplazo de pastillas de freno'),
            (102, 'Alineacion y balanceo', 'Alineacion de llantas y balanceo'),
        ],
        'description': 'Cuando freno se escucha un chillido metalico en las ruedas de adelante',
        'answer': {'suggestions': [{'service_id': 101, 'confidence': 'high',
                                    'reason': 'El chillido metalico al frenar suele indicar pastillas gastadas.'}],
                   'notes': 'Un problema de frenos es un riesgo de seguridad; conviene revisarlo pronto.'},
    },
    {
        'catalog': [
            (103, 'Diagnostico con escaner', 'Lectura de codigos de falla de la computadora'),
            (104, 'Sincronizacion de motor', 'Bujias, inyectores y ajuste de mezcla'),
            (105, 'Cambio de aceite', 'Cambio de aceite y filtro'),
        ],
        'description': 'Se prendio la luz de check engine y el carro tiembla cuando esta prendido sin acelerar',
        'answer': {'suggestions': [
            {'service_id': 103, 'confidence': 'high',
             'reason': 'La luz de check engine requiere leer los codigos de falla para saber la causa.'},
            {'service_id': 104, 'confidence': 'medium',
             'reason': 'El temblor en minimo puede deberse a bujias o inyectores en mal estado.'}],
            'notes': ''},
    },
    {
        'catalog': [
            (105, 'Cambio de aceite', 'Cambio de aceite y filtro'),
            (106, 'Revision de embrague', 'Ajuste o cambio del kit de embrague'),
        ],
        'description': 'Quiero polarizar los vidrios del carro',
        'answer': {'suggestions': [],
                   'notes': 'El catalogo del taller no incluye polarizado de vidrios.'},
    },
]


def format_catalog(services):
    """Contexto RAG: una linea por servicio con id, nombre y descripcion (sin precio)."""
    return '\n'.join(f'[{s.service_id}] {s.service_name} - {s.description or "sin descripcion"}'
                     for s in services)


def _format_example(example, index):
    catalog = '\n'.join(f'[{sid}] {name} - {desc}' for sid, name, desc in example['catalog'])
    return (f'Example {index}\n'
            f'CATALOG CONTEXT:\n{catalog}\n'
            f'CUSTOMER DESCRIPTION: {example["description"]}\n'
            f'ANSWER: {json.dumps(example["answer"], ensure_ascii=False)}')


def build_prompt(technique, description, services):
    """Devuelve (system_prompt, user_prompt) para la tecnica indicada."""
    if technique not in TECHNIQUES:
        raise ValueError(f'Unknown technique: {technique}')

    parts = []
    if technique == 'few_shot':
        examples = '\n\n'.join(_format_example(e, i) for i, e in enumerate(FEW_SHOT_EXAMPLES, 1))
        parts.append('The following solved examples show the expected answer. They use an example '
                     'catalog; for the real request use ONLY the real CATALOG CONTEXT below.\n\n' + examples)

    parts.append('Now the real request.' if technique == 'few_shot' else '')
    parts.append(f'CATALOG CONTEXT:\n{format_catalog(services)}')
    parts.append(f'CUSTOMER DESCRIPTION: {description}')
    parts.append(COT_OUTPUT_FORMAT if technique == 'cot' else OUTPUT_FORMAT)

    return SYSTEM_PROMPT, '\n\n'.join(p for p in parts if p)
