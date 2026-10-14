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
# 1. جداول علم الحرف والابراج الباطنية والأيام والأنواء
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
    1: {'name': 'الحمل (Aries)', 'simple_name': 'حمل', 'degrees': [1, 13, 25], 'index': 0},
    2: {'name': 'الثور (Taurus)', 'simple_name': 'ثور', 'degrees': [2, 14, 26], 'index': 1},
    3: {'name': 'الجوزاء (Gemini)', 'simple_name': 'جوزاء', 'degrees': [3, 15, 27], 'index': 2},
    4: {'name': 'السرطان (Cancer)', 'simple_name': 'سرطان', 'degrees': [4, 16, 28], 'index': 3},
    5: {'name': 'الأسد (Leo)', 'simple_name': 'أسد', 'degrees': [5, 17, 29], 'index': 4},
    6: {'name': 'العذراء (Virgo)', 'simple_name': 'عذراء', 'degrees': [6, 18, 30], 'index': 5},
    7: {'name': 'الميزان (Libra)', 'simple_name': 'ميزان', 'degrees': [7, 19], 'index': 6},
    8: {'name': 'العقرب (Scorpio)', 'simple_name': 'عقرب', 'degrees': [8, 20], 'index': 7},
    9: {'name': 'القوس (Sagittarius)', 'simple_name': 'قوس', 'degrees': [9, 21], 'index': 8},
    10: {'name': 'الجدي (Capricorn)', 'simple_name': 'جدي', 'degrees': [10, 22], 'index': 9},
    11: {'name': 'الدلو (Aquarius)', 'simple_name': 'دلو', 'degrees': [11, 23], 'index': 10},
    12: {'name': 'الحوت (Pisces)', 'simple_name': 'حوت', 'degrees': [12, 24], 'index': 11}
}

DAYS_PLANETS = {
    'احد': {'planet': 'شمس', 'day_name': 'احد'},
    'اثنين': {'planet': 'قمر', 'day_name': 'اثنين'},
    'ثلاثاء': {'planet': 'مريخ', 'day_name': 'ثلاثاء'},
    'اربعاء': {'planet': 'عطارد', 'day_name': 'اربعاء'},
    'خميس': {'planet': 'مشتري', 'day_name': 'خميس'},
    'جمعه': {'planet': 'زهره', 'day_name': 'جمعه'},
    'سبت': {'planet': 'زحل', 'day_name': 'سبت'}
}

def calculate_text_value(text: str) -> int:
    """حساب القيمة الحرفية بالجمل الكبير مع استبعاد الهمزة المنفردة"""
    total = 0
    text = text.strip()
    for char in text:
        if char in ['ء']:
            continue
        if char in ABJAD_DICT:
            total += ABJAD_DICT[char]
    return total

def reduce_to_12(number: int) -> int:
    """طرح الرقم 12 بشكل متكرر حتى يبقى الناتج بين 1 و 12"""
    while number > 12:
        number -= 12
    if number <= 0:
        number = ((number - 1) % 12) + 1
    return number

def get_current_naw(check_date: Optional[datetime] = None) -> str:
    """تحديد النوء الفلكي الحالي بناءً على التاريخ"""
    if check_date is None:
        check_date = datetime.now()
    
    month = check_date.month
    day = check_date.day
    
    if (month == 5 and day >= 12) or (month == 5 and day < 25):
        return "ثريا"
    elif (month == 5 and day >= 25) or (month == 6 and day < 7):
        return "ثريا"
    elif (month == 6 and day >= 7) or (month == 6 and day < 20):
        return "ثريا"
    elif (month == 6 and day >= 20) or (month == 7 and day < 3):
        return "تويبع"
    elif (month == 7 and day >= 3) or (month == 7 and day < 16):
        return "جوزاء"
    elif (month == 7 and day >= 16) or (month == 7 and day < 29):
        return "جوزاء"
    elif (month == 7 and day >= 29) or (month == 8 and day < 11):
        return "مرزم"
    elif (month == 8 and day >= 11) or (month == 8 and day < 24):
        return "كليبين"
    elif (month == 8 and day >= 24) or (month == 9 and day < 6):
        return "سهيل"
    elif (month == 9 and day >= 6) or (month == 9 and day < 20):
        return "سهيل"
    elif (month == 9 and day >= 20) or (month == 10 and day < 3):
        return "سهيل"
    elif (month == 10 and day >= 3) or (month == 10 and day < 16):
        return "سهيل"
    elif (month == 10 and day >= 16) or (month == 10 and day < 29):
        return "وسم"
    elif (month == 10 and day >= 29) or (month == 11 and day < 11):
        return "وسم"
    elif (month == 11 and day >= 11) or (month == 11 and day < 24):
        return "وسم"
    elif (month == 11 and day >= 24) or (month == 12 and day < 7):
        return "وسم"
    elif (month == 12 and day >= 7) or (month == 12 and day < 20):
        return "مربعانيه"
    elif (month == 12 and day >= 20) or (month == 1 and day < 2):
        return "مربعانيه"
    elif (month == 1 and day >= 2) or (month == 1 and day < 15):
        return "مربعانيه"
    elif (month == 1 and day >= 15) or (month == 1 and day < 28):
        return "شبط"
    elif (month == 1 and day >= 28) or (month == 2 and day < 10):
        return "شبط"
    elif (month == 2 and day >= 10) or (month == 2 and day < 23):
        return "عقارب"
    elif (month == 2 and day >= 23) or (month == 3 and day < 8):
        return "عقارب"
    elif (month == 3 and day >= 8) or (month == 3 and day < 21):
        return "عقارب"
    elif (month == 3 and day >= 21) or (month == 4 and day < 3):
        return "حميمين"
    elif (month == 4 and day >= 3) or (month == 4 and day < 16):
        return "حميمين"
    elif (month == 4 and day >= 16) or (month == 4 and day < 29):
        return "ذراعين"
    else:
        return "ذراعين"

def get_esoteric_degree(first_name: str, mother_name: str, birth_date_str: str) -> Tuple[str, str, int, int]:
    """استخراج البرج الباطني والدرجة الدلالية"""
    val_first = calculate_text_value(first_name)
    val_mother = calculate_text_value(mother_name)
    
    digits_sum = sum(int(char) for char in birth_date_str if char.isdigit())
    total_sum = val_first + val_mother + digits_sum
    
    zodiac_index = reduce_to_12(total_sum)
    zodiac_data = DETAILED_ZODIAC_DEGREES[zodiac_index]
    
    zodiac_name = zodiac_data['name']
    zodiac_simple_name = zodiac_data['simple_name']
    degrees_list = zodiac_data['degrees']
    
    quotient = total_sum // 12
    degree_index = quotient % len(degrees_list)
    exact_degree = degrees_list[degree_index]
    
    return zodiac_name, zodiac_simple_name, exact_degree, zodiac_data['index']

def calculate_spiritual_condition_diagnosis(first_name: str, mother_name: str, birth_date_str: str, 
                                            day_key: str, is_night: bool, check_date: datetime) -> Tuple[int, int, str]:
    """حساب المجموع الكلي الثماني واستخراج التشخيص الروحي للطاقة"""
    val_first = calculate_text_value(first_name)
    val_mother = calculate_text_value(mother_name)
    digits_sum = sum(int(char) for char in birth_date_str if char.isdigit())
    
    # البرج الباطني
    zodiac_calc = val_first + val_mother
    zodiac_index = reduce_to_12(zodiac_calc)
    zodiac_simple_name = DETAILED_ZODIAC_DEGREES[zodiac_index]['simple_name']
    val_zodiac = calculate_text_value(zodiac_simple_name)
    
    # اليوم والحاكم والوقت
    day_info = DAYS_PLANETS.get(day_key.lower(), DAYS_PLANETS['اربعاء'])
    val_day = calculate_text_value(day_info['day_name'])
    val_planet = calculate_text_value(day_info['planet'])
    time_val = 340 if is_night else 400
    
    # النوء الفلكي
    naw_name = get_current_naw(check_date)
    val_naw = calculate_text_value(naw_name)
    
    # المجموع الثماني الكلي
    total_octal_sum = (val_first + val_mother + digits_sum + val_zodiac + 
                       val_day + val_planet + time_val + val_naw)
    
    final_res_num = reduce_to_12(total_octal_sum)
    
    # تحديد التشخيص النصي
    if final_res_num == 12:
        diagnosis = "هالتك في هذا الوقت معرضة لمرض نفسي."
    elif final_res_num == 9:
        diagnosis = "هالتك في هذا الوقت معرضة لمرض عضوي."
    elif final_res_num in [2, 4]:
        diagnosis = f"هالتك في هذا الوقت معرضة لمرض طاقي سلبي سببه كائن مرئي (الرقم {final_res_num})."
    else:
        diagnosis = f"هالتك في هذا الوقت معرضة لمرض روحاني طاقي سلبي سببه كائن غير مرئي (الرقم {final_res_num})."
        
    return total_octal_sum, final_res_num, diagnosis

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
    page_title="دمج علم الحرف مع الفلك الغربي",
    layout="wide",
)

st.title("🌟 نظام فحص الهالة الروحية و استخراج الطالع و ساعه الميلاد")
st.markdown("يتم دمج قيم الحروف الأبجدية لاسم المستفيد واسم أمه مع تاريخ الميلاد لاستخراج البرج والدرجة الباطنية، ومطابقتها فلكياً عبر النقطة الشرقية ، بالإضافة للتشخيص الروحي للطاقة.")
st.markdown(" برمجة و تطوير الفلكي استرو رادار")
st.markdown("---")

# ----------------- لوحة المدخلات الجانبية -----------------
st.sidebar.header('📋 بيانات المستفيد والموقع الجغرافي')

name_input = st.sidebar.text_input('الاسم الأول (بالعربية)', 'ماجد')
mother_name_input = st.sidebar.text_input('اسم الأم (بالعربية)', 'مها')

birth_date = st.sidebar.date_input("تاريخ الميلاد:", value=date(1990, 5, 15), min_value=date(1900, 1, 1), max_value=date.today())

selected_country_name = st.sidebar.selectbox('دولة الميلاد', country_list)
c_code = country_map.get(selected_country_name)

country_cities = cities_by_country.get(c_code, [])
if not country_cities:
    country_cities = [{'name': 'المدينة المركزية', 'latitude': 33.5138, 'longitude': 36.2765, 'population': 1000000}]

city_options = [f"{c['name']} (السكان: {c.get('population', 0):,})" for c in country_cities]
selected_city_str = st.sidebar.selectbox('مدينة الميلاد', city_options)

selected_city_obj = country_cities[city_options.index(selected_city_str)]
city_lat = selected_city_obj['latitude']
city_lon = selected_city_obj['longitude']

auto_tz = tf.timezone_at(lng=city_lon, lat=city_lat)
if not auto_tz:
    auto_tz = 'UTC'

timezone_str = st.sidebar.text_input('المنطقة الزمنية', value=auto_tz)

time_intervals = [
    'من شروق الشمس إلى 10 ص',
    'من 10 ص - 2 ظهرا',
    'من 2 ظهرا - 6 م',
    'من 6 م - 10 مساءا',
    'من 10 م - 2 فجرا',
    'من 2 فجرا حتى شروق الشمس',
]
selected_interval = st.sidebar.selectbox('الفترة الزمنية المتوقعة (فترات 4 ساعات)', time_intervals)

st.sidebar.subheader("🔮 إعدادات الكشف عن الطاقة واليوم")
day_key = st.sidebar.selectbox("يوم الكشف الروحي:", options=["احد", "اثنين", "ثلاثاء", "اربعاء", "خميس", "جمعه", "سبت"], index=3)
is_night_radio = st.sidebar.radio("وقت الكشف:", options=["نهار (بعد شروق الشمس إلى قبل غروبها)", "ليل (بعد غروب الشمس إلى قبل شروقها)"], index=1)

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
# 4. محرك الحساب والربط الفلكي الحرفي
# ==========================================
if st.button('🚀 إطلاق التحليل الروحي والفلكي المدمج'):
    if not name_input or not mother_name_input:
        st.error("الرجاء إدخال الاسم الأول واسم الأم بشكل صحيح.")
    else:
        birth_date_str_input = f"{birth_date.day}.{birth_date.month}.{birth_date.year}"
        is_night = True if "ليل" in is_night_radio else False
        
        # 1. حساب البرج والدرجة الباطنية
        esoteric_zodiac_full, esoteric_simple_name, esoteric_deg, target_sign_idx = get_esoteric_degree(
            name_input, mother_name_input, birth_date_str_input
        )
        
        # 2. حساب المرض الروحاني وتأثير الطاقة
        octal_total, final_num, spiritual_diagnosis = calculate_spiritual_condition_diagnosis(
            name_input, mother_name_input, birth_date_str_input, day_key, is_night, datetime.now()
        )
        
        interval_map = {
            'من شروق الشمس إلى 10 ص': (6.0, 10.0),
            'من 10 ص - 2 ظهرا': (10.0, 14.0),
            'من 2 ظهرا - 6 م': (14.0, 18.0),
            'من 6 م - 10 مساءا': (18.0, 22.0),
            'من 10 م - 2 فجرا': (22.0, 26.0),
            'من 2 فجرا حتى شروق الشمس': (2.0, 6.0),
        }

        start_h, end_h = interval_map[selected_interval]
        
        best_time = None
        min_diff = 999.0
        final_asc_deg = 0.0
        final_ep_deg = 0.0
        
        current_step_h = start_h
        while current_step_h < end_h:
            h_local = current_step_h % 24
            calc_date = birth_date
            if current_step_h >= 24:
                calc_date = birth_date + timedelta(days=1)
            elif current_step_h < 0:
                calc_date = birth_date - timedelta(days=1)
                
            hr = int(h_local)
            mn = int((h_local - hr) * 60)
            t_obj = time(hour=hr, minute=mn, second=0)
            
            try:
                jd = get_utc_julian_day(calc_date, t_obj, timezone_str)
                cusps, ascmc = swe.houses(jd, city_lat, city_lon, b'P')
                asc = ascmc[0]
                ep = ascmc[4]
                
                asc_sign = int(asc // 30)
                asc_rem_deg = asc % 30
                
                if asc_sign == target_sign_idx:
                    diff = abs(asc_rem_deg - esoteric_deg)
                    if diff < min_diff:
                        min_diff = diff
                        best_time = (hr, mn)
                        final_asc_deg = asc
                        final_ep_deg = ep
            except:
                pass
            
            current_step_h += 1 / 60.0
            
        if best_time is None:
            current_step_h = start_h
            while current_step_h < end_h:
                h_local = current_step_h % 24
                hr = int(h_local)
                mn = int((h_local - hr) * 60)
                t_obj = time(hour=hr, minute=mn, second=0)
                try:
                    jd = get_utc_julian_day(birth_date, t_obj, timezone_str)
                    cusps, ascmc = swe.houses(jd, city_lat, city_lon, b'P')
                    asc = ascmc[0]
                    diff = abs((asc % 30) - esoteric_deg)
                    if diff < min_diff:
                        min_diff = diff
                        best_time = (hr, mn)
                        final_asc_deg = asc
                        final_ep_deg = ascmc[4]
                except:
                    pass
                current_step_h += 5 / 60.0
                
        if best_time is None:
            mid_h = (start_h + end_h) / 2.0
            h_local = mid_h % 24
            hr = int(h_local)
            mn = int((h_local - hr) * 60)
            best_time = (hr, mn)
            t_obj = time(hour=hr, minute=mn, second=0)
            jd = get_utc_julian_day(birth_date, t_obj, timezone_str)
            cusps, ascmc = swe.houses(jd, city_lat, city_lon, b'P')
            final_asc_deg = ascmc[0]
            final_ep_deg = ascmc[4]

        precise_time_str = f"{best_time[0]:02d}:{best_time[1]:02d}"
        asc_str = format_degree(final_asc_deg)
        ep_str = format_degree(final_ep_deg)

        st.success(f"✅ تم دمج الحسابات الحرفية والفلكية والكشف الروحي بنجاح للمستفيد: **{name_input}**")
        st.markdown("---")
        
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"### 🔮 التحليل الحرفي الباطني")
            st.markdown(f"**البرج والدرجة المستخرجة:** {esoteric_zodiac_full} - الدرجة {esoteric_deg}")
            st.markdown(f"**ساعة الميلاد الدقيقة المطابقة:** {precise_time_str}")
        with col2:
            st.markdown(f"### 🌅 التحليل الفلكي الدقيق (Swiss Ephemeris)")
            st.markdown(f"**الطالع الفلكي الدقيق (ASC):** {asc_str}")
            st.markdown(f"**النقطة الشرقية (EP):** {ep_str}")

        # توليد التقرير
        html_report = f"""
        <!DOCTYPE html>
        <html lang="ar" dir="rtl">
        <head>
            <meta charset="UTF-8">
            <title>التقرير الروحي والفلكي المدمج - {name_input}</title>
            <style>
                body {{ font-family: 'Amiri', Tahoma, Arial, sans-serif; background: #f9f9f9; color: #333; direction: rtl; padding: 20px; }}
                .container {{ max-width: 800px; margin: auto; background: #fff; padding: 30px; border-radius: 10px; box-shadow: 0 0 10px rgba(0,0,0,0.1); }}
                h1 {{ text-align: center; color: #1a202c; border-bottom: 2px solid #3182ce; padding-bottom: 10px; }}
                .section {{ margin-top: 20px; padding: 15px; background: #edf2f7; border-radius: 8px; }}
                .highlight {{ font-weight: bold; color: #2b6cb0; }}
                .spiritual-alert {{ background-color: #fff5f5; border-right: 4px solid #e53e3e; padding: 12px; margin-top: 10px; font-weight: bold; color: #c53030; border-radius: 4px; }}
                table {{ width: 100%; border-collapse: collapse; margin-top: 15px; }}
                th, td {{ border: 1px solid #cbd5e0; padding: 10px; text-align: right; }}
                th {{ background-color: #2b6cb0; color: #fff; }}
                .footer {{ text-align: center; margin-top: 30px; font-size: 0.9em; color: #718096; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>تقرير الكشف الروحي والفلكي المدمج</h1>
                <div class="section">
                    <h3>بيانات المستفيد الشخصية والجغرافية</h3>
                    <p><strong>اسم المستفيد:</strong> {name_input}</p>
                    <p><strong>اسم الأم:</strong> {mother_name_input}</p>
                    <p><strong>تاريخ الميلاد:</strong> {birth_date.strftime('%Y-%m-%d')}</p>
                    <p><strong>دولة / مدينة الميلاد:</strong> {selected_country_name} - {selected_city_str}</p>
                    <p><strong>الإحداثيات الجغرافية:</strong> خط عرض {city_lat}°، خط طول {city_lon}°</p>
                    <p><strong>المنطقة الزمنية:</strong> {timezone_str}</p>
                </div>
                
                <div class="section">
                    <h3>النتائج النهائية (ساعة الميلاد الدقيقة والطالع)</h3>
                    <table>
                        <tr>
                            <th>المؤشر الفلكي والحرفي</th>
                            <th>القيمة النهائية المستخرجة</th>
                        </tr>
                        <tr>
                            <td>ساعة ودقيقة الميلاد الدقيقة</td>
                            <td class="highlight">{precise_time_str}</td>
                        </tr>
                        <tr>
                            <td>البرج الباطني والدرجة الدلالية</td>
                            <td class="highlight">{esoteric_zodiac_full} - الدرجة {esoteric_deg}</td>
                        </tr>
                        <tr>
                            <td>الطالع الفلكي الدقيق (ASC)</td>
                            <td>{asc_str}</td>
                        </tr>
                        <tr>
                            <td>النقطة الشرقية (EP)</td>
                            <td>{ep_str}</td>
                        </tr>
                    </table>
                </div>

                <div class="section">
                    <h3>⚡ كشف الحالة الروحانية والتأثير الطاقي للهالة</h3>
                    <div class="spiritual-alert">
                        📌 {spiritual_diagnosis}
                    </div>
                </div>
                
                <div class="footer">
                    <p>تم إصدار هذا التقرير آلياً عبر نظام دمج علوم الحرف الأبجدي والفلك السويسري - جميع الحقوق محفوظة للفلكي استرو رادار .</p>
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
            file_name=f"spiritual_astrology_report_{name_input.replace(' ', '_')}.html",
            mime="text/html"
        )
