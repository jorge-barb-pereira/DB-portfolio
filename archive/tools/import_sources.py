from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import re

import argparse
parser = argparse.ArgumentParser(description='Import the explicitly selected academic sources; environments and datasets are excluded')
parser.add_argument('source',type=Path)
source = parser.parse_args().source.resolve(strict=True)
target = Path(__file__).resolve().parents[2]
records = []
selected = []
for folder in ('Project/sql','Project/etl','Project/app'):
    selected.extend(p for p in (source/folder).glob('*') if p.suffix in ('.py','.sql'))
selected.append(source/'Project/app/templates/index.html')
selected.extend((source/'DB_1/Trabalho').glob('*.sql'))
selected = [p for p in selected if p.name != 'povoar.sql']
for folder in (source/'DB_1/Trabalho').iterdir():
    if folder.is_dir():
        selected.extend(p for p in folder.glob('*.sql') if not p.name.startswith('povoar'))
selected.extend(p for p in (source/'db_ii/Laboratorial Classes').rglob('*.sql') if 'solutions' not in p.name.lower())
for original in sorted(set(selected)):
    relative = original.relative_to(source)
    raw = original.read_bytes()
    text = raw.decode('utf-8-sig')
    sanitized = re.sub(r'os\.getenv\("DB_PASS",\s*"[^"]*"\)', 'os.environ["DB_PASS"]', text)
    if original.suffix == '.py':
        sanitized = re.sub(r"password\s*=\s*(['\"])[^'\"]+\1", 'password=os.environ["DB_PASS"]', sanitized)
        if sanitized != text and 'import os' not in sanitized:
            sanitized = 'import os\n' + sanitized
    data = sanitized.encode('utf-8') if sanitized != text else raw
    if relative.parts[0] == 'Project':
        published = Path('archive/election-analytics').joinpath(*relative.parts[1:])
    elif relative.parts[0] == 'DB_1':
        published = Path('archive/healthcare-db').joinpath(*relative.parts[1:])
    else:
        published = Path('archive/sql-labs').joinpath(*relative.parts[2:])
    destination = target/published
    destination.parent.mkdir(parents=True,exist_ok=True)
    destination.write_bytes(data)
    records.append({'source':relative.as_posix(),'published':destination.relative_to(target).as_posix(),
                    'original_sha256':hashlib.sha256(raw).hexdigest(),
                    'published_sha256':hashlib.sha256(data).hexdigest(),
                    'modified_utc':datetime.fromtimestamp(original.stat().st_mtime,timezone.utc).isoformat(),
                    'change':'Remove fallback or inline database password' if data != raw else 'Verbatim byte copy'})
(target/'archive/manifest.json').write_text(json.dumps({'imported_on':'2026-10-18','files':records},indent=2)+'\n',encoding='utf-8')
print(f'Imported {len(records)} selected source files. Environment files, data, seed records, binaries and solutions excluded.')

