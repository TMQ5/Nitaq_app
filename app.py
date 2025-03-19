import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from PIL import Image

# 1) Must be the FIRST Streamlit command
st.set_page_config(
    page_title="طريقك لإيجاد نِطاقك المفضّل في الرياض",
    layout="wide"
)

st.image('logo.png', width=400)  # Adjust width to make the logo size appropriate

# 2) Custom CSS for Styling
st.markdown(
    """
    <style>
    /* Make sidebar background light */
    [data-testid="stSidebar"] {
        background-color: #F5F5F5;
    }
    /* Make sidebar scrollable if content is long */
    [data-testid="stSidebar"] > div:first-child {
        overflow-y: auto;
        height: 100%;
    }
    /* Adjust main content padding */
    .css-18e3th9 {
        padding: 2rem 4rem;
    }
    /* Headings color */
    h1, h2, h3, h4 {
        color: #2C3E50;
    }
    .stats-box {
        background-color: #f0e5d8; /* Beige color */
        padding: 15px;
        margin: 10px;
        border-radius: 5px;
        display: inline-block;
        width: 30%;
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
    }
    .stats-icon {
        font-size: 2rem;
    }
    /* Button styles */
    .stButton>button {
        background-color: #8D6E63;
        color: white;
        font-size: 16px;
        padding: 10px 20px;
        border-radius: 5px;
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
        width: 100%;
        margin-bottom: 10px;
    }
    .stButton>button:hover {
        background-color: #6D4C41;
    }
    
    /* Custom styling for search options in sidebar */
    .sidebar .stWrite {
        color: #5A3E36;  /* Brown color */
        font-size: 16px;
    }
    
    .sidebar .stButton button {
        color: #9C27B0; /* Purple color */
    }
    
    /* Sidebar section title color */
    .sidebar .stSidebarHeader h2 {
        color: #2C3E50; /* Darker color for better visibility */
    }
    
    /* Sidebar labels */
    .sidebar label {
        color: #2C3E50; /* Dark text for contrast */
    }

    /* Professional Style for Main Content */
    .main-content {
        background-color: #2C3E50;
        padding: 3rem;
        border-radius: 10px;
        color: #ffffff;
        text-align: center;
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
    }

    /* Heading Style */
    .main-content h1 {
        font-size: 3.5rem;
        font-weight: bold;
        margin-bottom: 20px;
    }

    /* Paragraph Style */
    .main-content p {
        font-size: 1.2rem;
        color: #bdc3c7;
        line-height: 1.6;
    }
    
    /* Sidebar input field styling */
    .stNumberInput, .stMultiselect, .stTextInput {
        background-color: #F5F5F5;
        color: #2C3E50;
        border-radius: 5px;
    }

    .stNumberInput input {
        color: #2C3E50;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# 3) Title & Logo (Main Area)
st.markdown(
    "<div class='main-content'><h1>طريقك لإيجاد نطاقك المفضّل في الرياض!</h1></div>",
    unsafe_allow_html=True
)

st.markdown(
    """
    <div class='main-content'>
    <p style="font-size: 1.5rem; font-weight: bold;">مرحبًا بك في تطبيق <strong>نِطاق</strong>!</p>
    <p>نساعدك في استكشاف الرياض والعثور على النّـطاق المثالي الذي يناسبك، بناءً على المعالم والخدمات القريبة منك.</p>
    <p>حدّد خياراتك من القائمة اليسرى، ثم قم بتحديد موقعك على الخريطة أو تكبيرها لاختيار الموقع المفضل لديك. 
    بعد ذلك، اضغط على زر "<em>تأكيد الموقع</em>" في الأسفل لإكمال العملية.</p>
    <p>بعد تأكيد الموقع، سنقوم بالخطوات التالية:</p>
    <ul>
        <li>سنريك تحليل مدروس للنّطاق</li>
        <li>سنقترح عليك الشقق المتاحة للإيجار في نِطاقك</li>
    </ul>
    </div>
    """,
    unsafe_allow_html=True
)


# 4) Sidebar: Inputs & Selections
with st.sidebar:
    st.header("<span style='color: #6B4F31;'>خيارات البحث🔍</span>")  # Dark Brown color
    st.write("<span style='color: #6B4F31;'>اِختـر فِئـاتَـك المفضّلـة عند السكن *من هنــا*⬇️</span>", unsafe_allow_html=True)

    # Correct paths based on your images
    icon_mapping = {
        "مراكز تسوق": "icons/mall.png",
        "صالات رياضية": "icons/gym.jpg",
        "مستشفيات": "icons/hospital.png",
        "صيدليات": "icons/pharmacy.png",
        "المعالم السياحية": "icons/fireworks.png",
        "محطات باصات": "icons/bus.png",
        "محلات تجارية": "icons/grocery.png",
        "محطات مترو": "icons/metro.png",
        "مقاهي": "icons/cafes.png",
        "مطاعم": "icons/restaurant.png"
    }

    selected_features = []
    cols = st.columns(5)  # Create columns to arrange icons

    # Displaying the icons as clickable buttons
    for idx, (icon_name, icon_path) in enumerate(icon_mapping.items()):
        col = cols[idx % 5]  # Wrap around to next column if necessary
        with col:
            icon_img = Image.open(icon_path)  # Load each icon image dynamically
            st.image(icon_img, width=50, caption=icon_name)
            if st.button(icon_name, key=icon_name):
                if icon_name in selected_features:
                    selected_features.remove(icon_name)
                else:
                    selected_features.append(icon_name)

    st.write(f"الميزات المحددة: {', '.join(selected_features)}")

    # Location & Radius
    st.write("---")
    st.write("<span style='color: #6B4F31;'>حدد الموقع والنّـطـاق للسكن *من هنــا*⬇️</span>", unsafe_allow_html=True)
    st.write("<span style='color: #6B4F31;'>(نِطاق البحث (كم</span>", unsafe_allow_html=True)
    radius_km = st.number_input("نطاق البحث (كم):", min_value=1.0, max_value=20.0, value=5.0)
    default_lat = 24.7136
    default_lon = 46.6753
    user_lat = st.number_input("خط العرض (Latitude):", value=default_lat, format="%.6f")
    user_lon = st.number_input("خط الطول (Longitude):", value=default_lon, format="%.6f")

# 5) Data Loading & Helper Functions
def fix_latlon_columns(df):
    lowercase_cols = [col.lower() for col in df.columns]
    lat_candidates = ["latitude", "lat", "latt", "latitiude"]
    lon_candidates = ["longitude", "long", "lon", "lng", "longtiude"]
    lat_col, lon_col = None, None
    for i, col in enumerate(lowercase_cols):
        if col in lat_candidates:
            lat_col = df.columns[i]
        if col in lon_candidates:
            lon_col = df.columns[i]
    if lat_col and lat_col != "Latitude":
        df.rename(columns={lat_col: "Latitude"}, inplace=True)
    if lon_col and lon_col != "Longitude":
        df.rename(columns={lon_col: "Longitude"}, inplace=True)
    return df

def load_feature_data(filename):
    df = pd.read_excel(filename)
    df = fix_latlon_columns(df)
    return df

# 6) Load Feature Data
feature_files = {
    "مطاعم": "data/restaurants.xlsx",
    "صيدليات": "data/pharmacies.xlsx",
    "صالات رياضية": "data/gym.xlsx",
    "مقاهي": "data/cafes_bakeries.xlsx",
    "مستشفيات": "data/hospitals_clinics.xlsx",
    "محلات تجارية": "data/groceries_supermarket.xlsx",
    "مراكز تسوق": "data/malls.xlsx",
    "المعالم السياحية": "data/entertainment.xlsx",
    "محطات باصات": "data/bus_stops.xlsx"
}

feature_dfs = []
for feat in selected_features:
    try:
        df_feat = load_feature_data(feature_files[feat])
        df_feat = df_feat[["Name", "Latitude", "Longitude"]].dropna(subset=["Latitude", "Longitude"]).copy()
        df_feat["feature"] = feat
        feature_dfs.append(df_feat)
    except Exception as e:
        st.error(f"حدث خطأ أثناء تحميل بيانات '{feat}': {e}")

if feature_dfs:
    combined_features = pd.concat(feature_dfs, ignore_index=True)
else:
    combined_features = pd.DataFrame(columns=["Name", "Latitude", "Longitude", "feature"])

# 7) Display the Map (using Plotly)
fig = go.Figure()

# Add markers for each feature
for idx, row in combined_features.iterrows():
    fig.add_trace(go.Scattermapbox(
        lat=[row["Latitude"]],
        lon=[row["Longitude"]],
        mode='markers',
        marker=go.scattermapbox.Marker(
            size=14,
            color='blue'
        ),
        text=row["Name"]
    ))

# Customize the layout
fig.update_layout(
    mapbox_style="open-street-map",
    mapbox_center={"lat": user_lat, "lon": user_lon},
    mapbox_zoom=12,
    margin={"r":0,"t":0,"l":0,"b":0}
)

# Render the map
st.plotly_chart(fig, use_container_width=True)

# 8) Finalize Location (Under Development)
st.markdown("<hr>", unsafe_allow_html=True)

# Move the confirm button under the explanation
st.markdown(
    """
    <p style='text-align: center; color: #7F8C8D; font-size: 1.2rem;'>
    اضغط على زر <strong>تأكيد الموقع</strong> بعد الانتهاء من اختيار الموقع.
    </p>
    """,
    unsafe_allow_html=True
)

if st.button("تأكيد الموقع"):
    st.success("تم تأكيد الموقع! (الميزة التالية قيد التطوير)")

st.markdown("<hr>", unsafe_allow_html=True)

# Footer with Project, Academy, and Bootcamp Names
st.markdown(
    """
    <p style='text-align: center; color: #7F8C8D; font-size: 1rem;'>
    تم تطوير هذا التطبيق بواسطة <strong>نِـطــاق</strong> | 
    أكاديمية طويق | 
    <strong>Data Science and Machine Learning Bootcamp</strong> | 
    Tuwaiq Academy 2025
    </p>
    """,
    unsafe_allow_html=True
)
