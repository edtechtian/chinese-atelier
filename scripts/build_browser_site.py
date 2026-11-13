#!/usr/bin/env python3
"""Build a private, on-device learning edition for static GitHub Pages hosting."""
import hashlib, json, re, zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
SITE=ROOT/'site'
SITE.mkdir(exist_ok=True)

def routes(text):
    return (text.replace('/teacher#/teacher/', '#/teacher/')
        .replace("'/teacher'", "'#/teacher/overview'")
        .replace('"/teacher"', '"#/teacher/overview"')
        .replace('/#/', '#/')
        .replace('/assets/', '../public/assets/'))

for source in (ROOT/'public').iterdir():
    if source.suffix not in {'.js','.css'}:continue
    text=source.read_text()
    if source.name=='lib.js':
        start=text.index('async function localFetch(')
        end=text.index('export const paths')
        text=text[:start]+"import {browserApi,browserDownload} from './browser-api.js';\nexport const api=browserApi;\n"+text[end:]
        text=text[:text.index('export async function download(')]+"export const download=browserDownload;\n"
    if source.name=='app.js':
        text=text.replace("location.pathname==='/teacher'","location.hash.startsWith('#/teacher')")
        text=text.replace('Progress and writing stay in local files and browser drafts. No analytics, cloud AI or third-party services. Keep shared devices and exports private.','Progress and writing stay in this browser on this device. Export a portfolio backup before clearing site data or changing devices. Teacher review is a same-device view, not remote synchronization.')
        text=text.replace('<main class="main"','<aside class="browser-privacy" aria-label="Browser storage">Online learning · Saved in this browser only. Export your portfolio to back up or share your work.</aside><main class="main"')
    if source.name=='teacher.js':
        a=text.index('function login(){');b=text.index('function tabs(',a)
        text=text[:a]+"function login(){return '<section class=\"teacher-login\"><span class=\"brand-mark\">师</span><h1>Same-device teaching view</h1><p>This view reads only the work saved in this browser. It is not password-protected, does not verify reviewer identity, and cannot see another device. For remote feedback, ask the learner to share a portfolio export. The local Python app provides the protected teacher workspace.</p><button class=\"button\" data-action=\"teacher-browser-open\">Open same-device teaching view</button><a href=\"#/home\">Return to learning</a></section>'; }\n\n"+text[b:]
        text=text.replace("export async function teacherEvent(action,target,ctx){","export async function teacherEvent(action,target,ctx){if(action==='teacher-browser-open'){await api('/api/browser/teacher/open',{});T=null;await ctx.refresh();await ctx.render();return;}")
    text=routes(text)
    text=text.replace('Private local workspace','Same-device teaching view').replace('Teacher desk locked.','Teaching view closed.').replace('Lock teacher desk','Close teaching view')
    text=text.replace('Teacher assessment of this revision.','Same-device feedback; reviewer identity is not authenticated.')
    (SITE/source.name).write_text(text)

html=(ROOT/'public/index.html').read_text()
html=routes(html).replace('href="/styles.css"','href="./styles.css"').replace('href="/daily.css"','href="./daily.css"').replace('href="/adventure.css"','href="./adventure.css"').replace('src="/app.js"','src="./boot.js"')
html=html.replace('Getting your next adventure ready…','<span id="engine-status" role="status">Preparing your 20-lesson course…</span><small>First visit downloads a private learning engine. Progress stays in this browser.</small>')
html=html.replace('This local learning app','This learning app')
html=html.replace('</head>','<link rel="stylesheet" href="./browser.css"></head>')
(SITE/'index.html').write_text(html)
(SITE/'boot.js').write_text("if(!location.hash)location.hash='#/home';\nawait import('./app.js');\n")
(SITE/'browser.css').write_text('.browser-privacy{background:#edf5e8;color:#304530;padding:10px 28px;font-size:12px;border-bottom:1px solid #c9debd;line-height:1.5}.loading-screen small{display:block;max-width:340px;margin:12px auto;color:#566657;font-size:13px;line-height:1.5}.teacher-login a{display:block;margin-top:20px}\n')

files=[ROOT/'server.py',*(ROOT/'app').glob('*.py'),ROOT/'data/curriculum.json',ROOT/'curriculum/visual_learning.json',SITE/'bridge.py']
with zipfile.ZipFile(SITE/'course.zip','w',zipfile.ZIP_DEFLATED,compresslevel=9) as archive:
    for p in files:
        name='bridge.py' if p.name=='bridge.py' else str(p.relative_to(ROOT))
        text=p.read_text()
        if p.suffix=='.json':text=routes(text)
        archive.writestr(name,text)
manifest={'schemaVersion':1,'engine':'Pyodide 0.29.0','lessonCount':20,'storage':'IndexedDB on this browser; no cloud student records','files':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in SITE.iterdir() if p.is_file() and p.name!='build.json'}}
(SITE/'build.json').write_text(json.dumps(manifest,indent=2))
print('Built',len(files),'source modules/data files; course.zip', (SITE/'course.zip').stat().st_size,'bytes')
