# Template Lab

Quick sandbox for visually testing a single template.  
Edit `play.py`, render, watch the video. Repeat.

---

## Workflow

1. **Pick a template** from `../llm_knowledge/manim_skill/templates/`.
2. **Give the LLM the prompt below** (paste in the template source + `visual_kit.py`).
3. **Paste the LLM output** into `play.py`.
4. **Render** (see command below).
5. **Open** `media/videos/play/480p15/PlayScene.mp4`.

---

## LLM prompt template

```
You are filling in a Manim template test scene.

Files attached:
- visual_kit.py          (SafeScene base class — provides show_title, show_main, set_bottom_text, transform_main, play_action, clear_content, fade_out_all)
- <TemplateName>.py      (the template to test — read VALID_STATES and __init__ carefully)

Task:
Rewrite the `construct` method in play.py so it exercises the template across ALL of its VALID_STATES with realistic parameter values, and also calls every animation method the template exposes (e.g. advance_step, set_expression, highlight_formula, or whatever the template provides). Each state should demonstrate at least one animation so the video proves the animations actually work.

Rules:
- Keep the imports at the top (sys.path + visual_kit + the one template class).
- Use SafeScene helpers (show_title / show_main / set_bottom_text) for every scene beat.
- Call self.wait(1) between steps so the video is watchable.
- Do NOT use any other manim primitives outside what the template itself exposes.
- Keep the class name PlayScene.
```

---

## Render command

Run from the `ai_workflow_lab/` directory (or anywhere with the venv active):

```bash
# Fast preview (480p, low quality — good enough for shape checks)
manim -ql template_lab/play.py PlayScene --media_dir template_lab/media

# Full quality (720p) when the shape looks right
manim -qm template_lab/play.py PlayScene --media_dir template_lab/media
```

Output lands in `template_lab/media/` which is git-ignored.
