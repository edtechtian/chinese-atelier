#!/usr/bin/env python3
"""Run the actual app with a separate temporary student record for browser QA."""
import argparse
from pathlib import Path
import shutil
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from server import AppServer


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port', type=int, default=8002)
    parser.add_argument('--reuse-root', type=Path, help='Restart a previous emmalyne-qa temporary directory')
    args = parser.parse_args()
    if args.reuse_root:
        qa_root = args.reuse_root.resolve()
        if not qa_root.name.startswith('emmalyne-qa-') or not (qa_root / 'data/curriculum.json').is_file():
            parser.error('Reuse only a previous isolated emmalyne-qa directory')
    else:
        qa_root = Path(tempfile.mkdtemp(prefix='emmalyne-qa-'))
        (qa_root / 'data').mkdir()
        shutil.copy2(ROOT / 'data/curriculum.json', qa_root / 'data/curriculum.json')
        (qa_root / 'public').symlink_to(ROOT / 'public', target_is_directory=True)
        (qa_root / 'sources').symlink_to(ROOT / 'sources', target_is_directory=True)
    server = AppServer(('127.0.0.1', args.port), root=qa_root, teacher_key='qa-local-only')
    print(f'Isolated QA app: http://localhost:{server.server_port}', flush=True)
    print(f'Temporary QA records: {qa_root}', flush=True)
    print('Test-only teacher key: qa-local-only. Real student records are untouched.', flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print('QA server stopped. Temporary records retained for inspection.', flush=True)
    finally:
        server.server_close()


if __name__ == '__main__':
    main()
