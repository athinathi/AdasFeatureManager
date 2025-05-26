import streamlit as st
from streamlit_folium import folium_static
import folium
from geopy.geocoders import Nominatim

# App title
st.title("ADAS Route-Based Feature Manager")

# Sidebar: Input source and destination names
st.sidebar.header("Enter Source and Destination Places")
source_place = st.sidebar.text_input("Source Place", value="Coimbatore")
destination_place = st.sidebar.text_input("Destination Place", value="Chennai")

# Geocode the place names into coordinates
geolocator = Nominatim(user_agent="adas_feature_manager")

source_location = geolocator.geocode(source_place)
destination_location = geolocator.geocode(destination_place)

if source_location and destination_location:
    # Show locations on map
    source_coords = [source_location.latitude, source_location.longitude]
    dest_coords = [destination_location.latitude, destination_location.longitude]
    
    # Center the map between source and destination
    mid_lat = (source_coords[0] + dest_coords[0]) / 2
    mid_lon = (source_coords[1] + dest_coords[1]) / 2
    m = folium.Map(location=[mid_lat, mid_lon], zoom_start=6)
    
    # Add markers
    folium.Marker(source_coords, tooltip="Source: " + source_place, icon=folium.Icon(color='green')).add_to(m)
    folium.Marker(dest_coords, tooltip="Destination: " + destination_place, icon=folium.Icon(color='red')).add_to(m)
    
    # Draw a route (straight line)
    folium.PolyLine([source_coords, dest_coords], color="blue", weight=5, opacity=0.7, tooltip="Route").add_to(m)
    
    # Display map
    folium_static(m)
else:
    st.error("Could not find coordinates for one or both places. Please check the names and try again.")
    folium_static(m)