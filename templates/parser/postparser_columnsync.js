// Main-column scroll anchoring for multi-column sections. The marker
// attributes come from the column pre-parser: data-mdcss-cols on the grid
// container, data-mdcss-col="main"/"side" on the columns.
//
// MPE scroll sync builds a line -> offset map from data-source-line
// attributes and fills missing lines by linear interpolation (crossnote
// buildScrollMap; duplicate lines keep the first element in DOM order, the
// container wins). For every tagged section this block reshapes that map:
//   1. anchor the container at the section's first source line, so lines of
//      side columns BEFORE the main column interpolate between two offsets
//      that both sit at the section top -> preview frozen while editing them;
//   2. strip data-source-line from side columns so they stop driving the map;
//   3. for side columns AFTER the main column, drop two empty sentinel divs
//      at the end of the main column carrying that line range, so the whole
//      range interpolates between two identical offsets (main column bottom)
//      -> preview frozen while editing them. The sentinels reuse line numbers
//      freed by step 2, so they cannot collide with real elements.
(function () {
    function divCloseIndex(html, from) {
        // `from` points just past a "<div ...>" open tag; return the index of
        // its matching "</div>", or -1. Literal "<div" inside code blocks is
        // entity-escaped in the rendered html, so token scanning is safe.
        const tokenRe = /<div\b[^>]*>|<\/div>/g;
        tokenRe.lastIndex = from;
        let depth = 1;
        let token;
        while ((token = tokenRe.exec(html)) !== null) {
            depth += token[0][1] === "/" ? -1 : 1;
            if (depth === 0) {
                return token.index;
            }
        }
        return -1;
    }

    const edits = [];
    const containerRe = /<div\b[^>]*\bdata-mdcss-cols\b[^>]*>/g;
    let match;
    while ((match = containerRe.exec(html)) !== null) {
        const openStart = match.index;
        const openEnd = openStart + match[0].length;
        const closeIdx = divCloseIndex(html, openEnd);
        if (closeIdx < 0) {
            continue;
        }
        // direct children of the grid container that carry a column marker
        const columns = [];
        const tokenRe = /<div\b[^>]*>|<\/div>/g;
        tokenRe.lastIndex = openEnd;
        let depth = 0;
        let token;
        while ((token = tokenRe.exec(html)) !== null && token.index < closeIdx) {
            if (token[0][1] === "/") {
                depth -= 1;
            } else if (depth === 0 && token[0].includes("data-mdcss-col=")) {
                columns.push({
                    isMain: token[0].includes('data-mdcss-col="main"'),
                    openEnd: token.index + token[0].length,
                    close: -1,
                    lines: [],
                });
                depth += 1;
            } else {
                depth += 1;
            }
        }
        const mainCol = columns.find((col) => col.isMain);
        if (!mainCol) {
            continue;
        }
        for (const col of columns) {
            col.close = divCloseIndex(html, col.openEnd);
        }
        if (columns.some((col) => col.close < 0)) {
            continue;
        }
        for (const col of columns) {
            const lineRe = /data-source-line="(\d+)"/g;
            lineRe.lastIndex = col.openEnd;
            let lineMatch;
            while ((lineMatch = lineRe.exec(html)) !== null && lineMatch.index < col.close) {
                col.lines.push(parseInt(lineMatch[1], 10));
            }
        }
        const allLines = columns.flatMap((col) => col.lines);
        if (allLines.length === 0) {
            continue;
        }
        const anchor = Math.min(...allLines);
        // strip data-source-line from side columns (leading space included so
        // the removal leaves clean tag syntax)
        for (const col of columns) {
            if (col.isMain) {
                continue;
            }
            const stripRe = / data-source-line="\d+"/g;
            stripRe.lastIndex = col.openEnd;
            let stripMatch;
            while ((stripMatch = stripRe.exec(html)) !== null && stripMatch.index < col.close) {
                edits.push({ start: stripMatch.index, end: stripMatch.index + stripMatch[0].length, text: "" });
            }
        }
        // anchor the container itself at the section's first source line
        if (!match[0].includes("data-source-line=")) {
            edits.push({ start: openEnd - 1, end: openEnd - 1, text: ` data-source-line="${anchor}"` });
        }
        // sentinel pair for side columns whose lines sit after the main
        // column's last line (side columns that follow the main column)
        if (mainCol.lines.length > 0) {
            const mainMax = Math.max(...mainCol.lines);
            let x = null;
            let y = null;
            for (const col of columns) {
                if (col.isMain || col.lines.length === 0) {
                    continue;
                }
                const colMin = Math.min(...col.lines);
                if (colMin > mainMax) {
                    x = x === null ? colMin : Math.min(x, colMin);
                    y = y === null ? Math.max(...col.lines) : Math.max(y, ...col.lines);
                }
            }
            if (x !== null) {
                edits.push({
                    start: mainCol.close,
                    end: mainCol.close,
                    text: `<div data-source-line="${x}"></div><div data-source-line="${y}"></div>`,
                });
            }
        }
    }
    edits.sort((a, b) => b.start - a.start);
    for (const edit of edits) {
        html = html.slice(0, edit.start) + edit.text + html.slice(edit.end);
    }
})();
