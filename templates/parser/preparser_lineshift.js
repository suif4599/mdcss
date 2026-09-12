// Line-shift ledger shared between the markdown pre-hooks and the html
// post-hooks. Pre-hooks that change the physical line count of the markdown
// (indent wrapper, pdf wrappers, column divs) record their insertions here in
// ORIGINAL line coordinates, so the post-hooks can map markdown-it's
// data-source-line values (computed against the transformed text) back to
// real editor line numbers for scroll sync.
// State lives on globalThis because onWillParseMarkdown and
// onDidParseMarkdown are separate function bodies evaluated once in a
// persistent QuickJS context.
globalThis.__MDCSS_LINE_SHIFTS__ = [];
globalThis.__mdcssRecordShift = function (origLine, delta) {
    if (delta) {
        globalThis.__MDCSS_LINE_SHIFTS__.push({ o: origLine, d: delta });
    }
};
// Map a line number of the current (already mutated) markdown string back to
// its original numbering. Entries mean "original lines >= o have d extra
// lines in front of them" and are cumulative, so original -> current is
// strictly increasing and the inverse is a simple piecewise walk.
globalThis.__mdcssOrigLine = function (cur) {
    const shifts = globalThis.__MDCSS_LINE_SHIFTS__.slice().sort((a, b) => a.o - b.o);
    let cum = 0;
    for (const s of shifts) {
        if (cur < s.o + cum) {
            return cur - cum;
        }
        cum += s.d;
    }
    return cur - cum;
};
