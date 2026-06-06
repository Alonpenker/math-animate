from pathlib import Path
from uuid import UUID

from .categories import ExampleCategory, RuleCategory, SkillCategory, TemplateCategory
from schemas import KnowledgeDocumentSeed, KnowledgeType


LLMKNOWLEDGE_DIR = Path(__file__).resolve().parent


def read_knowledge_file(path: str) -> str:
    return (LLMKNOWLEDGE_DIR / path).read_text(encoding="utf-8")


REGISTRY: list[KnowledgeDocumentSeed] = [
    KnowledgeDocumentSeed(
        document_id=UUID("2626829d-bee5-51ff-94f4-92d7bd78c910"),
        doc_type=KnowledgeType.SKILL,
        priority="core",
        title="Manim Skill Overview",
        category=SkillCategory.CORE,
        tags=[],
        path="manim_skill/SKILL.md",
    ),
    KnowledgeDocumentSeed(
        document_id=UUID("4ea2e34e-32c1-58ae-9060-8ae705d0eb3c"),
        doc_type=KnowledgeType.RULE,
        priority="recommended",
        title="Layout Composition",
        category=RuleCategory.VISUAL_LAYOUT,
        tags=["layout", "composition", "frame", "positioning", "readability"],
        path="manim_skill/rules/layout-composition.md",
    ),
    KnowledgeDocumentSeed(
        document_id=UUID("7a2dc7df-0a12-4b31-bd74-9c3bd0fd3a21"),
        doc_type=KnowledgeType.RULE,
        priority="core",
        title="Visual Kit API",
        category=RuleCategory.VISUAL_LAYOUT,
        tags=["visual-kit", "safe-scene", "templates", "helpers", "layout"],
        path="manim_skill/rules/visual-kit-api.md",
    ),
    KnowledgeDocumentSeed(
        document_id=UUID("9223951a-5446-5627-b190-4fd973b632ee"),
        doc_type=KnowledgeType.RULE,
        priority="recommended",
        title="Animation Patterns",
        category=RuleCategory.GENERAL,
        tags=["animation", "animate", "transform", "timing", "laggedstart"],
        path="manim_skill/rules/animation-patterns.md",
    ),
    KnowledgeDocumentSeed(
        document_id=UUID("46db4ed5-18a1-5750-8449-673c163b043a"),
        doc_type=KnowledgeType.RULE,
        priority="recommended",
        title="Visual Styling",
        category=RuleCategory.GENERAL,
        tags=["colors", "styling", "contrast", "fill", "stroke", "opacity"],
        path="manim_skill/rules/visual-styling.md",
    ),
    KnowledgeDocumentSeed(
        document_id=UUID("b71ee4c4-d184-5e81-a25f-fd579ebb6303"),
        doc_type=KnowledgeType.RULE,
        priority="recommended",
        title="Mobject Layout Basics",
        category=RuleCategory.VISUAL_LAYOUT,
        tags=["mobject", "vgroup", "group", "arrange", "positioning", "layout"],
        path="manim_skill/rules/mobject-layout-basics.md",
    ),
    KnowledgeDocumentSeed(
        document_id=UUID("b99f64e9-0553-5ba8-a3ce-f3b4ff7427d0"),
        doc_type=KnowledgeType.RULE,
        priority="recommended",
        title="Axes and Graphing",
        category=RuleCategory.GENERAL,
        tags=["axes", "numberplane", "graphing", "plot", "coordinates"],
        path="manim_skill/rules/axes-and-graphing.md",
    ),
    KnowledgeDocumentSeed(
        document_id=UUID("54abc614-55a9-56f7-b4d0-d15119e80565"),
        doc_type=KnowledgeType.RULE,
        priority="recommended",
        title="Lines, Arrows, and Labels",
        category=RuleCategory.LAYOUT_SAFETY,
        tags=["lines", "arrows", "labels", "brace", "connector", "overlap"],
        path="manim_skill/rules/lines-arrows-and-labels.md",
    ),
    KnowledgeDocumentSeed(
        document_id=UUID("57f68508-2a7b-5bf9-9e3c-6248c45443b8"),
        doc_type=KnowledgeType.RULE,
        priority="recommended",
        title="Geometry Shapes and Labels",
        category=RuleCategory.GEOMETRY,
        tags=["geometry", "shapes", "polygon", "angle", "labels"],
        path="manim_skill/rules/geometry-shapes-and-labels.md",
    ),
    KnowledgeDocumentSeed(
        document_id=UUID("fcfe4aa1-c79d-504d-8178-4e1a91c6a2d1"),
        doc_type=KnowledgeType.RULE,
        priority="recommended",
        title="Camera and 3D",
        category=RuleCategory.GENERAL,
        tags=["camera", "movingcamerascene", "threedscene", "3d", "zoom"],
        path="manim_skill/rules/camera-and-3d.md",
    ),
    KnowledgeDocumentSeed(
        document_id=UUID("383001f1-3d38-5081-b94b-797a0d7aba2a"),
        doc_type=KnowledgeType.RULE,
        priority="recommended",
        title="Educational Storyboarding",
        category=RuleCategory.GENERAL,
        tags=["educational", "storyboarding", "scene-architecture"],
        path="manim_skill/rules/educational-storyboarding.md",
    ),
    KnowledgeDocumentSeed(
        document_id=UUID("a7389fbd-0c95-50d2-99c0-ca812d8cd6b0"),
        doc_type=KnowledgeType.RULE,
        priority="recommended",
        title="Equation Transitions",
        category=RuleCategory.GENERAL,
        tags=["equation", "transitions", "algebra", "MathTex"],
        path="manim_skill/rules/equation-transitions.md",
    ),
    KnowledgeDocumentSeed(
        document_id=UUID("bc00b640-c72f-5945-a8dd-aad4b6bebf56"),
        doc_type=KnowledgeType.RULE,
        priority="recommended",
        title="LaTeX",
        category=RuleCategory.GENERAL,
        tags=["latex", "mathtex", "tex", "equation", "formula"],
        path="manim_skill/rules/latex.md",
    ),
    KnowledgeDocumentSeed(
        document_id=UUID("c8836c15-83e3-5c6f-b904-5d942ba2dd2a"),
        doc_type=KnowledgeType.RULE,
        priority="recommended",
        title="Math Visual Clarity",
        category=RuleCategory.GENERAL,
        tags=["math", "visual", "clarity", "emphasis", "readability"],
        path="manim_skill/rules/math-visual-clarity.md",
    ),
    KnowledgeDocumentSeed(
        document_id=UUID("d4e5f6a7-b8c9-0123-def0-234567890123"),
        doc_type=KnowledgeType.RULE,
        priority="recommended",
        title="Matrix Drawing Patterns",
        category=RuleCategory.GEOMETRY,
        tags=["matrix", "matrices", "multiplication", "grid", "highlight"],
        path="manim_skill/rules/matrix-drawing-patterns.md",
    ),
    KnowledgeDocumentSeed(
        document_id=UUID("44b83051-e2d4-59b7-be38-337a6f1d0090"),
        doc_type=KnowledgeType.RULE,
        priority="recommended",
        title="Scenes",
        category=RuleCategory.GENERAL,
        tags=["scenes", "construct", "setup", "render"],
        path="manim_skill/rules/scenes.md",
    ),
    KnowledgeDocumentSeed(
        document_id=UUID("d309e921-1ad5-5dad-a062-408849cd9bce"),
        doc_type=KnowledgeType.RULE,
        priority="recommended",
        title="Text",
        category=RuleCategory.GENERAL,
        tags=["text", "markup", "paragraph", "mathtex", "font-size"],
        path="manim_skill/rules/text.md",
    ),
    KnowledgeDocumentSeed(
        document_id=UUID("bea74d86-fe73-54a3-ab68-2812ecb40f9c"),
        doc_type=KnowledgeType.RULE,
        priority="recommended",
        title="Updaters",
        category=RuleCategory.GENERAL,
        tags=["updaters", "valuetracker", "dynamic", "always_redraw"],
        path="manim_skill/rules/updaters.md",
    ),
    KnowledgeDocumentSeed(
        document_id=UUID("6b2d8d1a-4e5f-4f20-9c31-2a7f90c51101"),
        doc_type=KnowledgeType.TEMPLATE,
        priority="recommended",
        title="Right Triangle Diagram Template",
        category=TemplateCategory.TEMPLATES,
        tags=["right-triangle", "geometry", "labels", "right-angle", "hypotenuse"],
        path="manim_skill/templates/right_triangle_diagram_template.py",
        planning_capability=(
            "A mathematically valid right triangle can be shown with a correct "
            "right-angle marker, outward side labels, and a highlighted "
            "hypotenuse opposite the right angle."
        ),
    ),
    KnowledgeDocumentSeed(
        document_id=UUID("7c3e9e2b-5f60-4a31-8d42-3b8091d62202"),
        doc_type=KnowledgeType.TEMPLATE,
        priority="recommended",
        title="Triangle Comparison Template",
        category=TemplateCategory.TEMPLATES,
        tags=["triangle", "comparison", "right-triangle", "non-right-triangle"],
        path="manim_skill/templates/triangle_comparison_template.py",
        planning_capability=(
            "A right triangle and a non-right triangle can be compared side by "
            "side with correct labels and clear valid or invalid emphasis."
        ),
    ),
    KnowledgeDocumentSeed(
        document_id=UUID("8d4faf3c-6071-4b42-9e53-4c91a2e73303"),
        doc_type=KnowledgeType.TEMPLATE,
        priority="recommended",
        title="Squares On Triangle Sides Template",
        category=TemplateCategory.TEMPLATES,
        tags=["triangle", "squares", "area", "geometry", "labels"],
        path="manim_skill/templates/squares_on_triangle_sides_template.py",
        planning_capability=(
            "Squares can be constructed outward from every side of a valid "
            "right triangle with correct area labels and no inward overlap."
        ),
    ),
    KnowledgeDocumentSeed(
        document_id=UUID("3d8f9c2a-45f2-5525-92f5-2f1e8b94b6ad"),
        doc_type=KnowledgeType.TEMPLATE,
        priority="recommended",
        title="Pythagorean Area Template",
        category=TemplateCategory.TEMPLATES,
        tags=["pythagorean", "geometry", "template", "area-proof"],
        path="manim_skill/templates/pythagorean_area_template.py",
        planning_capability=(
            "Four identical right triangles can be rearranged inside the same "
            "outer square, first revealing one central square and then two "
            "smaller squares, so the unchanged area visually proves their "
            "relationship."
        ),
    ),
    KnowledgeDocumentSeed(
        document_id=UUID("f6a7b8c9-d0e1-2345-f012-456789012345"),
        doc_type=KnowledgeType.EXAMPLE,
        priority="recommended",
        title="Derivatives From Limits",
        category=ExampleCategory.MATHEMATICAL_PROOF,
        tags=["calculus", "derivatives", "limits", "slope", "tangent"],
        path="manim_skill/examples/derivatives_from_limits.py",
    ),
    KnowledgeDocumentSeed(
        document_id=UUID("a7b8c9d0-e1f2-3456-0123-567890123456"),
        doc_type=KnowledgeType.EXAMPLE,
        priority="recommended",
        title="Function Transformations",
        category=ExampleCategory.VISUALIZATION,
        tags=["functions", "transformations", "graphing", "shift", "stretch"],
        path="manim_skill/examples/function_transformations.py",
    ),
    KnowledgeDocumentSeed(
        document_id=UUID("b8c9d0e1-f2a3-4567-1234-678901234567"),
        doc_type=KnowledgeType.EXAMPLE,
        priority="recommended",
        title="Matrix Multiplication",
        category=ExampleCategory.VISUALIZATION,
        tags=["matrix", "multiplication", "linear-algebra", "dot-product"],
        path="manim_skill/examples/matrix_multiplication.py",
    ),
    KnowledgeDocumentSeed(
        document_id=UUID("c9d0e1f2-a3b4-5678-2345-789012345678"),
        doc_type=KnowledgeType.EXAMPLE,
        priority="recommended",
        title="External Circle Tangent Construction",
        category=ExampleCategory.CONSTRUCTION,
        tags=["geometry", "circle", "tangent", "construction", "compass"],
        path="manim_skill/examples/external_circle_tangent_construction.py",
    ),
]

REGISTRY_BY_ID: dict[UUID, KnowledgeDocumentSeed] = {
    entry.document_id: entry for entry in REGISTRY
}

CORE_DOCUMENTS: list[KnowledgeDocumentSeed] = [
    entry for entry in REGISTRY if entry.priority == "core"
]
