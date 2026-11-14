# Hero label correction

The built-in image editor repeatedly rendered 횐 instead of 흰. Do not reuse the generated glyph for the first checklist label.

`assets/img/2026-11-14-2x2-cube-beginner-guide-hero-corrected.svg` preserves the existing raster artwork as an embedded image, covers the erroneous label, and displays the exact Unicode text `흰색 첫 층` with a native Korean font. The first syllable is U+D770; it is not U+D690.

The SVG has no external image dependency. Korean fonts: Malgun Gothic, Noto Sans CJK KR, sans-serif. Its XML text and the rendered first glyph were checked. The oval and the long horizontal stroke of 흰 have a visible gap.
