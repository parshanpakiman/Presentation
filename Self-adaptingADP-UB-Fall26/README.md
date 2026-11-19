# Self-Adapting Approximations of Markov Decision Processes

## Open the presentation

### Online

[View slides](https://parshanpakiman.github.io/Presentation/Self-adaptingADP-UB-Fall26/)
in your browser. This link works after the first successful GitHub Pages
deployment; see the [repository publishing instructions](../README.md#view-presentations-online).
Clicking **Open slides.html** on GitHub displays its source code.

### On your computer

After rendering the presentation (see below), double-click **Open slides.html**
in this folder. It opens the 28-slide presentation in your browser. Once built,
the main talk needs no Python or local server.

- Use the arrow keys to advance slides and animations.
- Press **Esc** for the slide overview.
- Use **Contents** or press **M** to jump to a slide.
- Press **F** for full screen.

Keep `presentation/_site/` intact: it contains the slides and their local images, styles, and JavaScript.
This generated folder is excluded from Git, so a fresh clone needs to be rendered
before the local launcher works.

## Edit the presentation

Edit `presentation/content/slides.qmd` for slide text and equations. The main slides and reading view share this content.

To rebuild after editing, install Quarto and run:

```sh
quarto render presentation
```

Rendering does not execute Python. Reopen **Open slides.html** or refresh your browser after rebuilding.

See [presentation/README.md](presentation/README.md) for the small source map and optional technical backup.
