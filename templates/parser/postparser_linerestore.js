// Restore real editor line numbers in data-source-line attributes.
// markdown-it computed them against the text AFTER the pre-hooks inserted
// extra lines (indent wrapper / pdf wrappers / column divs); the ledger kept
// on globalThis by preparser_lineshift.js maps them back so MPE scroll sync
// and the other data-source-line consumers target the right editor lines.
if (globalThis.__MDCSS_LINE_SHIFTS__ && globalThis.__MDCSS_LINE_SHIFTS__.length && typeof globalThis.__mdcssOrigLine === "function") {
    html = html.replace(/data-source-line="(\d+)"/g, (match, line) => `data-source-line="${globalThis.__mdcssOrigLine(parseInt(line, 10))}"`);
}
