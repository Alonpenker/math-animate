---
name: animation-patterns
description: Safe snapshot transitions that make mathematical changes visible
metadata:
  tags: animation, snapshot, show, transform, continuity, timing
---

# Animation Patterns

Each subscene owns one complete visual snapshot. Use `show` when the previous
idea should leave before the new snapshot appears. Use `transform` when visible
continuity helps explain how the current snapshot becomes the next one.
Template-owned actions animate sequential changes within the newly shown or
transformed snapshot. A subscene may contain multiple related actions when they
develop one teaching idea on the same visual setup.

## Compatible Transform Snapshots

Whole-snapshot transforms pair children by semantic order. Across consecutive
transform snapshots:

- Keep persistent objects in the same child slots.
- Keep unchanged context, such as axes or an outer frame, geometrically
  identical.
- Move an object by placing its corresponding target child at the intended new
  position.
- Move attached labels and markers with the object they describe.
- Keep optional content in stable placeholder slots instead of changing the
  structure unpredictably.

Use `show` rather than `transform` when the snapshots do not represent the same
visual system.

## Readable Motion

Each transform should communicate one dominant change. Separate unrelated
changes into later subscenes. Hold each completed snapshot briefly so the viewer
can understand the resulting state.

Build a template that receives an action in its lesson-appropriate state
immediately before that action runs. The action must produce an observable
change from that state, so do not build the template with the action's target
state already applied. Starting states may use any valid values required by the
lesson, not only template defaults. For sequential actions on one template,
each action starts from the state left by the previous action.

Temporary arrows, highlights, and guides belong inside the snapshot that needs
them. Remove them in the next snapshot by replacing their stable slots with
invisible placeholders.
