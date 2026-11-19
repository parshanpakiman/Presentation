# Academic Presentations

Academic presentations by Parshan Pakiman, including slides, source files, and
supporting materials.

## Presentations

- [Self-Adapting Approximations of Markov Decision Processes](Self-adaptingADP-UB-Fall26/)
  — Departmental presentation at the University at Buffalo, Fall 2026, on
  self-adapting approximate dynamic programming, drawing on my tutorial and earlier
  *Management Science* paper.
  [View slides](https://parshanpakiman.github.io/Presentation/Self-adaptingADP-UB-Fall26/)
  · [Source and local instructions](Self-adaptingADP-UB-Fall26/).

## View presentations online

Use **View slides** to open the presentation as a website. Clicking an HTML file
in GitHub's file browser displays its source code.

The website is published by [GitHub Actions](.github/workflows/pages.yml).
For the first deployment:

1. Open the repository's [Pages settings](https://github.com/parshanpakiman/Presentation/settings/pages).
2. Under **Build and deployment → Source**, select **GitHub Actions**.
3. Commit and push the publishing workflow to `main`. In the **Actions** tab,
   wait for **Publish presentations** to finish successfully.

The **View slides** link becomes available after the first successful deployment.
Later changes to the presentation on `main` are published automatically. To retry
after enabling Pages, open **Actions → Publish presentations → Run workflow**.

## Organization

Keep each presentation in its own folder, using a descriptive name such as
`YYYY-MM-DD-presentation-title/`. Store its slides, references, and supporting
assets together. Add build instructions to that folder when needed.

Presentation source files and final exports (including PDFs) can be committed.
Temporary files and common LaTeX build artifacts are excluded by `.gitignore`.

## License

This repository is licensed under the [MIT License](LICENSE). Third-party
materials remain subject to their respective licenses and attributions.
