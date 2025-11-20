import os
import logging
import importlib
from pathlib import Path
from typing import Dict, Any

from diagrams import Diagram, Cluster, Edge, Node

logger = logging.getLogger(__name__)

def generate_architecture(req: Dict[str, Any]):
    """Generates an architecture diagram based on the YAML requirement."""
    req_id = req.get("id")
    req_name = req.get("name")
    components = req.get("components", [])
    relationships = req.get("relationships", [])
    
    # Output directory
    out_dir = Path("generated_diagrams") / f"{req_id}"
    out_dir.mkdir(parents=True, exist_ok=True)
    
    # Filename
    filename = out_dir / f"{req_id}_{req_name.replace(' ', '_')}"
    
    logger.info(f"Generating Architecture Diagram for {req_id}")
    
    graph_attr = {
        "splines": "ortho",
        "nodesep": "1.0",
        "ranksep": "1.2",
        "fontsize": "14",
        "bgcolor": "white",
        "pad": "1.0",
        "compound": "true",
    }

    try:
        with Diagram(f"{req_id}: {req_name}", filename=str(filename), show=False, graph_attr=graph_attr):
            nodes = {}
            
            # Helper to dynamically create node from string path
            def create_node(name, type_str):
                # type_str example: diagrams.azure.compute.AppService
                # or: azure.compute.AppService (legacy support)
                
                if not type_str:
                    from diagrams.programming.flowchart import Action
                    return Action(name)

                # Normalize path if it doesn't start with 'diagrams.'
                if not type_str.startswith("diagrams."):
                    type_str = f"diagrams.{type_str}"

                try:
                    # Split into module and class
                    # e.g. diagrams.azure.compute.AppService -> module: diagrams.azure.compute, class: AppService
                    parts = type_str.split(".")
                    module_path = ".".join(parts[:-1])
                    class_name = parts[-1]
                    
                    module = importlib.import_module(module_path)
                    cls = getattr(module, class_name)
                    return cls(name)
                    
                except (ImportError, AttributeError) as e:
                    logger.warning(f"Could not import {type_str} for {name}: {e}. Fallback to generic Node.")
                    # Fallback to a generic node if specific one fails
                    from diagrams.programming.flowchart import Action
                    return Action(name)

            # 1. Create Components
            for comp in components:
                c_name = comp.get("name")
                c_type = comp.get("type")
                nodes[c_name] = create_node(c_name, c_type)

            # 2. Create Relationships
            for rel in relationships:
                src = rel.get("source")
                tgt = rel.get("target")
                label = rel.get("label", "")
                
                if src in nodes and tgt in nodes:
                    nodes[src] >> Edge(label=label) >> nodes[tgt]
                else:
                    logger.warning(f"Skipping relationship {src} -> {tgt}: Node not found.")

        logger.info(f"Architecture diagram generated at {filename}.png")

    except Exception as e:
        logger.error(f"Error generating architecture diagram: {e}")
