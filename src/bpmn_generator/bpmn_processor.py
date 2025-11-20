import logging
from pathlib import Path
from typing import Dict, Any

from processpiper import ProcessMap, EventType, ActivityType, GatewayType

logger = logging.getLogger(__name__)

def generate_bpmn(req: Dict[str, Any]):
    """Generates a BPMN diagram based on YAML requirements."""
    req_id = req.get("id")
    req_name = req.get("name")
    lanes_def = req.get("lanes", [])

    if not lanes_def:
        logger.warning(f"No lanes defined for BPMN {req_id}. Skipping.")
        return

    # Output directory
    out_dir = Path("generated_diagrams") / f"{req_id}"
    out_dir.mkdir(parents=True, exist_ok=True)
    filename = out_dir / f"{req_id}_{req_name.replace(' ', '_')}.png"

    logger.info(f"Generating BPMN for {req_id}")

    try:
        # Increase width for better spacing and use a theme
        with ProcessMap(req_name, width=1200, height=800, colour_theme="BLUEMOUNTAIN") as my_process:
            lanes = {}
            elements = {}

            # 1. Create Lanes and Elements
            for lane_data in lanes_def:
                lane_name = lane_data.get("name")
                lane_obj = my_process.add_lane(lane_name)
                lanes[lane_name] = lane_obj
                
                for elem in lane_data.get("elements", []):
                    e_name = elem.get("name")
                    e_type = elem.get("type", "task")
                    
                    piper_type = _map_type(e_type)
                    element_obj = lane_obj.add_element(e_name, piper_type)
                    elements[e_name] = {
                        "obj": element_obj,
                        "data": elem
                    }

            # 2. Connect Elements
            for e_name, e_info in elements.items():
                current_obj = e_info["obj"]
                elem_data = e_info["data"]
                
                # "connected_to" is a list of names
                connections = elem_data.get("connected_to", [])
                for target_name in connections:
                    if target_name in elements:
                        target_obj = elements[target_name]["obj"]
                        current_obj.connect(target_obj)
                    else:
                        logger.warning(f"Target element '{target_name}' not found for '{e_name}'")

            my_process.draw()
            my_process.save(str(filename))
            logger.info(f"BPMN generated at {filename}")

    except Exception as e:
        logger.error(f"Error generating BPMN: {e}")

def _map_type(type_str: str):
    """Maps string type to ProcessPiper enum."""
    type_str = type_str.lower()
    if "start" in type_str:
        return EventType.START
    elif "end" in type_str:
        return EventType.END
    elif "task" in type_str:
        return ActivityType.TASK
    elif "subprocess" in type_str:
        return ActivityType.SUBPROCESS
    elif "gateway" in type_str:
        return GatewayType.EXCLUSIVE
    else:
        return ActivityType.TASK
