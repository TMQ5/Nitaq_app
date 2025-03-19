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

# تحميل صورة الشعار وعرضه في الشريط الجانبي
with st.sidebar:
    st.image('logo.png', use_container_width=True)
    st.header("🔍 خيارات البحث")
    
    # نطاق البحث كشريط تمرير بين 0 و15 كم بفواصل 0.5 كم
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
    # تحويل الاختيارات العربية إلى الأصلية للتصفية
    selected_services = [key for key, value in category_translation.items() if value in selected_services_ar]

# تحميل بيانات الشقق من ملف Cleaned_airbnb_v1.xlsx
apartments_file = "Cleaned_airbnb_v1.xlsx"
df_apartments = pd.read_excel(apartments_file, sheet_name='Sheet1')
# الاحتفاظ بالأعمدة المهمة
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

# ===== قسم خرائط الأماكن =====
@st.cache_data
def load_places_data(path):
    return pd.read_excel(path, engine="openpyxl")

# تحديد مسار ملف بيانات الأماكن (Riyadh_data.xlsx)
path = "Riyadh_data.xlsx"
try:
    places_df = load_places_data(path)
    st.success("تم تحميل بيانات الخدمات بنجاح!")
except Exception as e:
    st.error(f"حدث خطأ أثناء تحميل الملف: {e}")
    st.stop()

# تعريف ألوان وأيقونات العلامات لكل فئة
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

# تهيئة الحالة الخاصة بالإحداثيات عند النقر
if "clicked_lat" not in st.session_state:
    st.session_state["clicked_lat"] = None
if "clicked_lng" not in st.session_state:
    st.session_state["clicked_lng"] = None
if "selected_categories" not in st.session_state:
    st.session_state["selected_categories"] = []

# إنشاء خريطة مركزها الرياض
riyadh_center = [24.7136, 46.6753]
m = folium.Map(location=riyadh_center, zoom_start=12)

# إذا قام المستخدم بالنقر على الخريطة، يتم عرض الدائرة والعلامة
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
        
        # إضافة علامات الأماكن المصفاة على الخريطة
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

# عرض الخريطة والتقاط نقرات المستخدم
returned_data = st_folium(m, width=700, height=500, key="map")
if returned_data and returned_data["last_clicked"] is not None:
    lat = returned_data["last_clicked"]["lat"]
    lon = returned_data["last_clicked"]["lng"]
    if 16 <= lat <= 32 and 34 <= lon <= 56:
        st.session_state["clicked_lat"] = lat
        st.session_state["clicked_lng"] = lon
    else:
        st.warning("يبدو أن الإحداثيات خارج حدود السعودية. انقر ضمن الخريطة في نطاق السعودية.")

# ===== نهاية قسم خرائط الأماكن =====

# قسم عرض بيانات الصيدليات بتنسيق HTML باستخدام st.markdown
# التأكد من تعريف pharmacies_df، user_location، ونطاق البحث (radius_km)
# إذا لم تكن معرفّة، نقوم بتعريف مثال وهمي:
if "pharmacies_df" not in st.session_state:
    data = {
        "Name": ["صيدلية ألف", "صيدلية باء", "صيدلية جيم"],
        "Latitude": [24.7136, 24.715, 24.710],
        "Longitude": [46.6753, 46.678, 46.670]
    }
    pharmacies_df = pd.DataFrame(data)
    st.session_state["pharmacies_df"] = pharmacies_df
else:
    pharmacies_df = st.session_state["pharmacies_df"]

# تحديد موقع المستخدم للصيدليات: إذا لم يتم النقر، نستخدم موقع افتراضي (مركز الرياض)
if not st.session_state["clicked_lat"] or not st.session_state["clicked_lng"]:
    user_location = (24.7136, 46.6753)
else:
    user_location = (st.session_state["clicked_lat"], st.session_state["clicked_lng"])

filtered_pharmacies = []
for _, row in pharmacies_df.iterrows():
    pharmacy_location = (row["Latitude"], row["Longitude"])
    distance = geodesic(user_location, pharmacy_location).km  
    if distance <= radius_km:
        row_dict = row.to_dict()
        row_dict["Distance (km)"] = round(distance, 2)
        filtered_pharmacies.append(row_dict)
filtered_pharmacies_df = pd.DataFrame(filtered_pharmacies)

# تحديد مسار الصورة (تأكد من صحة المسار حسب بيئتك)
image_path = "/content/Pharmacy.webp"  

html_content = f"""
<style>
    .container {{
        display: flex;
        align-items: center;
        justify-content: space-between;
    }}
    .stats {{
        width: 60%;
        font-size: 16px;
        line-height: 1.6;
    }}
    .stats strong {{
        color: #D72638;
    }}
    .image {{
        width: 35%;
        text-align: right;
    }}
    img {{
        max-width: 100%;
        border-radius: 10px;
    }}
    .hidden {{
        display: none;
    }}
    .pharmacy-list li {{
        margin-bottom: 5px;
    }}
    .btn {{
        background-color: #007BFF;
        color: white;
        padding: 8px 12px;
        border: none;
        cursor: pointer;
        margin-top: 10px;
        border-radius: 5px;
    }}
    .btn:hover {{
        background-color: #0056b3;
    }}
</style>

<div class="container">
    <div class="stats">
"""

if filtered_pharmacies_df.empty:
    html_content += """
        <h2>🚨 لا توجد أي صيدليات داخل هذا النطاق!</h2>
        <p>💀 <strong>إذا مفاصلك تعبانة أو تحتاج دواء يومي، فكر مليون مرة قبل تسكن هنا!</strong> 😵‍💫 <br>
        فجأة يهجم عليك صداع، تدور بانادول… وما تلاقي إلا مشوار طويل بانتظارك! 🚗 <br>
        <strong>تبي مغامرة يومية للبحث عن صيدلية؟ ولا تبي صيدلية جنب البقالة؟ القرار لك!</strong> 🔥</p>
    """
elif len(filtered_pharmacies_df) == 1:
    pharmacy = filtered_pharmacies_df.iloc[0]
    html_content += f"""
        <h2>⚠️ عدد الصيدليات في هذا النطاق: 1 فقط!</h2>
        <p>📍 <strong>الصيدلية الوحيدة هنا هي:</strong> {pharmacy['Name']} وتبعد عنك <strong>{pharmacy['Distance (km)']} كم!</strong></p>
        <p>💊 <strong>إذا كنت شخص يعتمد على الأدوية اليومية أو عندك إصابات متكررة، فكر مرتين قبل تسكن هنا، لأن الصيدلية الوحيدة ممكن تكون مغلقة وقت الحاجة!</strong> 😬</p>
    """
else:
    html_content += f"""
        <h2>📊 عدد الصيدليات داخل {radius_km} كم: {len(filtered_pharmacies_df)} 💊</h2>
        <p>👏 <strong>تقدر تطمن!</strong> لو احتجت بانادول في نص الليل، فيه خيارات متاحة لك. 😉 <br>
        📍 عندك عدة صيدليات حولك، وما يحتاج تطق مشوار طويل عشان تجيب دواء بسيط! 🚗💨</p>
        <h3>🏥 أقرب 3 صيدليات إليك:</h3>
        <ul id="pharmacy-list" class="pharmacy-list">
    """
    for i, row in filtered_pharmacies_df.head(3).iterrows():
        html_content += f"<li>🔹 {row['Name']} - تبعد {row['Distance (km)']} كم</li>"
    html_content += """
        </ul>
        <button class="btn" onclick="showMore()">عرض الكل</button>
        <button class="btn hidden" onclick="showLess()">إظهار أقل</button>
        <ul id="hidden-pharmacies" class="pharmacy-list hidden">
    """
    for i, row in filtered_pharmacies_df.iloc[3:].iterrows():
        html_content += f"<li>🔹 {row['Name']} - تبعد {row['Distance (km)']} كم</li>"
    html_content += """
        </ul>
    """

html_content += f"""
    </div>
    <div class="image">
        <img src="{image_path}" alt="No Pharmacies Warning">
    </div>
</div>

<script>
    function showMore() {{
        document.getElementById('hidden-pharmacies').classList.remove('hidden');
        document.querySelector('.btn.hidden').classList.remove('hidden');
        document.querySelector('button[onclick="showMore()"]').classList.add('hidden');
    }}
    function showLess() {{
        document.getElementById('hidden-pharmacies').classList.add('hidden');
        document.querySelector('.btn.hidden').classList.add('hidden');
        document.querySelector('button[onclick="showMore()"]').classList.remove('hidden');
    }}
</script>
"""

st.markdown(html_content, unsafe_allow_html=True)

# قسم عرض بيانات الشقق (يظل كما هو)
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
