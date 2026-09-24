// Protect table-cell backslash runs from markdown-it's escape rule, which
// halves them before any mdcss code can see the source count. A cell made
// of N backslashes is rewritten to the @MDCSS_BS_N@ token; postparser_table
// interprets it (N=1 deletes the cell, N>=2 renders N-1 literal backslashes).
// Only whole-cell runs on 0-3-space-indented '|' rows are taken, so escapes
// inside cell content (\*, the \| separator, inline code) stay untouched.
// Tokens surviving elsewhere are restored by the post pass. Must run after
// fence extraction; never changes line counts, so the line ledger holds.
markdown = markdown.replace(/^([ ]{0,3}\|.*)$/gm, (line) =>
    line.replace(/(\|[ \t]*)(\\+)(?=[ \t]*(?:\||$))/g, (m, left, run) => left + "@MDCSS_BS_" + run.length + "@")
);
