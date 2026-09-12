// Table: caption support
// Usage: write "Caption text" on a line right before a markdown table.
//        If caption starts with ".", the "表N:" prefix is shown.

// This regex handles:
//   - Direct adjacency: <p>Table: title</p>\n<table>...</table>
//   - With wrapper div: <p>Table: title</p>\n<div ...>\n<table>...</table>\n</div>
//     (the wrapper open/close tags are captured together with the table and
//     re-emitted INSIDE the figure, so wrappers like Inkstone's
//     ".table-wrap" — and any data-* attributes on them — survive)
//   - Whitespace-only gap between </p> and the (optional) wrapper / table
//
// The wrapper alternative is all-or-nothing (div open + table + div close)
// so a bare table is never paired with someone else's stray </div>, and it
// must not be an mdcss column div (data-mdcss-col*), otherwise a "Table:"
// line right before a column block that starts with a table would swallow
// the column's opening div.
html = html.replace(
    /<p[^>]*>\s*Table:\s*(.*?)<\/p>\s*(<div(?![^>]*data-mdcss-col)[^>]*>\s*<table[\s\S]*?<\/table>\s*<\/div>|<table[\s\S]*?<\/table>)/gi,
    (_match, caption, tableHtml) => {
        caption = caption.trim();
        if (!caption) return _match;
        const prefix = caption.startsWith('.') ? '表@TABLE_COUNT_PLACEHOLDER@:\t' : '';
        const displayCaption = caption.startsWith('.') ? caption.slice(1) : caption;
        return `<figure style="width: fit-content; max-width: 100%; margin: 0 auto;">
<figcaption style="text-align: center; overflow-wrap: break-word;">${prefix}${displayCaption}</figcaption>
${tableHtml}
</figure>`;
    }
);

let tableCnt = 0;
html = html.replace(/@TABLE_COUNT_PLACEHOLDER@/g, () => {
    tableCnt += 1;
    return tableCnt;
});
