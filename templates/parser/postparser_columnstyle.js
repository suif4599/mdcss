// Rebuild the inline styles of mdcss column containers after a sanitizing
// consumer stripped them. preparser_column.js duplicates the layout values
// into data-mdcss-cols (grid-template-columns) and data-mdcss-col-align
// (justify-content); this pass restores the style attributes DOMPurify's
// FORBID_ATTR: ['style'] removed. Divs whose style attribute survived are
// not matched, because after sanitization the marker attributes come first.
html = html.replace(
    /<div data-mdcss-cols="([^"]*)">/g,
    (match, cols) =>
        `<div style="display: grid; grid-template-columns: ${cols}; gap: 20px; width: 100%; min-width: 0; box-sizing: border-box;" data-mdcss-cols="${cols}">`
);
html = html.replace(
    /<div data-mdcss-col="(main|side)"(?: data-mdcss-col-align="([^"]*)")?>/g,
    (match, role, align) =>
        `<div style="display: flex; flex-direction: column; justify-content: ${align || "flex-start"}; min-width: 0; max-width: 100%;" data-mdcss-col="${role}"${align ? ` data-mdcss-col-align="${align}"` : ""}>`
);
