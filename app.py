import streamlit as st
import pandas as pd
from geopy.distance import geodesic
from scipy.spatial import cKDTree

# 🔹 إعداد الصفحة
st.set_page_config(
    page_title="طريقك لإيجاد نِطاقك المفضّل في الرياض",
    layout="wide"
)

# 🔹 تحميل الشعار في الشريط الجانبي
with st.sidebar:
    st.image('logo.png', use_container_width=True)

    st.header("🔍 خيارات البحث")
    
    # 🔹 إدخال الإحداثيات مرة واحدة فقط
    user_lat = st.number_input("خط العرض:", value=24.7136, format="%.6f")
    user_lon = st.number_input("خط الطول:", value=46.6753, format="%.6f")
    user_location = (user_lat, user_lon)

    # 🔹 تحديد نطاق البحث
    radius_km = st.slider("نطاق البحث (كم):", min_value=1.0, max_value=15.0, value=5.0, step=0.5)

    # 🔹 اختيار الخدمات المفضلة
    services_file = "merged_places.xlsx"
    df_services = pd.read_excel(services_file, sheet_name='Sheet1', engine="openpyxl")

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

# 🔹 تحميل بيانات الصيدليات فقط
df_pharmacies = df_services[df_services["Category"] == "pharmacies"]

# 🔹 حساب المسافات للصيدليات
filtered_pharmacies = []
for _, row in df_pharmacies.iterrows():
    pharmacy_location = (row["Latitude"], row["Longitude"])
    distance = geodesic(user_location, pharmacy_location).km
    if distance <= radius_km:
        row_dict = row.to_dict()
        row_dict["المسافة (كم)"] = round(distance, 2)
        filtered_pharmacies.append(row_dict)

filtered_pharmacies_df = pd.DataFrame(filtered_pharmacies)
# 🔹 عرض إحصائيات الصيدليات فقط إذا تم اختيارها
if "pharmacies" in selected_services:
    # تقسيم الصفحة إلى عمودين: النص في اليسار والصورة في اليمين
    col1, col2 = st.columns([3, 1])  # العمود الأول أكبر ليحتوي على النص

    with col1:
        st.markdown(f"### 🏥 عدد الصيدليات داخل {radius_km} كم: **{len(filtered_pharmacies_df)}**")

        if filtered_pharmacies_df.empty:
            st.markdown("""
                🚨 **لا توجد أي صيدليات داخل هذا النطاق!**  
                💀 **إذا مفاصلك تعبانة أو تحتاج دواء يومي، فكر مليون مرة قبل تسكن هنا!** 😵‍💫  
                فجأة يهجم عليك صداع، تدور بانادول… وما تلاقي إلا مشوار طويل بانتظارك! 🚗  
                **تبي مغامرة يومية للبحث عن صيدلية؟ ولا تبي صيدلية جنب البقالة؟ القرار لك!** 🔥
            """, unsafe_allow_html=True)
        elif len(filtered_pharmacies_df) == 1:
            pharmacy = filtered_pharmacies_df.iloc[0]
            st.markdown(f"""
                ⚠️ **عدد الصيدليات في هذا النطاق: 1 فقط!**  
                📍 **الصيدلية الوحيدة هنا هي:** `{pharmacy['Name']}` وتبعد عنك **{pharmacy['المسافة (كم)']} كم!**  
                💊 **إذا كنت شخص يعتمد على الأدوية اليومية أو عندك إصابات متكررة، فكر مرتين قبل تسكن هنا، لأن الصيدلية الوحيدة ممكن تكون مغلقة وقت الحاجة!** 😬
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
                📊 **عدد الصيدليات داخل {radius_km} كم: {len(filtered_pharmacies_df)} 💊**  
                👏 **تقدر تطمن!** لو احتجت بانادول في نص الليل، فيه خيارات متاحة لك 😉  
                📍 **عندك عدة صيدليات حولك، وما يحتاج تطق مشوار طويل عشان تجيب دواء بسيط!** 🚗💨
            """, unsafe_allow_html=True)

            st.markdown("### 🏥 أقرب 3 صيدليات إليك:")
            closest_pharmacies = filtered_pharmacies_df.nsmallest(3, "المسافة (كم)")
            for _, row in closest_pharmacies.iterrows():
                st.markdown(f"🔹 **{row['Name']}** - تبعد {row['المسافة (كم)']} كم")

            # 🔹 **إضافة زر لعرض جميع الصيدليات**
            if len(filtered_pharmacies_df) > 3:
                with st.expander("🔍 عرض جميع الصيدليات"):
                    st.dataframe(filtered_pharmacies_df[['Name', 'المسافة (كم)']], use_container_width=True)

    with col2:
        # تحميل الصورة
        st.image("Pharmacy.webp", use_container_width=True)

# 🔹 عرض إحصائيات محطات المترو فقط إذا تم اختيارها
if "metro" in selected_services:
    # تقسيم الصفحة إلى عمودين: النص في اليسار والصورة في اليمين
    col1, col2 = st.columns([3, 1])  # العمود الأول أكبر ليحتوي على النص

    with col1:
        st.markdown(f"### 🚉 عدد محطات المترو داخل {radius_km} كم: **{len(filtered_metro_df)}**")

        if filtered_metro_df.empty:
            st.markdown("""
                🚨 **لا توجد أي محطات مترو داخل هذا النطاق!**  
                💀 **إذا كنت تعتمد على المترو يوميًا، فكر مليون مرة قبل تسكن هنا!** 😵‍💫  
                فجأة تحتاج مشوار سريع، وتكتشف أنك عالق في الزحمة 🚗🚦  
                **تبي تعيش بدون مترو؟ ولا تبي محطة جنب بيتك؟ القرار لك!** 🔥
            """, unsafe_allow_html=True)

        elif len(filtered_metro_df) == 1:
            metro = filtered_metro_df.iloc[0]
            st.markdown(f"""
                ⚠️ **عدد محطات المترو في هذا النطاق: 1 فقط!**  
                📍 **المحطة الوحيدة هنا هي:** `{metro['Name']}` وتبعد عنك **{metro['المسافة (كم)']} كم!**  
                🚆 **إذا كنت تعتمد على المترو يوميًا، فكر مرتين قبل تسكن هنا، لأن المحطة الوحيدة قد تكون بعيدة وقت الحاجة!** 😬
            """, unsafe_allow_html=True)

        else:
            st.markdown(f"""
                📊 **عدد محطات المترو داخل {radius_km} كم: {len(filtered_metro_df)} 🚆**  
                👏 **تقدر تطمن!** لو احتجت المترو في أي وقت، عندك خيارات متاحة لك 😉  
                📍 **عندك عدة محطات مترو حولك، وما تحتاج تفكر في الزحمة!** 🚄💨
            """, unsafe_allow_html=True)

            st.markdown("### 🚉 أقرب 3 محطات مترو إليك:")
            closest_metro = filtered_metro_df.nsmallest(3, "المسافة (كم)")
            for _, row in closest_metro.iterrows():
                st.markdown(f"🔹 **{row['Name']}** - تبعد {row['المسافة (كم)']} كم")

            # 🔹 **إضافة زر لعرض جميع محطات المترو**
            if len(filtered_metro_df) > 3:
                with st.expander("🔍 عرض جميع محطات المترو"):
                    st.dataframe(filtered_metro_df[['Name', 'المسافة (كم)']], use_container_width=True)

    with col2:
        # تحميل صورة لمحطات المترو
        st.image("Metro.webp", use_container_width=True)


# 🔹 تحميل بيانات الشقق
apartments_file = "Cleaned_airbnb_v1.xlsx"
df_apartments = pd.read_excel(apartments_file, sheet_name='Sheet1', engine="openpyxl")

df_apartments = df_apartments[['room_id', 'name', 'price_per_month', 'rating', 'latitude', 'longitude', 'URL']]

# 🔹 تصفية الشقق بناءً على الخدمات المحددة
filtered_services = df_services[df_services["Category"].isin(selected_services)]

if not filtered_services.empty:
    # 🔹 بناء شجرة KDTree للبحث عن الشقق القريبة
    apartments_tree = cKDTree(df_apartments[["latitude", "longitude"]].values)

    # 🔹 تحويل نطاق البحث إلى درجات جغرافية
    radius = radius_km / 111

    # 🔹 البحث عن الشقق القريبة لكل خدمة
    nearest_indices = apartments_tree.query_ball_point(filtered_services[["Latitude", "Longitude"]].values, r=radius)

    # 🔹 استخراج الشقق القريبة
    nearby_apartments = df_apartments.iloc[[idx for sublist in nearest_indices for idx in sublist]]

    # 🔹 إزالة التكرارات
    nearby_apartments = nearby_apartments.drop_duplicates(subset=["room_id"])

    # 🔹 عرض الشقق القريبة
    if not nearby_apartments.empty:
        st.write("### 🏠 الشقق القريبة من الخدمات المختارة")
        st.dataframe(nearby_apartments[['name', 'price_per_month', 'rating', 'URL']], use_container_width=True)
    else:
        st.warning("لم يتم العثور على شقق بالقرب من الخدمات المختارة. جرب توسيع نطاق البحث أو اختيار خدمات أخرى.")
else:
    st.warning("يرجى اختيار خدمات للبحث عن الشقق القريبة منها.")

# 🔹 زر تأكيد الموقع
if st.button("تأكيد الموقع"):
    st.success("تم تأكيد الموقع! (الميزة التالية قيد التطوير)")
