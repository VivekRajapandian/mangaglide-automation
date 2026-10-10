"""Generate ONE MangaGlide frame using approved references; dry-run by default.

Usage:
    python generate.py --shot 1A
    python generate.py --shot 1A --execute
No automatic retries, no unattended bulk purchases.
"""

from dotenv import load_dotenv

load_dotenv()

import argparse
import base64
import json
import os
from pathlib import Path
from contextlib import ExitStack

ROOT = Path(__file__).resolve().parent
MASTER = ROOT / 'input' / 'MangaGlide_Master_Shot_Script_AUTOMATION.json'
REGISTRY = ROOT / 'input' / 'MangaGlide_Approved_Asset_Registry.json'
OUT = ROOT / 'output'


def main():
    ap = argparse.ArgumentParser(description='Generate one shot (dry-run unless --execute is passed).')
    ap.add_argument('--shot', default='1A', help='Shot ID, e.g. 1A')
    ap.add_argument('--execute', action='store_true', help='Authorize ONE paid API image request')
    ap.add_argument('--quality', choices=['low', 'medium'], default='low')
    ap.add_argument('--model', default='gpt-image-1.5')
    ap.add_argument('--max-references', type=int, default=5)
    args = ap.parse_args()
    if args.max_references < 1 or args.max_references > 10:
        ap.error('--max-references must be 1..10')
    shots = json.loads(MASTER.read_text(encoding='utf-8'))['shots']
    assets = {a['reference_id']: a for a in json.loads(REGISTRY.read_text(encoding='utf-8'))['assets']}
    shot = next((s for s in shots if s['shot_id'].lower() == args.shot.lower()), None)
    if shot is None:
        ap.error('Unknown shot ID. Choose one of: ' + ', '.join(s['shot_id'] for s in shots))
    sid = shot['shot_id']
    destination = OUT / 'Images' / f'Shot_{sid}.png'
    if destination.exists():
        print(f'Already generated: {destination}. Refusing to overwrite. Review this image first.')
        return 0
    if shot.get('production_type') == 'REUSE_IMAGE':
        print('This shot is REUSE_IMAGE. No image-generation request should be sent.')
        return 0
    if shot.get('validation_status') != 'READY':
        raise SystemExit(f'Shot {sid} is not READY according to the Master Shot Script.')
    if not shot.get('visual_prompt'):
        raise SystemExit(f'Shot {sid} is missing visual_prompt.')
    refs = shot.get('reference_asset_ids', [])
    if len(refs) > args.max_references:
        raise SystemExit(f'Shot requires {len(refs)} approved references, but max is {args.max_references}. Do not silently omit references; increase --max-references after reviewing cost.')
    paths = []
    for ref in refs:
        if ref not in assets:
            raise SystemExit(f'Unknown approved asset ID: {ref}')
        asset = assets[ref]
        if asset.get('approval_status') != 'APPROVED':
            raise SystemExit(f'Unapproved asset: {ref}')
        path = ROOT / 'assets' / asset['approved_filename']
        if not path.is_file() or path.stat().st_size == 0:
            raise SystemExit(f'Missing physical reference image for {ref}: {path}')
        paths.append(path)
    if not paths:
        raise SystemExit('No reference images listed; manual review required before text-only generation.')

    prompt = (
        'Create ONE NEW horizontal 16:9 MangaGlide production frame. Use supplied images as binding '
        'approved visual references in the SAME ORDER as the labeled asset IDs below, not as separate '
        'panels, collages, or a reference sheet. Preserve the exact character identity and designs. '
        'Match the shot composition; keep edges safe for CapCut camera movement. '
        'Render artwork WITHOUT embedded captions, speech bubbles, subtitles, watermarks or labels: '
        'text overlays will be added separately in CapCut. '
        'Requested shot and reference IDs: ' + sid + ' / ' + ', '.join(refs) + '\n\n'
        + shot['visual_prompt'] + '\n\nEXCLUSIONS:\n- '
        + '\n- '.join(shot.get('negative_constraints') or [])
    )
    print(f'Shot {sid} | model={args.model} | quality={args.quality} | references={len(paths)}')
    for ref, path in zip(refs, paths):
        print(f'  {ref}: {path.name}')
    print(f'Planned output (not written yet): {destination}')
    print('Billing warning: reference-image input tokens cost extra; this script has no real-time balance API or guaranteed dollar spending ceiling.')
    if not args.execute:
        print('DRY RUN ONLY: no API call and no charge. Add --execute to authorize exactly one request.')
        return 0
    if not os.environ.get('OPENAI_API_KEY'):
        raise SystemExit('OPENAI_API_KEY environment variable missing. Do not paste it into chat or source code.')
    try:
        from openai import OpenAI
    except ImportError as exc:
        raise SystemExit('Install SDK first: python -m pip install --upgrade openai') from exc
    destination.parent.mkdir(parents=True, exist_ok=True)
    with ExitStack() as stack:
        streams = [stack.enter_context(p.open('rb')) for p in paths]
        client = OpenAI(max_retries=0, timeout=180.0)
        print('API request: sending one images.edit request.')
        result = client.images.edit(
            model=args.model,
            image=streams,
            prompt=prompt,
            size='1536x1024',
            quality=args.quality,
        )
    if not result.data or not result.data[0].b64_json:
        raise SystemExit('No image returned. Check API response/billing before trying again.')
    image_bytes = base64.b64decode(result.data[0].b64_json, validate=True)
    if not image_bytes.startswith(b'\x89PNG\r\n\x1a\n'):
        raise SystemExit('API returned data that is not a PNG image. No output image was saved.')
    destination.write_bytes(image_bytes)
    saved_size = destination.stat().st_size
    if saved_size != len(image_bytes):
        raise SystemExit(f'Image write verification failed: expected {len(image_bytes)} bytes, found {saved_size}.')
    print(f'IMAGE SAVED: {destination} ({saved_size:,} bytes)')
    metadata = {
        'shot_id': sid, 'image_file': str(destination.relative_to(ROOT)),
        'model': args.model, 'quality': args.quality, 'size': '1536x1024',
        'approved_reference_ids': refs, 'master_start_frame': shot['start_frame'],
        'master_end_frame': shot['end_frame'], 'capcut_motion': shot.get('capcut_motion'),
        'review_status': 'PENDING_MANUAL_APPROVAL',
        'note': '1536x1024 is a 3:2 output, not exact 16:9. Crop/resize to 1920x1080 after inspecting safe margins.'
    }
    (OUT / 'Images' / f'Shot_{sid}.metadata.json').write_text(json.dumps(metadata, indent=2, ensure_ascii=False), encoding='utf-8')
    print(f'GENERATED: {destination}\nReview Mira identity, sword shape, 16:9 crop, and shot composition before proceeding.')
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
