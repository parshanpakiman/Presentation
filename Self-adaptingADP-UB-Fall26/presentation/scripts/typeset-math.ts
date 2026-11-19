// Quarto runs this with its bundled Deno; no separate Node installation is needed.
import {createRequire} from "node:module";
const require = createRequire(import.meta.url);
await require("./typeset-math.cjs");
