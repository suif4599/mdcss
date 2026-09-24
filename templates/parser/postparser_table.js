function mergeInlineStyle(tagStart, styleText) {
    const styleMatch = tagStart.match(/style="(.*?)"/i);
    if (styleMatch) {
        const existing = styleMatch[1].trim();
        const merged = existing ? `${existing}; ${styleText}` : styleText;
        return tagStart.replace(styleMatch[0], `style="${merged}"`);
    }
    return `${tagStart} style="${styleText}"`;
}

const wrapStyle = 'white-space: normal !important; overflow-wrap: anywhere; word-break: break-word;';
const cr_regex = /(<td.*?)>(:?c\d+:?|:?r\d+:?|:?c\d+r\d+:?|:?r\d+c\d+:?)\s+(.*)<\/td>/g;
html = html.replace(cr_regex, (match, tdStart, spanInfo, content) => {
    let colspan = 1;
    let rowspan = 1;
    let align = '';
    const colMatch = spanInfo.match(/c(\d+)/);
    if (colMatch) {
        colspan = parseInt(colMatch[1], 10);
    }
    const rowMatch = spanInfo.match(/r(\d+)/);
    if (rowMatch) {
        rowspan = parseInt(rowMatch[1], 10);
    }
    if (spanInfo.startsWith(':') && spanInfo.endsWith(':')) {
        align = 'center';
    } else if (spanInfo.startsWith(':')) {
        align = 'left';
    } else if (spanInfo.endsWith(':')) {
        align = 'right';
    }
    const alignStyle = align ? `text-align: ${align} !important;` : '';
    tdStart = mergeInlineStyle(tdStart, `${alignStyle} ${wrapStyle}`.trim());
    return `${tdStart} colspan="${colspan}" rowspan="${rowspan}">${content}</td>`;
});
const rm_regex = /<td[^>]*>\\<\/td>/g;
html = html.replace(rm_regex, '');
const esc_regex = /<td([^>]*)>\\\\<\/td>/g;
html = html.replace(esc_regex, '<td$1>\\</td>');
const th_regex = /(<th.*?)>(:?c\d+:?)\s+(.*)<\/th>/g;
html = html.replace(th_regex, (match, thStart, spanInfo, content) => {
    let colspan = 1;
    let align = '';
    const colMatch = spanInfo.match(/c(\d+)/);
    if (colMatch) {
        colspan = parseInt(colMatch[1], 10);
    }
    if (spanInfo.startsWith(':') && spanInfo.endsWith(':')) {
        align = 'center';
    } else if (spanInfo.startsWith(':')) {
        align = 'left';
    } else if (spanInfo.endsWith(':')) {
        align = 'right';
    }
    const alignStyle = align ? `text-align: ${align} !important;` : '';
    thStart = mergeInlineStyle(thStart, `${alignStyle} ${wrapStyle}`.trim());
    return `${thStart} colspan="${colspan}">${content}</th>`;
});
const rm_th_regex = /<th[^>]*>\\<\/th>/g;
html = html.replace(rm_th_regex, '');
const esc_th_regex = /<th([^>]*)>\\\\<\/th>/g;
html = html.replace(esc_th_regex, '<th$1>\\</th>');
// Backslash cells protected by preparser_tablecell.js arrive as @MDCSS_BS_N@
// tokens carrying the count typed in the markdown source: N=1 deletes the
// cell, N>=2 renders N-1 literal backslashes. Tokens surviving elsewhere
// (false-positive rows, inline code spans) are restored to ceil(N/2), what
// markdown-it's escape rule would have produced.
html = html.replace(/<t[dh][^>]*>@MDCSS_BS_1@<\/t[dh]>/g, '');
html = html.replace(/<t([dh])([^>]*)>@MDCSS_BS_(\d+)@<\/t\1>/g, (m, tag, attrs, n) => `<t${tag}${attrs}>${'\\'.repeat(Number(n) - 1)}</t${tag}>`);
html = html.replace(/@MDCSS_BS_(\d+)@/g, (m, n) => '\\'.repeat(Math.ceil(Number(n) / 2)));