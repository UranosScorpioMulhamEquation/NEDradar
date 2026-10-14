from datetime import datetime, date, time, timedelta
import os
from typing import Dict, List, Tuple, Any, Optional
import geonamescache
import pandas as pd
import pytz
import streamlit as st
import swisseph as swe
from timezonefinder import TimezoneFinder

# ==========================================
# 0. تهيئة مسار ملفات الـ Ephemeris والإعدادات
# ==========================================
EPHE_PATH = "./ephe"
if not os.path.exists(EPHE_PATH):
    os.makedirs(EPHE_PATH)

swe.set_ephe_path(EPHE_PATH)

# ==========================================
# 1. جداول علم الحرف والدرجات التفصيلية للأبراج
# ==========================================
ABJAD_DICT = {
    'ا': 1, 'أ': 1, 'إ': 1, 'آ': 1,
    'ب': 2,
    'ج': 3,
    'د': 4,
    'ه': 5, 'ة': 5,
    'و': 6,
    'ز': 7,
    'ح': 8,
    'ط': 9,
    'ي': 10, 'ى': 10,
    'ك': 20,
    'ل': 30,
    'م': 40,
    'ن': 50,
    'س': 60,
    'ع': 70,
    'ف': 80,
    'ص': 90,
    'ق': 100,
    'ر': 200,
    'ش': 300,
    'ت': 400,
    'ث': 500,
    'خ': 600,
    'ذ': 700,
    'ض': 800,
    'ظ': 900,
    'غ': 1000
}

DETAILED_ZODIAC_DEGREES = {
    1: {'name': 'الحمل (Aries)', 'degrees': [1, 13, 25], 'index': 0},
    2: {'name': 'الثور (Taurus)', 'degrees': [2, 14, 26], 'index': 1},
    3: {'name': 'الجوزاء (Gemini)', 'degrees': [3, 15, 27], 'index': 2},
    4: {'name': 'السرطان (Cancer)', 'degrees': [4, 16, 28], 'index': 3},
    5: {'name': 'الأسد (Leo)', 'degrees': [5, 17, 29], 'index': 4},
    6: {'name': 'العذراء (Virgo)', 'degrees': [6, 18, 30], 'index': 5},
    7: {'name': 'الميزان (Libra)', 'degrees': [7, 19], 'index': 6},
    8: {'name': 'العقرب (Scorpio)', 'degrees': [8, 20], 'index': 7},
    9: {'name': 'القوس (Sagittarius)', 'degrees': [9, 21], 'index': 8},
    10: {'name': 'الجدي (Capricorn)', 'degrees': [10, 22], 'index': 9},
    11: {'name': 'الدلو (Aquarius)', 'degrees': [11, 23], 'index': 10},
    12: {'name': 'الحوت (Pisces)', 'degrees': [12, 24], 'index': 11}
}

def calculate_text_value(text):
    """حساب القيمة الحرفية للجمل الكبير مع استبعاد الهمزة المنفردة"""
    total = 0
    text = text.strip()
    for char in text:
        if char in ['ء']:
            continue
        if char in ABJAD_DICT:
            total += ABJAD_DICT[char]
    return total

def get_esoteric_degree(first_name: str, mother_name: str, birth_date_obj: date) -> Tuple[str, int, int]:
    """استخراج البرج الباطني والدرجة الدقيقة بناءً على منطق الدورات وقائمة الدرجات"""
    val_first = calculate_text_value(first_name)
    val_mother = calculate_text_value(mother_name)
    
    date_str = birth_date_obj.strftime('%d%m%Y')
    digits_sum = sum(int(char) for char in date_str if char.isdigit())
    
    total_sum = val_first + val_mother + digits_sum
    
    zodiac_index = total_sum % 12
    if zodiac_index == 0:
        zodiac_index = 12
        
    zodiac_data = DETAILED_ZODIAC_DEGREES[zodiac_index]
    zodiac_name = zodiac_data['name']
    degrees_list = zodiac_data['degrees']
    
    quotient = total_sum // 12
    degree_index = quotient % len(degrees_list)
    exact_degree = degrees_list[degree_index]
    
    return zodiac_name, exact_degree, zodiac_data['index']

# ==========================================
# 2. خدمات البيانات الجغرافية والزمنية
# ==========================================
@st.cache_data
def load_geo_data() -> Tuple[Any, Dict[str, str], List[str], Dict[str, List[Dict[str, Any]]]]:
    gc = geonamescache.GeonamesCache()
    countries = gc.get_countries()
    cities = gc.get_cities()

    country_map = {c["name"]: code for code, c in countries.items()}
    sorted_countries = sorted(list(country_map.keys()))

    cities_by_country: Dict[str, List[Dict[str, Any]]] = {}
    for c_code in country_map.values():
        c_cities = [city for city in cities.values() if city["countrycode"] == c_code]
        c_cities_sorted = sorted(c_cities, key=lambda x: x.get("population", 0), reverse=True)
        cities_by_country[c_code] = c_cities_sorted

    return gc, country_map, sorted_countries, cities_by_country

gc, country_map, country_list, cities_by_country = load_geo_data()

@st.cache_resource
def get_tz_finder() -> TimezoneFinder:
    return TimezoneFinder()

tf = get_tz_finder()

def get_utc_julian_day(date_obj: date, time_obj: time, tz_str: str) -> float:
    local_tz = pytz.timezone(tz_str)
    dt = datetime.combine(date_obj, time_obj)
    local_dt = local_tz.localize(dt)
    utc_dt = local_dt.astimezone(pytz.utc)
    return swe.julday(
        utc_dt.year,
        utc_dt.month,
        utc_dt.day,
        utc_dt.hour + utc_dt.minute / 60.0 + utc_dt.second / 3600.0,
    )

# ==========================================
# 3. إعدادات واجهة المستخدم (Streamlit)
# ==========================================
st.set_page_config(
    page_title="الطالع من علم الحرف",
    layout="wide",
)

st.title("🌟 نظام تحديد النقطة الشرقية و تعديل درجتها بعلم الحرف - برمجة و تطوير الفلكي استرو رادار")
st.markdown("استخراج الطالع من النقطة الشرقية و استبدال درجتها بالدرجة المستخرجة من البرج الباطني المطور")
st.markdown("---")

# ----------------- لوحة المدخلات الجانبية -----------------
st.sidebar.header('📋 بيانات المستفيد والموقع الجغرافي')

name_input = st.sidebar.text_input('الاسم الأول (بالعربية)', 'ماجد')
mother_name_input = st.sidebar.text_input('اسم الأم (بالعربية)', 'مها')

birth_date = st.sidebar.date_input(
    "تاريخ الميلاد:", 
    value=date(1990, 4, 15), 
    min_value=date(1900, 1, 1), 
    max_value=date.today()
)

selected_country_name = st.sidebar.selectbox('دولة الميلاد', country_list, index=country_list.index('Syria') if 'Syria' in country_list else 0)
c_code = country_map.get(selected_country_name)

country_cities = cities_by_country.get(c_code, [])
if not country_cities:
    country_cities = [{'name': 'المدينة المركزية', 'latitude': 33.5138, 'longitude': 36.2765, 'population': 1000000}]

city_options = [f"{c['name']} (السكان: {c.get('population', 0):,})" for c in country_cities]
default_city_idx = 0
for idx, opt in enumerate(city_options):
    if 'Hama' in opt or 'حماة' in opt:
        default_city_idx = idx
        break

selected_city_str = st.sidebar.selectbox('مدينة الميلاد', city_options, index=default_city_idx)

selected_city_obj = country_cities[city_options.index(selected_city_str)]
city_lat = selected_city_obj['latitude']
city_lon = selected_city_obj['longitude']

auto_tz = tf.timezone_at(lng=city_lon, lat=city_lat)
if not auto_tz:
    auto_tz = 'UTC'

timezone_str = st.sidebar.text_input('المنطقة الزمنية', value=auto_tz)

time_intervals = [
    'من 10 ص - 1 م',
    'من 1 م - 4 م',
    'من 4 م - 7 م',
    'من 7 م - 10 م',
    'من 10 م الى 1 فجرا',
    'من 1 فجرا - 4 فجرا',
    'من 4 فجرا - 7 ص',
    'من 7 ص الى 10 ص',
]
default_interval_idx = 0 if len(time_intervals) > 0 else 0
selected_interval = st.sidebar.selectbox('الفترة الزمنية المتوقعة (مراحل دقيقة)', time_intervals, index=default_interval_idx)

zodiac_names_list = [
    'الحمل (Aries)', 'الثور (Taurus)', 'الجوزاء (Gemini)', 'السرطان (Cancer)',
    'الأسد (Leo)', 'العذراء (Virgo)', 'الميزان (Libra)', 'العقرب (Scorpio)',
    'القوس (Sagittarius)', 'الجدي (Capricorn)', 'الدلو (Aquarius)', 'الحوت (Pisces)'
]

def format_degree(deg):
    sign_idx = int(deg // 30) % 12
    rem = deg % 30
    d_int = int(rem)
    m_int = int((rem - d_int) * 60)
    return f"{d_int}° {m_int:02d}' - {zodiac_names_list[sign_idx]}"

# ==========================================
# 4. محرك الحساب والربط الفلكي الحرفي المعدل
# ==========================================
if st.button('🚀 إطلاق التحليل وتوليد التقرير'):
    if not name_input or not mother_name_input:
        st.error("الرجاء إدخال الاسم الأول واسم الأم بشكل صحيح.")
    else:
        interval_map = {
            'من 10 ص - 1 م': (10.0, 13.0),
            'من 1 م - 4 م': (13.0, 16.0),
            'من 4 م - 7 م': (16.0, 19.0),
            'من 7 م - 10 م': (19.0, 22.0),
            'من 10 م الى 1 فجرا': (22.0, 1.0),
            'من 1 فجرا - 4 فجرا': (1.0, 4.0),
            'من 4 فجرا - 7 ص': (4.0, 7.0),
            'من 7 ص الى 10 ص': (7.0, 10.0),
        }
        start_h, end_h = interval_map[selected_interval]
        
        # 1. تحديد برج الـ EP عند منتصف النطاق الزمني بدقة
        mid_h = (start_h + end_h) / 2.0
        mid_h_local = mid_h % 24
        calc_date_mid = birth_date
        if mid_h >= 24:
            calc_date_mid = birth_date + timedelta(days=1)
        elif mid_h < 0:
            calc_date_mid = birth_date - timedelta(days=1)
            
        hr_mid = int(mid_h_local)
        mn_mid = int((mid_h_local - hr_mid) * 60)
        t_obj_mid = time(hour=hr_mid, minute=mn_mid, second=0)
        
        try:
            jd_mid = get_utc_julian_day(calc_date_mid, t_obj_mid, timezone_str)
            _, ascmc_mid = swe.houses(jd_mid, city_lat, city_lon, b'P')
            natural_ep = ascmc_mid[4]
            natural_ep_sign_idx = int(natural_ep // 30) % 12
        except:
            natural_ep_sign_idx = 3  # افتراضي السرطان في حال أي استثناء
            
        # 2. استخراج البرج الباطني والدرجة الباطنية من علم الحرف
        esoteric_zodiac, esoteric_exact_deg, _ = get_esoteric_degree(
            name_input, mother_name_input, birth_date
        )
        
        # 3. الاعتماد على برج الـ EP عند منتصف النطاق + درجة البرج الباطني
        target_sign_idx = natural_ep_sign_idx
        target_degree = esoteric_exact_deg
        
        # حساب الدرجة المعدلة للـ EP
        adjusted_ep_deg = (target_sign_idx * 30) + target_degree
        adjusted_ep_str = format_degree(adjusted_ep_deg)
        natural_ep_sign_name = zodiac_names_list[natural_ep_sign_idx]

        st.success(f"✅ تم إنجاز التحليل بنجاح للمستفيد: **{name_input}**")
        st.markdown("---")
        
        astrotheme_instruction = (
            "ارسم خريطتك الميلادية على برنامج الاستروثيم من هذا الرابط "
            "(https://www.astrotheme.com/birth-chart-sign-ascendant.php) "
            "مستخدما تاريخ ميلادك و دولة ميلادك و مدينة ميلادك ثم عدل الساعه و الدقيقه "
            "حسب الطالع الذي ظهر لك و حسب درجة الطالع الذي ظهر لك"
        )

        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"### 🔮 التحليل الحرفي والفلكي")
            st.markdown(f"**الاسم:** {name_input}")
            st.markdown(f"**اسم الأم:** {mother_name_input}")
            st.markdown(f"**تاريخ الميلاد:** {birth_date.strftime('%Y-%m-%d')}")
            st.markdown(f"**الدولة والمدينة:** {selected_country_name} - {selected_city_str}")
            st.markdown(f"**درجة البرج الباطني المطور:** {esoteric_zodiac} - الدرجة {target_degree}")
        with col2:
            st.markdown(f"### 🌅 النتائج المعايرة")
            st.markdown(f"**برج النقطة الشرقية (EP):** {natural_ep_sign_name}")
            st.markdown(f"**درجة الـ EP المعدلة:** {adjusted_ep_str}")
            st.info(astrotheme_instruction)

        # تقرير HTML القابل للطباعة المحدث بالكامل
        html_report = f"""
        <!DOCTYPE html>
        <html lang="ar" dir="rtl">
        <head>
            <meta charset="UTF-8">
            <title>تقرير النقطة الشرقية المعدلة وعلم الحرف - {name_input}</title>
            <style>
                body {{ font-family: 'Amiri', Tahoma, Arial, sans-serif; background: #f9f9f9; color: #333; direction: rtl; padding: 20px; }}
                .container {{ max-width: 800px; margin: auto; background: #fff; padding: 30px; border-radius: 10px; box-shadow: 0 0 10px rgba(0,0,0,0.1); }}
                h1 {{ text-align: center; color: #000; border-bottom: 2px solid #3182ce; padding-bottom: 10px; }}
                .section {{ margin-top: 20px; padding: 15px; background: #edf2f7; border-radius: 8px; }}
                .highlight {{ font-weight: bold; color: #000; }}
                .notice {{ background: #e2e8f0; padding: 12px; border-right: 4px solid #3182ce; margin-top: 15px; font-size: 0.95em; }}
                table {{ width: 100%; border-collapse: collapse; margin-top: 15px; }}
                th, td {{ border: 1px solid #cbd5e0; padding: 10px; text-align: right; }}
                th {{ background-color: #2b6cb0; color: #000; }}
                .footer {{ text-align: center; margin-top: 30px; font-size: 0.9em; color: #718096; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>تقرير دمج النقطة الشرقية (EP) وعلم الحرف</h1>
                
                <div class="section">
                    <h3>بيانات المستفيد والنتائج</h3>
                    <table>
                        <tr>
                            <th>المؤشر الأساسي</th>
                            <th>القيمة</th>
                        </tr>
                        <tr>
                            <td>الاسم</td>
                            <td class="highlight">{name_input}</td>
                        </tr>
                        <tr>
                            <td>اسم الأم</td>
                            <td class="highlight">{mother_name_input}</td>
                        </tr>
                        <tr>
                            <td>تاريخ الميلاد</td>
                            <td>{birth_date.strftime('%Y-%m-%d')}</td>
                        </tr>
                        <tr>
                            <td>دولة الميلاد</td>
                            <td>{selected_country_name}</td>
                        </tr>
                        <tr>
                            <td>مدينة الميلاد</td>
                            <td>{selected_city_str}</td>
                        </tr>
                        <tr>
                            <td>درجة البرج الباطني المطور</td>
                            <td class="highlight">{esoteric_zodiac} - الدرجة {target_degree}</td>
                        </tr>
                        <tr>
                            <td>برج النقطة الشرقية (EP)</td>
                            <td>{natural_ep_sign_name}</td>
                        </tr>
                        <tr>
                            <td>درجة الـ EP المعدلة</td>
                            <td class="highlight">{adjusted_ep_str}</td>
                        </tr>
                    </table>
                    
                    <div class="notice">
                        <strong>إرشادات ضبط الوقت:</strong><br>
                        {astrotheme_instruction}
                        <br><br>
                        <a href="https://www.astrotheme.com/birth-chart-sign-ascendant.php" target="_blank">انقر هنا لفتح موقع الاستروثيم</a>
                    </div>
                </div>
                
                <div class="footer">
                    <p>تم إصدار هذا التقرير آلياً عبر دمج النقطة الشرقية (EP) وععلم الحرف والفلك السويسري (Swiss Ephemeris).</p>
                </div>
            </div>
        </body>
        </html>
        """

        st.markdown("---")
        st.subheader("📄 تحميل التقرير النهائي")
        st.download_button(
            label="📥 تحميل تقرير HTML المتكامل والجاهز للطباعة",
            data=html_report,
            file_name=f"EP_Adjusted_Report_{name_input.replace(' ', '_')}.html",
            mime="text/html"
        )
