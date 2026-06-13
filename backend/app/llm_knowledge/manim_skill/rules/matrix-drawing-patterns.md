---
name: matrix-drawing-patterns
description: Structured matrix snapshots and compatible highlights
metadata:
  tags: matrix, matrices, multiplication, grid, highlight, cells
---

# Matrix Drawing Patterns

Use `Matrix` or `MobjectMatrix` for standard matrices. Keep brackets, entries,
labels, and dimensions together as one semantic matrix object. Scale large
matrices before placing them in a snapshot.

For multiplication walkthroughs, create one snapshot per active row, active
column, and result cell. Keep matrices and operators in stable child slots, and
place row, column, result-cell, connector, and formula highlights in consistent
slots across snapshots.

Only the active highlights and computed result should change between consecutive
snapshots. Keep sufficient spacing for operators, highlights, and short
connectors.
