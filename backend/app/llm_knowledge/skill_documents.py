from pathlib import Path
from uuid import UUID

from app.llm_knowledge.categories import RuleCategory, SkillCategory, TemplateCategory
from app.schemas.knowledge import KnowledgeDocumentSeed, KnowledgeType, TemplateDocumentSeed


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
        document_id=UUID("7a2dc7df-0a12-4b31-bd74-9c3bd0fd3a21"),
        doc_type=KnowledgeType.RULE,
        priority="core",
        title="Visual Kit API",
        category=RuleCategory.VISUAL_LAYOUT,
        tags=["visual-kit", "safe-scene", "templates", "helpers", "layout"],
        path="manim_skill/rules/visual-kit-api.md",
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
        document_id=UUID("d309e921-1ad5-5dad-a062-408849cd9bce"),
        doc_type=KnowledgeType.RULE,
        priority="recommended",
        title="Text",
        category=RuleCategory.GENERAL,
        tags=["text", "markup", "paragraph", "mathtex", "font-size"],
        path="manim_skill/rules/text.md",
    ),
    TemplateDocumentSeed(
        document_id=UUID("e0d7a77c-f1e1-4e99-95a7-6df24d09d0d1"),
        doc_type=KnowledgeType.TEMPLATE,
        priority="recommended",
        title="Equation Template",
        category=TemplateCategory.TEMPLATES,
        tags=["equation", "math", "latex", "expression", "transition"],
        path="manim_skill/templates/equation_template.py",
        planning_capability=(
            "A mathematical expression can be shown alone or developed through "
            "a stable three-line derivation history. New solution steps can "
            "advance the history, while a statements state shows up to three "
            "equally important expressions. A displayed or final formula can "
            "receive a temporary yellow outline highlight."
        ),
    ),
    TemplateDocumentSeed(
        document_id=UUID("14cc02d4-4301-4c9b-a080-09dd819474ad"),
        doc_type=KnowledgeType.TEMPLATE,
        priority="recommended",
        title="Number Line Template",
        category=TemplateCategory.TEMPLATES,
        tags=[
            "number-line",
            "integers",
            "inequalities",
            "intervals",
            "absolute-value",
            "distance",
        ],
        path="manim_skill/templates/number_line_template.py",
        planning_capability=(
            "A configurable number line can show labeled points, open or closed "
            "single or multiple intervals with excluded points, arithmetic movement, "
            "distance between two values, or a center with a fixed radius. An "
            "optional short title can identify what the number line represents."
        ),
    ),
    TemplateDocumentSeed(
        document_id=UUID("fc301da8-1e26-4eed-a566-f9645558dc83"),
        doc_type=KnowledgeType.TEMPLATE,
        priority="recommended",
        title="Function Graph Template",
        category=TemplateCategory.TEMPLATES,
        tags=[
            "functions",
            "graphs",
            "calculus",
            "secant",
            "tangent",
            "area",
            "signed-area",
            "piecewise",
            "intercepts",
        ],
        path="manim_skill/templates/function_graph_template.py",
        planning_capability=(
            "Reliable named function families can be plotted on fixed axes with "
            "marked points, secants, tangents, shaded intervals, intercept "
            "emphasis, or a second comparison graph. A signed-areas state can "
            "preserve constant segments, shade positive regions in teal and "
            "negative regions in red, and label their signed areas."
        ),
    ),
    TemplateDocumentSeed(
        document_id=UUID("49bcf4ce-a2ce-46d1-bb22-e20df320937d"),
        doc_type=KnowledgeType.TEMPLATE,
        priority="recommended",
        title="Matrix Template",
        category=TemplateCategory.TEMPLATES,
        tags=[
            "matrix",
            "matrices",
            "multiplication",
            "row",
            "column",
            "dot-product",
        ],
        path="manim_skill/templates/matrix_template.py",
        planning_capability=(
            "A matrix can be displayed and highlighted by row, column, or cell. "
            "Compatible matrix products can show dimensions, select a row-column "
            "pair, display its dot product, and reveal the computed result cell."
        ),
    ),
    TemplateDocumentSeed(
        document_id=UUID("e9cf8cb7-1456-4c47-9823-c05bb52f41c7"),
        doc_type=KnowledgeType.TEMPLATE,
        priority="recommended",
        title="Linear Transformation Template",
        category=TemplateCategory.TEMPLATES,
        tags=[
            "vector",
            "vectors",
            "linear-transformation",
            "eigenvector",
            "eigenvalue",
            "matrix",
        ],
        path="manim_skill/templates/linear_transformation_template.py",
        planning_capability=(
            "A numeric 2D matrix transformation can show vectors as arrows from "
            "the origin, their transformed images, optional span lines, and an "
            "optional unit square becoming a parallelogram. Comparison and "
            "eigenvector states distinguish vectors that turn from vectors that "
            "remain on their span."
        ),
    ),
    TemplateDocumentSeed(
        document_id=UUID("c8a796a1-272c-43af-a897-37122d9034ed"),
        doc_type=KnowledgeType.TEMPLATE,
        priority="recommended",
        title="Fraction Model Template",
        category=TemplateCategory.TEMPLATES,
        tags=[
            "fraction",
            "fractions",
            "equivalent-fraction",
            "ratio",
            "percentage",
            "area-model",
        ],
        path="manim_skill/templates/fraction_model_template.py",
        planning_capability=(
            "A proper or improper fraction can be represented with partitioned "
            "bars, grids, or circles. Filled parts and completed wholes can be "
            "emphasized, and equivalent fractions can refine the same proportion."
        ),
    ),
    TemplateDocumentSeed(
        document_id=UUID("2920a434-7a1b-4961-bf02-92745fa6290e"),
        doc_type=KnowledgeType.TEMPLATE,
        priority="recommended",
        title="Vector Template",
        category=TemplateCategory.TEMPLATES,
        tags=[
            "vector",
            "vectors",
            "components",
            "addition",
            "subtraction",
            "scalar-multiple",
            "dot-product",
            "projection",
        ],
        path="manim_skill/templates/vector_template.py",
        planning_capability=(
            "Numeric 2D vectors can show components, head-to-tail addition or "
            "subtraction, scalar multiples, dot products, and projections. "
            "Computed resultants and relationships can be revealed and emphasized."
        ),
    ),
    TemplateDocumentSeed(
        document_id=UUID("46de0a97-5095-46f7-8e80-fd7398b5aba3"),
        doc_type=KnowledgeType.TEMPLATE,
        priority="recommended",
        title="Unit Circle Template",
        category=TemplateCategory.TEMPLATES,
        tags=[
            "unit-circle",
            "trigonometry",
            "sine",
            "cosine",
            "reference-angle",
            "quadrants",
        ],
        path="manim_skill/templates/unit_circle_template.py",
        planning_capability=(
            "A unit circle can rotate a radius to a numeric angle, reveal its "
            "coordinate projections and reference triangle, and emphasize the "
            "active quadrant or sine and cosine projections."
        ),
    ),
    TemplateDocumentSeed(
        document_id=UUID("6b2d8d1a-4e5f-4f20-9c31-2a7f90c51101"),
        doc_type=KnowledgeType.TEMPLATE,
        priority="recommended",
        title="Triangle Template",
        category=TemplateCategory.TEMPLATES,
        tags=[
            "triangle",
            "right-triangle",
            "non-right-triangle",
            "geometry",
            "labels",
            "squares",
            "hypotenuse",
            "altitude",
            "median",
            "angle-bisector",
            "area",
            "angle-sum",
            "similarity",
            "congruence",
        ],
        path="manim_skill/templates/triangle_template.py",
        planning_capability=(
            "One independent triangle can preserve the existing right-triangle "
            "and Pythagorean visuals or use reliable general presets with custom "
            "labels, altitudes, medians, angle bisectors, area, angle sums, and "
            "similarity or congruence markings. Comparisons use two instances."
        ),
    ),
    TemplateDocumentSeed(
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
    TemplateDocumentSeed(
        document_id=UUID("2f4a7c93-10de-4b6a-a8d1-93f0c6d27e11"),
        doc_type=KnowledgeType.TEMPLATE,
        priority="recommended",
        title="Function Translation Template",
        category=TemplateCategory.TEMPLATES,
        tags=[
            "functions",
            "graphing",
            "translation",
            "fixed-axes",
            "horizontal-shift",
            "vertical-shift",
        ],
        path="manim_skill/templates/function_translation_template.py",
        planning_capability=(
            "A parent-function graph can move horizontally and vertically on "
            "fixed axes while an optional meaningful anchor point moves with it, "
            "then the original and translated graphs can be compared."
        ),
    ),
]

REGISTRY_BY_ID: dict[UUID, KnowledgeDocumentSeed] = {
    entry.document_id: entry for entry in REGISTRY
}

TEMPLATE_TITLES: tuple[str, ...] = tuple(
    entry.title for entry in REGISTRY if isinstance(entry, TemplateDocumentSeed)
)

CORE_DOCUMENTS: list[KnowledgeDocumentSeed] = [
    entry for entry in REGISTRY if entry.priority == "core"
]
