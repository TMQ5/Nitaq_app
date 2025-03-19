import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from scipy.spatial import cKDTree
from PIL import Image

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
    
    # إحداثيات الموقع
    user_lat = st.number_input("خط العرض:", value=24.7136, format="%.6f")
    user_lon = st.number_input("خط الطول:", value=46.6753, format="%.6f")
    
    # اختيار الخدمات المفضلة
    services_file = "merged_places.xlsx"
    df_services = pd.read_excel(services_file, sheet_name='Sheet1')
    service_types = df_services['Type_of_Utility'].unique().tolist()
    selected_services = st.multiselect("اختر الخدمات المفضلة:", service_types, default=[service_types[0]])

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

# تصفية الخدمات بناءً على اختيار المستخدم
filtered_services = df_services[df_services["Category"].isin(selected_services)]

if not filtered_services.empty:
    # بناء شجرة KDTree لتسريع البحث عن الشقق القريبة
    apartments_tree = cKDTree(df_apartments[["latitude", "longitude"]].values)
    
    # تحويل النطاق إلى نطاق بحث فعلي بالأمتار
    radius = radius_km / 111  # تحويل من كم إلى درجات جغرافية
    
    # البحث عن الشقق القريبة لكل خدمة
    nearest_indices = apartments_tree.query_ball_point(filtered_services[["Latitude", "Longitude"]].values, r=radius)
    
    # استخراج الشقق القريبة
    nearby_apartments = df_apartments.iloc[[idx for sublist in nearest_indices for idx in sublist]]
    
    # إزالة التكرارات
    nearby_apartments = nearby_apartments.drop_duplicates(subset=["room_id"])
    
    # عرض النتائج
    if not nearby_apartments.empty:
        st.write("### 🏠 الشقق القريبة من الخدمات المختارة")
        st.dataframe(nearby_apartments[['name', 'price_per_month', 'rating', 'URL']], use_container_width=True)
        
        # عرض الشقق على الخريطة
        fig = px.scatter_mapbox(nearby_apartments,
                                lat="latitude", lon="longitude",
                                hover_name="name",
                                hover_data=["price_per_month", "rating"],
                                zoom=12, height=500)
        
        fig.update_layout(mapbox_style="open-street-map")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("لم يتم العثور على شقق بالقرب من الخدمات المختارة. جرب توسيع نطاق البحث أو اختيار خدمات أخرى.")
else:
    st.warning("يرجى اختيار خدمات للبحث عن الشقق القريبة منها.")

# زر تأكيد الموقع
if st.button("تأكيد الموقع"):
    st.success("تم تأكيد الموقع! (الميزة التالية قيد التطوير)")
