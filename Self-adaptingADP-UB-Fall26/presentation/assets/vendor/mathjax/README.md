# Local MathJax renderer

MathJax 4.1.3 and matching MathJax-Newcm SVG glyph data from the official npm packages `mathjax` and `@mathjax/mathjax-newcm-font`. Apache-2.0 license included. Original package files are unchanged; `checksums.json` records their hashes.

The Quarto post-render hook `scripts/typeset-math.ts` uses the bundled Deno runtime to call `scripts/typeset-math.cjs`. It renders the main deck, reading view, and technical backup into inline SVG equations using this same MathJax and NewCM font. TeX annotations remain editable in the QMD source and are retained in `data-tex` attributes. Published HTML contains the glyph paths and shared SVG styles, so opening it as a local file does not require font downloads, a speech worker, or browser-time TeX conversion. `components/math-polish.js` skips the loader for these finished pages and remains a fallback for unprocessed authoring previews.

The build uses the official liteDOM adaptor and MathML input component for the few original native MathML formulas without TeX annotations. These package files are unchanged and included in the checksum manifest. No npm installation or external math service is needed.

Included: the combined TeX-to-SVG component, TeX extension components, SVG glyph data, and local speech-rule resources for accessible math. Browser Python runs separately and remains on demand.
