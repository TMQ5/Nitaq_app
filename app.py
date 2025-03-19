import streamlit as st  
import pandas as pd
from geopy.distance import geodesic
from scipy.spatial import cKDTree

# ✅ يجب أن يكون هذا أول أمر يتم تنفيذه
st.set_page_config(
    page_title="طريقك لإيجاد نِطاقك المفضّل في الرياض",
    layout="wide"
)

def set_background(image_url):
    st.markdown(
        f"""
        <style>
        .stApp {{
            background: url("{image_url}") no-repeat center center fixed;
            background-size: cover;
        }}
        </style>
        """,
        unsafe_allow_html=True
    )

# ✅ استدعاء الدالة مع رابط الصورة الخلفية
set_background("https://i.postimg.cc/Twtn64Zr/image.jpg")


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

if "metro" in selected_services:
    # 🔹 تصفية محطات المترو داخل النطاق المحدد
    filtered_metro = []
    for _, row in df_services[df_services["Category"] == "metro"].iterrows():
        metro_location = (row["Latitude"], row["Longitude"])
        distance = geodesic(user_location, metro_location).km
        if distance <= radius_km:
            row_dict = row.to_dict()
            row_dict["المسافة (كم)"] = round(distance, 2)
            filtered_metro.append(row_dict)

    # 🔹 تحويل القائمة إلى DataFrame
    filtered_metro_df = pd.DataFrame(filtered_metro)

    # 🔹 الآن يمكن استخدام `filtered_metro_df` بأمان
    col1, col2 = st.columns([3, 1])

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


# 🔹 تحميل بيانات الأندية الرياضية فقط
if "gyms" in selected_services:
    df_gyms = df_services[df_services["Category"] == "gyms"]

    # 🔹 حساب المسافات للأندية الرياضية
    filtered_gyms = []
    for _, row in df_gyms.iterrows():
        gym_location = (row["Latitude"], row["Longitude"])
        distance = geodesic(user_location, gym_location).km
        if distance <= radius_km:
            row_dict = row.to_dict()
            row_dict["المسافة (كم)"] = round(distance, 2)
            filtered_gyms.append(row_dict)

    filtered_gyms_df = pd.DataFrame(filtered_gyms)

    # 🔹 تقسيم الصفحة إلى عمودين: النص في اليسار والصورة في اليمين
    col1, col2 = st.columns([3, 1])

    with col1:
        st.markdown(f"### 🏋️‍♂️ عدد الأندية الرياضية داخل {radius_km} كم: **{len(filtered_gyms_df)}**")

        if filtered_gyms_df.empty:
            st.markdown("""
                🚨 **لا توجد أي أندية رياضية داخل هذا النطاق!**  
                💀 **إذا كنت ناوي تصير فتنس مود، فكر مليون مرة قبل تسكن هنا!** 😵‍💫  
                بتضطر تتمرن في البيت مع فيديوهات يوتيوب، لأن النادي بعيد جدًا! 🚶‍♂️💨  
                **تبي نادي قريب، ولا تكتفي بتمارين الضغط في الصالة؟ القرار لك!** 🔥
            """, unsafe_allow_html=True)

        elif len(filtered_gyms_df) == 1:
            gym = filtered_gyms_df.iloc[0]
            st.markdown(f"""
                ⚠️ **عدد الأندية الرياضية في هذا النطاق: 1 فقط!**  
                📍 **النادي الوحيد هنا هو:** `{gym['Name']}` وتبعد عنك **{gym['المسافة (كم)']} كم!**  
                🏋️‍♂️ *يعني لو كان زحمة، ما عندك خيارات ثانية! لازم تستحمل الانتظار على الأجهزة الرياضية!* 😬  
                **هل أنت مستعد لهذا التحدي؟**
            """, unsafe_allow_html=True)

        else:
            st.markdown(f"""
                📊 **عدد الأندية الرياضية داخل {radius_km} كم: {len(filtered_gyms_df)} 🏋️‍♂️**  
                👏 *هنيالك! عندك أكثر من خيار، وتقدر تختار النادي اللي يناسبك بدون عناء!* 😉  
                📍 *ما يحتاج تتمرن في البيت، عندك أندية قريبة توفر لك كل شيء تحتاجه!* 💪🔥
            """, unsafe_allow_html=True)

            st.markdown("### 🏋️‍♂️ أقرب 3 أندية رياضية إليك:")
            closest_gyms = filtered_gyms_df.nsmallest(3, "المسافة (كم)")
            for _, row in closest_gyms.iterrows():
                st.markdown(f"🔹 **{row['Name']}** - تبعد {row['المسافة (كم)']} كم")

            # 🔹 **إضافة زر لعرض جميع الأندية**
            if len(filtered_gyms_df) > 3:
                with st.expander("🔍 عرض جميع الأندية"):
                    st.dataframe(filtered_gyms_df[['Name', 'المسافة (كم)']], use_container_width=True)

    with col2:
        # تحميل الصورة
        st.image("GYM.webp", use_container_width=True)



# 🔹 عرض إحصائيات المستشفيات فقط إذا تم اختيارها
# 🔹 تصفية بيانات المستشفيات
df_hospitals = df_services[df_services["Category"] == "hospitals_clinics"]

# 🔹 حساب المسافات للمستشفيات
filtered_hospitals = []
for _, row in df_hospitals.iterrows():
    hospital_location = (row["Latitude"], row["Longitude"])
    distance = geodesic(user_location, hospital_location).km
    if distance <= radius_km:
        row_dict = row.to_dict()
        row_dict["المسافة (كم)"] = round(distance, 2)
        filtered_hospitals.append(row_dict)

filtered_hospitals_df = pd.DataFrame(filtered_hospitals)

if "hospitals_clinics" in selected_services:
    # تقسيم الصفحة إلى عمودين: النص في اليسار والصورة في اليمين
    col1, col2 = st.columns([3, 1])  # العمود الأول أكبر ليحتوي على النص

    with col1:
        st.markdown(f"### 🏥 عدد المستشفيات داخل {radius_km} كم: **{len(filtered_hospitals_df)}**")

        if filtered_hospitals_df.empty:
            st.markdown("""
                🚨 **لا توجد أي مستشفيات داخل هذا النطاق!**  
                💀 **إذا كنت كثير الإصابات أو لديك مراجعات طبية متكررة، فكر مليون مرة قبل تسكن هنا!** 😵‍💫  
                🚑 **ما فيه مستشفى قريب؟ يعني لو صادك مغص نص الليل، بتصير عندك مغامرة إسعافية مشوّقة!**  
                **هل تحب تعيش بعيدًا عن المستشفيات، أم تفضل أن تكون قريبًا من الرعاية الصحية؟ القرار لك!** 🔥
            """, unsafe_allow_html=True)
        elif len(filtered_hospitals_df) == 1:
            hospital = filtered_hospitals_df.iloc[0]
            st.markdown(f"""
                ⚠️ **عدد المستشفيات في هذا النطاق: 1 فقط!**  
                📍 **المستشفى الوحيد هنا هو:** `{hospital['Name']}` وتبعد عنك **{hospital['المسافة (كم)']} كم!**  
                🏥 **إذا كنت تحتاج إلى مستشفى قريب، هذا هو خيارك الوحيد! هل أنت مستعد لهذا التحدي؟** 🤔
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
                📊 **عدد المستشفيات داخل {radius_km} كم: {len(filtered_hospitals_df)} 🏥🚑**  
                👏 **إذا صار شيء، عندك خيارات كثيرة، وما تحتاج تسوي رحلة عبر القارات عشان توصل للطوارئ!** 😅  
                📍 **المستشفيات قريبة منك، وصحتك في أمان!** 💉💊
            """, unsafe_allow_html=True)

            st.markdown("### 🏥 أقرب 3 مستشفيات إليك:")
            closest_hospitals = filtered_hospitals_df.nsmallest(3, "المسافة (كم)")
            for _, row in closest_hospitals.iterrows():
                st.markdown(f"🔹 **{row['Name']}** - تبعد {row['المسافة (كم)']} كم")

            # 🔹 **إضافة زر لعرض جميع المستشفيات**
            if len(filtered_hospitals_df) > 3:
                with st.expander("🔍 عرض جميع المستشفيات"):
                    st.dataframe(filtered_hospitals_df[['Name', 'المسافة (كم)']], use_container_width=True)

    with col2:
        # تحميل الصورة
        st.image("Hospital.webp", use_container_width=True)


# 🔹 تصفية بيانات المولات
df_malls = df_services[df_services["Category"] == "malls"]

# 🔹 حساب المسافات للمولات
filtered_malls = []
for _, row in df_malls.iterrows():
    mall_location = (row["Latitude"], row["Longitude"])
    distance = geodesic(user_location, mall_location).km
    if distance <= radius_km:
        row_dict = row.to_dict()
        row_dict["المسافة (كم)"] = round(distance, 2)
        filtered_malls.append(row_dict)

filtered_malls_df = pd.DataFrame(filtered_malls)

# 🔹 عرض إحصائيات المولات فقط إذا تم اختيارها
if "malls" in selected_services:
    # تقسيم الصفحة إلى عمودين: النص في اليسار والصورة في اليمين
    col1, col2 = st.columns([3, 1])  # العمود الأول أكبر ليحتوي على النص

    with col1:
        st.markdown(f"### 🛍️ عدد المولات داخل {radius_km} كم: **{len(filtered_malls_df)}**")

        if filtered_malls_df.empty:
            st.markdown("""
                🚨 **لا توجد أي مولات داخل هذا النطاق!**  
                💀 **إذا كنت من محبي التسوق، فكر مليون مرة قبل تسكن هنا!** 😵‍💫  
                **ما فيه مول قريب؟ يعني لا مقاهي، لا براندات، لا تخفيضات فجائية؟ بتعيش حياة صعبة!** 🥲
            """, unsafe_allow_html=True)

        elif len(filtered_malls_df) == 1:
            mall = filtered_malls_df.iloc[0]
            st.markdown(f"""
                ⚠️ **عدد المولات في هذا النطاق: 1 فقط!**  
                📍 **المول الوحيد هنا هو:** `{mall['Name']}` وتبعد عنك **{mall['المسافة (كم)']} كم!**  
                🛍️ **يعني لو كنت تدور على تنوع في المحلات، لا تتحمس… هذا هو خيارك الوحيد!** 😬  
            """, unsafe_allow_html=True)

        else:
            st.markdown(f"""
                📊 **عدد المولات داخل {radius_km} كم: {len(filtered_malls_df)} 🛍️✨**  
                👏 **هنيالك!** إذا طفشت، عندك خيارات كثيرة للشوبينغ، ما يحتاج تسافر بعيد عشان تشتري جزمة جديدة! 😉  
                📍 **يعني بكل بساطة، خذ راحتك، وجرب أكثر من مول حسب مزاجك!** 💃🕺
            """, unsafe_allow_html=True)

            st.markdown("### 🛒 أقرب 3 مولات إليك:")
            closest_malls = filtered_malls_df.nsmallest(3, "المسافة (كم)")
            for _, row in closest_malls.iterrows():
                st.markdown(f"🔹 **{row['Name']}** - تبعد {row['المسافة (كم)']} كم")

            # 🔹 **إضافة زر لعرض جميع المولات**
            if len(filtered_malls_df) > 3:
                with st.expander("🔍 عرض جميع المولات"):
                    st.dataframe(filtered_malls_df[['Name', 'المسافة (كم)']], use_container_width=True)

    with col2:
        # تحميل الصورة الخاصة بالمولات
        st.image("Mall.webp", use_container_width=True)



# 🔹 تصفية بيانات محلات البقالة والسوبرماركت
df_groceries = df_services[df_services["Category"] == "groceries"]

# 🔹 حساب المسافات لمحلات السوبرماركت
filtered_groceries = []
for _, row in df_groceries.iterrows():
    grocery_location = (row["Latitude"], row["Longitude"])
    distance = geodesic(user_location, grocery_location).km
    if distance <= radius_km:
        row_dict = row.to_dict()
        row_dict["المسافة (كم)"] = round(distance, 2)
        filtered_groceries.append(row_dict)

filtered_groceries_df = pd.DataFrame(filtered_groceries)

# 🔹 عرض إحصائيات السوبرماركت فقط إذا تم اختيارها
if "groceries" in selected_services:
    # تقسيم الصفحة إلى عمودين: النص في اليسار والصورة في اليمين
    col1, col2 = st.columns([3, 1])  # العمود الأول أكبر ليحتوي على النص

    with col1:
        st.markdown(f"### 🛒 عدد محلات البقالة داخل {radius_km} كم: **{len(filtered_groceries_df)}**")

        if filtered_groceries_df.empty:
            st.markdown("""
                🚨 **لا توجد أي محلات بقالة أو سوبرماركت داخل هذا النطاق!**  
                💀 **إذا كنت من النوع اللي يشتري أكل بيومه، فكر مليون مرة قبل تسكن هنا!** 😵‍💫  
                **يعني إذا خلصت البيض فجأة؟ لازم مشوار عشان تجيب كرتون جديد!** 🥚🚗
            """, unsafe_allow_html=True)

        elif len(filtered_groceries_df) == 1:
            grocery = filtered_groceries_df.iloc[0]
            st.markdown(f"""
                ⚠️ **عدد محلات البقالة في هذا النطاق: 1 فقط!**  
                📍 **المحل الوحيد هنا هو:** `{grocery['Name']}` وتبعد عنك **{grocery['المسافة (كم)']} كم!**  
                🛒 **يعني إذا كان زحمة، أو سكّر بدري، فأنت في ورطة! جهّز نفسك لطلب التوصيل أو خزن الأكل مسبقًا!** 😬  
            """, unsafe_allow_html=True)

        else:
            st.markdown(f"""
                📊 **عدد محلات البقالة داخل {radius_km} كم: {len(filtered_groceries_df)} 🛒🥦**  
                👏 **ما يحتاج تشيل هم الأكل، عندك محلات كثيرة تقدر تشتري منها أي وقت!** 😉  
                📍 **لو نسيت تشتري خبز، ما يحتاج مشوار طويل، أقرب بقالة عندك!** 🍞🥛
            """, unsafe_allow_html=True)

            st.markdown("### 🛒 أقرب 3 محلات بقالة إليك:")
            closest_groceries = filtered_groceries_df.nsmallest(3, "المسافة (كم)")
            for _, row in closest_groceries.iterrows():
                st.markdown(f"🔹 **{row['Name']}** - تبعد {row['المسافة (كم)']} كم")

            # 🔹 **إضافة زر لعرض جميع محلات البقالة**
            if len(filtered_groceries_df) > 3:
                with st.expander("🔍 عرض جميع محلات البقالة"):
                    st.dataframe(filtered_groceries_df[['Name', 'المسافة (كم)']], use_container_width=True)

    with col2:
        # تحميل الصورة الخاصة بالسوبرماركت
        st.image("supermarket.webp", use_container_width=True)


# 🔹 تصفية بيانات أماكن الترفيه
df_entertainment = df_services[df_services["Category"] == "entertainment"]

# 🔹 حساب المسافات لأماكن الترفيه
filtered_entertainment = []
for _, row in df_entertainment.iterrows():
    entertainment_location = (row["Latitude"], row["Longitude"])
    distance = geodesic(user_location, entertainment_location).km
    if distance <= radius_km:
        row_dict = row.to_dict()
        row_dict["المسافة (كم)"] = round(distance, 2)
        filtered_entertainment.append(row_dict)

filtered_entertainment_df = pd.DataFrame(filtered_entertainment)

# 🔹 عرض إحصائيات أماكن الترفيه فقط إذا تم اختيارها
if "entertainment" in selected_services:
    # تقسيم الصفحة إلى عمودين: النص في اليسار والصورة في اليمين
    col1, col2 = st.columns([3, 1])  # العمود الأول أكبر ليحتوي على النص

    with col1:
        st.markdown(f"### 🎭 عدد أماكن الترفيه داخل {radius_km} كم: **{len(filtered_entertainment_df)}**")

        if filtered_entertainment_df.empty:
            st.markdown("""
                🚨 **لا توجد أي أماكن ترفيه داخل هذا النطاق!**  
                💀 **إذا كنت تحب الطلعات والأماكن الحماسية، فكر مليون مرة قبل تسكن هنا!** 😵‍💫  
                **يعني لا سينما، لا ملاهي، لا جلسات حلوة؟! الحياة بتكون مملة جدًا! 😭**
            """, unsafe_allow_html=True)

        elif len(filtered_entertainment_df) == 1:
            entertainment = filtered_entertainment_df.iloc[0]
            st.markdown(f"""
                ⚠️ **عدد أماكن الترفيه في هذا النطاق: 1 فقط!**  
                📍 **المكان الوحيد هنا هو:** `{entertainment['Name']}` وتبعد عنك **{entertainment['المسافة (كم)']} كم!**  
                🎢 **يعني لو طفشت، عندك خيار واحد فقط! تحب تكرر نفس المشوار؟ ولا تفضل يكون عندك تنوع؟** 🤔
            """, unsafe_allow_html=True)

        else:
            st.markdown(f"""
                📊 **عدد أماكن الترفيه داخل {radius_km} كم: {len(filtered_entertainment_df)} 🎢🎭**  
                👏 **يا حظك! عندك أماكن كثيرة للترفيه، يعني ما فيه ملل أبد!** 😍  
                📍 **إذا كنت تحب السينما، الألعاب، أو الجلسات الممتعة، تقدر تخطط لطلعات بدون تفكير!** 🍿🎮
            """, unsafe_allow_html=True)

            st.markdown("### 🎭 أقرب 3 أماكن ترفيه إليك:")
            closest_entertainment = filtered_entertainment_df.nsmallest(3, "المسافة (كم)")
            for _, row in closest_entertainment.iterrows():
                st.markdown(f"🔹 **{row['Name']}** - تبعد {row['المسافة (كم)']} كم")

            # 🔹 **إضافة زر لعرض جميع أماكن الترفيه**
            if len(filtered_entertainment_df) > 3:
                with st.expander("🔍 عرض جميع أماكن الترفيه"):
                    st.dataframe(filtered_entertainment_df[['Name', 'المسافة (كم)']], use_container_width=True)

    with col2:
        # تحميل الصورة الخاصة بأماكن الترفيه
        st.image("Event.webp", use_container_width=True)


# 🔹 تصفية بيانات المقاهي والمخابز
df_cafes_bakeries = df_services[df_services["Category"] == "cafes_bakeries"]

# 🔹 حساب المسافات للمقاهي والمخابز
filtered_cafes_bakeries = []
for _, row in df_cafes_bakeries.iterrows():
    cafe_location = (row["Latitude"], row["Longitude"])
    distance = geodesic(user_location, cafe_location).km
    if distance <= radius_km:
        row_dict = row.to_dict()
        row_dict["المسافة (كم)"] = round(distance, 2)
        filtered_cafes_bakeries.append(row_dict)

filtered_cafes_bakeries_df = pd.DataFrame(filtered_cafes_bakeries)

# 🔹 عرض إحصائيات المقاهي والمخابز فقط إذا تم اختيارها
if "cafes_bakeries" in selected_services:
    # تقسيم الصفحة إلى عمودين: النص في اليسار والصورة في اليمين
    col1, col2 = st.columns([3, 1])  # العمود الأول أكبر ليحتوي على النص

    with col1:
        st.markdown(f"### ☕ عدد المقاهي والمخابز داخل {radius_km} كم: **{len(filtered_cafes_bakeries_df)}**")

        if filtered_cafes_bakeries_df.empty:
            st.markdown("""
                🚨 **لا توجد أي مقاهي أو مخابز داخل هذا النطاق!**  
                💀 **إذا كنت من مدمني القهوة أو عاشق الدونات، فكر مليون مرة قبل تسكن هنا!** 😵‍💫  
                **يعني لا كابتشينو صباحي؟ لا كرواسون طازج؟ بتعيش حياة جافة جدًا! 😭☕🥐**
            """, unsafe_allow_html=True)

        elif len(filtered_cafes_bakeries_df) == 1:
            cafe = filtered_cafes_bakeries_df.iloc[0]
            st.markdown(f"""
                ⚠️ **عدد المقاهي والمخابز في هذا النطاق: 1 فقط!**  
                📍 **المكان الوحيد هنا هو:** `{cafe['Name']}` وتبعد عنك **{cafe['المسافة (كم)']} كم!**  
                ☕ **يعني لو طفشت من نفس المقهى، ما عندك غيره! تحب تكرر نفس القهوة كل يوم؟ ولا تفضّل تنوع؟** 🤔
            """, unsafe_allow_html=True)

        else:
            st.markdown(f"""
                📊 **عدد المقاهي والمخابز داخل {radius_km} كم: {len(filtered_cafes_bakeries_df)} ☕🍩**  
                👏 **أنت في نعيم! عندك مقاهي ومخابز كثيرة، يعني صباحاتك بتكون مثالية وكل يوم تجرب شيء جديد!** 😍  
                📍 **سواء تحب اللاتيه، الإسبريسو، أو الدونات، الخيارات عندك كثيرة!** 🥐☕
            """, unsafe_allow_html=True)

            st.markdown("### 🍩 أقرب 3 مقاهي ومخابز إليك:")
            closest_cafes_bakeries = filtered_cafes_bakeries_df.nsmallest(3, "المسافة (كم)")
            for _, row in closest_cafes_bakeries.iterrows():
                st.markdown(f"🔹 **{row['Name']}** - تبعد {row['المسافة (كم)']} كم")

            # 🔹 **إضافة زر لعرض جميع المقاهي والمخابز**
            if len(filtered_cafes_bakeries_df) > 3:
                with st.expander("🔍 عرض جميع المقاهي والمخابز"):
                    st.dataframe(filtered_cafes_bakeries_df[['Name', 'المسافة (كم)']], use_container_width=True)

    with col2:
        # تحميل الصورة الخاصة بالمقاهي والمخابز
        st.image("Cafe.webp", use_container_width=True)


# 🔹 تصفية بيانات المطاعم
df_restaurants = df_services[df_services["Category"] == "restaurants"]

# 🔹 حساب المسافات للمطاعم
filtered_restaurants = []
for _, row in df_restaurants.iterrows():
    restaurant_location = (row["Latitude"], row["Longitude"])
    distance = geodesic(user_location, restaurant_location).km
    if distance <= radius_km:
        row_dict = row.to_dict()
        row_dict["المسافة (كم)"] = round(distance, 2)
        filtered_restaurants.append(row_dict)

filtered_restaurants_df = pd.DataFrame(filtered_restaurants)

# 🔹 عرض إحصائيات المطاعم فقط إذا تم اختيارها
if "restaurants" in selected_services:
    # تقسيم الصفحة إلى عمودين: النص في اليسار والصورة في اليمين
    col1, col2 = st.columns([3, 1])  # العمود الأول أكبر ليحتوي على النص

    with col1:
        st.markdown(f"### 🍽️ عدد المطاعم داخل {radius_km} كم: **{len(filtered_restaurants_df)}**")

        if filtered_restaurants_df.empty:
            st.markdown("""
                🚨 **لا توجد أي مطاعم داخل هذا النطاق!**  
                💀 **إذا كنت تعتمد على المطاعم وما تطبخ، فكر مليون مرة قبل تسكن هنا!** 😵‍💫  
                **يعني لا برجر، لا بيتزا، لا شاورما؟ بتعيش على النودلز والبيض المقلي؟ 🥲🍳**
            """, unsafe_allow_html=True)

        elif len(filtered_restaurants_df) == 1:
            restaurant = filtered_restaurants_df.iloc[0]
            st.markdown(f"""
                ⚠️ **عدد المطاعم في هذا النطاق: 1 فقط!**  
                📍 **المطعم الوحيد هنا هو:** `{restaurant['Name']}` وتبعد عنك **{restaurant['المسافة (كم)']} كم!**  
                🍽️ **يعني لو ما عجبك، مالك إلا تطبخ بنفسك! تبي تعيش على منيو محدود؟ ولا تفضل يكون عندك تنوع؟** 🤔
            """, unsafe_allow_html=True)

        else:
            st.markdown(f"""
                📊 **عدد المطاعم داخل {radius_km} كم: {len(filtered_restaurants_df)} 🍔🍕**  
                👏 **هنيالك! عندك مطاعم كثيرة، يعني خياراتك مفتوحة سواء تبغى شاورما، سوشي، ولا مندي!** 😍  
                📍 **كل يوم تقدر تجرب مطعم جديد، وما فيه ملل أبد!** 🍛🍣
            """, unsafe_allow_html=True)

            st.markdown("### 🍔 أقرب 3 مطاعم إليك:")
            closest_restaurants = filtered_restaurants_df.nsmallest(3, "المسافة (كم)")
            for _, row in closest_restaurants.iterrows():
                st.markdown(f"🔹 **{row['Name']}** - تبعد {row['المسافة (كم)']} كم")

            # 🔹 **إضافة زر لعرض جميع المطاعم**
            if len(filtered_restaurants_df) > 3:
                with st.expander("🔍 عرض جميع المطاعم"):
                    st.dataframe(filtered_restaurants_df[['Name', 'المسافة (كم)']], use_container_width=True)

    with col2:
        # تحميل الصورة الخاصة بالمطاعم
        st.image("restaurant.webp", use_container_width=True)


# 🔹 تصفية بيانات محطات الباص
df_bus_stations = df_services[df_services["Category"] == "bus"]

# 🔹 حساب المسافات لمحطات الباص
filtered_bus_stations = []
for _, row in df_bus_stations.iterrows():
    bus_location = (row["Latitude"], row["Longitude"])
    distance = geodesic(user_location, bus_location).km
    if distance <= radius_km:
        row_dict = row.to_dict()
        row_dict["المسافة (كم)"] = round(distance, 2)
        filtered_bus_stations.append(row_dict)

filtered_bus_stations_df = pd.DataFrame(filtered_bus_stations)

# 🔹 عرض إحصائيات محطات الباص فقط إذا تم اختيارها
if "bus" in selected_services:
    # تقسيم الصفحة إلى عمودين: النص في اليسار والصورة في اليمين
    col1, col2 = st.columns([3, 1])  # العمود الأول أكبر ليحتوي على النص

    with col1:
        st.markdown(f"### 🚌 عدد محطات الباص داخل {radius_km} كم: **{len(filtered_bus_stations_df)}**")

        if filtered_bus_stations_df.empty:
            st.markdown("""
                🚨 **لا توجد أي محطات باص داخل هذا النطاق!**  
                💀 **إذا كنت تعتمد على الباصات في تنقلاتك، فكر مليون مرة قبل تسكن هنا!** 😵‍💫  
                **يعني لازم تمشي مشوار محترم عشان تلقى محطة؟ بتصير خبير في المشي بالغصب! 🚶‍♂️😂**
            """, unsafe_allow_html=True)

        elif len(filtered_bus_stations_df) == 1:
            bus_station = filtered_bus_stations_df.iloc[0]
            st.markdown(f"""
                ⚠️ **عدد محطات الباص في هذا النطاق: 1 فقط!**  
                📍 **المحطة الوحيدة هنا هي:** `{bus_station['Name']}` وتبعد عنك **{bus_station['المسافة (كم)']} كم!**  
                🚌 *🚏 يعني لو فاتك الباص، لا تشيل هم، بعد ٦ دقايق بيجيك الثاني! بس المشكلة؟ إذا كانت المحطة بعيدة، بتتمشى مشوار محترم كل مرة! 😬 تبي تعتمد على محطة وحدة؟ ولا تفضل يكون عندك خيارات أقرب؟* 🤔
            """, unsafe_allow_html=True)

        else:
            st.markdown(f"""
                📊 **عدد محطات الباص داخل {radius_km} كم: {len(filtered_bus_stations_df)} 🚌🚏**  
                👏 **يا سلام! عندك محطات باص كثيرة، تنقلاتك صارت سهلة وما تحتاج تنتظر طويل!** 😍  
                📍 **ما تحتاج تمشي كثير، أقرب محطة جنبك، ومستعد تنطلق لمشاويرك!** 🚍💨
            """, unsafe_allow_html=True)

            st.markdown("### 🚏 أقرب 3 محطات باص إليك:")
            closest_bus_stations = filtered_bus_stations_df.nsmallest(3, "المسافة (كم)")
            for _, row in closest_bus_stations.iterrows():
                st.markdown(f"🔹 **{row['Name']}** - تبعد {row['المسافة (كم)']} كم")

            # 🔹 **إضافة زر لعرض جميع محطات الباص**
            if len(filtered_bus_stations_df) > 3:
                with st.expander("🔍 عرض جميع محطات الباص"):
                    st.dataframe(filtered_bus_stations_df[['Name', 'المسافة (كم)']], use_container_width=True)

    with col2:
        # تحميل الصورة الخاصة بمحطات الباص
        st.image("bus.webp", use_container_width=True)





# -------------------------------------------------------------
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
