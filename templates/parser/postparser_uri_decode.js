// crossnote 渲染时会对含非 ASCII 字符的图片路径先 encodeURI 一次（`超` -> `%E8%B6%85`），
// 之后转 file:// 绝对路径时又对已编码的 `%` 再编码一次（`%` -> `%25`），产生双重编码，
// 导致「Open in Browser」/ 导出 HTML 时图片 404（预览端有归一化逻辑，不受影响）。
// 这里将本地图片 src 中的双重编码还原一次（`%25XX` -> `%XX`）。
// 注意：文件名本身含字面 `%XX` 时无法与双重编码区分，属于已知边界。
html = html.replace(/<img\b[^>]*>/gi, (imgTag) =>
    imgTag.replace(/\bsrc=(['"])(.*?)\1/i, (attr, quote, src) => {
        if (/^(?:https?|data|blob|mailto):/i.test(src)) return attr;
        if (!/%25[0-9A-Fa-f]{2}/.test(src)) return attr;
        return `src=${quote}${src.replace(/%25([0-9A-Fa-f]{2})/g, '%$1')}${quote}`;
    }),
);
