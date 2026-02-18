# andalus-taraweeh

Taraweeh livestream website for **Andalus Centre Glasgow** built with Next.js 14, TypeScript, and TailwindCSS.

## Local development

```bash
npm install
npm run dev
```

Open http://localhost:3000.

## Deploy to Vercel

1. Push this project to GitHub.
2. Import the repository in Vercel.
3. Keep default framework settings (Next.js).
4. Deploy.

## Update YouTube IDs

Edit:

- `data/taraweehVideos.ts`

Use day keys from `1` to `30` and set each value to a YouTube video ID.

## Manual video override

Use URL query param:

- `?video=VIDEO_ID`

Example:

- `http://localhost:3000?video=dQw4w9WgXcQ`

## Future AI JSON index files

Place day index JSON files in:

- `public/data/day-{N}.json`

Examples:

- `public/data/day-1.json`
- `public/data/day-2.json`

If a selected day JSON exists, the site shows **Indexed Surahs**. If not, it hides that section automatically.
