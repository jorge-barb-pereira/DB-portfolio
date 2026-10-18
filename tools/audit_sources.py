"""Check imported source hashes and prevent accidental environment/data packaging."""
import hashlib
import json
from pathlib import Path
import subprocess

ROOT=Path(__file__).resolve().parents[1]
manifest=json.loads((ROOT/'archive/manifest.json').read_text(encoding='utf-8'))
for record in manifest['files']:
    path=ROOT/record['published']
    assert hashlib.sha256(path.read_bytes()).hexdigest()==record['published_sha256'],path
if (ROOT/'.git').exists():
    files=subprocess.check_output(['git','ls-files','-z'],cwd=ROOT).decode().split('\0')
    for name in filter(None,files):
        path=Path(name)
        assert path.name not in ('.env','profiles.yml','profiles.yaml'),name
        assert not any(part in ('venv','.venv','site-packages','__pycache__') for part in path.parts),name
        assert path.suffix not in ('.zip','.shp','.dbf','.pdf','.docx','.pptx'),name
        assert (ROOT/path).stat().st_size<5_000_000,name
print(f"Source audit passed for {len(manifest['files'])} imported files.")
