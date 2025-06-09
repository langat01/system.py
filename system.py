# kenya_vehicle_tracking_system_enhanced.py

import streamlit as st
import pandas as pd
import random
from datetime import datetime
import folium
from streamlit_folium import st_folium

# ------------------ Vehicle Metadata ------------------
vehicles_info = {
    'KDA123A': {'type': 'private_car', 'assigned_route': 'Mau Mau - Narok'},
    'KBX456B': {'type': 'truck', 'assigned_route': 'Nakuru Road'},
    'KCZ789C': {'type': 'private_car', 'assigned_route': 'Mau Mau - Narok'},
    'KTX987D': {'type': 'bus', 'assigned_route': 'Nakuru Road'},
    'KLM654E': {'type': 'private_car', 'assigned_route': 'Mau Mau - Narok'},
}

speed_limits_by_vehicle_type = {
    'private_car': 80,
    'truck': 60,
    'bus': 70,
}

speed_limits_by_route = {
    'Mau Mau - Narok': 70,
    'Nakuru Road': 60,
}

def get_speed_limit(vehicle_id):
    route = vehicles_info[vehicle_id]['assigned_route']
    v_type = vehicles_info[vehicle_id]['type']
    # Use route speed limit if defined, else vehicle type speed limit
    return speed_limits_by_route.get(route, speed_limits_by_vehicle_type.get(v_type, 80))

# ------------------ Data Simulation ------------------

@st.cache_data
def generate_sample_data():
    # Simulate vehicle positions around Nairobi (approximate center)
    # We simulate lat/lon around Nairobi, but for demonstration we pretend the vehicle is on its route
    base_coords = {
        'Mau Mau - Narok': (-1.286389, 36.816944),  # Nairobi approximate
        'Nakuru Road': (-0.3031, 36.0800)           # Nakuru approximate
    }
    data = []
    for vehicle_id, meta in vehicles_info.items():
        route = meta['assigned_route']
        base_lat, base_lon = base_coords.get(route, (-1.2921, 36.8219))
        # Randomize location slightly near base coordinates for route simulation
        lat = base_lat + random.uniform(-0.03, 0.03)
        lon = base_lon + random.uniform(-0.03, 0.03)
        # Generate random speed but with a bias (private cars a bit faster, trucks slower)
        v_type = meta['type']
        if v_type == 'private_car':
            speed = random.randint(40, 100)
        elif v_type == 'truck':
            speed = random.randint(30, 70)
        elif v_type == 'bus':
            speed = random.randint(30, 75)
        else:
            speed = random.randint(20, 90)
        data.append({
            'vehicle_id': vehicle_id,
            'latitude': lat,
            'longitude': lon,
            'speed_kmph': speed,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'vehicle_type': v_type,
            'route': route,
            'speed_limit': get_speed_limit(vehicle_id),
        })
    return pd.DataFrame(data)

# ------------------ Streamlit UI ------------------

st.set_page_config(page_title="Kenya Vehicle Tracking System", layout="wide")
st.title("🚗 Kenya Vehicle Tracking & Analytics System")

st.markdown("""
This system monitors vehicle **location**, **speed**, and supports **route-based analysis** with speed limit enforcement.
""")

# Generate / load data
data = generate_sample_data()

# Sidebar: select route filter
routes = ['All Routes'] + sorted(list(set(data['route'])))
selected_route = st.sidebar.selectbox("Select Route to Filter Vehicles", routes)

# Filter data by route if not 'All Routes'
if selected_route != 'All Routes':
    filtered_data = data[data['route'] == selected_route]
else:
    filtered_data = data.copy()

# Show vehicle list on selected route
st.subheader(f"📋 Vehicles on Route: {selected_route}")
if filtered_data.empty:
    st.info("No vehicles found for the selected route.")
else:
    # Add overspeeding flag
    filtered_data['overspeeding'] = filtered_data['speed_kmph'] > filtered_data['speed_limit']
    # Show table with highlighting
    def highlight_overspeed(row):
        return ['background-color: #ffcccc' if row.overspeeding else '' for _ in row]

    st.dataframe(filtered_data[['vehicle_id', 'vehicle_type', 'speed_kmph', 'speed_limit', 'route', 'timestamp', 'overspeeding']]
                 .style.apply(highlight_overspeed, axis=1))

# ------------------ Map ------------------

if not filtered_data.empty:
    # Center map on average vehicle location
    avg_lat = filtered_data['latitude'].mean()
    avg_lon = filtered_data['longitude'].mean()

    m = folium.Map(location=[avg_lat, avg_lon], zoom_start=12)

    # Add vehicle markers
    for _, row in filtered_data.iterrows():
        color = 'red' if row['speed_kmph'] > row['speed_limit'] else 'green'
        folium.Marker(
            location=[row['latitude'], row['longitude']],
            tooltip=(f"ID: {row['vehicle_id']} | "
                     f"Type: {row['vehicle_type']} | "
                     f"Speed: {row['speed_kmph']} km/h | "
                     f"Limit: {row['speed_limit']} km/h"),
            icon=folium.Icon(color=color)
        ).add_to(m)

    st.subheader("📍 Vehicle Locations on Map")
    st_folium(m, width=800, height=500)

# ------------------ Speeding Alerts ------------------

st.subheader("🚨 Speeding Vehicles Summary")
if filtered_data.empty:
    st.info("No vehicles to check for speeding.")
else:
    speeding = filtered_data[filtered_data['speed_kmph'] > filtered_data['speed_limit']]
    if speeding.empty:
        st.success("No speeding vehicles detected on this route.")
    else:
        st.error(f"{len(speeding)} vehicle(s) detected speeding on {selected_route if selected_route != 'All Routes' else 'all routes'}!")
        for _, row in speeding.iterrows():
            st.write(f"- Vehicle {row['vehicle_id']} ({row['vehicle_type']}) at {row['speed_kmph']} km/h, limit {row['speed_limit']} km/h")

# ------------------ Footer ------------------

st.markdown("---")
st.markdown("Created by Weldon Langat | Powered by Streamlit | Prototype for Kenya Vehicle Tracking & Analytics System")
