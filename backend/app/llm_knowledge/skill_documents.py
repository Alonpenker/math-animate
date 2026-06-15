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
        document_id=UUID("383001f1-3d38-5081-b94b-797a0d7aba2a"),
        doc_type=KnowledgeType.RULE,
        priority="recommended",
        title="Educational Storyboarding",
        category=RuleCategory.GENERAL,
        tags=["educational", "storyboarding", "scene-architecture"],
        path="manim_skill/rules/educational-storyboarding.md",
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
