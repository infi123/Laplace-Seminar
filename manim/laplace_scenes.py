"""Mathematical animations for the Laplace-transform seminar.

Manim Community Edition 0.19.x. Render e.g.:
    manim -qh manim/laplace_scenes.py EulerRotation

Mathematics and symbols are isolated from the Hebrew Beamer typesetting.
These animations are original illustrations, not clips from 3Blue1Brown.
"""
from manim import *
import numpy as np

config.background_color = "#0b1428"
CYAN = "#41c9e8"
GOLD = "#ffcd66"
ROSE = "#fb7185"
MINT = "#7bdcb5"
VIOLET = "#a89af7"
MUTED = "#60708c"


def heading(tex):
    return MathTex(tex, font_size=42, color=WHITE).to_edge(UP)


def simple_axes(x_range, y_range, width=10.3, height=4.5):
    return Axes(
        x_range=x_range,
        y_range=y_range,
        x_length=width,
        y_length=height,
        tips=False,
        axis_config={"include_numbers": False, "color": MUTED, "stroke_width": 2},
    )


class ExponentialDerivative(Scene):
    def construct(self):
        axes = simple_axes([-1.3, 2.5, 1], [0, 11, 2]).shift(DOWN * 0.45)
        curve = axes.plot(lambda x: np.exp(x), x_range=[-1.3, 2.35], color=CYAN)
        tracker = ValueTracker(-.4)
        point = always_redraw(lambda: Dot(axes.c2p(tracker.get_value(), np.exp(tracker.get_value())), color=GOLD))
        tangent = always_redraw(lambda: axes.plot(
            lambda x: np.exp(tracker.get_value()) * (1 + x - tracker.get_value()),
            x_range=[max(-1.3, tracker.get_value() - .8), min(2.5, tracker.get_value() + .8)],
            color=GOLD,
        ))
        eq = heading(r"\frac{d}{dt}e^t=e^t")
        self.play(Write(eq), Create(axes), Create(curve))
        self.play(Create(tangent), FadeIn(point))
        self.play(tracker.animate.set_value(1.7), run_time=5, rate_func=linear)
        self.wait(.5)


class EulerRotation(Scene):
    def construct(self):
        plane = NumberPlane(x_range=[-1.5, 1.5, 1], y_range=[-1.4, 1.4, 1],
                            x_length=6.0, y_length=5.5,
                            background_line_style={"stroke_color": MUTED, "stroke_opacity": .3})
        plane.shift(DOWN * .4)
        unit = Circle(radius=plane.x_axis.unit_size, color=CYAN).move_to(plane.c2p(0, 0))
        theta = ValueTracker(.25)
        vec = always_redraw(lambda: Arrow(plane.c2p(0, 0), plane.c2p(np.cos(theta.get_value()), np.sin(theta.get_value())),
                                         buff=0, color=GOLD, stroke_width=6))
        point = always_redraw(lambda: Dot(plane.c2p(np.cos(theta.get_value()), np.sin(theta.get_value())), color=GOLD))
        horizontal = always_redraw(lambda: DashedLine(
            plane.c2p(0, 0), plane.c2p(np.cos(theta.get_value()), 0), color=CYAN))
        vertical = always_redraw(lambda: DashedLine(
            plane.c2p(np.cos(theta.get_value()), 0),
            plane.c2p(np.cos(theta.get_value()), np.sin(theta.get_value())), color=VIOLET))
        formula = heading(r"e^{it}=\cos t+i\sin t")
        self.play(Create(plane), Create(unit), Write(formula))
        self.play(GrowArrow(vec), FadeIn(point), Create(horizontal), Create(vertical))
        self.play(theta.animate.set_value(TAU * 2 + .25), run_time=8, rate_func=linear)
        self.wait(.4)


class ComplexMode(Scene):
    def construct(self):
        ax = simple_axes([0, 9, 1], [-1.2, 1.2, .5], width=11.2, height=4.25).shift(DOWN * .55)
        env_plus = ax.plot(lambda t: np.exp(-.28 * t), color=GOLD)
        env_minus = ax.plot(lambda t: -np.exp(-.28 * t), color=GOLD)
        tracker = ValueTracker(.05)
        curve = always_redraw(lambda: ax.plot(
            lambda t: np.exp(-.28*t) * np.cos(3.3*t),
            x_range=[0, max(.06, tracker.get_value())], color=CYAN))
        point = always_redraw(lambda: Dot(ax.c2p(tracker.get_value(),
                                            np.exp(-.28*tracker.get_value()) * np.cos(3.3*tracker.get_value())), color=CYAN))
        self.play(Write(heading(r"e^{(\sigma+i\omega)t}=e^{\sigma t}(\cos\omega t+i\sin\omega t)")))
        self.play(Create(ax), Create(env_plus), Create(env_minus))
        self.add(curve, point)
        self.play(tracker.animate.set_value(9), run_time=7, rate_func=linear)
        self.wait(.3)


class ModesSPlane(Scene):
    def construct(self):
        plane = NumberPlane(x_range=[-2, 2, 1], y_range=[-3, 3, 1],
                            x_length=6.7, y_length=5.6,
                            background_line_style={"stroke_color": MUTED, "stroke_opacity": .25}).shift(DOWN*.3)
        labels = [(-1.2, 1.4), (-.5, 2.2), (.35, 1), (-.7, -1.8)]
        dots=VGroup(*[Dot(plane.c2p(x,y), radius=.09, color=c) for (x,y),c in
                      zip(labels, [CYAN,GOLD,ROSE,VIOLET])])
        self.play(Create(plane), Write(heading(r"s=\sigma+i\omega")))
        self.play(LaggedStart(*[GrowFromCenter(d) for d in dots], lag_ratio=.3))
        left = MathTex(r"\sigma<0:\;\mathrm{decay}", color=CYAN, font_size=33).to_corner(DL)
        right = MathTex(r"\sigma>0:\;\mathrm{growth}", color=ROSE, font_size=33).to_corner(DR)
        self.play(FadeIn(left), FadeIn(right)); self.wait(2)


class LaplaceWeighting(Scene):
    def construct(self):
        ax = simple_axes([0, 8, 1], [0, 2.1, .5], width=10.8, height=4.5).shift(DOWN*.45)
        curve = ax.plot(lambda t: 1+.55*np.sin(2.3*t)+.18*np.sin(4.6*t), color=VIOLET)
        weighted = ax.plot(lambda t: (1+.55*np.sin(2.3*t)+.18*np.sin(4.6*t))*np.exp(-.36*t), color=CYAN)
        kernel = ax.plot(lambda t: np.exp(-.36*t), color=GOLD)
        self.play(Write(heading(r"F(s)=\int_0^\infty e^{-st}f(t)\,dt")))
        self.play(Create(ax), Create(curve)); self.play(Create(kernel)); self.play(ReplacementTransform(curve.copy(), weighted), run_time=2.5)
        self.wait(1)


class FirstShift(Scene):
    def construct(self):
        plane = NumberPlane(x_range=[-3,3,1], y_range=[-2,2,1], x_length=10, y_length=5,
                            background_line_style={"stroke_color": MUTED, "stroke_opacity":.25})
        plane.shift(DOWN*.45)
        old = VGroup(Dot(plane.c2p(-1,1), color=CYAN), Dot(plane.c2p(-1,-1), color=CYAN))
        new = VGroup(Dot(plane.c2p(.6,1), color=GOLD), Dot(plane.c2p(.6,-1), color=GOLD))
        self.play(Write(heading(r"\mathcal L\{e^{at}f(t)\}(s)=F(s-a)")))
        self.play(Create(plane), FadeIn(old))
        self.play(Transform(old,new),run_time=3)
        self.wait(1)


class DelayedInput(Scene):
    def construct(self):
        ax = simple_axes([0,10,1],[-1.25,1.25,.5],width=11,height=4.6).shift(DOWN*.45)
        original = ax.plot(lambda x: np.sin(x), x_range=[0,10], color=MUTED)
        tau=ValueTracker(0)
        shifted = always_redraw(lambda: ax.plot(
            lambda t: np.sin(t-tau.get_value()) if t >= tau.get_value() else 0,
            x_range=[0,10], color=CYAN))
        onset=always_redraw(lambda: DashedLine(ax.c2p(tau.get_value(),-1.1),ax.c2p(tau.get_value(),1.1), color=GOLD))
        self.play(Write(heading(r"\mathcal L\{u_a(t)f(t-a)\}=e^{-as}F(s)")))
        self.play(Create(ax),Create(original),Create(shifted),Create(onset))
        self.play(tau.animate.set_value(4),run_time=5,rate_func=linear)
        self.wait(.6)


class DiracLimit(Scene):
    def construct(self):
        ax = simple_axes([0,6,1],[0,5,.5],width=10,height=4.6).shift(DOWN*.4)
        epsilon=ValueTracker(1.4)
        a=3
        pulse=always_redraw(lambda: Polygon(
            ax.c2p(a-epsilon.get_value()/2,0),
            ax.c2p(a-epsilon.get_value()/2,1/epsilon.get_value()),
            ax.c2p(a+epsilon.get_value()/2,1/epsilon.get_value()),
            ax.c2p(a+epsilon.get_value()/2,0),
            fill_color=GOLD, fill_opacity=.25, stroke_color=GOLD, stroke_width=4))
        eq = heading(r"\mathrm{height}=\frac1\varepsilon,\quad \mathrm{area}=1")
        self.play(Create(ax),Write(eq),Create(pulse))
        self.play(epsilon.animate.set_value(.25),run_time=6,rate_func=linear)
        self.wait(.8)


class ODESolution(Scene):
    def construct(self):
        ax=simple_axes([0,8,1],[0,1.4,.2],width=10.7,height=4.5).shift(DOWN*.45)
        graph=ax.plot(lambda t: 2*np.exp(-t)-np.exp(-2*t),x_range=[0,8],color=CYAN)
        self.play(Write(heading(r"y(t)=2e^{-t}-e^{-2t}")))
        self.play(Create(ax),Create(graph,run_time=4));self.wait(1)


class ConvolutionSweep(Scene):
    def construct(self):
        top = simple_axes([-.5,3,.5],[0,1.5,.5],width=10.2,height=3.1).shift(UP*.6)
        bot = simple_axes([-.5,3,.5],[0,1.3,.5],width=10.2,height=2.7).shift(DOWN*2.25)
        a=ValueTracker(.1)
        def box_fn(ax,x0,x1,color):
            return VMobject(color=color, stroke_width=4).set_points_as_corners([
                ax.c2p(x0,0),ax.c2p(x0,1),ax.c2p(x1,1),ax.c2p(x1,0)])
        fbox=box_fn(top,0,1,CYAN)
        gbox=always_redraw(lambda:box_fn(top,a.get_value()-1,a.get_value(),GOLD))
        fill=always_redraw(lambda:Polygon(
            top.c2p(max(0,a.get_value()-1),0),
            top.c2p(max(0,a.get_value()-1),1),
            top.c2p(max(0,min(1,a.get_value())),1),
            top.c2p(max(0,min(1,a.get_value())),0),
            color=MINT, fill_opacity=.20, stroke_opacity=0))
        triangle=bot.plot(lambda t: max(0,1-abs(t-1)),x_range=[0,2.3],color=MINT)
        moving_dot=always_redraw(lambda:Dot(bot.c2p(a.get_value(), max(0,1-abs(a.get_value()-1))),color=GOLD))
        self.add(heading(r"(f*g)(t)=\int_0^t f(\tau)g(t-\tau)\,d\tau"))
        self.play(Create(top),Create(bot),Create(fbox),Create(triangle))
        self.add(fill,gbox,moving_dot)
        self.play(a.animate.set_value(2.4),run_time=7,rate_func=linear)
        self.wait(.6)


class ImpulseResponse(Scene):
    def construct(self):
        ax=simple_axes([0,8,1],[0,1.25,.25],width=11,height=4.5).shift(DOWN*.5)
        h=ax.plot(lambda t:np.exp(-t),x_range=[0,8],color=CYAN)
        y=ax.plot(lambda t:0 if t<1 else (1-np.exp(-(t-1))),x_range=[0,8],color=GOLD)
        self.play(Write(heading(r"y(t)=(x*h)(t)")))
        self.play(Create(ax),Create(h));self.play(Create(y),run_time=3);self.wait(.8)


class SteadyState(Scene):
    def construct(self):
        ax=simple_axes([0,10,1],[-.85,.85,.25],width=11,height=4.5).shift(DOWN*.5)
        steady=ax.plot(lambda t:.5*(np.sin(t)-np.cos(t)),color=VIOLET)
        total=ax.plot(lambda t:.5*np.exp(-t)+.5*(np.sin(t)-np.cos(t)),color=GOLD)
        self.play(Write(heading(r"y(t)=y_{\mathrm{transient}}(t)+y_{\mathrm{steady}}(t)")))
        self.play(Create(ax),Create(steady));self.play(Create(total),run_time=3);self.wait(.8)
