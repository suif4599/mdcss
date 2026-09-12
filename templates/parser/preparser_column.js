const columnRegex = /(^-?\|\|\|-?:?\d*(?:%|px)?:?!?:?$)/m;
function parseCulumnSpec(spec) {
    let type = "separator";
    let width = "";
    let align = "";
    let main = false;
    if (spec.startsWith("|||-")) {
        type = "start";
        spec = spec.slice(4);
    } else if (spec.startsWith("-|||")) {
        if (spec.length != 4) {
            return null;
        }
        type = "end";
        return { type, align, width, main };
    } else {
        spec = spec.slice(3);
    }
    // A single trailing "!" marks this column as the main column, which the
    // column scroll-sync post-parser anchors the preview scroll to
    if (spec.includes("!")) {
        main = true;
        spec = spec.replace("!", "");
    }
    // Standalone ":" should be treated as flex-end
    align = "flex-start";
    if (spec.endsWith(":")) {
        align = "flex-end";
        spec = spec.slice(0, -1);
        if (spec.startsWith(":")) {
            align = "center";
            spec = spec.slice(1);
        }
    } else if (spec.startsWith(":")) {
        spec = spec.slice(1);
    }
    let unit = "%";
    if (spec.endsWith("px")) {
        unit = "px";
        spec = spec.slice(0, -2);
    } else if (spec.endsWith("%")) {
        spec = spec.slice(0, -1);
    }
    if (!/^-?\d+$/.test(spec)) {
        width = "1fr";
    } else {
        const num = parseInt(spec, 10);
        width = isNaN(num) ? `1fr` : `${num}${unit}`;
    }
    return { type, align, width, main };
}

function formatNumber(num) {
    const rounded = Math.round(num * 10000) / 10000;
    return Number.isInteger(rounded) ? `${rounded}` : `${rounded}`.replace(/\.?0+$/, "");
}

function normalizeColumnWidths(entries) {
    const percentEntries = [];
    let percentTotal = 0;

    for (const entry of entries) {
        const width = entry.spec.width;
        const percentMatch = width.match(/^(\d+(?:\.\d+)?)%$/);
        if (percentMatch) {
            const value = Number(percentMatch[1]);
            if (Number.isFinite(value) && value > 0) {
                percentEntries.push(entry);
                percentTotal += value;
            }
        }
    }

    if (percentTotal > 100 && percentEntries.length > 0) {
        const scale = 100 / percentTotal;
        for (const entry of percentEntries) {
            const value = Number(entry.spec.width.replace("%", ""));
            entry.spec.width = `${formatNumber(value * scale)}%`;
        }
    }

    return entries;
}
function mergeColumnSpec(markdown) {
    let parts = markdown.split(columnRegex);
    let specIndex = {};
    // 1-based line number of each part's first character in the input string,
    // used to report the line shifts introduced by the div replacements below.
    // A spec match is the line content without its trailing newline, so the
    // part after a spec begins on the same line (its empty tail): a spec part
    // does not advance the line cursor.
    const partLine = [];
    let lineCounter = 1;
    for (const part of parts) {
        partLine.push(lineCounter);
        lineCounter += columnRegex.test(part) ? 0 : (part.match(/\n/g) || []).length;
    }
    // partLine positions are in pre-column coordinates: when converting them
    // to original line numbers, this template's own shifts (and those of any
    // earlier column section in the same document) must not be applied, so
    // convert against a snapshot of the ledger taken before any recording.
    const preLedger = globalThis.__MDCSS_LINE_SHIFTS__.slice().sort((a, b) => a.o - b.o);
    function preOrigLine(cur) {
        let cum = 0;
        for (const s of preLedger) {
            if (cur < s.o + cum) {
                return cur - cum;
            }
            cum += s.d;
        }
        return cur - cum;
    }
    const pendingShifts = [];
    for (let i = 0; i < parts.length; i++) {
    if (!columnRegex.test(parts[i])) {
        continue;
    }
    const spec = parseCulumnSpec(parts[i]);
    if (!spec) {
        continue;
    }
    switch (spec.type) {
        case "start":
            if (Object.keys(specIndex).length > 0) {
                specIndex = {};
            }
            specIndex[i] = spec;
            break;
        case "separator":
            if (Object.keys(specIndex).length === 0) {
                break;
            }
            specIndex[i] = spec;
            break;
        case "end":
            if (Object.keys(specIndex).length === 0) {
                break;
            }
            {
                const orderedSpecs = normalizeColumnWidths(
                    Object.keys(specIndex).map((index) => ({ index, spec: specIndex[index] }))
                );
                // The main column drives preview scroll sync; if no column is
                // marked with "!", the first one is the main column
                let mainIdx = orderedSpecs.findIndex(({ spec: s }) => s.main);
                if (mainIdx < 0) {
                    mainIdx = 0;
                }
                const cols = orderedSpecs.map(({ spec }) => `minmax(auto, ${spec.width})`).join(' ');
                // data-mdcss-cols / data-mdcss-col-align duplicate the layout
                // values that live in inline styles, so consumers that strip
                // inline styles (e.g. Inkstone's DOMPurify) can rebuild them
                // in postparser_columnstyle.js after sanitization.
                let outerDiv = `

<div style="display: grid; grid-template-columns: ${cols}; gap: 20px; width: 100%; min-width: 0; box-sizing: border-box;" data-mdcss-cols="${cols}">

`;
                for (let c = 0; c < orderedSpecs.length; c++) {
                const { index, spec: s } = orderedSpecs[c];
                const innerDiv = `

<div style="display: flex; flex-direction: column; justify-content: ${s.align}; min-width: 0; max-width: 100%;" data-mdcss-col="${c === mainIdx ? "main" : "side"}" data-mdcss-col-align="${s.align}">

`;
                parts[index] = outerDiv + innerDiv;
                outerDiv = `</div>`;
                }
                parts[i] = `</div></div>`;
                // every spec line is replaced inside parts.join("\n"), which
                // pads each replacement with one extra newline on each side:
                // lines after the spec shift by (replacement newlines + 2)
                for (const { index } of orderedSpecs) {
                    pendingShifts.push({ line: partLine[index], d: (parts[index].match(/\n/g) || []).length + 2 });
                }
                pendingShifts.push({ line: partLine[i], d: 2 });
                specIndex = {};
            }
            break;
        }
    }
    for (const s of pendingShifts) {
        globalThis.__mdcssRecordShift(preOrigLine(s.line) + 1, s.d);
    }
    return parts.join("\n");
}
markdown = mergeColumnSpec(markdown);
