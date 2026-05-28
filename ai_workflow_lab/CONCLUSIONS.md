# AI Workflow Lab Notes

Quick notes for tracking what we tried, what worked, and what to try next.

## Current Best

- Workflow:
- Why:
- Main problem:
- Next thing to try:

## Runs

| Run | What changed | Result | Keep? |
| --- | --- | --- | --- |
| `runs/e2e` | Fake API calls, real verify/render | Renders after 1 fix | Keep as plumbing check |

Use simple results like:

- `great`
- `better`
- `same`
- `worse`
- `failed`
- `needs another run`

## Notes Template

Copy this when a run needs more detail:

```markdown
### <run-name>

Changed:
Result:
Liked:
Did not like:
Conclusion:
Next:
```

## What To Look At

- `summary.json`: status, fix attempts, token usage.
- `plan.txt`: did the idea make sense before code?
- `attempts/*/code.py`: what broke and what got fixed?
- Final video: did it actually teach better?

## Rules Of Thumb

- Fewer fix attempts is good, but not if the video gets worse.
- Pretty output is not enough if the code is fragile.
- E2E checks plumbing only. It does not prove the AI workflow is good.
- Do not keep a change just because one run got lucky.
