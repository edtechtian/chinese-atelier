#!/usr/bin/env python3
"""Build clearly labelled, device-local translation support for public course text.

Only curriculum text is sent to the public Google Translate endpoint. No state,
student drafts, credentials or file paths are read or sent. No runtime API is used.
The endpoint is best-effort and has no availability guarantee; existing entries
are reused, partial failures remain explicit, and teacher corrections are kept.
"""
import argparse, concurrent.futures, hashlib, json, re, subprocess, time
from pathlib import Path
from urllib.parse import urlencode
ROOT=Path(__file__).resolve().parents[1]
OUTPUT=ROOT/'public/language-support.json'
HAN=re.compile(r'[\u3400-\u9fff]')
RUN=re.compile(r'[\u3400-\u9fff]+(?:[\s，。！？；：、“”‘’（）《》…—·0-9]+[\u3400-\u9fff]+)*[。！？；]?')
def norm(text):return re.sub(r'[\s，。！？,.!?、；;：:（）()“”‘’《》…—·]','',text)
def collect():
    data=json.loads((ROOT/'data/curriculum.json').read_text());records={}
    def add(text,refs):
        if len(HAN.findall(text))<2 or len(text)>650:return
        key=norm(text)
        if not key:return
        row=records.setdefault(key,{'id':'tr-'+hashlib.sha256(key.encode()).hexdigest()[:16],'chinese':text.strip(),'en':'','th':'','origin':'supplementary_translation','reviewStatus':'machine_translation_pending_teacher_review','sourceRefs':[]})
        row['sourceRefs']=sorted(set(row['sourceRefs']+refs))
    def walk(value,refs=[]):
        if isinstance(value,dict):
            refs=value.get('sourceRefs',refs)
            for key,item in value.items():
                if key not in {'sourceSlides','sourceRefs','exampleSourceRefs','fileInventory','sourcePath','storedName','fileHash','renderedSlide'}:walk(item,refs)
        elif isinstance(value,list):
            for item in value:walk(item,refs)
        elif isinstance(value,str) and HAN.search(value):
            for match in RUN.finditer(value):
                text=match.group().strip();add(text,refs)
                for sentence in re.findall(r'[^。！？；\n]+[。！？；]?',text):add(sentence.strip(),refs)
    for lesson in data['lessons']+data['supplementary']:
        walk(lesson)
        for v in lesson['vocabulary']:
            add(v['chinese'],v['sourceRefs'])
            row=records.get(norm(v['chinese']))
            if row:
                row['en']=v['meaning'];row['th']=v.get('gloss',{}).get('th','');row['reviewStatus']='existing_vocabulary_gloss';row['origin']='editorial_english_and_source_thai_gloss'
        for slide in lesson['sourceSlides']:
            for line in slide.get('text','').splitlines():
                if HAN.search(line):
                    for match in RUN.finditer(line):add(match.group().strip(),[slide['id']])
    visual=json.loads((ROOT/'curriculum/visual_learning.json').read_text());walk(visual)
    return records
def translate_batch(strings,language):
    text='\n'.join(strings);url='https://translate.googleapis.com/translate_a/single?'+urlencode({'client':'gtx','sl':'zh-CN','tl':language,'dt':'t','q':text})
    for attempt in range(3):
        try:
            run=subprocess.run(['curl','--fail','--silent','--show-error','--max-time','25',url],check=True,capture_output=True)
            result=json.loads(run.stdout);translated=''.join(segment[0] or '' for segment in result[0]);lines=translated.split('\n')
            if len(lines)==len(strings) and all(s.strip() for s in lines):return [s.strip() for s in lines]
            if len(strings)==1 and translated.strip():return [translated.strip()]
            break
        except (subprocess.SubprocessError,ValueError,IndexError,TypeError):
            if attempt==2:raise
            time.sleep(attempt+1)
    # Preserve alignment: never silently assign one sentence's translation to another.
    if len(strings)>1:return sum([translate_batch([s],language) for s in strings],[])
    raise ValueError('No usable translation returned')
def main():
    parser=argparse.ArgumentParser();parser.add_argument('--translate',action='store_true');args=parser.parse_args()
    records=collect();old=json.loads(OUTPUT.read_text()).get('entries',[]) if OUTPUT.exists() else []
    for previous in old:
        key=norm(previous['chinese'])
        if key in records:
            for field in ['en','th']:
                if previous.get(field):records[key][field]=previous[field]
            if previous.get('reviewStatus')=='teacher_reviewed' or previous.get('editorialCorrection'):records[key].update(previous)
    missing=[r for r in records.values() if not r['en'] or not r['th']]
    print(json.dumps({'entries':len(records),'needsTranslation':len(missing),'chineseCharacters':sum(len(r['chinese']) for r in missing)}),flush=True)
    def save():OUTPUT.write_text(json.dumps({'schemaVersion':1,'notice':'Supplementary translation support. Machine translations require teacher review; source content remains authoritative. No runtime translation service or student-data transmission.','entries':list(records.values())},ensure_ascii=False,indent=2)+'\n')
    if not args.translate:save();return
    tasks=[]
    for language in ['en','th']:
        group=[];length=0
        for row in records.values():
            if row[language]:continue
            if group and (length+len(row['chinese'])>650 or len(group)>=18):tasks.append((language,group));group=[];length=0
            group.append(row);length+=len(row['chinese'])+1
        if group:tasks.append((language,group))
    failures=[]
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        futures={pool.submit(translate_batch,[r['chinese'] for r in rows],lang):(lang,rows) for lang,rows in tasks}
        for n,future in enumerate(concurrent.futures.as_completed(futures),1):
            lang,rows=futures[future]
            try:
                for row,translation in zip(rows,future.result()):row[lang]=translation
            except Exception as error:failures.extend(r['id']+':'+lang for r in rows);print('Translation batch needs review:',type(error).__name__,flush=True)
            save()
            if n%10==0:print('Completed',n,'/',len(tasks),'batches',flush=True)
    print(json.dumps({'entries':len(records),'complete':sum(bool(r['en'] and r['th']) for r in records.values()),'failures':failures}),flush=True)
if __name__=='__main__':main()
