"""Build final-slide, self-contained videos for Laplace seminar.

All legends, Hebrew titles, axes, values and formula labels are encoded into MP4 pixels.
No HTML overlays or hand-positioned browser labels are used.

Run via build_all.py or manually:
  python tools/native_animations.py --id convolution --output /tmp/convolution.mp4
"""
from __future__ import annotations

import argparse
import math
import subprocess
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

W, H = 1134, 638
BG=(11,20,40); GRID=(31,47,71); FG=(224,235,249); MUTED=(174,193,216)
CYAN=(65,201,232); GOLD=(255,205,102); MINT=(123,220,181); PURPLE=(172,145,255)
GREY=(65,84,111)
FREG='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
FBOLD='/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'


def font(sz:int, bold=False):
    return ImageFont.truetype(FBOLD if bold else FREG, sz)


def he(draw:ImageDraw.ImageDraw, text:str, right:int, top:int, size:int, color=FG, bold=False):
    draw.text((right,top), text, font=font(size,bold), fill=color, anchor='ra', direction='rtl')


def text(draw, value, xy, size=19, color=FG, anchor='la'):
    draw.text(xy, value, font=font(size), fill=color, anchor=anchor)


def poly(draw, pts, color, width=3):
    if len(pts)>1: draw.line(pts,fill=color,width=width,joint='curve')


def line(draw,coords,color,width=3):draw.line(coords,fill=color,width=width)


def arrow(draw, xy1, xy2, color, width=3):
    x1,y1=xy1; x2,y2=xy2
    line(draw,(x1,y1,x2,y2),color,width)
    angle=math.atan2(y2-y1,x2-x1)
    size=10
    pts=[(x2,y2), (x2+size*math.cos(angle+2.55),y2+size*math.sin(angle+2.55)),
                   (x2+size*math.cos(angle-2.55),y2+size*math.sin(angle-2.55))]
    draw.polygon(pts,fill=color)


def base(title,subtitle,slide):
    im=Image.new('RGB',(W,H),BG); d=ImageDraw.Draw(im)
    he(d,title,1100,19,34,FG,True)
    if subtitle: he(d,subtitle,1050,561,21,FG)
    text(d,str(slide),(52,598),15,MUTED)
    he(d,'סמינר: התמרת לפלס',1100,594,15,MUTED)
    return im,d


class Graph:
    def __init__(self, rect, xmin,xmax,ymin,ymax):
        self.x,self.y,self.w,self.h=rect; self.xmin,self.xmax,self.ymin,self.ymax=xmin,xmax,ymin,ymax
    def p(self,x,y):
        return (round(self.x+(x-self.xmin)/(self.xmax-self.xmin)*self.w),
                round(self.y+(self.ymax-y)/(self.ymax-self.ymin)*self.h))
    def axes(self,d,xticks=(),yticks=(),grid=True,axis_labels=('t',''),label_size=15):
        if grid:
            for v in xticks: line(d,(*self.p(v,self.ymin),*self.p(v,self.ymax)), GRID,1)
            for v in yticks: line(d,(*self.p(self.xmin,v),*self.p(self.xmax,v)),GRID,1)
        line(d,(self.x,self.y+self.h,self.x+self.w,self.y+self.h),MUTED,1)
        line(d,(self.x,self.y,self.x,self.y+self.h),MUTED,1)
        for v in xticks:
            x,y=self.p(v,self.ymin);text(d,f'{v:g}',(x,y+8),label_size,MUTED,anchor='ma')
        for v in yticks:
            x,y=self.p(self.xmin,v);text(d,f'{v:g}',(x-14,y),label_size,MUTED,anchor='rm')
        if axis_labels[0]:text(d,axis_labels[0],(self.x+self.w/2,self.y+self.h+32),19,MUTED,anchor='ma')
        if axis_labels[1]:text(d,axis_labels[1],(self.x-20,self.y-21),17,MUTED,anchor='ra')
    def curve(self,d,fn,a,b,color,width=3,steps=300):
        pts=[]
        for i in range(steps+1):
            x=a+(b-a)*i/steps; y=fn(x)
            if math.isfinite(y) and self.ymin <= y <= self.ymax:
                pts.append(self.p(x,y))
            else:
                poly(d,pts,color,width);pts=[]
        poly(d,pts,color,width)
    def rectangle(self,d,a,b,h,color,width=4,fill=None):
        x0,y0=self.p(a,0); x1,y1=self.p(b,h)
        if fill: d.rectangle([x0,y1,x1,y0],fill=fill)
        poly(d,[self.p(a,0),self.p(a,h),self.p(b,h),self.p(b,0)],color,width)


def legend(d,items,x,y,spacing=30,size=18):
    for i,(name,color) in enumerate(items):
        yy=y+i*spacing;line(d,(x,yy+8,x+31,yy+8),color,4)
        text(d,name,(x+42,yy),size,FG)


def scene_euler_decay(u,title,subtitle,slide):
    im,d=base(title,subtitle,slide)
    # Circle with both Cartesian axes and labels.
    cx,cy,r=300,297,161
    line(d,(cx-r-36,cy,cx+r+34,cy),MUTED,2)
    line(d,(cx,cy+r+32,cx,cy-r-34),MUTED,2)
    d.ellipse((cx-r,cy-r,cx+r,cy+r),outline=CYAN,width=4)
    for dx,dy,v in [(r,0,'1'),(-r,0,'−1'),(0,-r,'1'),(0,r,'−1')]:
        text(d,v,(cx+dx+5,cy+dy+8),15,MUTED)
    text(d,'Re(z)',(cx+r+34,cy+14),15,MUTED)
    text(d,'Im(z)',(cx+9,cy-r-38),15,MUTED)
    angle=2*math.pi*u; x2=cx+r*math.cos(angle); y2=cy-r*math.sin(angle)
    arrow(d,(cx,cy),(x2,y2),GOLD,5)
    d.ellipse((x2-6,y2-6,x2+6,y2+6),fill=GOLD)
    text(d,'e^(iωt)',(cx-51,cy+r+65),23,FG)
    # Damped oscillation
    ax=Graph((637,161,407,269),0,9,-1.15,1.15)
    ax.axes(d,[0,2,4,6,8],[-1,0,1],axis_labels=('t','amplitude'))
    fn=lambda t:math.exp(-.25*t)*math.cos(2.5*t)
    ax.curve(d,fn,0,9,CYAN,4)
    ax.curve(d,lambda t:math.exp(-.25*t),0,9,GREY,2)
    ax.curve(d,lambda t:-math.exp(-.25*t),0,9,GREY,2)
    axx,ayy=ax.p(9*u,fn(9*u));d.ellipse((axx-5,ayy-5,axx+5,ayy+5),fill=GOLD)
    legend(d,[('e^(−0.25t) cos(2.5t)',CYAN)],652,453,size=16)
    return im


def scene_complex_modes(u,title,subtitle,slide):
    im,d=base(title,subtitle,slide)
    ax=Graph((112,136,470,332),-2.2,2.2,-2.2,2.2)
    ax.axes(d,[-2,-1,0,1,2],[-2,-1,0,1,2],axis_labels=('Re(s)','Im(s)'))
    pts=[(-1.2,.8),(-.65,1.5),(.75,1.0),(-1.3,-1.1)]
    for i,(x,y) in enumerate(pts):
        px,py=ax.p(x,y);c=[CYAN,GOLD,PURPLE,MINT][i]
        d.ellipse((px-8,py-8,px+8,py+8),fill=c)
        text(d,f's{i+1}',(px+13,py-13),17,c)
    x= -1.35+2.4*u; omega=2.1
    px,py=ax.p(x,omega); d.ellipse((px-11,py-11,px+11,py+11),fill=GOLD)
    tx=Graph((692,162,354,266),0,8,-1.25,1.25)
    tx.axes(d,[0,2,4,6,8],[-1,0,1],axis_labels=('t','value'))
    tx.curve(d,lambda t:math.exp(x*t/5)*math.cos(omega*t),0,8,CYAN,3)
    text(d,f's = {x:+.2f} + {omega:.1f}i',(660,457),21,GOLD)
    text(d,'Re(s): growth / decay',(130,496),19,MUTED)
    return im


def scene_time_shift(u,title,subtitle,slide):
    im,d=base(title,subtitle,slide)
    ax=Graph((196,126,731,332),0,10,-1.2,1.2)
    ax.axes(d,[0,2,4,6,8,10],[-1,0,1],axis_labels=('t','amplitude'))
    ax.curve(d,lambda t:math.sin(t),0,10,GREY,3)
    a=3*u
    ax.curve(d,lambda t:0 if t<a else math.sin(t-a),0,10,CYAN,4)
    xa,ya=ax.p(a,0)
    line(d,(xa,ax.y,xa,ax.y+ax.h),GOLD,2)
    legend(d,[('f(t)',GREY),('uₐ(t) f(t−a)',CYAN)],755,174,spacing=38)
    text(d,f'a = {a:.1f}',(245,491),20,GOLD)
    arrow(d,(335,498),(xa,498),GOLD,3)
    return im


def scene_dirac_pulse(u,title,subtitle,slide):
    im,d=base(title,subtitle,slide)
    ax=Graph((242,120,675,338),0,6,0,5.0)
    ax.axes(d,[0,1,2,3,4,5,6],[0,1,2,3,4,5],axis_labels=('t','height'))
    epslist=[1.30,.75,1.30-(1.30-.27)*u]
    colors=[PURPLE,CYAN,GOLD]
    for e,c in zip(epslist,colors):ax.rectangle(d,3-e/2,3+e/2,1/e,c,3)
    legend(d,[(f'ε = {e:.2f}',c) for e,c in zip(epslist,colors)],763,150,spacing=38)
    text(d,'area = 1',(785,332),24,FG)
    text(d,'height = 1 / ε',(758,391),18,MUTED)
    return im


def scene_convolution(u,title,subtitle,slide):
    im,d=base(title,subtitle,slide)
    t=2.3*u
    top=Graph((245,115,639,166),-.3,2.8,0,1.18)
    bot=Graph((245,343,639,157),-.3,2.8,0,1.16)
    top.axes(d,[0,.5,1,1.5,2,2.5],[0,1],axis_labels=('τ','height'),label_size=13)
    bot.axes(d,[0,.5,1,1.5,2,2.5],[0,.5,1],axis_labels=('t','(f*g)(t)'),label_size=13)
    top.rectangle(d,0,1,1,CYAN,4)
    top.rectangle(d,t-1,t,1,GOLD,4)
    lo=max(0,t-1);hi=min(1,t); area=max(0,hi-lo)
    if area>0.00001:
        x0,y1=top.p(lo,1);x1,y0=top.p(hi,0)
        if x1-x0>=5: d.rectangle([x0+2,y1+2,x1-2,y0-2], fill=(41,79,80))
        line(d,(*top.p(lo,1),*top.p(hi,1)),MINT,4)
    bot.curve(d,lambda a:max(0,1-abs(a-1)),0,2.3,MINT,4)
    x,y=bot.p(t,area); d.ellipse((x-6,y-6,x+6,y+6),fill=GOLD)
    line(d,(x,bot.y,x,bot.y+bot.h),GOLD,1)
    legend(d,[('f(τ)',CYAN),('g(t−τ)',GOLD),('overlap area',MINT)],907,139,spacing=31,size=16)
    text(d,f't = {t:.2f}',(907,361),17,GOLD)
    text(d,f'(f*g)(t) = {area:.2f}',(907,401),17,MINT)
    return im


def scene_system_response(u,title,subtitle,slide):
    im,d=base(title,subtitle,slide)
    ax=Graph((184,129,722,335),0,9,0,1.23)
    ax.axes(d,[0,1,2,3,4,5,6,7,8,9],[0,.5,1],axis_labels=('t','response'))
    # show input and impulse response completely, output grows as time progresses
    ax.curve(d,lambda t:0 if t<1 else 1,0,9,PURPLE,3)
    ax.curve(d,lambda t:math.exp(-t),0,9,CYAN,3)
    ax.curve(d,lambda t:0 if t<1 else 1-math.exp(-(t-1)),0,9*u,GOLD,4,steps=250)
    legend(d,[('x(t) = u(t−1)',PURPLE),('h(t) = e^(−t)u(t)',CYAN),('y(t) = (x*h)(t)',GOLD)],655,167,spacing=31,size=17)
    return im

SCENES={
    'euler_decay':(scene_euler_decay,6),
    'complex_modes':(scene_complex_modes,8),
    'time_shift':(scene_time_shift,21),
    'dirac_pulse':(scene_dirac_pulse,23),
    'convolution':(scene_convolution,27),
    'system_response':(scene_system_response,29),
}


def render_video(anim_id, output:Path, title:str,subtitle:str,slide:int, fps=12,duration=5):
    if anim_id not in SCENES:raise ValueError(f'Unknown animation id: {anim_id}')
    output.parent.mkdir(parents=True,exist_ok=True)
    frames=max(2,round(fps*duration))
    command=['ffmpeg','-hide_banner','-loglevel','error','-y','-f','rawvideo',
             '-vcodec','rawvideo','-pix_fmt','rgb24','-s',f'{W}x{H}',
             '-r',str(fps),'-i','-','-an','-vcodec','libx264','-preset','veryfast',
             '-crf','26','-pix_fmt','yuv420p','-movflags','+faststart',str(output)]
    p=subprocess.Popen(command,stdin=subprocess.PIPE)
    fn,_=SCENES[anim_id]
    try:
        for i in range(frames):
            im=fn(i/(frames-1),title,subtitle,slide)
            p.stdin.write(im.tobytes())
        p.stdin.close()
        if p.wait()!=0:raise RuntimeError(f'ffmpeg failed for {anim_id}')
    except BaseException:
        try:p.kill()
        except:pass
        raise
    return output


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--id',choices=SCENES,required=True)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--title',default='המחשה מתמטית')
    parser.add_argument('--subtitle',default='')
    parser.add_argument('--slide',type=int,default=1)
    parser.add_argument('--fps',type=int,default=12)
    parser.add_argument('--duration',type=int,default=5)
    a=parser.parse_args()
    render_video(a.id,a.output,a.title,a.subtitle,a.slide,a.fps,a.duration)
    print(a.output)

if __name__=='__main__':main()
