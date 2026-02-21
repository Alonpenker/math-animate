from manim import *


class RotatingSurface(ThreeDScene):
    def construct(self):
        axes = ThreeDAxes(
            x_range=[-3, 3, 1],
            y_range=[-3, 3, 1],
            z_range=[-1, 1, 0.5],
        )
        surface = Surface(
            lambda u, v: axes.c2p(u, v, np.sin(np.sqrt(u**2 + v**2))),
            u_range=[-3, 3],
            v_range=[-3, 3],
            resolution=(30, 30),
            fill_opacity=0.7,
        )
        surface.set_style(fill_color=[BLUE, GREEN, YELLOW])

        self.set_camera_orientation(phi=60 * DEGREES, theta=-45 * DEGREES)
        self.play(Create(axes), Create(surface))
        self.begin_ambient_camera_rotation(rate=0.3)
        self.wait(6)
        self.stop_ambient_camera_rotation()
        self.wait(1)
