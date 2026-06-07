---
name: lines-arrows-and-labels
description: Derived connectors and labels for stable snapshots
metadata:
  tags: line, arrow, dashedline, brace, label, connector
---

# Lines, Arrows, And Labels

Use connectors only when they clarify a relationship. Derive their endpoints
from the objects or coordinate system they describe, after those targets are in
their final snapshot positions.

Use edge points such as `get_left()` and `get_right()` for nearby objects, and
use `axes.c2p(...)` for graph annotations. Offset labels from connector shafts
and tips, keep labels short, and group each connector with its label.

For consecutive transform snapshots, rebuild connectors and labels from the
target snapshot's geometry. Keep corresponding connector groups in stable child
slots so they transform with the visual system.
