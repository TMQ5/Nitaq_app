import streamlit as st
import pandas as pd
from geopy.distance import geodesic

# 🔹 تحميل بيانات الصيدليات
services_file = "merged_places.xlsx"
df_services = pd.read_excel(services_file, sheet_name='Sheet1', engine="openpyxl")

# 🔹 تصفية الصيدليات فقط
df_services = df_services[df_services["Category"] == "pharmacies"]

# 🔹 إدخال بيانات الموقع يدويًا
user_lat = st.number_input("خط العرض:", value=24.7136, format="%.6f")
user_lon = st.number_input("خط الطول:", value=46.6753, format="%.6f")
user_location = (user_lat, user_lon)

radius_km = st.slider("نطاق البحث (كم):", min_value=1.0, max_value=15.0, value=5.0, step=0.5)

# 🔹 حساب المسافة وتصنيف الصيدليات
filtered_pharmacies = []
for _, row in df_services.iterrows():
    pharmacy_location = (row["Latitude"], row["Longitude"])
    distance = geodesic(user_location, pharmacy_location).km
    if distance <= radius_km:
        row_dict = row.to_dict()
        row_dict["المسافة (كم)"] = round(distance, 2)
        filtered_pharmacies.append(row_dict)

# 🔹 تحويل البيانات إلى DataFrame
filtered_pharmacies_df = pd.DataFrame(filtered_pharmacies)

# 📌 **عرض عدد الصيدليات المتاحة**
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

    # 🔹 **عرض أقرب 3 صيدليات**
    st.markdown("### 🏥 أقرب 3 صيدليات إليك:")
    closest_pharmacies = filtered_pharmacies_df.nsmallest(3, "المسافة (كم)")
    for _, row in closest_pharmacies.iterrows():
        st.markdown(f"🔹 **{row['Name']}** - تبعد {row['المسافة (كم)']} كم")

    # 🔹 **إضافة زر لعرض جميع الصيدليات**
    if len(filtered_pharmacies_df) > 3:
        with st.expander("🔍 عرض جميع الصيدليات"):
            st.dataframe(filtered_pharmacies_df[['Name', 'المسافة (كم)']], use_container_width=True)
