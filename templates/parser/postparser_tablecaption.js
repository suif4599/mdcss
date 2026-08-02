// Table: caption support
// Usage: write "Caption text" on a line right before a markdown table.
//        If caption starts with ".", the "表N:" prefix is shown.

// This regex handles:
//   - Direct adjacency: <p>Table: title</p>\n<table>...</table>
//   - With wrapper div: <p>Table: title</p>\n<div ...>\n<table>...</table>\n</div>
//   - Whitespace-only gap between </p> and the (optional) wrapper / table
//
// The `([\s\S]*?)` in the middle is guarded by a check that it doesn't
// contain another <table> — that prevents pairing the wrong caption
// with a table when there are multiple tables in the document.
html = html.replace(
    /<p[^>]*>\s*Table:\s*(.*?)<\/p>\s*(<table[\s\S]*?<\/table>)/gi,
    (_match, caption, tableHtml) => {
        caption = caption.trim();
        if (!caption) return _match;
        const prefix = caption.startsWith('.') ? '表@TABLE_COUNT_PLACEHOLDER@:\t' : '';
        const displayCaption = caption.startsWith('.') ? caption.slice(1) : caption;
        return `<figure style="width: 100%; margin: 0 auto;">
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
