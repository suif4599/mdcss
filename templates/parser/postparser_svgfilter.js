// Append the shared invert-brightness SVG filter definition to the rendered
// document. The MPE target appends this SVG in the pre pass
// (preparser_invert_brightness.js — the canonical copy of the filter
// matrices; keep the two in sync). For sanitizing consumers (Inkstone) the
// pre pass cannot be used: the SVG would pass through DOMPurify, whose
// style stripping would un-hide it (a bare <svg> renders as a visible empty
// box), so the inkstone assembly appends it here after sanitization instead.
// Hiding uses width/height attributes in addition to the style so the SVG
// stays invisible even if some later consumer strips styles again.
// The guard keeps nested renders (note embeds, md-example) from stacking
// duplicate copies of the same filter id.
if (!html.includes('id="invert-brightness"')) {
    html += `

<svg xmlns="http://www.w3.org/2000/svg" width="0" height="0" style="position: absolute; visibility: hidden;">
  <defs>
    <filter id="invert-brightness" color-interpolation-filters="sRGB">
      <feColorMatrix type="matrix" values="
        0.299   0.587   0.114   0  0
       -0.147  -0.289   0.436   0  0
        0.615  -0.515  -0.100   0  0
        0       0       0       1  0" />
      <feColorMatrix type="matrix" values="
        -1   0   0   0   1
         0   1   0   0   0
         0   0   1   0   0
         0   0   0   1   0" />
      <feColorMatrix type="matrix" values="
        1       0        1.13983  0   -0.569915
        1      -0.39465 -0.58060  0    0
        1       2.03211  0        0    0
        0       0        0        1    0" />
    </filter>
  </defs>
</svg>
`;
}
