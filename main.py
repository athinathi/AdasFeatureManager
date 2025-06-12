import streamlit as st
from streamlit_folium import folium_static
import folium
import openrouteservice
from bsm_check import evaluate_bsm_conditions
import time
from math import radians, cos, sin, asin, sqrt

# Way category mapping from ORS codes to names
WAYCATEGORY_MAPPING = {
    0: "motorway", 1: "trunk", 2: "primary", 3: "secondary",
    4: "tertiary", 5: "residential", 6: "service", 7: "unclassified",
    8: "track", 9: "pedestrian", 10: "cycleway", 11: "footway"
}

LANE_COUNT_MAP = {
    "motorway": 3, "trunk": 3, "primary": 2, "secondary": 2,
    "tertiary": 2, "residential": 1, "service": 1,
    "cycleway": 1, "footway": 1
}

# Coordinates for cities
location_coords = {
    "Coimbatore": [76.9558, 11.0168],
    "Erode": [77.7274, 11.3410],
    "Karur": [78.0766, 10.9575],
    "Salem": [78.1510, 11.6643],
    "Namakkal": [78.1664, 11.2183]
}

# Streamlit config
st.set_page_config(layout="wide")
st.title("ADAS BSM – Real Road-Based Simulation")

# User inputs
places = list(location_coords.keys())
source = st.sidebar.selectbox("Source", places, index=0)
destination = st.sidebar.selectbox("Destination", places, index=1)
speed_kmph = st.sidebar.slider("Vehicle Speed (km/h)", 20, 10000, 60)
auto_run = st.sidebar.checkbox("Auto Run", True)

# ORS setup
ors_key = "5b3ce3597851110001cf6248e346354ecc13425d95ab3101d6a6b4a4"  # Replace with your actual key
client = openrouteservice.Client(key=ors_key)

# Distance function
def haversine(coord1, coord2):
    lon1, lat1 = coord1
    lon2, lat2 = coord2
    R = 6371
    dlon = radians(lon2 - lon1)
    dlat = radians(lat2 - lat1)
    a = sin(dlat/2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a))
    return R * c

# Get route and segment metadata
@st.cache_data
def get_route_with_metadata(src, dst):
    route = client.directions(
        [src, dst],
        profile='driving-car',
        format='geojson',
        instructions=True,
        extra_info=["waycategory"]
    )

    geometry = route['features'][0]['geometry']['coordinates']
    steps = route['features'][0]['properties']['segments'][0]['steps']
    extras = route['features'][0]['properties'].get("extras", {})
    
    segments = []
    for step in steps:
        idx_start = step["way_points"][0]
        idx_end = step["way_points"][1]
        road_type_code = None
        for value in extras.get("waycategory", {}).get("values", []):
            start_idx, end_idx, cat_idx = value
            if start_idx <= idx_start <= end_idx:
                road_type_code = cat_idx
                break
        road_type = WAYCATEGORY_MAPPING.get(road_type_code, "primary")
        segments.append({
            "geometry_index": idx_start,
            "end_index": idx_end,
            "road_type": road_type
        })

    return geometry, segments

# Validate input
if source == destination:
    st.error("Source and destination must be different.")
    st.stop()

# Get route
src = location_coords[source]
dst = location_coords[destination]
geometry, segments = get_route_with_metadata(src, dst)
points = [(pt[1], pt[0]) for pt in geometry]
total_points = len(points)

# Initialize session state
if "vehicle_index" not in st.session_state:
    st.session_state.vehicle_index = 0
if "last_update" not in st.session_state:
    st.session_state.last_update = time.time()

cur_idx = min(st.session_state.vehicle_index, total_points - 1)
current_pos = points[cur_idx]

# Match road segment
def get_segment_for_index(idx):
    for segment in segments:
        if segment["geometry_index"] <= idx < segment["end_index"]:
            return segment
    return segments[-1]

segment = get_segment_for_index(cur_idx)
road_type = segment["road_type"]
lane_count = LANE_COUNT_MAP.get(road_type, 2)
adjacent_lanes_present = lane_count > 1

# BSM evaluation
decision = evaluate_bsm_conditions(
    speed_kmph=speed_kmph,
    road_type=road_type,
    lane_count=lane_count,
    adjacent_lanes_present=adjacent_lanes_present,
    active_adas_features=['LKA', 'ACC']
)

is_prompt = decision.startswith("Prompt")
bsm_color = "green" if is_prompt else "red"

# Sidebar
st.sidebar.markdown("---")
st.sidebar.subheader("🧠 BSM Evaluation (Live)")
st.sidebar.write(f"**Position:** {cur_idx + 1}/{total_points}")
st.sidebar.write(f"**Road Type:** {road_type}")
st.sidebar.write(f"**Lane Count:** {lane_count}")
st.sidebar.write(f"**Adjacent Lanes:** {'Yes' if adjacent_lanes_present else 'No'}")
st.sidebar.write(f"**Speed:** {speed_kmph} km/h")
# Proper BSM decision display
if is_prompt:
    st.sidebar.success(decision)
else:
    st.sidebar.warning(decision)


if st.sidebar.button("Reset Simulation"):
    st.session_state.vehicle_index = 0
    st.session_state.last_update = time.time()
    st.rerun()

# Vehicle movement
if cur_idx < total_points - 1:
    pt1 = points[cur_idx]
    pt2 = points[cur_idx + 1]
    dist_km = haversine((pt1[1], pt1[0]), (pt2[1], pt2[0]))
    time_required = (dist_km / speed_kmph) * 3600
    now = time.time()
    if now - st.session_state.last_update >= time_required:
        st.session_state.vehicle_index += 1
        st.session_state.last_update = now

# Map display
m = folium.Map(location=points[len(points)//2], zoom_start=10)
folium.PolyLine(points, color='gray', weight=5, opacity=0.6).add_to(m)
folium.Marker([src[1], src[0]], tooltip="Source", icon=folium.Icon(color='green')).add_to(m)
folium.Marker([dst[1], dst[0]], tooltip="Destination", icon=folium.Icon(color='red')).add_to(m)

folium.Marker(
    location=current_pos,
    icon=folium.Icon(icon="car", prefix="fa", color="blue"),
    tooltip="Vehicle"
).add_to(m)

folium.CircleMarker(
    location=current_pos,
    radius=8,
    color=bsm_color,
    fill=True,
    fill_color=bsm_color,
    fill_opacity=0.7,
    tooltip=f"BSM: {decision}"
).add_to(m)

legend_html = '''
 <div style="position: fixed; bottom: 50px; left: 50px; width: 250px; height: 100px;
 background-color: white; z-index:9999; font-size:14px; border:2px solid grey; padding: 10px;">
 <b>BSM Legend</b><br>
 <i style="color:green;">●</i> Prompt Driver<br>
 <i style="color:red;">●</i> Do Not Prompt
 </div>
'''
m.get_root().html.add_child(folium.Element(legend_html))
folium_static(m)

# Auto rerun
if auto_run and cur_idx < total_points - 1:
    time.sleep(0.05)
    st.rerun()
elif cur_idx == total_points - 1:
    st.sidebar.success("✅ Destination reached.")












