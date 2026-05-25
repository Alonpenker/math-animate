from enum import Enum
from pathlib import Path
from uuid import UUID

class RuleCategory(str, Enum):
    LAYOUT_SAFETY = "layout-safety"    # text framing, arrow placement, overlap
    GEOMETRY = "geometry"              # polygon labeling, matrices, shapes
    VISUAL_LAYOUT = "visual-layout"   # composition, frame structure, positioning
    GENERAL = "general"                # all other Manim API and rules


class ExampleCategory(str, Enum):
    MATHEMATICAL_PROOF = "mathematical-proof"   # Pythagorean, derivatives, theorems
    VISUALIZATION = "visualization"             # function graphs, transformations
    CONSTRUCTION = "construction"               # geometric constructions

class TemplateCategory(str, Enum):
    TEMPLATES = "templates"


from app.schemas.knowledge import KnowledgeDocumentSeed, KnowledgeType  

LLMKNOWLEDGE_DIR = Path(__file__).resolve().parent


def read_knowledge_file(path: str) -> str:
    return (LLMKNOWLEDGE_DIR / path).read_text(encoding="utf-8")


REGISTRY: list[KnowledgeDocumentSeed] = [
    KnowledgeDocumentSeed(
        document_id=UUID("2626829d-bee5-51ff-94f4-92d7bd78c910"),
        doc_type=KnowledgeType.SKILL,
        priority="core",
        title="Manim Skill Overview",
        category="core",
        tags=[],
        path="manim_skill/SKILL.md",
    ),
    KnowledgeDocumentSeed(
        document_id=UUID("4ea2e34e-32c1-58ae-9060-8ae705d0eb3c"),
        doc_type=KnowledgeType.RULE,
        priority="core",
        title="Layout Composition",
        category=RuleCategory.VISUAL_LAYOUT,
        tags=["layout", "composition", "frame", "positioning", "readability"],
        path="manim_skill/rules/layout-composition.md",
    ),
    KnowledgeDocumentSeed(
        document_id=UUID("bd9bb577-81f5-5ce1-969d-5a864f43c62e"),
        doc_type=KnowledgeType.RULE,
        priority="recommended",
        title="3D",
        category=RuleCategory.GENERAL,
        tags=["3d"],
        path="manim_skill/rules/3d.md",
    ),
    KnowledgeDocumentSeed(
        document_id=UUID("b03f4678-eb4b-56b5-b926-edf60886287a"),
        doc_type=KnowledgeType.RULE,
        priority="recommended",
        title="Animation Groups",
        category=RuleCategory.GENERAL,
        tags=["animation", "groups"],
        path="manim_skill/rules/animation-groups.md",
    ),
    KnowledgeDocumentSeed(
        document_id=UUID("7b007669-d641-5f9b-958b-f69bc520c804"),
        doc_type=KnowledgeType.RULE,
        priority="recommended",
        title="Animations",
        category=RuleCategory.GENERAL,
        tags=["animations"],
        path="manim_skill/rules/animations.md",
    ),
    KnowledgeDocumentSeed(
        document_id=UUID("713b7b88-9443-5fbf-ab4b-03e64c0af589"),
        doc_type=KnowledgeType.RULE,
        priority="recommended",
        title="Axes",
        category=RuleCategory.GENERAL,
        tags=["axes"],
        path="manim_skill/rules/axes.md",
    ),
    KnowledgeDocumentSeed(
        document_id=UUID("e8614981-b80e-5815-9cb2-ae40e0699378"),
        doc_type=KnowledgeType.RULE,
        priority="recommended",
        title="Camera",
        category=RuleCategory.GENERAL,
        tags=["camera"],
        path="manim_skill/rules/camera.md",
    ),
    KnowledgeDocumentSeed(
        document_id=UUID("8ab50393-3dac-51a1-86fe-ae20016739b4"),
        doc_type=KnowledgeType.RULE,
        priority="recommended",
        title="CLI",
        category=RuleCategory.GENERAL,
        tags=["cli"],
        path="manim_skill/rules/cli.md",
    ),
    KnowledgeDocumentSeed(
        document_id=UUID("54cdc928-a0c9-567c-9dc6-b250227c7437"),
        doc_type=KnowledgeType.RULE,
        priority="recommended",
        title="Colors",
        category=RuleCategory.GENERAL,
        tags=["colors"],
        path="manim_skill/rules/colors.md",
    ),
    KnowledgeDocumentSeed(
        document_id=UUID("a7c751e6-f9ff-58e4-addb-2cbe3bf6fd76"),
        doc_type=KnowledgeType.RULE,
        priority="recommended",
        title="Config",
        category=RuleCategory.GENERAL,
        tags=["config"],
        path="manim_skill/rules/config.md",
    ),
    KnowledgeDocumentSeed(
        document_id=UUID("e2c5cf48-c2f9-516a-9b10-6f3813689e02"),
        doc_type=KnowledgeType.RULE,
        priority="recommended",
        title="Creation Animations",
        category=RuleCategory.GENERAL,
        tags=["creation", "animations"],
        path="manim_skill/rules/creation-animations.md",
    ),
    KnowledgeDocumentSeed(
        document_id=UUID("383001f1-3d38-5081-b94b-797a0d7aba2a"),
        doc_type=KnowledgeType.RULE,
        priority="recommended",
        title="Educational Storyboarding",
        category=RuleCategory.GENERAL,
        tags=["educational", "storyboarding"],
        path="manim_skill/rules/educational-storyboarding.md",
    ),
    KnowledgeDocumentSeed(
        document_id=UUID("a7389fbd-0c95-50d2-99c0-ca812d8cd6b0"),
        doc_type=KnowledgeType.RULE,
        priority="recommended",
        title="Equation Transitions",
        category=RuleCategory.GENERAL,
        tags=["equation", "transitions"],
        path="manim_skill/rules/equation-transitions.md",
    ),
    KnowledgeDocumentSeed(
        document_id=UUID("9ae41aa7-7d60-5764-836b-ed69a56f4b90"),
        doc_type=KnowledgeType.RULE,
        priority="recommended",
        title="Graphing",
        category=RuleCategory.GENERAL,
        tags=["graphing"],
        path="manim_skill/rules/graphing.md",
    ),
    KnowledgeDocumentSeed(
        document_id=UUID("79eec5c8-fad7-5201-b67d-60cec1e3025a"),
        doc_type=KnowledgeType.RULE,
        priority="recommended",
        title="Grouping",
        category=RuleCategory.GENERAL,
        tags=["grouping"],
        path="manim_skill/rules/grouping.md",
    ),
    KnowledgeDocumentSeed(
        document_id=UUID("bc00b640-c72f-5945-a8dd-aad4b6bebf56"),
        doc_type=KnowledgeType.RULE,
        priority="recommended",
        title="LaTeX",
        category=RuleCategory.GENERAL,
        tags=["latex"],
        path="manim_skill/rules/latex.md",
    ),
    KnowledgeDocumentSeed(
        document_id=UUID("cca8df70-9ff2-5457-85c7-ec5b21527625"),
        doc_type=KnowledgeType.RULE,
        priority="recommended",
        title="Lines",
        category=RuleCategory.GENERAL,
        tags=["lines"],
        path="manim_skill/rules/lines.md",
    ),
    KnowledgeDocumentSeed(
        document_id=UUID("c8836c15-83e3-5c6f-b904-5d942ba2dd2a"),
        doc_type=KnowledgeType.RULE,
        priority="recommended",
        title="Math Visual Clarity",
        category=RuleCategory.GENERAL,
        tags=["math", "visual", "clarity"],
        path="manim_skill/rules/math-visual-clarity.md",
    ),
    KnowledgeDocumentSeed(
        document_id=UUID("5a8aac5d-cb84-5c81-8a7d-d65ec7c1efd4"),
        doc_type=KnowledgeType.RULE,
        priority="recommended",
        title="Mobjects",
        category=RuleCategory.GENERAL,
        tags=["mobjects"],
        path="manim_skill/rules/mobjects.md",
    ),
    KnowledgeDocumentSeed(
        document_id=UUID("19d9d3b8-895e-5fdf-9977-46af6d096d56"),
        doc_type=KnowledgeType.RULE,
        priority="recommended",
        title="Positioning",
        category=RuleCategory.VISUAL_LAYOUT,
        tags=["positioning"],
        path="manim_skill/rules/positioning.md",
    ),
    KnowledgeDocumentSeed(
        document_id=UUID("44b83051-e2d4-59b7-be38-337a6f1d0090"),
        doc_type=KnowledgeType.RULE,
        priority="recommended",
        title="Scenes",
        category=RuleCategory.GENERAL,
        tags=["scenes"],
        path="manim_skill/rules/scenes.md",
    ),
    KnowledgeDocumentSeed(
        document_id=UUID("22609bb1-06df-5deb-8516-a0803e205903"),
        doc_type=KnowledgeType.RULE,
        priority="recommended",
        title="Shapes",
        category=RuleCategory.GEOMETRY,
        tags=["shapes"],
        path="manim_skill/rules/shapes.md",
    ),
    KnowledgeDocumentSeed(
        document_id=UUID("ec002b09-a533-5d0a-9aba-5dc0b3536738"),
        doc_type=KnowledgeType.RULE,
        priority="recommended",
        title="Styling",
        category=RuleCategory.GENERAL,
        tags=["styling"],
        path="manim_skill/rules/styling.md",
    ),
    KnowledgeDocumentSeed(
        document_id=UUID("02f5a6dc-1ab0-519f-bda1-5d6cfb17e241"),
        doc_type=KnowledgeType.RULE,
        priority="recommended",
        title="Text Animations",
        category=RuleCategory.GENERAL,
        tags=["text", "animations"],
        path="manim_skill/rules/text-animations.md",
    ),
    KnowledgeDocumentSeed(
        document_id=UUID("d309e921-1ad5-5dad-a062-408849cd9bce"),
        doc_type=KnowledgeType.RULE,
        priority="recommended",
        title="Text",
        category=RuleCategory.GENERAL,
        tags=["text"],
        path="manim_skill/rules/text.md",
    ),
    KnowledgeDocumentSeed(
        document_id=UUID("3b036b93-ed4a-53de-b28e-0f415a9f0650"),
        doc_type=KnowledgeType.RULE,
        priority="recommended",
        title="Timing",
        category=RuleCategory.GENERAL,
        tags=["timing"],
        path="manim_skill/rules/timing.md",
    ),
    KnowledgeDocumentSeed(
        document_id=UUID("5c2ce180-8f28-5337-98bb-826bbf54511b"),
        doc_type=KnowledgeType.RULE,
        priority="recommended",
        title="Transform Animations",
        category=RuleCategory.GENERAL,
        tags=["transform", "animations"],
        path="manim_skill/rules/transform-animations.md",
    ),
    KnowledgeDocumentSeed(
        document_id=UUID("bea74d86-fe73-54a3-ab68-2812ecb40f9c"),
        doc_type=KnowledgeType.RULE,
        priority="recommended",
        title="Updaters",
        category=RuleCategory.GENERAL,
        tags=["updaters"],
        path="manim_skill/rules/updaters.md",
    ),
    KnowledgeDocumentSeed(
        document_id=UUID("a1b2c3d4-e5f6-7890-abcd-ef1234567890"),
        doc_type=KnowledgeType.RULE,
        priority="recommended",
        title="Text Framing & Safety",
        category=RuleCategory.LAYOUT_SAFETY,
        tags=["text", "framing", "offscreen", "font-size", "margins"],
        path="manim_skill/rules/text-framing-safety.md",
    ),
    KnowledgeDocumentSeed(
        document_id=UUID("b2c3d4e5-f6a7-8901-bcde-f12345678901"),
        doc_type=KnowledgeType.RULE,
        priority="recommended",
        title="Arrow & Label Placement",
        category=RuleCategory.LAYOUT_SAFETY,
        tags=["arrows", "labels", "placement", "overlap", "brace"],
        path="manim_skill/rules/arrow-label-placement.md",
    ),
    KnowledgeDocumentSeed(
        document_id=UUID("c3d4e5f6-a7b8-9012-cdef-123456789012"),
        doc_type=KnowledgeType.RULE,
        priority="recommended",
        title="Polygon & Geometry Labeling",
        category=RuleCategory.GEOMETRY,
        tags=["polygon", "geometry", "labeling", "angle", "vertex", "triangle"],
        path="manim_skill/rules/polygon-geometry-labeling.md",
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
        document_id=UUID("b5d6ad11-568f-508e-8c53-094810a55cdc"),
        doc_type=KnowledgeType.TEMPLATE,
        priority="recommended",
        title="Basic Scene Template",
        category=TemplateCategory.TEMPLATES,
        tags=["basic", "scene"],
        path="manim_skill/templates/basic_scene.py",
    ),
    KnowledgeDocumentSeed(
        document_id=UUID("eccb31c9-230d-5028-8617-5e64704bf132"),
        doc_type=KnowledgeType.TEMPLATE,
        priority="recommended",
        title="Camera Scene Template",
        category=TemplateCategory.TEMPLATES,
        tags=["camera", "scene"],
        path="manim_skill/templates/camera_scene.py",
    ),
    KnowledgeDocumentSeed(
        document_id=UUID("59fe067e-f8af-5d89-aeb2-2d06b8e1c674"),
        doc_type=KnowledgeType.TEMPLATE,
        priority="recommended",
        title="3D Scene Template",
        category=TemplateCategory.TEMPLATES,
        tags=["3d", "scene"],
        path="manim_skill/templates/threed_scene.py",
    ),
    KnowledgeDocumentSeed(
        document_id=UUID("e5f6a7b8-c9d0-1234-ef01-345678901234"),
        doc_type=KnowledgeType.EXAMPLE,
        priority="recommended",
        title="Pythagorean Theorem Proof",
        category=ExampleCategory.MATHEMATICAL_PROOF,
        tags=["geometry", "theorem", "proof", "triangle", "squares"],
        path="manim_skill/examples/pythagorean_theorem_proof.py",
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
