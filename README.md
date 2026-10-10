# MangaGlide Video 4 — Python automation starter

This archive includes the **four approved automation documents**, **ten exact approved reference images**, and an offline preflight/export script. No OpenAI API credentials, account connection, or image-generation charges are needed to run the script.

## On Windows

1. Extract the ZIP to a folder, e.g. `C:\MangaGlide_V4_starter`.
2. Install Python 3.11 or later if needed.
3. Open PowerShell in the extracted folder.
4. Run `python prepare.py --shots 5` to validate and export the first five shots.
5. Review `output/Preflight_Report.json`, `output/CapCut_Timeline.csv`, `output/Instructions/`, and `output/Generation_Queue.json`.
6. Run `python prepare.py` for all 27 shots.

## What is / isn't automated yet

- **Works now:** shot/frame checks, approved asset ID validation, local reference file verification, CapCut instruction export, standalone visual prompts and generation queue. Missing asset files stop validation.
- **Not yet implemented:** OpenAI API calls and paid image generation, automatic visual quality review, CapCut project editing, Google Flow, YouTube uploads.
- **Known nuance:** the source automation JSON stores CapCut's first keyframe as free text in `raw_instructions`, while later keyframes have structured numeric values. This package preserves the original text exactly. Before auto-applying keyframes to a video editor, normalize keyframe 1 into the structured data.
- The previous report's `/mnt/data/mangaglide_video4_assets/...` paths belonged to an earlier runtime and are **not** used by this package. The package verifies its own `assets/` folder instead.
- Original `audio[].path` fields likewise point to an earlier runtime; the three MP3 files are **not included** here. Obtain them for later rendered-video assembly.

## Next development phase

Implement a separate **opt-in paid** image API generator that reads `output/Generation_Queue.json`, uses actual `assets/` files as reference inputs, saves only missing images, uses limited retries, and requests manual approval. Confirm current API support/pricing before running. Images may not perfectly preserve characters; inspect all results.
