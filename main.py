import streamlit as st
from streamlit_folium import folium_static
import folium
import openrouteservice
from bsm_check import evaluate_bsm_conditions  # BSM logic

# Title
st.title("ADAS Route-Based Feature Manager with BSM Evaluation")

# Sidebar: Input for source and destination
st.sidebar.header("Enter Source and Destination Places")
places = ["Coimbatore", "Chennai", "Bangalore", "Madurai", "Salem"]
source_place = st.sidebar.selectbox("Source Place", places, index=0)
destination_place = st.sidebar.selectbox("Destination Place", places, index=1)

# ORS API Key (Replace with secure method in production)
ors_api_key = "5b3ce3597851110001cf6248e346354ecc13425d95ab3101d6a6b4a4"
client = openrouteservice.Client(key=ors_api_key)

# ORS Geocoding and Routing
try:
    source_geocode = client.pelias_search(text=source_place)['features'][0]
    destination_geocode = client.pelias_search(text=destination_place)['features'][0]
    source_coords = source_geocode['geometry']['coordinates']
    dest_coords = destination_geocode['geometry']['coordinates']

    # Get route
    route = client.directions([source_coords, dest_coords], profile='driving-car', format='geojson')
    summary = route['features'][0]['properties']['summary']
    distance_km = summary['distance'] / 1000
    duration_min = summary['duration'] / 60

    # Sidebar: Route summary
    st.sidebar.markdown("### Route Summary")
    st.sidebar.write(f"**Distance:** {distance_km:.2f} km")
    st.sidebar.write(f"**Estimated Time:** {duration_min:.1f} minutes")

    # Sidebar: BSM evaluation inputs
    st.sidebar.markdown("---")
    st.sidebar.subheader("BSM Evaluation Inputs")

    speed = st.sidebar.slider("Vehicle Speed (km/h)", 0, 200, 60)
    road_type = st.sidebar.selectbox("Road Type", ["motorway", "highway", "primary", "secondary", "residential"])
    lane_count = st.sidebar.slider("Number of Lanes", 1, 6, 3)
    adjacent_lanes = st.sidebar.checkbox("Adjacent Lanes Present", True)
    active_features = st.sidebar.multiselect(
        "Active ADAS Features", ["LKA", "ACC", "AEB", "TPMS"], default=["LKA"]
    )

    bsm_result = evaluate_bsm_conditions(speed, road_type, lane_count, adjacent_lanes, active_features)
    st.sidebar.markdown("#### BSM Decision")
    st.sidebar.write(f"🧠 {bsm_result}")

    # Main map rendering
    mid_lat = (source_coords[1] + dest_coords[1]) / 2
    mid_lon = (source_coords[0] + dest_coords[0]) / 2
    m = folium.Map(location=[mid_lat, mid_lon], zoom_start=6)

    # Add markers
    folium.Marker([source_coords[1], source_coords[0]], tooltip="Source", icon=folium.Icon(color='green')).add_to(m)
    folium.Marker([dest_coords[1], dest_coords[0]], tooltip="Destination", icon=folium.Icon(color='red')).add_to(m)

    # Add route to map
    folium.GeoJson(route, name="route").add_to(m)

    # Display map
    folium_static(m)

except Exception as e:
    st.error(f"Geocoding or routing failed: {e}")





