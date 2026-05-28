from collections.abc import Callable
from dataclasses import dataclass

from runtime.context import ExperimentContext
from workflow_state import NodeName, WorkflowState

from nodes.codegen import make_generate_code_node
from nodes.fail import make_fail_node
from nodes.fix import make_fix_code_node
from nodes.knowledge import make_load_static_knowledge_node
from nodes.plan import make_generate_plan_node
from nodes.render import make_render_node
from nodes.verify import make_verify_node


NodeHandler = Callable[[WorkflowState], dict]
NodeFactory = Callable[[ExperimentContext, NodeName], NodeHandler]


@dataclass(frozen=True)
class NodeSpec:
    name: NodeName
    factory: NodeFactory


NODE_SPECS: tuple[NodeSpec, ...] = (
    NodeSpec(NodeName.GENERATE_PLAN, make_generate_plan_node),
    NodeSpec(NodeName.LOAD_STATIC_KNOWLEDGE, make_load_static_knowledge_node),
    NodeSpec(NodeName.GENERATE_CODE, make_generate_code_node),
    NodeSpec(NodeName.VERIFY, make_verify_node),
    NodeSpec(NodeName.FIX_CODE, make_fix_code_node),
    NodeSpec(NodeName.RENDER, make_render_node),
    NodeSpec(NodeName.FAIL, make_fail_node),
)
