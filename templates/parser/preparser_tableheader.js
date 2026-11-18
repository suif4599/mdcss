// Multi-row table headers (pre pass).
// Every leading-pipe row directly above a GFM delimiter row belongs to the
// table header, but markdown-it takes only the last one as <thead>. The
// earlier rows are moved right after the delimiter, each preceded by a
// @MDCSS_THROW@ marker row, so markdown-it parses them as ordinary body rows
// (inline content, escaped pipes and control cells stay intact). Body rows
// are padded to the header's column count, which stays unchanged here.
// postparser_tableheader.js lifts the marked rows back into the thead.
// The line count changes here; preparser_linediff.js maps it for scroll sync.

const mdcssPipeRowRe = /^( {0,3})\|/;
const mdcssDelimiterCellRe = /^:?-+:?$/;

function mdcssSplitCells(line) {
    const cells = [];
    let current = "";
    let escaped = false;
    for (const char of line.trim()) {
        if (char === "|") {
            if (escaped) {
                current += char;
            } else {
                cells.push(current);
                current = "";
            }
            escaped = false;
            continue;
        }
        current += char;
        escaped = char === "\\";
    }
    cells.push(current);
    if (cells.length && cells[0] === "") cells.shift();
    if (cells.length && cells[cells.length - 1] === "") cells.pop();
    return cells;
}

// Mirrors markdown-it's table rule: returns the delimiter cell count or -1.
function mdcssDelimiterCellCount(line) {
    if (/^ {4}/.test(line)) return -1;
    const text = line.trim();
    if (text.length < 2 || /[^|:\-\s]/.test(text)) return -1;
    const first = text[0];
    if (first !== "|" && first !== "-" && first !== ":") return -1;
    const second = text[1];
    if (second !== "|" && second !== "-" && second !== ":" && second !== " " && second !== "\t") return -1;
    if (first === "-" && (second === " " || second === "\t")) return -1;
    const columns = text.split("|");
    let count = 0;
    for (let index = 0; index < columns.length; index += 1) {
        const cell = columns[index].trim();
        if (!cell) {
            if (index === 0 || index === columns.length - 1) continue;
            return -1;
        }
        if (!mdcssDelimiterCellRe.test(cell)) return -1;
        count += 1;
    }
    return count;
}

const mdcssHeaderOut = [];
for (const line of markdown.split("\n")) {
    const alignCount = mdcssDelimiterCellCount(line);
    const headerLine = mdcssHeaderOut.length ? mdcssHeaderOut[mdcssHeaderOut.length - 1] : null;
    if (
        alignCount < 1 ||
        headerLine === null ||
        !mdcssPipeRowRe.test(headerLine) ||
        mdcssSplitCells(headerLine).length !== alignCount
    ) {
        mdcssHeaderOut.push(line);
        continue;
    }
    let start = mdcssHeaderOut.length - 1;
    while (start > 0 && mdcssPipeRowRe.test(mdcssHeaderOut[start - 1])) start -= 1;
    const extraRows = mdcssHeaderOut.slice(start, mdcssHeaderOut.length - 1);
    // A delimiter inside the run means these rows are the previous table's
    // body, not headers of this one.
    if (extraRows.some((row) => mdcssDelimiterCellCount(row) >= 1)) {
        mdcssHeaderOut.push(line);
        continue;
    }
    mdcssHeaderOut.splice(start, extraRows.length);
    mdcssHeaderOut.push(line);
    for (const row of extraRows) {
        mdcssHeaderOut.push(`${row.slice(0, row.length - row.trimStart().length)}| @MDCSS_THROW@ |`);
        mdcssHeaderOut.push(row);
    }
}
markdown = mdcssHeaderOut.join("\n");
