"""MangaGlide Video 4 — offline, zero-API-cost preflight and export."""
import argparse, csv, json, pathlib, re, sys
ROOT = pathlib.Path(__file__).resolve().parent
SOURCE = ROOT / 'input'
ASSETS = ROOT / 'assets'
OUTPUT = ROOT / 'output'

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--shots', type=int, default=0, help='0 = all shots; otherwise first N')
    args = ap.parse_args()
    master = json.loads((SOURCE / 'MangaGlide_Master_Shot_Script_AUTOMATION.json').read_text(encoding='utf-8'))
    registry = json.loads((SOURCE / 'MangaGlide_Approved_Asset_Registry.json').read_text(encoding='utf-8'))
    shots_all = master['shots']; shots = shots_all[:args.shots or None]
    ids = {a['reference_id']: a for a in registry['assets']}
    errs=[]; notes=[]; prev=0
    OUTPUT.mkdir(exist_ok=True)
    (OUTPUT/'Instructions').mkdir(exist_ok=True)
    (OUTPUT/'Images').mkdir(exist_ok=True)
    available={}
    for k,a in ids.items():
        f=ASSETS/a['approved_filename']; available[k]=f.is_file() and f.stat().st_size>0
        if not available[k]: errs.append(f'Missing reference file: {k} => {f}')
        if a.get('approval_status')!='APPROVED': errs.append(f'Unapproved reference: {k}')
    rows=[]; sequence=[]
    for shot in shots:
        sid=shot['shot_id']; refs=shot.get('reference_asset_ids',[])
        start,end=shot['start_frame'],shot['end_frame']; dur=shot['duration_frames']; motion=shot.get('capcut_motion',{})
        if start!=prev: errs.append(f'{sid}: timeline gap/overlap expected start {prev}, got {start}')
        if end-start!=dur or dur<=0: errs.append(f'{sid}: invalid duration')
        if not shot.get('visual_prompt'): errs.append(f'{sid}: no visual prompt')
        if not motion.get('keyframes'): errs.append(f'{sid}: missing structured keyframes')
        if not motion.get('raw_instructions'): errs.append(f'{sid}: missing motion instructions')
        for r in refs:
            if r not in ids: errs.append(f'{sid}: unknown asset {r}')
            elif not available[r]: errs.append(f'{sid}: reference unavailable {r}')
        for kf in motion.get('keyframes',[]):
            if not all(v in kf for v in ('relative_frame','scale_percent','x','y')): errs.append(f'{sid}: incomplete keyframe')
            if kf.get('relative_frame',-1)<0 or kf.get('relative_frame',10**9)>dur: errs.append(f'{sid}: keyframe outside duration')
        # Original keyframe 1 is retained in the raw instructions, but absent in this JSON's keyframes array.
        if not any(k.get('relative_frame')==0 for k in motion.get('keyframes',[])):
            notes.append(f'{sid}: first keyframe only in raw_instructions; parser should normalize before automatic editing')
        safe_sid=re.sub(r'[^A-Za-z0-9_-]','_',sid)
        image=f'Images/Shot_{safe_sid}.png'
        refpaths=[str(pathlib.Path('assets')/ids[k]['approved_filename']) for k in refs if k in ids]
        report={'shot_id':sid,'start_frame':start,'end_frame':end,'duration_frames':dur,'fps':master['fps'],
                'production_type':shot['production_type'],'narration':shot.get('narration',''),
                'image_path':image,'reference_asset_ids':refs,'reference_files':refpaths,
                'visual_prompt':shot.get('visual_prompt',''),'negative_constraints':shot.get('negative_constraints',[]),
                'capcut_motion':motion,'transition':shot.get('transition'), 'flow_prompt':shot.get('flow_prompt'),
                'on_image_text':shot.get('on_image_text')}
        (OUTPUT/'Instructions'/f'Shot_{safe_sid}.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
        (OUTPUT/'Instructions'/f'Shot_{safe_sid}.txt').write_text(
            f'Shot {sid}: {shot.get("title", "")}\n'
            f'Frames {start}–{end} (end-exclusive) / {dur} frames @ {master["fps"]} fps\n'
            f'Timecode {shot.get("start_timecode")} → {shot.get("end_timecode")}\n'
            f'Type: {shot["production_type"]}\nReferences: {", ".join(refs)}\n'
            f'Narration: {shot.get("narration","")}\n\n'
            f'VISUAL PROMPT\n{shot.get("visual_prompt","")}\n\n'
            f'CAPCUT\n{motion.get("raw_instructions", "MISSING")}\n\n'
            f'FLOW\n{shot.get("flow_prompt") or "Not applicable"}\n',encoding='utf-8')
        rows.append({'shot_id':sid,'start_frame':start,'end_frame':end,'duration_frames':dur,
                     'start_timecode':shot.get('start_timecode'),'end_timecode':shot.get('end_timecode'),
                     'production_type':shot['production_type'],'image_file':image,
                     'references':';'.join(refs),'capcut_motion':motion.get('raw_instructions',''),
                     'flow_prompt':shot.get('flow_prompt') or ''})
        sequence.append({'id':sid,'image':image,'reference_files':refpaths,'prompt':shot.get('visual_prompt'),
                         'negative_constraints':shot.get('negative_constraints'), 'type':shot['production_type']})
        prev=end
    if not args.shots and prev!=master['total_frames']: errs.append(f'final frame: expected {master["total_frames"]}, got {prev}')
    with (OUTPUT/'CapCut_Timeline.csv').open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    (OUTPUT/'Generation_Queue.json').write_text(json.dumps(sequence,ensure_ascii=False,indent=2),encoding='utf-8')
    summary={'selected_shots':len(shots),'total_shots':len(shots_all),'reference_assets':len(ids),
             'physically_available_reference_assets':sum(available.values()),'errors':errs,'notes':notes,
             'api_images_generated':0,'dry_run':True}
    (OUTPUT/'Preflight_Report.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
    print(f"Preflight: {len(shots)} shots, {sum(available.values())}/{len(ids)} references, {len(errs)} errors, {len(notes)} notes")
    for e in errs: print('ERROR:',e)
    if notes: print('NOTE: Original JSON omits structured first keyframe; full values preserved in raw CapCut instructions.')
    return 1 if errs else 0
if __name__=='__main__': sys.exit(main())
