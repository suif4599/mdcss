html = html.replace(
    /<img[^\>]*>/g,
    (imgTag) => {
        let match = imgTag.match(/alt=(['"])(.*?)\1/i);
        const alt = match ? match[2] : '';
        match = alt.match(/\((.+)\)/i);
        let caption = match ? match[1] : '';
        let format = alt.replace(`(${caption})`, '').trim();
        const isFloat = format.includes('Lf') || format.includes('Rf');
        const isSideAligned = !isFloat && (format.includes('L') || format.includes('R'));
        const hasCaption = Boolean(caption);
        const shouldWrapWithoutCaption = format.includes('r');
        if (!hasCaption && !shouldWrapWithoutCaption) return imgTag;
        if (!format.includes("r")) {
            const finalCaption = caption.startsWith('.') ? `图@COUNT_PLACEHOLDER@:\t` + caption.slice(1) : caption;
            if (isFloat) {
                match = imgTag.match(/style=(['"])(.*?)\1/i);
                let style = match ? match[2] : '';
                style = style.replace(/float:\s*(left|right)\s*!?important?/gi, '');
                style = style.replace(/display:\s*inline-block/g, 'display: block');
                match = style.match(/width:\s*(\d{1,4}(?:px|%))/i);
                const width = match ? match[1] : '100%';
                style = style.replace(/width:\s*\d{1,4}(?:px|%)/g, `width: 100%`);
                if (!/display\s*:/i.test(style)) {
                    style = `${style}; display: block`;
                }
                style = style
                    .split(';')
                    .map((s) => s.trim())
                    .filter(Boolean)
                    .join('; ');
                if (imgTag.match(/style=(['"])(.*?)\1/i)) {
                    imgTag = imgTag.replace(/style=(['"])(.*?)\1/i, `style="${style}"`);
                } else {
                    imgTag = imgTag.replace(/\/>$/, ` style="${style}"/>`).replace(/>$/, ` style="${style}">`);
                }
                const floatDir = format.includes('Rf') ? 'right' : 'left';
                const margin = floatDir === 'left' ? '0 1em 1em 0' : '0 0 1em 1em';
                return `<figure style="float: ${floatDir}; width: ${width}; margin: ${margin};" alt="${format}">
${imgTag}
<figcaption style="text-align: center; overflow-wrap: break-word;">${finalCaption}</figcaption>
</figure>`;
            }

            if (isSideAligned) {
                match = imgTag.match(/style=(['"])(.*?)\1/i);
                let style = match ? match[2] : '';
                style = style.replace(/display:\s*inline-block/g, 'display: block');
                match = style.match(/width:\s*(\d{1,4}(?:px|%))/i);
                const width = match ? match[1] : '100%';
                style = style.replace(/width:\s*\d{1,4}(?:px|%)/g, `width: 100%`);
                style = style
                    .split(';')
                    .map((s) => s.trim())
                    .filter(Boolean)
                    .join('; ');
                if (imgTag.match(/style=(['"])(.*?)\1/i)) {
                    imgTag = imgTag.replace(/style=(['"])(.*?)\1/i, `style="${style}"`);
                } else {
                    imgTag = imgTag.replace(/\/>$/, ` style="${style}"/>`).replace(/>$/, ` style="${style}">`);
                }

                const margin = format.includes('R') ? '0 0 1em auto' : '0 auto 1em 0';
                return `<figure style="width: ${width}; margin: ${margin};" alt="${format}">
${imgTag}
<figcaption style="text-align: center; overflow-wrap: break-word;">${finalCaption}</figcaption>
</figure>`;
            }

            return `<figure style="width: 100%; margin: 0 auto; text-align: center;">
${imgTag}
<figcaption style="text-align: center; overflow-wrap: break-word;">${finalCaption}</figcaption>
</figure>`;
        }
        match = imgTag.match(/style=(['"])(.*?)\1/i);
        let style = match ? match[2] : '';
        style = style.replace(/display:\s*inline-block/g, 'display: block');
        match = style.match(/width:\s*(\d{1,4}(?:px|%))/i);
        const width = match ? match[1] : '100%';
        style = style.replace(/width:\s*\d{1,4}(?:px|%)/g, `width: 100%`);
        imgTag = imgTag.replace(/style=(['"])(.*?)\1/i, `style="${style}"`);
        // 子图标题：不参与全局图号，改用 (a)(b)(c) 占位符，在归组时按顺序替换
        const finalCaption = caption ? (caption.startsWith('.') ? `@SUBFIGURE_PLACEHOLDER@\t` + caption.slice(1) : caption) : '';
        return `<figure style="width: ${width}; margin: 0; display: inline-block; vertical-align: top;" alt="${format}">
${imgTag}
    ${finalCaption ? `<figcaption style="text-align: center; overflow-wrap: break-word;">${finalCaption}</figcaption>` : ''}
</figure>`;
    }
)

// 子图字母编号：0 → a, 1 → b, ..., 25 → z, 26 → aa, 27 → ab ...
function subLabel(n) {
    let label = '';
    n += 1;
    while (n > 0) {
        const rem = (n - 1) % 26;
        label = String.fromCharCode(97 + rem) + label;
        n = Math.floor((n - 1) / 26);
    }
    return label;
}

html = html.replace(
    /((<figure\b[^>]*\balt=(?:"[^"]*r[^"]*"|'[^']*r[^']*')[^>]*>[\s\S]*?<\/figure>\s*)+)/g,
    (match) => {
        let firstFigure = match.split('</figure>')[0];
        let captionMatch = firstFigure.match(/<figcaption.*?>(.*?)<\/figcaption>/i);
        let caption = captionMatch ? captionMatch[1] : '';
        let generalCaptionMatch = caption.match(/\((.+)\)/i);
        let generalCaption = generalCaptionMatch ? generalCaptionMatch[1] : '';
        if (generalCaption) {
            let modifiedCaption = caption.replace( /\((.+)\)/i, "");
            let modifiedCaptionTag = captionMatch[0].replace(caption, modifiedCaption);
            let modifiedFirstFigure = firstFigure.replace(captionMatch[0], modifiedCaptionTag);
            match = match.replace(firstFigure, modifiedFirstFigure);
            generalCaption = generalCaption.startsWith('.') ? `图@COUNT_PLACEHOLDER@:\t` + generalCaption.slice(1) : generalCaption;
            generalCaption = `<figcaption style="text-align: center; overflow-wrap: break-word;">${generalCaption}</figcaption>`;
        }
        // 子图 (a)(b)(c) 编号：每组从 (a) 开始，按组内顺序给带占位符的子图标题编号
        let subIdx = 0;
        match = match.replace(/@SUBFIGURE_PLACEHOLDER@/g, () => `(${subLabel(subIdx++)})`);
        return `<figure style="text-align: center; width: 100%; margin: 0 auto;">
${match}
${generalCaption || ''}
</figure>`;
    }
)

// In flex-column containers, float on sibling blocks will not wrap text.
// Merge "float figure + next paragraph" into one paragraph so wrapping still works.
html = html.replace(
    /(?:<p>\s*<\/p>\s*)?(<figure\b[^>]*\balt=(['"])[^'"]*(?:Lf|Rf)[^'"]*\2[^>]*>[\s\S]*?<\/figure>)\s*(?:<p>\s*<\/p>\s*)?<p>([\s\S]*?)<\/p>/g,
    (match, figureHtml, _q, nextParagraphContent) => `<p>${figureHtml}${nextParagraphContent}</p>`
)

let cnt = 0;
html = html.replace(/@COUNT_PLACEHOLDER@/g, (match) => {
    cnt += 1;
    return cnt;
});