# Presentation

## Open

[View slides online](https://parshanpakiman.github.io/Presentation/Self-adaptingADP-UB-Fall26/)
after GitHub Pages is deployed. See the [publishing instructions](../../README.md#view-presentations-online)
for first-time setup.

For local viewing, render the project first (see below), then double-click
**Open slides.html** in the parent folder, or open `_site/index.html` directly in
your browser. The generated `_site/` folder is excluded from Git. The main talk
has 28 slides and runs in browser JavaScript without Python or a local server.

Use arrows to advance, **Esc** for overview, **M** for Contents, and **F** for full screen. Presenter notes use **S**; browser restrictions may require serving the files over HTTP for that optional feature.

Other prepared views:

- `_site/reading.html`: the main talk as a reading page.
- `_site/backup.html`: technical appendix. Some legacy demonstrations here use browser Python and require HTTP hosting; they are optional and separate from the main talk.

Keep the entire `_site/` directory together when copying the presentation. External reference links require internet access.

## Edit and rebuild

| File | Purpose |
| --- | --- |
| `content/slides.qmd` | Main slide text, equations, notes, and reveal groups |
| `index.qmd` | Slide format and styling |
| `reading.qmd` | Reading view format |
| `styles/` | Presentation styles |
| `components/scripts.html` | Main talk JavaScript; no Python execution scripts |
| `components/backup-scripts.html` | Full legacy demonstration scripts for the appendix |
| `assets/` | Figures, papers, prepared data, and optional demo resources |
| `backup.qmd`, `content/backup.qmd` | Technical appendix |

Keep slide IDs, data attributes, and fragment indices when editing. The interactive figures use these to advance with the talk.

From the parent folder, rebuild with:

```sh
quarto render presentation
```

Quarto handles the build and math typesetting. No Python environment is needed. Refresh the browser to see your changes. Existing Python scripts and numerical checks are optional research utilities; you do not need them to present or rebuild the prepared slides.
