"""Preview the tutorial with reliable rebuilding of included slide sources.

Watch authoring files and run a fresh Quarto render after each change. Quarto's
preview server serves the output and refreshes connected browsers. Fresh render
processes avoid stale included Markdown in the preview process's content cache.

Key Components:
    - source_snapshot: Track source changes while excluding generated outputs.
    - render: Build all three presentation views in a fresh Quarto process.
    - main: Supervise the preview server and serialize rebuilds.

Usage Example:
    conda run --no-capture-output -n informstutorial python scripts/preview.py

Notes:
    - Authoring only; published slides still run entirely in the browser.
    - Uses the Quarto executable from the active informstutorial environment.
    - Does not modify source files and binds the server to the local computer.
"""
from __future__ import annotations

import argparse
import os
from pathlib import Path
import shutil
import signal
import subprocess
import time

ROOT = Path(__file__).resolve().parents[1]


def source_snapshot() -> dict[str, tuple[int, int]]:
    """Return modification times and sizes for inputs and bundled assets."""
    files = list(ROOT.glob('*.qmd')) + list(ROOT.glob('*.yml'))
    for directory in ('content', 'components', 'styles', 'assets'):
        files.extend(path for path in (ROOT / directory).rglob('*') if path.is_file())
    result = {}
    for path in files:
        try:
            stat = path.stat()
            result[str(path.relative_to(ROOT))] = (stat.st_mtime_ns, stat.st_size)
        except FileNotFoundError:
            # Editors may replace a file atomically while the scan runs.
            continue
    return result


def render(quarto: str) -> bool:
    """Build all outputs and report success without stopping after an edit error."""
    print('\nRebuilding presentation…', flush=True)
    result = subprocess.run([quarto, 'render'], cwd=ROOT, check=False)
    if result.returncode:
        print('Render failed. Correct the source and save again to retry.', flush=True)
    return result.returncode == 0


def main() -> None:
    """Serve the tutorial and rebuild after source changes until interrupted."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port', type=int, default=8767)
    args = parser.parse_args()
    quarto = shutil.which('quarto')
    if not quarto:
        raise SystemExit('Activate informstutorial first so Quarto is available.')
    snapshot = source_snapshot()
    if not render(quarto):
        raise SystemExit(1)
    server = subprocess.Popen([
        quarto, 'preview', 'index.qmd', '--port', str(args.port),
        '--host', '127.0.0.1', '--no-browser', '--no-watch-inputs',
    ], cwd=ROOT, start_new_session=True)
    print(f'Preview: http://localhost:{args.port} — save a source file to rebuild.', flush=True)
    try:
        while server.poll() is None:
            time.sleep(0.5)
            current = source_snapshot()
            if current == snapshot:
                continue
            # Wait for an editor's save/rename sequence to settle.
            time.sleep(0.4)
            current = source_snapshot()
            changed = sorted(key for key in current.keys() | snapshot.keys()
                             if current.get(key) != snapshot.get(key))
            print('Changed: ' + ', '.join(changed), flush=True)
            snapshot = current
            render(quarto)
        raise SystemExit(server.returncode)
    except KeyboardInterrupt:
        print('\nStopping preview.', flush=True)
    finally:
        if server.poll() is None:
            os.killpg(server.pid, signal.SIGTERM)
            try:
                server.wait(timeout=5)
            except subprocess.TimeoutExpired:
                os.killpg(server.pid, signal.SIGKILL)
                server.wait()


if __name__ == '__main__':
    main()
