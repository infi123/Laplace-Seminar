#!/usr/bin/env python3
"""Build Beamer PDF, per-slide PNGs and reliable HTML/MP4 seminar presentation.

Canonical source: main.tex + assets/ + animations_config.json +
                  tools/native_animations.py (+ optional manim scripts).

  python build_all.py
  python build_all.py --clean
  python build_all.py --no-tex  # use a previously built PDF
  python build_all.py --force-videos

Generated output: dist/index.html (self-contained), dist/viewer/index.html,
                  dist/presentation.pdf, dist/viewer/slides/, dist/viewer/videos/.
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parent
BUILD=ROOT/'.build'
DIST=ROOT/'dist'
VIEWER=DIST/'viewer'
MAIN=ROOT/'main.tex'
CFG=ROOT/'animations_config.json'
TOOL=ROOT/'tools/native_animations.py'


def sha(*blobs):
    h=hashlib.sha256()
    for blob in blobs:
        if isinstance(blob,Path):blob=blob.read_bytes()
        elif not isinstance(blob,bytes):blob=str(blob).encode('utf-8')
        h.update(blob)
    return h.hexdigest()


def run(cmd,cwd=ROOT):
    print('  $',' '.join(map(str,cmd)),flush=True)
    subprocess.run(list(map(str,cmd)),cwd=str(cwd),check=True)


def parse_braced(s,pos):
    while pos<len(s) and s[pos].isspace():pos+=1
    if pos>=len(s) or s[pos]!='{':raise ValueError('Expected { at position '+str(pos))
    i=pos+1;level=1
    while i<len(s):
        if s[i]=='{' and s[i-1]!='\\':level+=1
        elif s[i]=='}' and s[i-1]!='\\':
            level-=1
            if level==0:return s[pos+1:i],i+1
        i+=1
    raise ValueError('Unclosed {...} in visualframe')


def title_to_text(s):
    # Visual titles are plain Hebrew. Captions may contain inline TeX math.
    s=re.sub(r'\\(?:textenglish|textbf|emph)\{([^{}]*)\}',r'\1',s)
    s=s.replace('$','').replace('\\,','').replace('\\quad',' ')
    s=re.sub(r'\\[a-zA-Z]+','',s)
    return s.strip()


def frame_manifest(tex):
    """Map animation by attached % ANIM: id, not by fragile page numbers.

    Constraints: a frame generates exactly one PDF page; Beamer overlays
    are detected by a PDF-page-count mismatch rather than silently misaligned.
    """
    if '\\begin{document}' not in tex:raise ValueError('No \\begin{document} found')
    content=tex.split('\\begin{document}',1)[1].split('\\end{document}',1)[0]
    lines=content.splitlines()
    total=0; animations={};marker=None
    for lineno,raw in enumerate(lines,1):
        line=raw.strip()
        if not line:continue
        if line.startswith('% ANIM:'):
            marker=line.split(':',1)[1].strip()
            if not re.fullmatch('[a-z][a-z0-9_]*',marker):raise ValueError('Bad animation marker on line '+str(lineno))
            if marker in animations:raise ValueError('Duplicate marker '+marker)
            continue
        if line.startswith('%'):continue
        if line.startswith('\\begin{frame}') or line.startswith('\\visualframe{'):
            total+=1
            if marker:
                if not line.startswith('\\visualframe{'):
                    raise ValueError(f'% ANIM: {marker} must precede a \\visualframe{{...}} command')
                pos=line.index('\\visualframe')+len('\\visualframe')
                ttl,pos=parse_braced(line,pos)
                path,pos=parse_braced(line,pos)
                desc,pos=parse_braced(line,pos)
                animations[marker]={'slide':total,'title':title_to_text(ttl),'subtitle':title_to_text(desc),'asset':path}
                marker=None
        elif marker and line.startswith('\\end{frame}'):
            raise ValueError(f'Orphan animation marker {marker} on line {lineno}')
    if marker:raise ValueError(f'Orphan animation marker: {marker}')
    return total,animations


def assert_assets():
    for f in [MAIN,CFG,TOOL]:
        if not f.exists():raise FileNotFoundError(f)
    cfg=json.loads(CFG.read_text(encoding='utf-8'))
    source=MAIN.read_text(encoding='utf-8')
    count,slots=frame_manifest(source)
    cfg_ids=set(cfg['animations']);found_ids=set(slots)
    if cfg_ids!=found_ids:
        raise RuntimeError('Animation IDs do not match in main.tex and animations_config.json.\n'
                           f'Only in config: {sorted(cfg_ids-found_ids)}\nOnly in TeX: {sorted(found_ids-cfg_ids)}')
    for k,v in slots.items():
        image=ROOT/'assets'/v['asset']
        if not image.exists():raise FileNotFoundError(f'Frame {v["slide"]} uses missing image {image}')
    print(f'Validated {count} frames and {len(slots)} animation markers: '+
          ', '.join(f'{v["slide"]}:{k}' for k,v in slots.items()))
    return cfg,count,slots


def latex_compile(count,no_tex=False):
    texbuild=BUILD/'tex';texbuild.mkdir(parents=True,exist_ok=True)
    pdf=texbuild/'main.pdf'
    if not no_tex:
        run(['latexmk','-xelatex','-interaction=nonstopmode','-halt-on-error',
             '-output-directory='+str(texbuild),'main.tex'])
    elif not pdf.exists():
        # Allow users with only prior Overleaf PDF to regenerate HTML
        if (ROOT/'main.pdf').exists():shutil.copy2(ROOT/'main.pdf',pdf)
        else:raise RuntimeError('No built PDF available; run without --no-tex')
    import fitz
    with fitz.open(pdf) as doc:
        pages=len(doc)
    if pages!=count:
        raise RuntimeError(f'PDF has {pages} pages but {count} frames were parsed. '
                           'Beamer overlays or untagged multi-page frames need an explicit mapper.')
    DIST.mkdir(exist_ok=True)
    shutil.copy2(pdf,DIST/'presentation.pdf')
    return pdf


def render_slides(pdf,count,force=False):
    import fitz
    target=VIEWER/'slides';target.mkdir(parents=True,exist_ok=True)
    fingerprint=sha(pdf,'render-v3-2x')
    statefile=BUILD/'slides.sha256'
    if not force and statefile.exists() and statefile.read_text()==fingerprint and len(list(target.glob('*.png')))==count:
        print('PNG slide cache hit');return
    print('Rendering slide images...',flush=True)
    with fitz.open(pdf) as doc:
        for i,page in enumerate(doc,1):
            page.get_pixmap(matrix=fitz.Matrix(2.0,2.0),alpha=False).save(target/f'{i:02d}.png')
    statefile.write_text(fingerprint)


def render_animations(cfg,slots,force=False):
    from tools.native_animations import render_video
    vids=VIEWER/'videos';vids.mkdir(parents=True,exist_ok=True)
    statefile=BUILD/'animations.json'
    try:previous=json.loads(statefile.read_text())
    except (OSError,ValueError):previous={}
    new={};result={}
    w,h=cfg['resolution']
    if [w,h]!=[1134,638]:raise RuntimeError('Native renderer currently uses 1134x638 resolution')
    for key,spec in cfg['animations'].items():
        frame=slots[key];dest=vids/(key+'.mp4');engine=spec.get('engine','native')
        if engine=='native':
            fingerprint=sha(TOOL,frame['title'],frame['subtitle'],frame['slide'],spec,
                            cfg['resolution'],cfg['fps'],cfg['duration_seconds'])
            if force or previous.get(key)!=fingerprint or not dest.exists():
                print(f'Rendering {key} into slide {frame["slide"]} (all text encoded in video)...',flush=True)
                render_video(key,dest,frame['title'],frame['subtitle'],frame['slide'],
                             fps=cfg['fps'],duration=cfg['duration_seconds'])
            else:print(f'Video cache hit: {key}',flush=True)
        elif engine=='manim':
            # opt-in: original Manim scene source, may have different styling than Beamer frame.
            sc=spec.get('scene')
            if not sc:raise ValueError(f'Animation {key} requires a Manim scene name')
            script=ROOT/'manim/laplace_scenes.py'
            fingerprint=sha(script,sc,spec)
            if force or previous.get(key)!=fingerprint or not dest.exists():
                media=BUILD/'manim_media'
                run(['manim','-ql','--media_dir',str(media),'--output_file',key,
                     str(script),sc])
                matches=list(media.rglob(key+'.mp4'))
                if not matches:raise RuntimeError(f'Manim did not produce {key}.mp4')
                shutil.copy2(max(matches,key=lambda f:f.stat().st_mtime),dest)
        else:raise RuntimeError(f'Unknown animation engine for {key}: {engine}')
        if not dest.exists() or dest.stat().st_size<100:raise RuntimeError(f'No video generated: {dest}')
        result[frame['slide']]=dest
        new[key]=fingerprint
    statefile.parent.mkdir(exist_ok=True)
    statefile.write_text(json.dumps(new,indent=2),encoding='utf-8')
    for f in vids.glob('*.mp4'):
        if f not in result.values():f.unlink()
    return result


CSS='''
:root{color-scheme:dark;--bg:#07101f;--panel:#112039;--fg:#edf4ff;--muted:#bbd2ed}
*{box-sizing:border-box}html,body{height:100%;width:100%;margin:0;background:var(--bg);color:var(--fg);font-family:Arial,system-ui,sans-serif}
body{display:flex;flex-direction:column;overflow:hidden}
header{background:var(--panel);padding:8px 17px;display:flex;justify-content:space-between;align-items:center;gap:10px}
header small{color:var(--muted)}
main{flex:1;min-height:0;display:flex;align-items:center;justify-content:center;padding:7px}
#screen{position:relative;aspect-ratio:1134/638;height:auto;max-height:100%;width:min(100%,calc((100vh - 124px) * 1134 / 638));overflow:hidden;background:#0b1428;box-shadow:0 15px 40px #0009}
#slide,#video{position:absolute;inset:0;width:100%;height:100%;object-fit:contain}
#video{display:none}#screen.is-video #video{display:block}#screen.is-video #slide{visibility:hidden}
nav{min-height:56px;display:flex;flex-wrap:wrap;justify-content:center;align-items:center;gap:9px;padding:7px;background:var(--panel)}
button{background:#274663;color:var(--fg);border:1px solid #456987;border-radius:9px;padding:8px 14px;cursor:pointer;font:inherit}
button[hidden]{display:none!important}button:hover{background:#355f88}button:disabled{opacity:.4}
#count{direction:ltr;min-width:78px;text-align:center;font-weight:bold}
#message{display:none;position:absolute;bottom:8%;left:50%;transform:translateX(-50%);background:#153454;border-radius:7px;padding:12px;z-index:6}
#message.on{display:block}
@media(max-width:640px){header small{display:none}nav{gap:4px}button{padding:6px 9px;font-size:12px}}
'''

JS='''
"use strict";
const slidePaths=window.SLIDES, videoPaths=window.VIDEOS;
const img=document.getElementById('slide'),vid=document.getElementById('video');
const sc=document.getElementById('screen'),cnt=document.getElementById('count');
const btnPlay=document.getElementById('pause'),btnRestart=document.getElementById('restart');
const btnPrev=document.getElementById('prev'),btnNext=document.getElementById('next');
const msg=document.getElementById('message');
let page=1, serial=0;
const loadedUrls={};
function sourceFor(p){
 if(loadedUrls[p])return loadedUrls[p];
 const x=videoPaths[p];if(!x)return null;
 if(!x.startsWith('data:'))return loadedUrls[p]=x;
 // Blob is safer than very large data: URIs on local file:// documents
 const bytes=atob(x.slice(x.indexOf(',')+1));const arr=new Uint8Array(bytes.length);
 for(let i=0;i<bytes.length;i++)arr[i]=bytes.charCodeAt(i);
 return loadedUrls[p]=URL.createObjectURL(new Blob([arr],{type:'video/mp4'}));
}
function stop(){vid.pause();vid.removeAttribute('src');vid.load();sc.classList.remove('is-video');msg.classList.remove('on');}
async function playAtCurrent(){
 if(!videoPaths[page])return;
 const token=serial;
 try{vid.muted=true;await vid.play();if(serial!==token){vid.pause();return}
     sc.classList.add('is-video');btnPlay.textContent='⏸ השהה';msg.classList.remove('on');}
 catch(e){if(serial===token){msg.classList.add('on');btnPlay.textContent='▶ הפעל';}}
}
function show(){
 serial++;stop();img.src=slidePaths[page-1];
 cnt.textContent=page+' / '+slidePaths.length;
 btnPrev.disabled=page<=1;btnNext.disabled=page>=slidePaths.length;
 const yes=!!videoPaths[page];btnPlay.hidden=!yes;btnRestart.hidden=!yes;
 if(yes){vid.src=sourceFor(page);vid.load();playAtCurrent();}
}
function move(n){const p=Math.max(1,Math.min(slidePaths.length,page+n));if(p!==page){page=p;show();}}
function togglePlayback(){
 if(!videoPaths[page])return;
 if(vid.paused)playAtCurrent();
 else{vid.pause();btnPlay.textContent='▶ המשך';sc.classList.add('is-video');}
}
function restart(){if(!videoPaths[page])return;try{vid.currentTime=0;}catch(e){}playAtCurrent();}
function fullscreen(){document.fullscreenElement?document.exitFullscreen?.():document.documentElement.requestFullscreen?.();}
window.addEventListener('keydown',e=>{
 const k=e.key;
 if([' ','ArrowLeft','ArrowRight','PageDown','PageUp'].includes(k))e.preventDefault();
 if(k==='ArrowLeft'||k==='PageDown'||k===' ')move(1);
 else if(k==='ArrowRight'||k==='PageUp')move(-1);
 else if(k==='f'||k==='F')fullscreen();
 else if(k==='p'||k==='P')togglePlayback();
 else if(k==='r'||k==='R')restart();
});
let x0=null;
document.addEventListener('touchstart',e=>{x0=e.touches[0].clientX},{passive:true});
document.addEventListener('touchend',e=>{if(x0!==null){let dx=e.changedTouches[0].clientX-x0;if(Math.abs(dx)>75)move(dx>0?1:-1);x0=null;}},{passive:true});
img.addEventListener('error',()=>{msg.textContent='שקף לא נמצא. ודא שהקבצים הועתקו יחד.';msg.classList.add('on');});
show();
'''

def html_document(slides,videos,standalone):
    if standalone:
        slide_files=['data:image/png;base64,'+base64.b64encode(p.read_bytes()).decode('ascii') for p in slides]
        video_files={str(page):'data:video/mp4;base64,'+base64.b64encode(p.read_bytes()).decode('ascii') for page,p in videos.items()}
    else:
        slide_files=['slides/'+p.name for p in slides]
        video_files={str(page):'videos/'+p.name for page,p in videos.items()}
    source_js='window.SLIDES='+json.dumps(slide_files,separators=(',',':'))+';\nwindow.VIDEOS='+json.dumps(video_files,separators=(',',':'))+';'
    return '''<!DOCTYPE html><html lang="he" dir="rtl"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>התמרת לפלס — Beamer והמחשות</title><style>'''+CSS+'''</style></head><body>
<header><strong>התמרת לפלס — מצגת מונפשת</strong><small>מצגת Beamer · סרטונים מקוריים · שקפים והמחשות מסונכרנים</small></header>
<main><div id="screen"><img id="slide" alt="שקף"><video id="video" muted playsinline loop preload="auto" aria-label="המחשה מונפשת בתוך שקף"></video><div id="message">הדפדפן חסם ניגון אוטומטי. לחץ על 'הפעל'.</div></div></main>
<nav><button id="next" onclick="move(1)">הבא ◀</button><span id="count">1 / 1</span><button id="prev" onclick="move(-1)">▶ הקודם</button><button id="pause" onclick="togglePlayback()" hidden>⏸ השהה</button><button id="restart" onclick="restart()" hidden>↺ התחלה</button><button onclick="fullscreen()">⛶ מסך מלא</button></nav>
<script>'''+source_js+JS+'''</script></body></html>'''


def build_html(count,videos):
    slides=[VIEWER/'slides'/f'{n:02d}.png' for n in range(1,count+1)]
    assert all(p.exists() for p in slides)
    VIEWER.mkdir(parents=True,exist_ok=True)
    (VIEWER/'index.html').write_text(html_document(slides,videos,False),encoding='utf-8')
    (DIST/'index.html').write_text(html_document(slides,videos,True),encoding='utf-8')
    # In case user wants an independent shareable HTML file
    print(f'Generated self-contained HTML ({(DIST/"index.html").stat().st_size/1024/1024:.1f} MB)')


def main(argv=None):
    a=argparse.ArgumentParser()
    a.add_argument('--clean',action='store_true',help='Delete all build caches and outputs first')
    a.add_argument('--force-videos',action='store_true',help='Force regeneration of all videos')
    a.add_argument('--no-tex',action='store_true',help='Rebuild HTML from previous compiled PDF')
    opts=a.parse_args(argv)
    if opts.clean:
        shutil.rmtree(BUILD,ignore_errors=True)
        shutil.rmtree(DIST,ignore_errors=True)
    BUILD.mkdir(parents=True,exist_ok=True)
    cfg,count,slots=assert_assets()
    pdf=latex_compile(count,opts.no_tex)
    render_slides(pdf,count)
    videos=render_animations(cfg,slots,opts.force_videos)
    build_html(count,videos)
    print('\nBUILD SUCCESS:')
    for path in [DIST/'presentation.pdf',DIST/'index.html',VIEWER/'index.html']:
        print(' ',path.relative_to(ROOT),f'({path.stat().st_size:,} bytes)')
    print(' Animation slides:',', '.join(map(str,sorted(videos))))

if __name__=='__main__':main()
