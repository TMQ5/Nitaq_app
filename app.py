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
import chardet

# إعداد صفحة التطبيق
st.set_page_config(
    page_title="طريقك لإيجاد نطاقك المفضّل في الرياض",
    layout="wide"
)

# تحميل صورة الشعار وعرضه في الشريط الجانبي في المنتصف
with st.sidebar:
    st.image('logo.png', use_container_width=True)
    
    st.header("🔍 خيارات البحث")
    
    # نطاق البحث كـ شريط تمرير بين 0 و 15 كم بفواصل 0.5 كم
    radius_km = st.slider("نطاق البحث (كم):", min_value=0.0, max_value=15.0, value=5.0, step=0.5)
    
    # اختيار الخدمات المفضلة من ملف merged_places.xlsx
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

# تحميل بيانات الشقق من ملف Cleaned_airbnb_v1.xlsx
apartments_file = "Cleaned_airbnb_v1.xlsx"
df_apartments = pd.read_excel(apartments_file, sheet_name='Sheet1')

# الاحتفاظ فقط بالأعمدة المهمة في كلا الملفين
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

# ===== استبدال كود الخرائط التفاعلية =====
# (هذا هو الجزء الجديد الذي يعرض الأماكن مع ألوان وأيقونات متعددة)

@st.cache_data
def load_places_data(path):
    with open(path, 'rb') as f:
        raw_data = f.read(10000)  # قراءة عينة من الملف
        result = chardet.detect(raw_data)
        encoding_type = result['encoding']
    return pd.read_csv(path, encoding=encoding_type)

# تحديث مسار ملف بيانات الأماكن حسب الحاجة
places_file_path = "Riyadh_data.xlsx"
try:
    places_df = load_places_data(places_file_path)
    st.success("تم تحميل بيانات الخدمات بنجاح!")
except Exception as e:
    st.error(f"حدث خطأ أثناء تحميل الملف: {e}")
    st.stop()

# تعريف ألوان وأيقونات العلامات لكل فئة من الخدمات
category_styles = {
    "cafes_bakeries": {"color": "orange", "icon": "coffee"},
    "entertainment": {"color": "purple", "icon": "film"},
    "bus": {"color": "blue", "icon": "bus"},
    "groceries": {"color": "green", "icon": "shopping-cart"},
    "gyms": {"color": "red", "icon": "heartbeat"},
    "hospitals_clinics": {"color": "darkred", "icon": "plus-square"},
    "malls": {"color": "pink", "icon": "shopping-cart"},
    "metro": {"color": "darkblue", "icon": "train"},
    "pharmacies": {"color": "lightblue", "icon": "plus-square"}
}

# استخدام نفس قيمة الشريط الخاص بنطاق البحث من الشريط الجانبي (radius_km)
# تهيئة الحالة الخاصة بالإحداثيات عند النقر (إن لم تكن موجودة)
if "clicked_lat" not in st.session_state:
    st.session_state["clicked_lat"] = None
if "clicked_lng" not in st.session_state:
    st.session_state["clicked_lng"] = None
if "selected_categories" not in st.session_state:
    st.session_state["selected_categories"] = []

# إنشاء خريطة مركزها الرياض
riyadh_center = [24.7136, 46.6753]
m = folium.Map(location=riyadh_center, zoom_start=12)

# إذا قام المستخدم بالنقر على الخريطة، عرض العلامة والدائرة الخاصة بالموقع المختار
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

    # السماح للمستخدم باختيار فئات الخدمات من بيانات الأماكن
    st.subheader("اختر نوع الخدمة (يمكن اختيار أكثر من نوع):")
    categories = sorted(places_df["Category"].unique())
    st.session_state["selected_categories"] = st.multiselect("اختر نوع الخدمة:", categories)

    if st.session_state["selected_categories"]:
        # حساب المنطقة الجغرافية (bounding box) لتصفية الأماكن
        lat_deg = radius_km / 111.0
        lon_deg = radius_km / (111.0 * math.cos(math.radians(user_location[0])))

        lat_min = user_location[0] - lat_deg
        lat_max = user_location[0] + lat_deg
        lon_min = user_location[1] - lon_deg
        lon_max = user_location[1] + lon_deg

        mask_bbox = (
            (places_df["Latitude"] >= lat_min) &
            (places_df["Latitude"] <= lat_max) &
            (places_df["Longitude"] >= lon_min) &
            (places_df["Longitude"] <= lon_max)
        )
        places_in_bbox = places_df[mask_bbox]

        # تصفية الأماكن بناءً على المسافة والفئة المختارة
        filtered_places = []
        for _, row in places_in_bbox.iterrows():
            place_location = (row["Latitude"], row["Longitude"])
            distance_km_calc = geodesic(user_location, place_location).km
            if distance_km_calc <= radius_km and row["Category"] in st.session_state["selected_categories"]:
                row_dict = row.to_dict()
                row_dict["Distance (km)"] = round(distance_km_calc, 2)
                filtered_places.append(row_dict)

        # إضافة علامات للأماكن المصفاة مع تنسيق خاص (ألوان وأيقونات)
        for place in filtered_places:
            category = place["Category"]
            marker_color = category_styles.get(category, {}).get("color", "gray")
            marker_icon = category_styles.get(category, {}).get("icon", "info-sign")

            popup_content = (
                f"<b>{place['Name']}</b><br>"
                f"التصنيف: {place['Category']}<br>"
                f"التقييم: {place.get('Rating', 'غير متوفر')} ⭐<br>"
                f"عدد التقييمات: {place.get('Number_of_Ratings', 'غير متوفر')}<br>"
                f"المسافة: {place['Distance (km)']} كم"
            )
            folium.Marker(
                location=(place["Latitude"], place["Longitude"]),
                popup=folium.Popup(popup_content, max_width=300),
                tooltip=popup_content,
                icon=folium.Icon(color=marker_color, icon=marker_icon)
            ).add_to(m)

# عرض الخريطة والتقاط نقرات المستخدم عليها
returned_data = st_folium(m, width=700, height=500, key="map")

# تحديث الحالة الخاصة بالإحداثيات بناءً على آخر نقرة للمستخدم
if returned_data and returned_data["last_clicked"] is not None:
    lat = returned_data["last_clicked"]["lat"]
    lon = returned_data["last_clicked"]["lng"]
    if 16 <= lat <= 32 and 34 <= lon <= 56:
        st.session_state["clicked_lat"] = lat
        st.session_state["clicked_lng"] = lon
    else:
        st.warning("يبدو أن الإحداثيات خارج حدود السعودية. انقر ضمن الخريطة في نطاق السعودية.")

# ===== نهاية كود الخرائط التفاعلية =====

# باقي الكود يبقى كما هو (مثلاً تصفية وعرض بيانات الشقق)
if st.session_state["clicked_lat"] and st.session_state["clicked_lng"]:
    user_location = (st.session_state["clicked_lat"], st.session_state["clicked_lng"])
    apartments_tree = cKDTree(df_apartments[["latitude", "longitude"]].values)
    radius_conv = radius_km / 111
    nearest_indices = apartments_tree.query_ball_point([[st.session_state["clicked_lat"], st.session_state["clicked_lng"]]], r=radius_conv)[0]
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

if st.button("تأكيد الموقع"):
    st.success("تم تأكيد الموقع! (الميزة التالية قيد التطوير)")
