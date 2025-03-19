import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from scipy.spatial import cKDTree
from PIL import Image
from streamlit_folium import st_folium
import folium
import math
from geopy.distance import geodesic

# إعداد صفحة التطبيق
st.set_page_config(
    page_title="طريقك لإيجاد نِطاقك المفضّل في الرياض",
    layout="wide"
)

# تحميل صورة الشعار وعرضه في الشريط الجانبي في المنتصف
with st.sidebar:
    st.image('logo.png', use_container_width=True)
    
    st.header("🔍 خيارات البحث")
    
    # نطاق البحث كـ شريط تمرير بين 0 و 15 كم بفواصل 0.5 كم
    radius_km = st.slider("نطاق البحث (كم):", min_value=0.0, max_value=15.0, value=5.0, step=0.5)
    
    # اختيار الخدمات المفضلة
    services_file = "merged_places.xlsx"
    df_services = pd.read_excel(services_file, sheet_name='Sheet1')
    
    # تحويل أسماء الفئات إلى العربية
    category_translation = {
        "malls": "المولات",
        "entertainment": "الترفيه",
        "hospitals_clinics": "المستشفيات والعيادات",
        "gyms": "الصالات الرياضية",
        "groceries": "البقالات",
        "bus": "محطات الباص",
        "metro": "محطات المترو",
        "cafes_bakeries": "المقاهي والمخابز",
        "pharmacies": "الصيدليات",
        "restaurants": "المطاعم"
    }
    
    df_services['Category_Arabic'] = df_services['Category'].map(category_translation)
    service_types = df_services['Category_Arabic'].dropna().unique().tolist()
    
    selected_services_ar = st.multiselect("اختر الخدمات المفضلة:", service_types, default=service_types[:1] if service_types else [])
    
    # تحويل الاختيارات العربية إلى الأصلية لاستخدامها في التصفية
    selected_services = [key for key, value in category_translation.items() if value in selected_services_ar]

# تحميل بيانات الشقق
apartments_file = "Cleaned_airbnb_v1.xlsx"
df_apartments = pd.read_excel(apartments_file, sheet_name='Sheet1')

# الاحتفاظ فقط بالأعمدة المهمة
df_services = df_services[['Name', 'Category', 'Longitude', 'Latitude']]
df_apartments = df_apartments[['room_id', 'name', 'price_per_month', 'rating', 'latitude', 'longitude', 'URL']]

st.markdown(
    """
    <div class='main-content'>
    <h1>طريقك لإيجاد نطاقك المفضّل في الرياض!</h1>
    <p style="font-size: 1.5rem; font-weight: bold;">مرحبًا بك في تطبيق <strong>نِطاق</strong>!</p>
    <p>نساعدك في استكشاف الرياض والعثور على النّـطاق المثالي الذي يناسبك، بناءً على المعالم والخدمات القريبة منك.</p>
    </div>
    """,
    unsafe_allow_html=True
)

# === إضافة الخريطة التفاعلية ===
if "clicked_lat" not in st.session_state:
    st.session_state["clicked_lat"] = None
if "clicked_lng" not in st.session_state:
    st.session_state["clicked_lng"] = None

riyadh_center = [24.7136, 46.6753]
m = folium.Map(location=riyadh_center, zoom_start=12)

if st.session_state["clicked_lat"] and st.session_state["clicked_lng"]:
    user_location = (st.session_state["clicked_lat"], st.session_state["clicked_lng"])
    folium.Circle(
        location=user_location,
        radius=radius_km * 1000,
        color="blue",
        fill=True,
        fill_color="blue",
        fill_opacity=0.2
    ).add_to(m)
    folium.Marker(
        location=user_location,
        popup=f"الإحداثيات المختارة\nنصف قطر البحث: {radius_km} كم",
        icon=folium.Icon(color="red", icon="info-sign")
    ).add_to(m)

returned_data = st_folium(m, width=700, height=500, key="map")

if returned_data and returned_data["last_clicked"] is not None:
    lat = returned_data["last_clicked"]["lat"]
    lon = returned_data["last_clicked"]["lng"]
    if 16 <= lat <= 32 and 34 <= lon <= 56:
        st.session_state["clicked_lat"] = lat
        st.session_state["clicked_lng"] = lon
    else:
        st.warning("يبدو أن الإحداثيات خارج حدود السعودية. انقر ضمن الخريطة في نطاق السعودية.")

# تصفية الشقق بناءً على الموقع المختار
if st.session_state["clicked_lat"] and st.session_state["clicked_lng"]:
    user_location = (st.session_state["clicked_lat"], st.session_state["clicked_lng"])
    apartments_tree = cKDTree(df_apartments[["latitude", "longitude"]].values)
    radius = radius_km / 111
    nearest_indices = apartments_tree.query_ball_point([[st.session_state["clicked_lat"], st.session_state["clicked_lng"]]], r=radius)[0]
    nearby_apartments = df_apartments.iloc[nearest_indices].drop_duplicates(subset=["room_id"])
    
    if not nearby_apartments.empty:
        st.write("### 🏠 الشقق القريبة من الموقع المختار")
        st.dataframe(nearby_apartments[['name', 'price_per_month', 'rating', 'URL']], use_container_width=True)
        
        fig = px.scatter_mapbox(nearby_apartments,
                                lat="latitude", lon="longitude",
                                hover_name="name",
                                hover_data=["price_per_month", "rating"],
                                zoom=12, height=500)
        fig.update_layout(mapbox_style="open-street-map")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("لم يتم العثور على شقق بالقرب من الموقع المختار. جرب توسيع نطاق البحث.")

# زر تأكيد الموقع
if st.button("تأكيد الموقع"):
    st.success("تم تأكيد الموقع! (الميزة التالية قيد التطوير)")
