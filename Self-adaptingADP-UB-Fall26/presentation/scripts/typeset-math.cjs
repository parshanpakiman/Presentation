#!/usr/bin/env node
/* Convert Quarto's MathML/TeX annotations into the site's existing MathJax SVG
 * format at build time. Finished slides then work over HTTP and file:// without
 * loading fonts, workers, or a TeX renderer in the audience's browser.
 *
 * Usage: node scripts/typeset-math.cjs [generated.html ...]
 * Defaults: _site/index.html, _site/reading.html, _site/backup.html.
 * Quarto invokes this through typeset-math.ts with its bundled Deno.
 * Direct invocation also supports Node.js; all math dependencies are local.
 */
'use strict';

const fs = require('node:fs');
const path = require('node:path');
const root = path.resolve(__dirname, '..');
const vendor = path.join(root, 'assets', 'vendor', 'mathjax');
const font = path.join(vendor, 'fonts', 'mathjax-newcm-font');
const inputs = process.argv.slice(2);
const files = inputs.length ? inputs.map(file => path.resolve(file)) :
  ['index.html', 'reading.html', 'backup.html'].map(file => path.join(root, '_site', file));

global.MathJax = {
  loader: {
    paths: {mathjax: vendor, fonts: path.join(vendor, 'fonts')},
    load: ['adaptors/liteDOM'],
    require,
  },
  startup: {typeset: false, input: ['tex', 'mml']},
  tex: {packages: {'[-]': ['noundefined']}},
  // The liteDOM adaptor has no browser accessibility worker. Keep SVG output
  // independent of the optional speech/enrichment services as well.
  options: {enableEnrichment: false, enableSpeech: false, enableBraille: false},
  output: {font: 'mathjax-newcm', fontPath: font, displayOverflow: 'scroll'},
  svg: {fontCache: 'local', dynamicPrefix: path.join(font, 'svg', 'dynamic')},
};
require(path.join(vendor, 'tex-svg.js'));
// tex-svg bundles the MathML classes but does not register the input adaptor
// when browser accessibility is disabled. Register it before startup resolves.
require(path.join(vendor, 'input', 'mml.js'));

async function typesetFile(file, adaptor) {
  const input = fs.readFileSync(file, 'utf8');
  const matches = [...input.matchAll(/<math\b[^>]*>[\s\S]*?<\/math\s*>/gi)];
  const chunks = [];
  let previous = 0;
  for (const [index, match] of matches.entries()) {
    // Parsing only each math element preserves every unrelated HTML byte,
    // including scripts, Reveal settings, inline images, and fragment markers.
    const document = adaptor.parse(`<html><head></head><body>${match[0]}</body></html>`, 'text/html');
    const math = adaptor.tags(adaptor.body(document), 'math')[0];
    const annotation = adaptor.tags(math, 'annotation').find(node =>
      adaptor.getAttribute(node, 'encoding') === 'application/x-tex');
    const tex = annotation ? adaptor.textContent(annotation) : null;
    const display = adaptor.getAttribute(math, 'display') === 'block';
    let equation;
    try {
      equation = tex === null ? await MathJax.mathml2svgPromise(match[0], {display}) :
        await MathJax.tex2svgPromise(tex, {display});
    } catch (error) {
      throw new Error(`${file}: equation ${index + 1} failed: ${tex}\n${error.message || error}`);
    }
    const svg = adaptor.outerHTML(equation);
    if (/data-mjx-error|data-mml-node=["']merror["']|<merror\b/i.test(svg)) {
      throw new Error(`${file}: equation ${index + 1} produced a MathJax error: ${tex}`);
    }
    const attributes = {
      class: `polished-math${display ? ' display-math' : ''}`,
      'data-math-static': 'true',
      role: 'math',
      'aria-label': adaptor.getAttribute(math, 'aria-label') || tex || adaptor.textContent(math),
    };
    if (tex !== null) attributes['data-tex'] = tex;
    if (display) attributes.display = 'block';
    const wrapper = adaptor.node('span', attributes, [equation]);
    chunks.push(input.slice(previous, match.index), adaptor.outerHTML(wrapper));
    previous = match.index + match[0].length;
  }
  chunks.push(input.slice(previous));
  let output = chunks.join('');
  if (matches.length) {
    const document = MathJax.startup.document;
    const stylesheet = adaptor.outerHTML(document.outputJax.styleSheet(document));
    if (!/<\/head\s*>/i.test(output)) throw new Error(`${file}: generated HTML has no head element.`);
    output = output.replace(/<style\b[^>]*id=["']MJX-SVG-styles["'][^>]*>[\s\S]*?<\/style\s*>/gi, '');
    output = output.replace(/<\/head\s*>/i, `${stylesheet}\n</head>`);
  }
  output = output.replace(/<html\b([^>]*)>/i, (all, attributes) => {
    const cleaned = attributes.replace(/\sdata-math-typeset=(?:"[^"]*"|'[^']*')/gi, '');
    return `<html${cleaned} data-math-typeset="static">`;
  });
  return {file, output, count: matches.length};
}

async function main() {
  await MathJax.startup.promise;
  const adaptor = MathJax.startup.adaptor;
  const results = [];
  // Validate every output before changing any of them. Each write is atomic.
  for (const file of files) results.push(await typesetFile(file, adaptor));
  for (const result of results) {
    const temporary = `${result.file}.math-${process.pid}.tmp`;
    try {
      fs.writeFileSync(temporary, result.output, 'utf8');
      fs.renameSync(temporary, result.file);
    } finally {
      if (fs.existsSync(temporary)) fs.unlinkSync(temporary);
    }
    console.log(`MathJax SVG: ${path.relative(root, result.file)} — ${result.count} equations`);
  }
}
const completion = main().catch(error => {
  console.error(`Math typesetting failed: ${error.message || error}`);
  process.exitCode = 1;
  throw error;
});
module.exports = completion;
if (require.main === module) completion.catch(() => {});
