import streamlit as st
from database.db import supabase
from datetime import datetime
import folium
from streamlit_folium import st_folium
from folium.plugins import MarkerCluster
from features.matching import calculate_match_score
from geopy.distance import geodesic
from streamlit_geolocation import streamlit_geolocation

st.markdown(
    """
    <style>
    
    /* Hide Streamlit deploy button (bottom right) */
    .stDeployButton {display:none;}

    /* Hide GitHub / Fork / menu icons (top right) */
    header {visibility: hidden;}

    /* Hide hamburger menu */
    #MainMenu {visibility: hidden;}

    /* Hide footer */
    footer {visibility: hidden;}

    </style>
    """,
    unsafe_allow_html=True
)

st.set_page_config(
    page_title="Universal Lost & Found System",
    layout="wide",
    initial_sidebar_state="expanded"
)
st.title("Universal Lost & Found System")

menu = st.sidebar.radio(
    "Menu",
    ["Report Lost", "Report Found", "View Reports"]
)

# ---------------- LOCATION ----------------

location_data = streamlit_geolocation()

if "user_location" not in st.session_state:
    st.session_state.user_location = None

if location_data:
    lat = location_data.get("latitude")
    lon = location_data.get("longitude")

    if lat and lon:
        st.session_state.user_location = [lat, lon]

if st.session_state.user_location:
    user_location = st.session_state.user_location
else:
    user_location = [19.0760, 72.8777]

if "selected_location" not in st.session_state:
    st.session_state.selected_location = None


# ---------------- HELPER ----------------

def description_match(search, description):

    search_words = search.lower().split()
    desc_words = description.lower().split()

    for w in search_words:
        if w in desc_words:
            return True

    return False

def report_card(report, distance=None):

    with st.expander(f"{report['entity_type']} • {report['description'][:40]}"):

        col1, col2 = st.columns([1,2])

        with col1:

            if report.get("image_url"):
                st.image(report["image_url"], width=200)

        with col2:

            st.write("Type:", report["report_type"])
            st.write("Description:", report["description"])
            st.write("Color:", report["color"])

            if distance is not None:
                st.write("Distance:", round(distance,2),"km")

            st.write("Contact:", report["contact"])
            st.write("Date:", report["date"])


# ---------------- REPORT LOST ----------------

if menu == "Report Lost":

    st.header("Report Lost Pet / Person")

    entity_type = st.selectbox("Type", ["pet","person"])
    name = st.text_input("Name")
    description = st.text_area("Description")
    color = st.text_input("Color")

    if st.button("Use My Location"):
        st.session_state.selected_location = user_location

    st.subheader("Select Location")

    m = folium.Map(location=user_location, zoom_start=12)

    folium.Marker(
        user_location,
        popup="Your Location",
        icon=folium.Icon(color="blue")
    ).add_to(m)

    if st.session_state.selected_location:

        folium.Marker(
            st.session_state.selected_location,
            popup="Selected",
            icon=folium.Icon(color="orange")
        ).add_to(m)

    map_data = st_folium(m,height=400,returned_objects=["last_clicked"])

    if map_data and map_data.get("last_clicked"):
        st.session_state.selected_location = [
            map_data["last_clicked"]["lat"],
            map_data["last_clicked"]["lng"]
        ]

    lat = None
    lon = None

    if st.session_state.selected_location:
        lat = st.session_state.selected_location[0]
        lon = st.session_state.selected_location[1]

    contact = st.text_input("Contact")
    photo = st.file_uploader("Upload Photo")

    if photo:
        st.image(photo,width=200)

    if st.button("Submit Lost Report"):

        if not description:
            st.error("Description required")
            st.stop()

        if lat is None or lon is None:
            st.error("Please select location on map")
            st.stop()

        if not contact:
            st.error("Contact information required")
            st.stop()

        data = {
            "report_type":"lost",
            "entity_type":entity_type,
            "name":name,
            "description":description,
            "color":color,
            "latitude":lat,
            "longitude":lon,
            "contact":contact,
            "date":str(datetime.now())
        }

        supabase.table("reports").insert(data).execute()
    
        st.success("Report submitted")

# ---------------- REPORT FOUND ----------------

elif menu == "Report Found":

    st.header("Report Found Pet / Person")

    entity_type = st.selectbox("Type",["pet","person"])
    description = st.text_area("Description")
    color = st.text_input("Color")

    if st.button("Use My Location"):
        st.session_state.selected_location = user_location

    st.subheader("Select Location")

    m = folium.Map(location=user_location, zoom_start=12)

    folium.Marker(
        user_location,
        popup="Your Location",
        icon=folium.Icon(color="blue")
    ).add_to(m)

    if st.session_state.selected_location:

        folium.Marker(
            st.session_state.selected_location,
            popup="Selected",
            icon=folium.Icon(color="orange")
        ).add_to(m)

    map_data = st_folium(m,height=400,returned_objects=["last_clicked"])

    if map_data and map_data.get("last_clicked"):

        st.session_state.selected_location = [
            map_data["last_clicked"]["lat"],
            map_data["last_clicked"]["lng"]
        ]

    lat=None
    lon=None

    if st.session_state.selected_location:
        lat=st.session_state.selected_location[0]
        lon=st.session_state.selected_location[1]

    contact=st.text_input("Contact")
    photo=st.file_uploader("Upload Photo")

    if photo:
        st.image(photo,width=200)

    if st.button("Submit Found Report"):

        if not description:
            st.error("Description required")
            st.stop()

        if lat is None or lon is None:
            st.error("Please select location on map")
            st.stop()

        if not contact:
            st.error("Contact information required")
            st.stop()

        data={
            "report_type":"found",
            "entity_type":entity_type,
            "description":description,
            "color":color,
            "latitude":lat,
            "longitude":lon,
            "contact":contact,
            "date":str(datetime.now())
        }

        supabase.table("reports").insert(data).execute()

        st.success("Report submitted")


# ---------------- VIEW REPORTS ----------------

elif menu=="View Reports":

    st.header("Search Reports")

    search_text=st.text_input("Search description")
    max_distance=st.slider("Distance (km)",1,10000,50)

    response=supabase.table("reports").select("*").execute()
    reports=response.data


    lost_count = len([r for r in reports if r["report_type"] == "lost"])  
    found_count = len([r for r in reports if r["report_type"] == "found"])

    col1, col2 = st.columns(2)

    with col1:
        st.metric("Lost Reports", lost_count)

    with col2:
        st.metric("Found Reports", found_count)

    filtered_reports=[]

    for r in reports:

        if r["latitude"] is None:
            continue

        dist=geodesic(user_location,(r["latitude"],r["longitude"])).km

        if dist>max_distance:
            continue

        if search_text:
            if not description_match(search_text,r["description"]):
                continue

        r["distance"]=dist
        filtered_reports.append(r)

    st.write("Results:",len(filtered_reports))

    # ---------- MAP ----------

    m=folium.Map(location=user_location,zoom_start=12)

    cluster=MarkerCluster().add_to(m)

    for r in filtered_reports:

        color="red" if r["report_type"]=="lost" else "green"

        folium.Marker(
            [r["latitude"],r["longitude"]],
            popup=f"{r['report_type']} - {r['description']}",
            icon=folium.Icon(color=color)
        ).add_to(cluster)

    st_folium(m,width=900)

    # ---------- RESULTS ----------

    st.subheader("Reports")

    if len(filtered_reports)==0:
        st.info("No reports found")

    for r in filtered_reports:
        report_card(r,r["distance"])

    # ---------- MATCHES ----------

    st.subheader("Possible Matches")

    lost=[r for r in filtered_reports if r["report_type"]=="lost"]
    found=[r for r in filtered_reports if r["report_type"]=="found"]

    matches=[]

    for l in lost:
        for f in found:

            score,distance=calculate_match_score(l,f)

            if score>=5:
                matches.append((l,f,score,distance))

    if len(matches)==0:
        st.info("No matches")

    for m in matches:

        l,f,score,distance=m

        with st.expander(f"Match Score {score}"):

            col1,col2=st.columns(2)

            with col1:
                report_card(l)

            with col2:
                report_card(f)

            st.write("Distance:",round(distance,2),"km")
