def evaluate_bsm_conditions(speed_kmph, road_type, lane_count, adjacent_lanes_present, active_adas_features):
    suitable_road_types = ['motorway', 'highway', 'primary', 'secondary']
    required_adas = {'LKA', 'ACC'}

    if speed_kmph < 20:
        return "Do Not Prompt: Speed below 20 km/h."
    
    if road_type not in suitable_road_types:
        return f"Do Not Prompt: Unsuitable road type ({road_type})."
    
    if lane_count < 2:
        return "Do Not Prompt: Not enough lanes for BSM."
    
    if not adjacent_lanes_present:
        return "Do Not Prompt: No adjacent lanes detected."
    
    if not required_adas.intersection(set(active_adas_features)):
        return "Do Not Prompt: No compatible ADAS features active (LKA or ACC)."

    return "Prompt Driver: Enable Blind Spot Monitoring?"

