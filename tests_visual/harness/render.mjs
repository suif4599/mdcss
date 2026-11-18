// Renders one note through crossnote's headless engine and writes the exact
// HTML that crossnote's chromeExport feeds to Chrome (isForPrint: true), so
// the browser can print it without crossnote owning the browser process.
import { createRequire } from "node:module";
import { readFileSync, writeFileSync } from "node:fs";
import path from "node:path";

const input = JSON.parse(readFileSync(0, "utf8"));
const require = createRequire(import.meta.url);
const { Notebook } = require("crossnote");

const notebook = await Notebook.init({
    notebookPath: input.notebookPath,
    config: input.config,
});
const engine = notebook.getNoteMarkdownEngine(input.noteFile);
if (!engine) {
    throw new Error(`crossnote: no markdown engine for ${input.noteFile}`);
}
const markdown = readFileSync(path.join(input.notebookPath, input.noteFile), "utf8");
const { html, yamlConfig } = await engine.parseMD(markdown, {
    useRelativeFilePath: false,
    hideFrontMatter: true,
    isForPreview: false,
    runAllCodeChunks: false,
});
const page = await engine.generateHTMLTemplateForExport(html, yamlConfig, {
    isForPrint: true,
    isForPrince: false,
    embedLocalImages: false,
    offline: true,
});
writeFileSync(input.htmlOutput, page);
process.stdout.write(JSON.stringify({ html: input.htmlOutput }));
