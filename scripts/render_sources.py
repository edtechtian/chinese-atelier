#!/usr/bin/env python3
"""Render complete original slides for visual audit, without interpreting missing text."""
from pathlib import Path
import json
import subprocess
import tempfile
import time
from PIL import Image, ImageOps, ImageDraw

ROOT=Path(__file__).resolve().parents[1]
c=json.loads((ROOT/'data/curriculum.json').read_text())
out=ROOT/'public/assets/source/rendered'
out.mkdir(parents=True,exist_ok=True)
qa=ROOT/'docs/source-contact-sheets'
qa.mkdir(exist_ok=True)
log=[]
with tempfile.TemporaryDirectory(prefix='emmalyne-render-') as tmp:
    for l in c['lessons']:
        folder=out/l['id']
        folder.mkdir(exist_ok=True)
        f=next(f for f in c['fileInventory'] if f['id'] in l['processing']['files'])
        source=ROOT/'sources'/f['storedName']
        start=time.monotonic()
        pdf=Path(tmp)/(source.stem+'.pdf')
        record={'lesson':l['number'],'source':f['filename'],'expectedSlides':len(l['sourceSlides'])}
        try:
            r=subprocess.run(['soffice','-env:UserInstallation='+(Path(tmp)/'profile').as_uri(),'--headless','--convert-to','pdf','--outdir',tmp,str(source)],capture_output=True,text=True,timeout=90)
            if r.returncode or not pdf.exists():raise RuntimeError('PDF conversion failed: '+r.stderr[:300])
            r=subprocess.run(['pdftoppm','-scale-to','1050','-png','-r','90',str(pdf),str(folder/'slide')],capture_output=True,text=True,timeout=90)
            if r.returncode:raise RuntimeError('Slide rasterization failed: '+r.stderr[:300])
            images=sorted(folder.glob('slide-*.png'))
            record['renderedSlides']=len(images)
            record['status']='rendered' if len(images)==len(l['sourceSlides']) else 'count_mismatch'
            # Contact sheets are QA thumbnails of originals, not newly drawn illustrations.
            width=1500;cellw=500;cellh=310;rows=(len(images)+2)//3
            sheet=Image.new('RGB',(width,rows*cellh),'#f0eee8')
            draw=ImageDraw.Draw(sheet)
            for i,img in enumerate(images):
                im=Image.open(img).convert('RGB')
                thumb=ImageOps.contain(im,(490,285))
                x=(i%3)*cellw;y=(i//3)*cellh
                sheet.paste(thumb,(x+5,y+20))
                draw.text((x+8,y+3),'L'+str(l['number'])+' / Slide '+str(i+1),fill='#252f2c')
                l['sourceSlides'][i]['renderedSlide']='/assets/source/rendered/'+l['id']+'/'+img.name
            sheet.save(qa/(l['id']+'.jpg'),quality=86)
        except Exception as e:
            record.update({'status':'render_failed','issues':[str(e)]})
        record['seconds']=round(time.monotonic()-start,1)
        log.append(record)
        (ROOT/'data/render-audit.json').write_text(json.dumps(log,ensure_ascii=False,indent=2))
        print(json.dumps(record,ensure_ascii=False),flush=True)
(ROOT/'data/curriculum.json').write_text(json.dumps(c,ensure_ascii=False,indent=2))
