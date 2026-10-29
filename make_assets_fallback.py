"""Render static slides and MP4 previews with matplotlib when Manim isn't present.
The definitive, editable Manim scenes live in manim/laplace_scenes.py.
"""
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation, FFMpegWriter
from matplotlib.patches import Rectangle, Circle, FancyArrowPatch

ROOT=Path(__file__).parent
AS=ROOT/'assets'; AN=ROOT/'animations'
AS.mkdir(exist_ok=True); AN.mkdir(exist_ok=True)
BG='#0b1428'; FG='#e9f3ff'; GRID='#31405b'; CYAN='#41c9e8'; GOLD='#ffcd66'; RED='#fb7185'; GREEN='#7bdcb5'; PURPLE='#a89af7'
plt.rcParams.update({
  'figure.facecolor':BG,'axes.facecolor':BG,'savefig.facecolor':BG,
  'axes.edgecolor':GRID,'text.color':FG,'axes.labelcolor':FG,
  'xtick.color':'#b9c5d7','ytick.color':'#b9c5d7','grid.color':GRID,
  'font.family':'DejaVu Sans','mathtext.fontset':'dejavusans',
  'font.size':15,'axes.titlesize':18,
})

def ax_style(ax,xlab='t',ylab='',grid=True):
    ax.spines[['top','right']].set_visible(False)
    ax.spines[['left','bottom']].set_color(GRID)
    ax.tick_params(length=0)
    ax.set_xlabel(xlab);ax.set_ylabel(ylab, rotation=0, labelpad=15)
    if grid: ax.grid(alpha=.30,linewidth=.75)

def save(fig,name):
    fig.savefig(AS/name,dpi=190,facecolor=BG,bbox_inches='tight',pad_inches=.24)
    plt.close(fig)

def movie(fig,animate,nframes,name,fps=20):
    ani=FuncAnimation(fig,animate,frames=nframes,interval=1000/fps,blit=False)
    ani.save(str(AN/name),writer=FFMpegWriter(fps=fps,bitrate=900,codec='libx264',extra_args=['-pix_fmt','yuv420p']))
    plt.close(fig)

# exponential derivative and tangent
fig,ax=plt.subplots(figsize=(10.6,5.8));t=np.linspace(-1.2,2.3,350);x0=.9;y0=np.exp(x0)
ax.plot(t,np.exp(t),c=CYAN,lw=4,label=r'$f(t)=e^t$');ax.plot(t,y0+y0*(t-x0),c=GOLD,lw=2.7,ls='--',label='tangent')
ax.scatter([x0],[y0],c=GOLD,s=85,zorder=4);ax.plot([x0,x0],[0,y0],c=GOLD,lw=1,ls=':');
ax.text(x0+.12,y0+.2,rf'$f({x0:.1f})=f\prime({x0:.1f})$',c=FG)
ax.set(xlim=(-1.2,2.3),ylim=(0,11));ax_style(ax);ax.legend(frameon=False,labelcolor=FG)
save(fig,'01_exponential.png')

# Euler complex plane + damped oscillation
fig,(ax,ax2)=plt.subplots(1,2,figsize=(12.5,5.7),gridspec_kw={'width_ratios':[1,1.3]});ang=1.0
th=np.linspace(0,2*np.pi,500);ax.plot(np.cos(th),np.sin(th),c=GRID,lw=2);ax.axhline(0,c=GRID,lw=1);ax.axvline(0,c=GRID,lw=1)
ax.annotate('',xy=(np.cos(ang),np.sin(ang)),xytext=(0,0),arrowprops={'arrowstyle':'-|>','lw':3.5,'color':GOLD});ax.plot([np.cos(ang),np.cos(ang)],[0,np.sin(ang)],c=PURPLE,ls='--',lw=2)
ax.plot([0,np.cos(ang)],[0,0],c=CYAN,ls='--',lw=2);ax.scatter([np.cos(ang)],[np.sin(ang)],c=GOLD,s=60)
ax.text(.10,.82,r'$e^{it}$',c=GOLD,fontsize=23);ax.text(.12,-.15,r'$\cos t$',c=CYAN);ax.text(.65,.45,r'$\sin t$',c=PURPLE)
ax.set(xlim=(-1.25,1.25),ylim=(-1.25,1.25),aspect='equal');ax.set_xticks([-1,0,1]);ax.set_yticks([-1,0,1]);ax.tick_params(length=0)
t=np.linspace(0,8,500);ax2.plot(t,np.exp(-.28*t)*np.cos(3.3*t),c=CYAN,lw=3)
ax2.plot(t,np.exp(-.28*t),ls='--',c=GOLD,alpha=.8);ax2.plot(t,-np.exp(-.28*t),ls='--',c=GOLD,alpha=.8)
ax2.set(xlim=(0,8),ylim=(-1.1,1.1));ax2.text(2.1,.78,r'$e^{-.28t}\cos(3.3t)$',c=FG)
ax_style(ax2);fig.tight_layout(pad=2);save(fig,'02_euler.png')

# modes in s-plane and time responses
fig,(ax,ax2)=plt.subplots(1,2,figsize=(12.3,5.65));pts=[(-.35,1.0),(-.72,2.0),(-.15,3.2),(.07,1.4)]
ax.axhline(0,c=GRID,lw=2);ax.axvline(0,c=GRID,lw=2);ax.axvspan(-1.1,0,color=GREEN,alpha=.06);ax.axvspan(0,.5,color=RED,alpha=.07)
for i,(sig,w) in enumerate(pts):
    c=[CYAN,GOLD,PURPLE,RED][i];ax.scatter([sig],[w],c=c,s=130,edgecolors=FG,linewidths=.7);ax.annotate(r'$s_%d$'%(i+1),(sig,w),xytext=(8,8),textcoords='offset points',c=c,fontsize=15)
ax.set(xlim=(-1.15,.52),ylim=(-.35,3.8));ax_style(ax,xlab=r'$\mathrm{Re}(s)=\sigma$',ylab=r'$\mathrm{Im}(s)=\omega$')
t=np.linspace(0,9,450)
for i,(sig,w) in enumerate(pts): ax2.plot(t,np.exp(sig*t)*np.cos(w*t),c=[CYAN,GOLD,PURPLE,RED][i],lw=2.2,label=r'$s_%d$'%(i+1))
ax2.set(xlim=(0,9),ylim=(-2.0,2.0));ax_style(ax2);ax2.legend(frameon=False,labelcolor=FG,ncol=2,fontsize=11)
fig.tight_layout(pad=2);save(fig,'03_modes.png')

# weighted integral kernel
fig,ax=plt.subplots(figsize=(10.9,5.8));t=np.linspace(0,9,550);f=1+.55*np.sin(2.3*t)+.18*np.sin(4.6*t);weight=np.exp(-.36*t)
ax.plot(t,f,c=PURPLE,lw=2,label=r'$f(t)$');ax.plot(t,weight,c=GOLD,lw=2.4,label=r'$e^{-\sigma t}$');ax.fill_between(t,0,f*weight,color=CYAN,alpha=.22,label=r'$f(t)e^{-\sigma t}$');ax.plot(t,f*weight,c=CYAN,lw=2.4)
ax.set(xlim=(0,9),ylim=(0,2.2));ax_style(ax);ax.legend(frameon=False,labelcolor=FG)
save(fig,'04_weighted.png')

# convergence growth bound
fig,ax=plt.subplots(figsize=(10.6,5.8));t=np.linspace(0,3.1,500)
ax.plot(t,np.exp(.85*t),c=CYAN,lw=3,label=r'$e^{0.85t}$');ax.plot(t,t**3+1,c=GREEN,lw=3,label=r'$1+t^3$');ax.plot(t,np.exp(t*t),c=RED,lw=3,label=r'$e^{t^2}$');ax.plot(t,2*np.exp(2*t),c=GOLD,ls='--',lw=2,label=r'$2e^{2t}$')
ax.set(xlim=(0,3.1),ylim=(0,45));ax_style(ax);ax.legend(frameon=False,labelcolor=FG,ncol=2)
save(fig,'05_growth.png')

# s shift: pole translating
fig,ax=plt.subplots(figsize=(10.6,5.8));ax.axhline(0,c=GRID,lw=2);ax.axvline(0,c=GRID,lw=2)
ax.scatter([-1,-1],[1.3,-1.3],c=CYAN,s=120,label=r'$F(s)$');ax.scatter([.45,.45],[1.3,-1.3],c=GOLD,s=120,label=r'$F(s-a)$')
for yy in (1.3,-1.3): ax.annotate('',xy=(.36,yy),xytext=(-.92,yy),arrowprops={'arrowstyle':'-|>','lw':2,'color':GOLD})
ax.text(-.96,1.65,r'$s_0$',c=CYAN);ax.text(.48,1.65,r'$s_0+a$',c=GOLD)
ax.set(xlim=(-2,1.7),ylim=(-2.2,2.2));ax_style(ax,xlab=r'$\mathrm{Re}(s)$',ylab=r'$\mathrm{Im}(s)$')
ax.legend(frameon=False,labelcolor=FG)
save(fig,'06_shift_s.png')

# ODE solution
fig,ax=plt.subplots(figsize=(10.7,5.8));t=np.linspace(0,7.5,450);y=2*np.exp(-t)-np.exp(-2*t)
ax.plot(t,y,c=CYAN,lw=3.6,label=r'$y(t)=2e^{-t}-e^{-2t}$');ax.axhline(0,c=GRID,lw=1.3)
ax.scatter([0],[1],c=GOLD,s=100,zorder=3);ax.annotate(r'$y(0)=1,\;y\prime(0)=0$',xy=(0,1),xytext=(2,1.3),c=GOLD,arrowprops={'arrowstyle':'->','color':GOLD})
ax.set(xlim=(0,7.5),ylim=(-.05,1.65));ax_style(ax,ylab='y');ax.legend(frameon=False,labelcolor=FG)
save(fig,'07_ode.png')

# shift in time step and ramp
fig,ax=plt.subplots(figsize=(10.7,5.7));t=np.linspace(0,9,500);a=3.0
ax.plot(t,np.sin(t),c=GRID,lw=2.5,alpha=.7,label=r'$f(t)$');delayed=np.where(t>=a,np.sin(t-a),0)
ax.plot(t,delayed,c=CYAN,lw=3.5,label=r'$u_a(t)f(t-a)$');ax.axvline(a,c=GOLD,ls='--',lw=2)
ax.axvspan(0,a,color=RED,alpha=.08);ax.annotate('delay $a$',xy=(a,-.65),xytext=(.6,-.65),c=GOLD,arrowprops={'arrowstyle':'<->','color':GOLD,'lw':1.8})
ax.set(xlim=(0,9),ylim=(-1.15,1.15));ax_style(ax);ax.legend(frameon=False,labelcolor=FG)
save(fig,'08_time_shift.png')

# delta approximating pulse
fig,ax=plt.subplots(figsize=(10.7,5.8));a=3.0
for ep,col in [(1.3,PURPLE),(.75,CYAN),(.35,GOLD)]:
    ax.plot([a-ep/2,a-ep/2,a+ep/2,a+ep/2],[0,1/ep,1/ep,0],c=col,lw=3,label=rf'$\varepsilon={ep:.2f}$')
ax.axhline(0,c=GRID,lw=1.5);ax.set(xlim=(0,6),ylim=(0,3.35));ax_style(ax,ylab='amplitude')
ax.text(4.05,2.05,r'$\mathrm{area}=1$',c=FG,fontsize=18)
ax.legend(frameon=False,labelcolor=FG)
save(fig,'09_dirac.png')

# projectile velocity/position
fig,ax=plt.subplots(figsize=(10.7,5.8));t=np.linspace(0,7,500);v0=2;k=1;m=1
vel=v0*np.exp(-k*t/m);pos=(m*v0/k)*(1-np.exp(-k*t/m))
ax.plot(t,vel,c=CYAN,lw=3.3,label=r'$v(t)=v_0e^{-kt/m}$');ax.plot(t,pos,c=GOLD,lw=3.3,label=r'$x(t)=\frac{mv_0}{k}(1-e^{-kt/m})$')
ax.set(xlim=(0,7),ylim=(0,2.3));ax_style(ax);ax.legend(frameon=False,labelcolor=FG)
save(fig,'10_impulse_motion.png')

# convolution moving overlap for 2 unit rectangles
fig,(ax,ax2)=plt.subplots(2,1,figsize=(11.3,6.0),sharex=True,gridspec_kw={'height_ratios':[1,1]})
t=1.45;x=np.linspace(-.4,3.2,1200)
f=((x>=0)&(x<=1)).astype(float);gshift=((x>=t-1)&(x<=t)).astype(float)
ax.plot(x,f,c=CYAN,lw=3,label=r'$f(\tau)$');ax.plot(x,gshift,c=GOLD,lw=3,label=r'$g(t-\tau)$');ax.fill_between(x,0,np.minimum(f,gshift),color=GREEN,alpha=.42)
ax.set(xlim=(-.3,3.2),ylim=(-.05,1.25));ax_style(ax,xlab='',ylab='height');ax.legend(frameon=False,labelcolor=FG,loc='upper right',ncol=2)
tt=np.linspace(0,2.8,400);conv=np.maximum(0,1-np.abs(tt-1));ax2.plot(tt,conv,c=GREEN,lw=3.2)
ax2.axvline(t,c=GOLD,ls='--',lw=1.8);ax2.scatter([t],[np.interp(t,tt,conv)],c=GOLD,s=95)
ax2.set(xlim=(-.3,3.2),ylim=(-.05,1.22));ax_style(ax2,ylab=r'$(f*g)(t)$')
fig.tight_layout(pad=1.25);save(fig,'11_convolution.png')

# response impulse h and input x output y
fig,ax=plt.subplots(figsize=(10.7,5.7));t=np.linspace(0,9,550)
x=(t>=1).astype(float);h=np.exp(-t)*(t>=0);y=np.where(t<1,0,1-np.exp(-(t-1)))
ax.plot(t,x,c=PURPLE,lw=2.6,label=r'$x(t)=u(t-1)$');ax.plot(t,h,c=CYAN,lw=2.7,label=r'$h(t)=e^{-t}u(t)$');ax.plot(t,y,c=GOLD,lw=3.2,label=r'$y(t)=(x*h)(t)$')
ax.set(xlim=(0,9),ylim=(-.1,1.2));ax_style(ax);ax.legend(frameon=False,labelcolor=FG,ncol=1,loc='lower right')
save(fig,'12_system.png')

# steady state damped forced
fig,ax=plt.subplots(figsize=(10.7,5.8));t=np.linspace(0,10,750)
trans=.5*np.exp(-t);steady=.5*(np.sin(t)-np.cos(t));total=trans+steady
ax.plot(t,trans,c=GREEN,lw=2.3,ls='--',label='transient')
ax.plot(t,steady,c=PURPLE,lw=2.3,label='steady state')
ax.plot(t,total,c=GOLD,lw=3,label='total response')
ax.set(xlim=(0,10),ylim=(-.85,.85));ax_style(ax);ax.legend(frameon=False,labelcolor=FG)
save(fig,'13_steady.png')

# short MP4 preview animations for 4 key concepts
FPS=18
# Euler movie
fig,ax=plt.subplots(figsize=(8,4.5));th=np.linspace(0,2*np.pi,350);ax.plot(np.cos(th),np.sin(th),c=GRID,lw=2)
ax.axhline(0,c=GRID);ax.axvline(0,c=GRID);arr=ax.plot([],[],c=GOLD,lw=3.5)[0];trace=ax.plot([],[],c=CYAN,lw=2,alpha=.8)[0];dot=ax.scatter([],[],c=GOLD,s=70)
ax.set(xlim=(-1.25,1.25),ylim=(-1.2,1.2),aspect='equal');ax.set_xticks([]);ax.set_yticks([])
angles=np.linspace(0,2*np.pi,78)
def euler_frame(i):
 a=angles[i];arr.set_data([0,np.cos(a)],[0,np.sin(a)]);trace.set_data(np.cos(angles[:i+1]),np.sin(angles[:i+1]));dot.set_offsets([[np.cos(a),np.sin(a)]])
movie(fig,euler_frame,78,'euler_rotation.mp4')

# decay and oscillation movie
fig,ax=plt.subplots(figsize=(8,4.5));tt=np.linspace(0,8,300)
ax.plot(tt,np.exp(-.25*tt),c=GRID,ls='--');ax.plot(tt,-np.exp(-.25*tt),c=GRID,ls='--');line=ax.plot([],[],c=CYAN,lw=3)[0];dot=ax.scatter([],[],c=GOLD,s=70);ax.set(xlim=(0,8),ylim=(-1.1,1.1));ax_style(ax)
def modal_frame(i):
 j=1+int((len(tt)-1)*i/83);xx=tt[:j];yy=np.exp(-.25*xx)*np.cos(3.2*xx);line.set_data(xx,yy);dot.set_offsets([[xx[-1],yy[-1]]])
movie(fig,modal_frame,84,'complex_mode.mp4')

# Dirac rectangular pulse shrinking
fig,ax=plt.subplots(figsize=(8,4.5));ax.axhline(0,c=GRID,lw=2);line=ax.plot([],[],c=GOLD,lw=3.5)[0]
ax.set(xlim=(0,6),ylim=(0,6));ax_style(ax,ylab='height')
def delta_frame(i):
 ep=1.4 - (i/83)*1.2; a=3;line.set_data([a-ep/2,a-ep/2,a+ep/2,a+ep/2],[0,1/ep,1/ep,0])
movie(fig,delta_frame,84,'dirac_limit.mp4')

# time shift moving sine
fig,ax=plt.subplots(figsize=(8,4.5));x=np.linspace(0,10,500);base=ax.plot(x,np.sin(x),c=GRID,lw=2)[0]
line=ax.plot([],[],c=CYAN,lw=3)[0];vline=ax.axvline(0,c=GOLD,ls='--',lw=1.5)
ax.set(xlim=(0,10),ylim=(-1.2,1.2));ax_style(ax)
def shift_frame(i):
 a=(i/83)*4;line.set_data(x,np.where(x>=a,np.sin(x-a),0));vline.set_xdata([a,a])
movie(fig,shift_frame,84,'time_shift.mp4')

# convolution sweep movie
fig,(ax,ax2)=plt.subplots(2,1,figsize=(8.0,5.0),sharex=True);x=np.linspace(-.4,3.0,1000)
f=((x>=0)&(x<=1)).astype(float);ax.plot(x,f,c=CYAN,lw=3);moving=ax.plot([],[],c=GOLD,lw=3)[0]
shaded=[None];ts=np.linspace(0,2.25,85);cv=np.maximum(0,1-np.abs(ts-1));ax2.plot(ts,cv,c=GREEN,lw=3)
pt=ax2.scatter([],[],c=GOLD,s=85)
for a in [ax,ax2]: a.set(xlim=(-.3,2.8),ylim=(-.05,1.2));ax_style(a)
fig.tight_layout(pad=1.8)
def conv_frame(i):
 t=ts[i];g=((x>=t-1)&(x<=t)).astype(float);moving.set_data(x,g);pt.set_offsets([[t,cv[i]]]);
 if shaded[0] is not None: shaded[0].remove()
 shaded[0]=ax.fill_between(x,0,np.minimum(f,g),color=GREEN,alpha=.35)
movie(fig,conv_frame,85,'convolution_sweep.mp4')
print('generated',len(list(AS.glob('*.png'))),'images,',len(list(AN.glob('*.mp4'))),'videos')
