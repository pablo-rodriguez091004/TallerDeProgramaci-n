import json
import os
from datetime import datetime

from domain.market_data.ports import Snapshot, SnapshotStore


class JsonFileSnapshotStore(SnapshotStore):
    """
    Guarda la ultima descarga de cada fuente como JSON en disco
    (<data_dir>/<fuente>.json). DuckDB lee estos archivos en la Fase 4.
    Se escribe en un temporal y se renombra: nunca queda un archivo a medias.
    """

    def __init__(self, data_dir):
        self.data_dir = data_dir

    def _path(self, source):
        return os.path.join(self.data_dir, f'{source}.json')

    def save(self, source, records, fetched_at):
        os.makedirs(self.data_dir, exist_ok=True)
        path = self._path(source)
        payload = {'source': source, 'fetched_at': fetched_at.isoformat(), 'rows': len(records), 'records': records}
        tmp = f'{path}.tmp'
        with open(tmp, 'w', encoding='utf-8') as f:
            json.dump(payload, f, ensure_ascii=False)
        os.replace(tmp, path)
        return Snapshot(source, fetched_at, len(records), path)

    def latest(self, source):
        path = self._path(source)
        if not os.path.exists(path):
            return None
        with open(path, encoding='utf-8') as f:
            meta = json.load(f)
        return Snapshot(source, datetime.fromisoformat(meta['fetched_at']), meta['rows'], path)
