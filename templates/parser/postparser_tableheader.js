// Multi-row table headers (post pass).
// Runs after postparser_table.js (cell spans are final) and before
// postparser_zebra.js (header rows must leave the body first). Each row
// following a @MDCSS_THROW@ marker row is a header row the pre pass moved
// into the body; it is lifted into the thead, in order, ahead of the row
// markdown-it parsed as the header, and retagged <td> -> <th>.
// Marker rows are dropped.

const mdcssHeaderMarkerRe = /^<tr[^>]*>\s*<td[^>]*>@MDCSS_THROW@<\/td>/;

function mdcssLiftHeaderRows(tableHtml) {
    const theadMatch = tableHtml.match(/(<thead[^>]*>)([\s\S]*?)(<\/thead>)/);
    const tbodyMatch = tableHtml.match(/(<tbody[^>]*>)([\s\S]*?)(<\/tbody>)/);
    if (!theadMatch || !tbodyMatch) return tableHtml;
    const rows = tbodyMatch[2].match(/<tr[^>]*>[\s\S]*?<\/tr>/g);
    if (!rows || !rows.some((row) => mdcssHeaderMarkerRe.test(row))) return tableHtml;
    const lifted = [];
    const kept = [];
    let marked = false;
    for (const row of rows) {
        if (mdcssHeaderMarkerRe.test(row)) {
            marked = true;
        } else if (marked) {
            lifted.push(row.replace(/<td([^>]*)>/g, "<th$1>").replace(/<\/td>/g, "</th>"));
            marked = false;
        } else {
            kept.push(row);
        }
    }
    const headInner = lifted.length ? "\n" + lifted.join("\n") + theadMatch[2] : theadMatch[2];
    const bodyInner = kept.length ? "\n" + kept.join("\n") + "\n" : "";
    return tableHtml
        .replace(theadMatch[0], theadMatch[1] + headInner + theadMatch[3])
        .replace(tbodyMatch[0], tbodyMatch[1] + bodyInner + tbodyMatch[3]);
}

html = html.replace(/<table[\s\S]*?<\/table>/g, mdcssLiftHeaderRows);
