"""Reproduce initial figures for the editable continuous-MDP browser demos.

Authoring helper only. Visitors execute the same code using the bundled Pyodide
worker. Existing pictures remain visible until Run Python recomputes a result.
Run with Python, NumPy, SciPy, and Matplotlib installed.
"""
from __future__ import annotations

import html
import os
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
os.environ.setdefault('MPLCONFIGDIR', '/tmp/tutorial-matplotlib')
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt


def main() -> None:
    directory = ROOT / 'assets/python/continuous'
    sys.dont_write_bytecode = True
    sys.path.insert(0, str(directory))
    scope = {'__name__': '__main__'}
    exec(compile((directory / 'demo_helpers.py').read_text(), 'demo_helpers.py', 'exec'), scope)
    scope.update(INK='#182c3e', PRIMARY='#226a85', TEAL='#267f77',
                 ACCENT='#a4592f', MUTED='#dce4e9', DANGER='#9b3f34')
    destination = ROOT / 'assets/figures/continuous-demos'
    destination.mkdir(parents=True, exist_ok=True)
    source = (ROOT / 'content/slides.qmd').read_text()
    labs = list(re.finditer(r'<div\b[^>]*data-continuous-python[^>]*>', source))
    for lab in labs:
        identifier = re.search(r'data-demo-id="([^"]+)"', lab.group()).group(1)
        editor = re.search(r'<textarea\b[^>]*>(.*?)</textarea>', source[lab.end():], re.S)
        code = html.unescape(editor.group(1))
        captured = []

        def capture(*args, **kwargs):
            for number in list(plt.get_fignums()):
                figure = plt.figure(number)
                filename = destination / f'{identifier}.png'
                figure.savefig(filename, dpi=160, bbox_inches='tight', facecolor='white')
                captured.append(filename)
                plt.close(figure)

        plt.show = capture
        exec(compile(code, identifier, 'exec'), scope)
        capture()
        if len(captured) != 1:
            raise RuntimeError(f'{identifier}: expected one figure, captured {len(captured)}')
        print(f'Wrote {captured[0].relative_to(ROOT)}', flush=True)
    if len(labs) != 9:
        raise RuntimeError(f'Expected nine demos, found {len(labs)}')


if __name__ == '__main__':
    main()
