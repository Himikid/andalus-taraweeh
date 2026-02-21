# Day Highlights Prompt Template

You are generating **Islamic recitation highlights** for a single Taraweeh day.
Return only high-signal items (avoid filler).

## Input
- Day: {{DAY_NUMBER}}
- Recitation range: {{SURAH_START}}:{{AYAH_START}} to {{SURAH_END}}:{{AYAH_END}}
- Canonical source for ayah boundaries: Quran text corpus provided in context
- Optional marker timestamps: {{MARKERS_JSON_OR_NOTE}}

## Task
Produce:
1. `day_summary` (short paragraph covering the major themes of the full day corpus)
2. `highlights` (3-8 max, fewer if quality is lower)

Important scope rule:
- Highlights must be ONLY one of:
  - `Dua`
  - `Famous Ayah`
- Do NOT include stories, fiqh rulings, historical narrative, or general thematic lessons as standalone highlights unless they are presented as a highly famous ayah itself.

Each highlight must include:
- `ayahRef` (example: `2:30-39`)
- `themeType` (`Dua` or `Famous Ayah` only)
- `shortTitle`
- `summary` (2-3 sentences)
- `keyTakeaway` (1 sentence)
- `whyNotable` (2 concise bullets)
- `references` (at least 2 links)
  - Include one tafsir link (required)
  - Include one direct Quran reference link

## Accuracy rules
- Do not invent stories, asbab, or rulings not present in reliable tafsir.
- Keep claims mainstream and well-established.
- You may discover candidate ayat from wider reputable Islamic sources, but final claims must be phrased and grounded in tafsir evidence.
- Prioritize ayat that are clearly well-known and widely used in worship, remembrance, protection, or foundational recitation.
- If uncertain, omit the item.
- Prefer fewer, stronger highlights over many weak ones.
- If no tafsir support is found for a candidate item, exclude it.

## Output format (JSON only)
{
  "day": {{DAY_NUMBER}},
  "day_summary": {
    "title": "...",
    "summary": "...",
    "themes": ["...", "...", "..."]
  },
  "highlights": [
    {
      "ayahRef": "2:30-39",
      "themeType": "Famous Ayah",
      "shortTitle": "Example Famous Passage",
      "whyNotable": ["...", "..."],
      "summary": "...",
      "keyTakeaway": "...",
      "references": [
        { "name": "Quran 2:30-39", "url": "https://quran.com/2:30-39" },
        { "name": "Ibn Kathir Tafsir (2:30)", "url": "https://quran.com/en/2:30/tafsirs/ar-tafsir-ibn-kathir" }
      ]
    }
  ]
}
