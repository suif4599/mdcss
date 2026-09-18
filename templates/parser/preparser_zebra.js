// Zebra strategy tag normalization (pre pass).
// "Table<auto|zebra|nozebra>: caption" on the caption line selects the zebra
// strategy of the table that follows. The tag is rewritten to the plain-text
// sentinel "Table@tag@:" before markdown-it so it survives every pipeline:
// with html:true markdown-it emits a raw inline element, which Inkstone's
// DOMPurify strips before the post pass could read it; with html:false the
// angle brackets get escaped. The sentinel is inert text under both settings
// and passes any sanitizer.
// Must run after fence extraction (tagged lines inside code fences stay
// untouched); it never changes line counts, so the line ledger stays valid.
markdown = markdown.replace(
    /(^|\n)([ \t]{0,3})table<(auto|zebra|nozebra)>:/gi,
    (_match, newline, indentText, mode) => `${newline}${indentText}Table@${mode.toLowerCase()}@:`
);
