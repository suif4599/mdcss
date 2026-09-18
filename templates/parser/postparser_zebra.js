// Table zebra strategies (post pass).
// Runs after postparser_table.js (rowspan attributes must already exist) and
// before postparser_tablecaption.js (which turns the "Table:" line into a
// figure caption). The tag arrives as the "Table@tag@:" sentinel written by
// preparser_zebra.js.
//   auto (default for every table): stripe by "bands" — a rowspan merge forces
//     all rows it covers into one band, so a merged cell shows a single color
//     across its whole span; staggered merges in different columns propagate
//     through the union-find. Bands alternate, first data band unstriped, so
//     merge-less tables render exactly like plain zebra.
//   zebra: keep plain nth-child striping; merged cells take their anchor row's
//     color (historical behavior).
//   nozebra: no body stripes.
// The tag is stripped from the caption line here so the caption fragment
// downstream sees a normal "Table:" line. Without the parser no class is ever
// added and the CSS nth-child rule stays the plain fallback.

// Case-sensitive on purpose: preparser_zebra.js always emits the canonical
// lowercase sentinel, so a hand-written uppercase sentinel cannot produce a
// class like "mdcss-ZEBRA" that no CSS rule would match.
const MDCSS_ZEBRA_TAG_RE = /(<p[^>]*>)\s*Table@(auto|zebra|nozebra)@:\s*(.*?)<\/p>\s*(<div(?![^>]*data-mdcss-col)[^>]*>\s*<table[\s\S]*?<\/table>\s*<\/div>|<table[\s\S]*?<\/table>)/g;

function zebraMergeClass(attrs, cls) {
    const classMatch = attrs.match(/\sclass="([^"]*)"/);
    if (classMatch) {
        const merged = classMatch[1] ? `${classMatch[1]} ${cls}` : cls;
        return attrs.replace(classMatch[0], ` class="${merged}"`);
    }
    return ` class="${cls}"${attrs}`;
}

// Mark the rows of every odd band with mdcss-z (auto mode). Bands come from a
// union-find over tbody row indices: each rowspan cell unions its anchor row
// with every row it covers, so staggered merges share one band transitively.
function zebraApplyBands(tablePart) {
    const tbodyMatch = tablePart.match(/(<tbody[^>]*>)([\s\S]*?)(<\/tbody>)/);
    if (!tbodyMatch) return tablePart;
    const rows = tbodyMatch[2].match(/<tr[^>]*>[\s\S]*?<\/tr>/g);
    if (!rows) return tablePart;
    const parent = [];
    for (let i = 0; i < rows.length; i += 1) parent.push(i);
    const find = (x) => {
        while (parent[x] !== x) {
            parent[x] = parent[parent[x]];
            x = parent[x];
        }
        return x;
    };
    rows.forEach((row, i) => {
        (row.match(/<t[dh][^>]*>/g) || []).forEach((tag) => {
            const spanMatch = tag.match(/rowspan="(\d+)"/);
            if (!spanMatch) return;
            const end = Math.min(i + parseInt(spanMatch[1], 10) - 1, rows.length - 1);
            for (let k = i + 1; k <= end; k += 1) {
                const ra = find(i);
                const rb = find(k);
                if (ra !== rb) {
                    if (ra < rb) parent[rb] = ra;
                    else parent[ra] = rb;
                }
            }
        });
    });
    const bandOf = new Map();
    const rowBand = [];
    for (let i = 0; i < rows.length; i += 1) {
        const root = find(i);
        if (!bandOf.has(root)) bandOf.set(root, bandOf.size);
        rowBand.push(bandOf.get(root));
    }
    let rowIndex = 0;
    const striped = tbodyMatch[2].replace(/<tr[^>]*>[\s\S]*?<\/tr>/g, (row) => {
        const band = rowBand[rowIndex];
        rowIndex += 1;
        if (band % 2 !== 1) return row;
        return row.replace(/<tr([^>]*)>/, (_t, attrs) => `<tr${zebraMergeClass(attrs, 'mdcss-z')}>`);
    });
    return tablePart.replace(tbodyMatch[0], () => tbodyMatch[1] + striped + tbodyMatch[3]);
}

// Tagged tables: strip the tag from the caption line and mark the table.
html = html.replace(MDCSS_ZEBRA_TAG_RE, (_match, pOpen, mode, caption, tablePart) => {
    let out = tablePart.replace(/<table([^>]*)>/, (_t, attrs) => `<table${zebraMergeClass(attrs, `mdcss-${mode}`)}>`);
    if (mode === 'auto') out = zebraApplyBands(out);
    return `${pOpen}Table: ${caption}</p>\n${out}`;
});

// Untagged tables default to auto.
html = html.replace(
    /<table(?![^>]*mdcss-(?:auto|zebra|nozebra))([^>]*)>([\s\S]*?)<\/table>/g,
    (_match, attrs, body) => zebraApplyBands(`<table${zebraMergeClass(attrs, 'mdcss-auto')}>${body}</table>`)
);
