// Line-shift ledger shared between the markdown pre-hooks and the html
// post-hooks. preparser_linediff.js (the last pre pass) records here the
// line shifts of the whole pipeline by diffing the original markdown
// against the transformed text, so the post-hooks can map markdown-it's
// data-source-line values (computed against the transformed text) back to
// real editor line numbers for scroll sync.
// State lives on globalThis because onWillParseMarkdown and
// onDidParseMarkdown are separate function bodies evaluated once in a
// persistent QuickJS context.
globalThis.__MDCSS_ORIGINAL_MARKDOWN__ = markdown;
globalThis.__MDCSS_LINE_SHIFTS__ = [];
globalThis.__mdcssRecordShift = function (origLine, delta) {
    if (delta) {
        globalThis.__MDCSS_LINE_SHIFTS__.push({ o: origLine, d: delta });
    }
};
// Map a line number of the current (already mutated) markdown string back to
// its original numbering. Entries mean "original lines >= o have d extra
// lines in front of them" and are cumulative, so original -> current is
// strictly increasing and the inverse is a simple piecewise walk.
globalThis.__mdcssOrigLine = function (cur) {
    const shifts = globalThis.__MDCSS_LINE_SHIFTS__.slice().sort((a, b) => a.o - b.o);
    let cum = 0;
    for (const s of shifts) {
        if (cur < s.o + cum) {
            return cur - cum;
        }
        cum += s.d;
    }
    return cur - cum;
};
// Anchored line diff: lines that appear exactly once in both texts (real
// content — headings, paragraphs, fenced lines) pin the alignment first, so
// blank-line-rich replacements cannot misalign them; each segment between
// anchors is then diffed with Myers. Every maximal run of non-match edits
// becomes one ledger entry anchored at the first original line BELOW the
// hunk (hunks at the very end shift nothing and are dropped, as are
// net-zero hunks).
globalThis.__mdcssRecordLineDiff = function (original, transformed) {
    const A = original.split("\n");
    const B = transformed.split("\n");
    const countA = new Map();
    const countB = new Map();
    for (const l of A) countA.set(l, (countA.get(l) || 0) + 1);
    for (const l of B) countB.set(l, (countB.get(l) || 0) + 1);
    const posA = new Map();
    for (let i = 0; i < A.length; i += 1) {
        if (countA.get(A[i]) === 1) posA.set(A[i], i);
    }
    const cands = [];
    for (let j = 0; j < B.length; j += 1) {
        const i = posA.get(B[j]);
        if (i !== undefined && countB.get(B[j]) === 1) cands.push([i, j]);
    }
    const lis = [];
    const pred = new Array(cands.length).fill(-1);
    for (let c = 0; c < cands.length; c += 1) {
        let lo = 0, hi = lis.length;
        while (lo < hi) {
            const mid = (lo + hi) >> 1;
            if (cands[lis[mid]][0] < cands[c][0]) lo = mid + 1; else hi = mid;
        }
        if (lo > 0) pred[c] = lis[lo - 1];
        if (lo < lis.length) lis[lo] = c; else lis.push(c);
    }
    const anchors = [];
    for (let c = lis.length ? lis[lis.length - 1] : -1; c !== -1; c = pred[c]) {
        anchors.push(cands[c]);
    }
    anchors.reverse();
    let pa = 0, pb = 0;
    for (const anchor of anchors) {
        __mdcssDiffSegment(A, B, pa, anchor[0], pb, anchor[1]);
        pa = anchor[0] + 1;
        pb = anchor[1] + 1;
    }
    __mdcssDiffSegment(A, B, pa, A.length, pb, B.length);
};

// Myers O(ND) diff over A[a0..a1) vs B[b0..b1), recording hunks into the
// ledger in absolute original-text coordinates.
function __mdcssDiffSegment(A, B, a0, a1, b0, b1) {
    const N = a1 - a0, M = b1 - b0;
    const off = N + M;
    if (off === 0) return;
    const V = new Array(2 * off + 1).fill(0);
    const trace = [];
    let total = off;
    search:
    for (let d = 0; d <= off; d += 1) {
        for (let k = -d; k <= d; k += 2) {
            let x;
            if (k === -d || (k !== d && V[off + k - 1] < V[off + k + 1])) {
                x = V[off + k + 1];
            } else {
                x = V[off + k - 1] + 1;
            }
            let y = x - k;
            while (x < N && y < M && A[a0 + x] === B[b0 + y]) {
                x += 1;
                y += 1;
            }
            V[off + k] = x;
            if (x >= N && y >= M) {
                total = d;
                trace.push(V.slice());
                break search;
            }
        }
        trace.push(V.slice());
    }
    const ops = [];
    let x = N, y = M;
    for (let d = total; d > 0; d -= 1) {
        const Vp = trace[d - 1];
        const k = x - y;
        const prevK = (k === -d || (k !== d && Vp[off + k - 1] < Vp[off + k + 1])) ? k + 1 : k - 1;
        const prevX = Vp[off + prevK];
        const prevY = prevX - prevK;
        while (x > prevX && y > prevY) {
            ops.push(0);
            x -= 1;
            y -= 1;
        }
        if (x === prevX) {
            ops.push(2);
            y -= 1;
        } else {
            ops.push(1);
            x -= 1;
        }
    }
    while (x > 0 && y > 0) {
        ops.push(0);
        x -= 1;
        y -= 1;
    }
    ops.reverse();
    let a = a0, b = b0, ha = -1, del = 0, ins = 0;
    const flush = () => {
        if (ha >= 0 && del !== ins && ha + del < A.length) {
            globalThis.__mdcssRecordShift(ha + del + 1, ins - del);
        }
        ha = -1;
        del = 0;
        ins = 0;
    };
    for (const op of ops) {
        if (op === 0) {
            flush();
            a += 1;
            b += 1;
        } else {
            if (ha < 0) ha = a;
            if (op === 1) {
                del += 1;
                a += 1;
            } else {
                ins += 1;
                b += 1;
            }
        }
    }
    flush();
}
