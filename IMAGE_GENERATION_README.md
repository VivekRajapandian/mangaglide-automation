# MangaGlide V4 — image generation (one shot at a time)

This add-on uses the approved reference PNGs and `MangaGlide_Master_Shot_Script_AUTOMATION.json`.
The original `prepare.py` and all existing instructions remain unchanged.

## Step 1 — install SDK
From the extracted `MangaGlide_V4_starter` directory in PowerShell:

    python -m pip install --upgrade openai python-dotenv

## Step 2 — check API key (do not print it)

    if ($env:OPENAI_API_KEY) { 'API key configured' } else { 'API key missing' }

If missing, set the key privately in Windows Environment Variables or run
`setx OPENAI_API_KEY "<your new key>"`, then open a NEW PowerShell window.
Never put a real key in a file sent to anyone or in version control.

## Step 3 — test safely: NO API charge

    python generate.py --shot 1A

## Step 4 — generate ONE paid image

    python generate.py --shot 1A --execute

The script prints a **planned output path** before execution. A dry run explicitly prints
`DRY RUN ONLY`; only a completed image write prints `IMAGE SAVED`, followed by `GENERATED`
after its metadata is written. Successful execution creates `output/Images/Shot_1A.png`
and `Shot_1A.metadata.json`.
CapCut instructions remain at `output/Instructions/Shot_1A.txt` (from `prepare.py`).

## Limits and important notes
- This script NEVER calls the API without `--execute`, and performs at most ONE request per execution.
- It does not auto-retry; errors should be reviewed before running again.
- It never overwrites a generated shot.
- Default quality is **low**, suitable for a cheap capability/continuity test. For a later approved medium-quality test run `--quality medium`.
- The API currently offers `1536x1024` on GPT Image 1.5: **this is not exact 16:9**, so inspect/crop before CapCut. Do not rely on it being 1920x1080.
- The image-edit endpoint uses all approved reference images attached to each shot. Input image tokens ADD to output charges. There is no in-script billing cap; your API dashboard is the source of truth.
- The image generation model may require project/org eligibility or verification; errors are reported without silently switching models.
- The generator keeps any caption/text OUT of generated pixels, for reliable CapCut overlays.
- The original script's first CapCut keyframe is still in `raw_instructions`; this image-generation add-on does NOT automate CapCut motion.
