---
name: camera-and-3d
description: MovingCameraScene, camera frame animation, ThreeDScene, and sparse 3D objects
metadata:
  tags: camera, movingcamerascene, threedscene, 3d, zoom, pan
---

# Camera And 3D

Use camera movement and 3D only when they help the viewer understand structure
or motion. Keep scenes sparse.

## MovingCameraScene

Use `MovingCameraScene` for zooms and pans in 2D:

```python
class ZoomScene(MovingCameraScene):
    def construct(self):
        diagram = VGroup(...)
        self.add(diagram)
        self.camera.frame.save_state()
        self.play(self.camera.frame.animate.scale(0.55).move_to(target))
        self.play(Restore(self.camera.frame))
```

Save and restore the frame when the zoom is temporary. Keep labels readable at
the zoomed scale.

## Zoom And Pan

Move the camera to reveal detail, then return to the full context. Avoid camera
motion while many unrelated objects are changing.

```python
self.play(self.camera.frame.animate.set(width=4).move_to(detail_group))
self.wait(0.4)
self.play(Restore(self.camera.frame))
```

## ThreeDScene

Use `ThreeDScene` for genuine spatial relationships:

```python
class ThreeDExample(ThreeDScene):
    def construct(self):
        axes = ThreeDAxes(x_range=[-2, 2], y_range=[-2, 2], z_range=[-1, 3])
        cube = Cube(side_length=1.4, fill_opacity=0.35)
        self.set_camera_orientation(phi=65 * DEGREES, theta=-45 * DEGREES)
        self.play(Create(axes), FadeIn(cube))
```

Use `set_camera_orientation` before showing the main 3D objects. Use
`move_camera` for a meaningful change in perspective:

```python
self.move_camera(phi=70 * DEGREES, theta=20 * DEGREES, run_time=1.5)
```

## Sparse 3D Objects

Common 3D mobjects include `ThreeDAxes`, `Surface`, `Sphere`, `Cube`,
`Prism`, `Line3D`, and `Arrow3D`. Prefer one main 3D object plus a few labels or
guides. Too many semi-transparent surfaces and axes labels quickly become hard
to read.

If a 2D diagram explains the idea more clearly, do not use 3D.
