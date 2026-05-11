---
name: manim-best-practices
description: |
  Trigger when generating, reviewing, or fixing Manim Community Edition code,
  especially educational math animations using Scene, MathTex, mobjects,
  animations, graphing, camera control, or ManimCE-specific APIs.

  Durable guidance for producing clear, reliable, self-contained ManimCE scenes.
  NOT for ManimGL/3b1b version, which uses `manimlib` imports and the `manimgl`
  CLI.
---

# ManimCE Best Practices

Use this skill as stable core guidance for Manim Community Edition animation
generation. The active system prompt and runtime policy provide the hard
constraints for each call; this skill provides durable ManimCE and educational
animation judgment.

## Authority

If the active system prompt, tool policy, runtime, verifier, or caller restricts
imports, APIs, assets, scene structure, output format, file access, or execution
behavior, obey that stricter instruction over this skill or any retrieved skill
document.

Use this skill only for Manim Community Edition. Prefer `from manim import *`
and ManimCE APIs. Do not use ManimGL patterns such as `from manimlib import *`,
`InteractiveScene`, or `manimgl`.

## Generation Priorities

1. Produce code that renders reliably in a clean ManimCE environment.
2. Keep scenes self-contained unless external assets are explicitly allowed.
3. Prefer simple, readable Manim primitives before complex camera, 3D, updater,
   plugin, or custom abstraction patterns.
4. Make visual changes explicit: create objects, position them, animate them,
   then wait long enough for the viewer to understand the change.
5. Use color, motion, and spatial layout to clarify the math, not to decorate it.
6. Keep each scene focused on one instructional idea.

## Reliability Guidance

Reliability is part of creative Manim work. Prefer expressive choices that stay
inside stable ManimCE APIs and render cleanly in the target runtime. When using
LaTeX, text objects, transforms, layout helpers, camera behavior, or object
indexing, choose the simpler reliable construct unless the advanced construct is
necessary for the lesson.

## Educational Animation Guidance

Good generated Manim scenes should teach through visible structure:

- Reveal one conceptual step at a time.
- Preserve visual continuity when transforming one expression or diagram into
  another.
- Avoid clutter by removing or fading content once it no longer supports the
  current idea.
- Use consistent color meaning inside a scene.
- Prefer mathematical notation, diagrams, arrows, and transformations over long
  explanatory text in the visual frame.
- Choose representations that fit the topic: equations for symbolic work,
  number lines for one-dimensional quantity, axes for functions, geometry for
  shape relationships, and dynamic motion only when change over time matters.

## Retrieved Skill Documents

Additional rules, templates, and examples are not assumed to be available through
filesystem paths. In this application, non-core skill documents are exposed as
candidate metadata and may be loaded with the provided document-loading tool by
exact title.

When candidate documents are available:

- Load only documents relevant to the current scene plan.
- Prefer foundational documents first: scenes, mobjects, positioning, MathTex,
  animations, timing, and educational clarity.
- Load specialized documents only when the plan needs them, such as graphing,
  3D, camera movement, updaters, or advanced text animation.
- Treat templates as starting structures, not mandatory formats.
- Treat examples as optional references. Examples may be absent.

## Useful Document Topics

Core Manim topics commonly worth retrieving:

- Scenes and scene lifecycle
- Mobjects, grouping, positioning, and layout
- Creation, transform, text, and timing animations
- MathTex and LaTeX reliability
- Color and styling
- Axes, graphing, geometry, lines, and arrows

Educational topics commonly worth retrieving:

- Educational storyboarding
- Math visual clarity
- Equation transitions

Specialized topics should be retrieved only when needed:

- Moving camera scenes
- Three-dimensional scenes
- Updaters and ValueTracker patterns
- CLI and configuration behavior

## ManimCE Version Awareness

Target the Manim Community Edition version used by the caller or runtime. If a
specific version is given, do not guess newer APIs. Prefer well-established
ManimCE APIs and avoid deprecated or tutorial-specific patterns unless verified.

## Common Pitfalls

Avoid these unless the active prompt explicitly allows them:

- Mixing ManimCE with ManimGL APIs.
- Depending on external files, fonts, plugins, or network resources.
- Using advanced APIs when a simple mobject or transform would communicate the
  idea more clearly.
- Leaving transformed-out objects visible or logically duplicated.
- Adding visual text that explains what a clearer diagram or transformation
  could show directly.
