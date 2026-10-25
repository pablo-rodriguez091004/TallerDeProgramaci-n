"""
Recuperacion (la "R" de RAG) de servicios del catalogo relevantes para la
descripcion del cliente, por coincidencia de palabras clave.

Algoritmo:
1. Normalizar: minusculas, sin tildes, solo letras; quitar stopwords.
2. Raiz simple: los primeros 4 caracteres de cada palabra ("frenar" y
   "freno" -> "fren"; "vibra" y "vibracion" -> "vibr").
3. Expandir el sintoma con un diccionario pequeno de sinonimos del oficio
   ("chillido" -> freno, pastilla), porque el cliente describe sintomas y
   el catalogo nombra servicios.
4. Puntaje de cada servicio = raices compartidas con el nombre (peso 2) +
   raices compartidas con la descripcion (peso 1). Se devuelven los TOP_K
   con puntaje > 0.
5. Si ninguno coincide se usa todo el catalogo activo (es pequeno) y se
   marca fallback=True: el LLM decide con todo el contexto en vez de nada.

Se eligio sobre embeddings porque es determinista, explicable, no agrega
dependencias ni otra llamada paga, y alcanza para un catalogo de ~12 items.
"""

import re
import unicodedata

TOP_K = 5
STEM_LENGTH = 4

STOPWORDS = {
    'a', 'al', 'algo', 'cada', 'como', 'con', 'cuando', 'de', 'del', 'desde', 'donde', 'el', 'ella', 'en',
    'era', 'es', 'esta', 'este', 'esto', 'hace', 'hay', 'la', 'las', 'le', 'lo', 'los', 'mas', 'me', 'mi',
    'muy', 'no', 'o', 'para', 'pero', 'poco', 'por', 'que', 'se', 'si', 'sin', 'sus', 'su', 'tambien',
    'tiene', 'un', 'una', 'uno', 'y', 'ya', 'yo', 'veces', 'dias', 'semana', 'ahora', 'hoy', 'ayer',
    # Palabras del dominio demasiado generales: aparecen en casi todo el catalogo.
    'carro', 'auto', 'vehiculo', 'camioneta', 'moto', 'cambio', 'revision', 'servicio', 'sistema',
    'mantenimiento', 'problema', 'falla', 'raro', 'extrano', 'creo', 'parece', 'siento', 'noto',
}

# Prefijo del sintoma -> terminos que usa el catalogo. La clave se compara
# con el INICIO de cada palabra ("traqueteo".startswith("traq")). Escrito con
# conocimiento general de mecanica, no a partir de los casos de evaluacion.
SYMPTOM_SYNONYMS = {
    'fren': ['freno', 'pastilla', 'disco'],
    'chil': ['freno', 'pastilla'],          # chilla, chillido
    'rech': ['freno', 'pastilla'],          # rechina
    'pedal': ['freno', 'embrague'],
    'vibr': ['disco', 'balanceo', 'alineacion'],
    'tiem': ['disco', 'balanceo', 'bujia'],  # tiembla
    'jala': ['alineacion'],                 # se jala hacia un lado
    'lado': ['alineacion'],
    'volan': ['alineacion', 'balanceo'],    # volante
    'llan': ['alineacion', 'balanceo'],     # llanta
    'desg': ['alineacion', 'pastilla'],     # desgaste
    'golp': ['amortiguador', 'suspension'],  # golpe, golpeteo
    'huec': ['amortiguador', 'suspension'],
    'rebo': ['amortiguador', 'suspension'],  # rebota
    'traq': ['amortiguador', 'suspension'],  # traqueteo
    'ruid': ['suspension', 'freno'],
    'arra': ['bateria', 'arranque'],        # arranca, arranque
    'pren': ['bateria', 'arranque'],        # prende
    'ence': ['bateria', 'arranque'],        # enciende
    'desc': ['bateria', 'alternador'],      # descargada
    'luce': ['bateria', 'alternador'],
    'test': ['escaner', 'codigos'],         # testigo
    'tabl': ['escaner', 'codigos'],         # tablero
    'chec': ['escaner', 'codigos'],
    'calie': ['refrigeracion', 'radiador', 'termostato'],  # calienta
    'calen': ['refrigeracion', 'radiador', 'termostato'],  # calentamiento
    'reca': ['refrigeracion', 'radiador', 'termostato'],  # recalienta
    'temp': ['refrigeracion', 'termostato'],
    'agua': ['refrigeracion', 'radiador', 'mangueras'],
    'vapo': ['refrigeracion', 'radiador'],
    'humo': ['refrigeracion', 'sincronizacion'],
    'frio': ['aire', 'acondicionado'],
    'calo': ['aire', 'acondicionado'],
    'olor': ['aire', 'filtro', 'cabina'],
    'enfr': ['aire', 'acondicionado'],
    'consu': ['sincronizacion', 'inyectores'],  # consume, consumo
    'gaso': ['sincronizacion', 'inyectores'],
    'comb': ['sincronizacion', 'inyectores'],
    'pote': ['sincronizacion', 'bujias'],      # potencia
    'fuerz': ['sincronizacion', 'bujias'],     # sin fuerza
    'tiro': ['sincronizacion', 'bujias'],      # tironea
    'aho': ['sincronizacion', 'bujias'],       # se ahoga
    'mini': ['sincronizacion', 'inyectores'],  # minimo
    'pati': ['embrague'],                      # patina
    'emb': ['embrague'],
    'clut': ['embrague'],
    'marc': ['embrague'],                      # marchas
    'kilo': ['aceite', 'correa', 'distribucion'],
    'corr': ['correa', 'distribucion'],
    'acei': ['aceite', 'filtro'],
}


def normalize(text):
    text = unicodedata.normalize('NFKD', text.lower())
    text = ''.join(c for c in text if not unicodedata.combining(c))
    return re.findall(r'[a-z]+', text)


def _stem(word):
    return word[:STEM_LENGTH]


def _stems(text):
    return {_stem(w) for w in normalize(text) if w not in STOPWORDS and len(w) > 2}


def query_terms(description):
    """Raices de la descripcion + raices de los sinonimos que dispara."""
    words = [w for w in normalize(description) if w not in STOPWORDS and len(w) > 2]
    terms = {_stem(w) for w in words}
    for word in words:
        for key, synonyms in SYMPTOM_SYNONYMS.items():
            if word.startswith(key):
                terms.update(_stem(s) for s in synonyms)
    return terms


def score_service(service, terms):
    name_hits = terms & _stems(service.service_name)
    description_hits = terms & _stems(service.description or '')
    return 2 * len(name_hits) + len(description_hits)


def retrieve(description, catalog, top_k=TOP_K):
    """
    Devuelve {'services': [...], 'scores': {id: puntaje}, 'fallback': bool}.
    `catalog` son los servicios activos (los que se pueden agendar); quien
    llama los obtiene del repositorio, asi esta funcion queda pura.
    """
    terms = query_terms(description)
    scored = [(score_service(s, terms), s) for s in catalog]
    matches = sorted((pair for pair in scored if pair[0] > 0), key=lambda p: (-p[0], p[1].service_id))[:top_k]

    if not matches:
        return {'services': catalog, 'scores': {}, 'fallback': True}
    return {'services': [s for _, s in matches],
            'scores': {s.service_id: score for score, s in matches},
            'fallback': False}
