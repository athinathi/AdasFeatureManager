import streamlit as st
from streamlit_folium import folium_static
import folium
from geopy.geocoders import Nominatim
import openrouteservice

# Title
st.title("ADAS Route-Based Feature Manager with Real Routing")

# Sidebar input
st.sidebar.header("Enter Source and Destination Places")
source_place = st.sidebar.text_input("Source Place", value="Coimbatore")
destination_place = st.sidebar.text_input("Destination Place", value="Chennai")

# Geocode
geolocator = Nominatim(user_agent="adas_feature_manager")
source_location = geolocator.geocode(source_place)
destination_location = geolocator.geocode(destination_place)

if source_location and destination_location:
    source_coords = [source_location.longitude, source_location.latitude]  # ORS uses [lon, lat]
    dest_coords = [destination_location.longitude, destination_location.latitude]

    # OpenRouteService client (replace with your own API key)
    ors_api_key = "5b3ce3597851110001cf6248e346354ecc13425d95ab3101d6a6b4a4"  # ← Replace this
    client = openrouteservice.Client(key=ors_api_key)

    # Get route coordinates
    route = client.directions([source_coords, dest_coords], profile='driving-car', format='geojson')

    # Create folium map centered at midpoint
    mid_lat = (source_coords[1] + dest_coords[1]) / 2
    mid_lon = (source_coords[0] + dest_coords[0]) / 2
    m = folium.Map(location=[mid_lat, mid_lon], zoom_start=6)

    # Add markers
    folium.Marker([source_coords[1], source_coords[0]], tooltip="Source", icon=folium.Icon(color='green')).add_to(m)
    folium.Marker([dest_coords[1], dest_coords[0]], tooltip="Destination", icon=folium.Icon(color='red')).add_to(m)

    # Add route line
    folium.GeoJson(route, name="route").add_to(m)

    # Show map
    folium_static(m)

else:
    st.error("Could not find coordinates for one or both places.")

