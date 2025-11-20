import logging
from pathlib import Path
from typing import Dict, Any

from diagrams import Diagram, Edge
from diagrams.programming.flowchart import Action, Database, Document, InputOutput

logger = logging.getLogger(__name__)

def generate_dfd(req: Dict[str, Any]):
    """Generates a Data Flow Diagram based on YAML requirements."""
    req_id = req.get("id")
    req_name = req.get("name")
    
    # Output directory
    out_dir = Path("generated_diagrams") / f"{req_id}"
    out_dir.mkdir(parents=True, exist_ok=True)
    filename = out_dir / f"{req_id}_{req_name.replace(' ', '_')}"

    logger.info(f"Generating DFD for {req_id}")

    graph_attr = {
        "splines": "spline",
        "nodesep": "1.0",
        "ranksep": "1.0",
        "fontsize": "14",
        "bgcolor": "white",
    }

    try:
        with Diagram(f"DFD: {req_name}", filename=str(filename), show=False, graph_attr=graph_attr):
            nodes = {}
            
            # Helper to create node based on type/context
            def get_node(n_id, n_name, n_type="process"):
                if n_type == "process":
                    return Action(n_name)
                elif n_type == "entity":
                    return InputOutput(n_name)
                elif n_type == "store":
                    return Database(n_name)
                else:
                    return Action(n_name)

            # 1. Create Nodes
            # Processes
            for proc in req.get("processes", []):
                pid = proc.get("id")
                pname = proc.get("name")
                nodes[pid] = get_node(pid, pname, "process")

            # External Entities
            for ent in req.get("external_entities", []):
                eid = ent.get("id")
                ename = ent.get("name")
                nodes[eid] = get_node(eid, ename, "entity")

            # Data Stores
            for store in req.get("data_stores", []):
                sid = store.get("id")
                sname = store.get("name")
                nodes[sid] = get_node(sid, sname, "store")

            # 2. Create Flows
            for flow in req.get("flows", []):
                src = flow.get("source")
                tgt = flow.get("target")
                label = flow.get("label", "")
                
                if src in nodes and tgt in nodes:
                    nodes[src] >> Edge(label=label) >> nodes[tgt]
                else:
                    logger.warning(f"Skipping flow {src} -> {tgt}: Node not found.")

        logger.info(f"DFD generated at {filename}.png")

    except Exception as e:
        logger.error(f"Error generating DFD: {e}")
