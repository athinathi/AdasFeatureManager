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

# ORS API Key (Replace with your secure key if needed)
ors_api_key = "5b3ce3597851110001cf6248e346354ecc13425d95ab3101d6a6b4a4"
client = openrouteservice.Client(key=ors_api_key)

# ORS Geocoding instead of geopy
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

    # Sidebar route summary
    st.sidebar.write(f"**Distance:** {distance_km:.2f} km")
    st.sidebar.write(f"**Estimated Time:** {duration_min:.1f} minutes")

    # Map rendering
    mid_lat = (source_coords[1] + dest_coords[1]) / 2
    mid_lon = (source_coords[0] + dest_coords[0]) / 2
    m = folium.Map(location=[mid_lat, mid_lon], zoom_start=6)

    folium.Marker([source_coords[1], source_coords[0]], tooltip="Source", icon=folium.Icon(color='green')).add_to(m)
    folium.Marker([dest_coords[1], dest_coords[0]], tooltip="Destination", icon=folium.Icon(color='red')).add_to(m)
    folium.GeoJson(route, name="route").add_to(m)

    folium_static(m)

    st.markdown("---")
    st.header("Blind Spot Monitoring (BSM) Evaluation")

    # BSM Inputs
    speed = st.slider("Vehicle Speed (km/h)", 0, 200, 60)
    road_type = st.selectbox("Road Type", ["motorway", "highway", "primary", "secondary", "residential"])
    lane_count = st.slider("Number of Lanes", 1, 6, 3)
    adjacent_lanes = st.checkbox("Adjacent Lanes Present", True)
    active_features = st.multiselect("Active ADAS Features", ["LKA", "ACC", "AEB", "TPMS"], default=["LKA"])

    bsm_result = evaluate_bsm_conditions(speed, road_type, lane_count, adjacent_lanes, active_features)

    st.subheader("BSM Decision")
    st.write(f"🧠 {bsm_result}")

except Exception as e:
    st.error(f"Geocoding or routing failed: {e}")




