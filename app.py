import streamlit as st
import pandas as pd
from googleapiclient.discovery import build
import isodate
from datetime import datetime, timezone

# --- PAGE SETUP ---
st.set_page_config(page_title="Viral Niche Finder Pro", layout="wide")
st.title("🚀 Viral Niche Finder (Global Edition)")

# ==========================================
# 🌍 GLOBAL DATA LISTS (Supported by YouTube)
# ==========================================

# 1. Languages (Display Name : ISO Code)
LANGUAGES = {
    "English": "en", "Hindi (हिन्दी)": "hi", "Urdu (اردو)": "ur", 
    "Arabic (العربية)": "ar", "Spanish (Español)": "es", "French (Français)": "fr",
    "German (Deutsch)": "de", "Russian (Русский)": "ru", "Portuguese (Português)": "pt",
    "Japanese (日本語)": "ja", "Korean (한국어)": "ko", "Bengali (বাংলা)": "bn",
    "Punjabi (ਪੰਜਾਬੀ)": "pa", "Marathi (मराठी)": "mr", "Telugu (తెలుగు)": "te",
    "Tamil (தமிழ்)": "ta", "Turkish (Türkçe)": "tr", "Vietnamese (Tiếng Việt)": "vi",
    "Indonesian (Bahasa)": "id", "Italian (Italiano)": "it", "Thai (ไทย)": "th",
    "Chinese (Traditional)": "zh-Hant", "Chinese (Simplified)": "zh-Hans",
    "Dutch": "nl", "Polish": "pl", "Filipino": "fil"
}

# 2. Regions (Display Name : ISO Code)
REGIONS = {
    "United States": "US", "India": "IN", "Pakistan": "PK", "United Arab Emirates": "AE",
    "United Kingdom": "GB", "Canada": "CA", "Australia": "AU", "Saudi Arabia": "SA",
    "Germany": "DE", "France": "FR", "Brazil": "BR", "Japan": "JP", "South Korea": "KR",
    "Russia": "RU", "Bangladesh": "BD", "Indonesia": "ID", "Turkey": "TR",
    "Philippines": "PH", "Vietnam": "VN", "Thailand": "TH", "Mexico": "MX",
    "Egypt": "EG", "Italy": "IT", "Spain": "ES", "South Africa": "ZA",
    "Nigeria": "NG", "Kenya": "KE", "Singapore": "SG", "Malaysia": "MY",
    "New Zealand": "NZ", "Netherlands": "NL", "Sweden": "SE", "Norway": "NO",
    "Switzerland": "CH", "Argentina": "AR", "Colombia": "CO", "Poland": "PL",
    "Ukraine": "UA", "Israel": "IL", "Qatar": "QA", "Kuwait": "KW", "Oman": "OM"
}

# ==========================================
# 1. SIDEBAR SETTINGS
# ==========================================
st.sidebar.header("⚙️ User Controls")

# API Key
api_key = st.sidebar.text_input("YouTube API Key", type="password")

# Search
keyword = st.sidebar.text_input("Niche/Keyword", "AI Tools")

# ✅ Scope Filters (Dropdowns se Name select karein, Code backend mein jayega)
st.sidebar.subheader("🌍 Location & Language")

selected_lang_name = st.sidebar.selectbox("Language", list(LANGUAGES.keys()), index=0)
target_lang = LANGUAGES[selected_lang_name] # Name se Code nikalna (e.g. 'English' -> 'en')

selected_region_name = st.sidebar.selectbox("Country/Region", list(REGIONS.keys()), index=0)
target_region = REGIONS[selected_region_name] # Name se Code nikalna (e.g. 'India' -> 'IN')

# ✅ Competition
st.sidebar.subheader("⚔️ Competition")
max_subs = st.sidebar.number_input("Max Subscribers (Competition)", min_value=1000, value=500000, step=5000)

# ✅ Demand
st.sidebar.subheader("📈 Demand")
min_views = st.sidebar.number_input("Min Views (Validation)", min_value=1000, value=5000, step=1000)

# ✅ Format
st.sidebar.subheader("📱 Platform/Format")
video_type = st.sidebar.selectbox("Format", ["Any", "Shorts (<60s)", "Long (>20m)", "Standard (1-20m)"])

# Sorting
search_order = st.sidebar.selectbox("Sort By", ["viewCount", "date", "relevance", "rating"])

# ==========================================
# 2. LOGIC FUNCTIONS
# ==========================================
def get_duration_sec(iso_duration):
    try: return isodate.parse_duration(iso_duration).total_seconds()
    except: return 0

def analyze_youtube(api_key, query, lang, region, max_sub_limit, min_view_limit, v_type, order):
    try:
        youtube = build('youtube', 'v3', developerKey=api_key)
        
        # 1. SEARCH
        st.info(f"Scanning: '{query}' in {selected_region_name} ({selected_lang_name})...")
        
        search_params = {
            'q': query,
            'part': 'snippet',
            'type': 'video',
            'order': order,
            'relevanceLanguage': lang, # Yahan code jayega (e.g. 'hi')
            'regionCode': region,      # Yahan code jayega (e.g. 'IN')
            'maxResults': 50
        }
        
        # Format Logic
        if v_type == "Shorts (<60s)": search_params['videoDuration'] = 'short'
        elif v_type == "Long (>20m)": search_params['videoDuration'] = 'long'
        elif v_type == "Standard (1-20m)": search_params['videoDuration'] = 'medium'

        search_response = youtube.search().list(**search_params).execute()
        video_ids = [item['id']['videoId'] for item in search_response['items']]
        
        if not video_ids: return None

        # 2. GET DETAILS
        video_response = youtube.videos().list(
            id=','.join(video_ids),
            part='snippet,statistics,contentDetails,status'
        ).execute()

        # 3. GET CHANNELS
        channel_ids = list(set([item['snippet']['channelId'] for item in video_response['items']]))
        channel_response = youtube.channels().list(id=','.join(channel_ids[:50]), part='statistics').execute()
        channel_map = {item['id']: int(item['statistics']['subscriberCount']) for item in channel_response['items'] if 'subscriberCount' in item['statistics']}

        data = []
        
        for item in video_response['items']:
            stats = item['statistics']
            snippet = item['snippet']
            content = item['contentDetails']
            status = item['status']

            views = int(stats.get('viewCount', 0))
            if views < min_view_limit: continue 

            channel_id = snippet['channelId']
            subs = channel_map.get(channel_id, 0)
            
            if max_sub_limit and subs > max_sub_limit: continue
            
            # Creator/Target
            title = snippet['title']
            is_kids = status.get('madeForKids', False)
            target_aud = "👶 Kids" if is_kids else "🧑 General"
            
            # Viral Ratio
            ratio = round(views / (subs if subs > 0 else 1), 2)
            
            data.append({
                'Thumbnail': snippet['thumbnails']['medium']['url'],
                'Title': title,
                'Views': views,
                'Subs': subs,
                'V/S Ratio': ratio,
                'Audience': target_aud,
                'Link': f"https://www.youtube.com/watch?v={item['id']}"
            })
            
        return pd.DataFrame(data)

    except Exception as e:
        st.error(f"Error: {e}")
        return None

# ==========================================
# 3. MAIN UI
# ==========================================
if st.sidebar.button("🔍 Analyze Market"):
    if not api_key:
        st.warning("Pehle API Key daaliye Sidebar mein!")
    else:
        df = analyze_youtube(api_key, keyword, target_lang, target_region, max_subs, min_views, video_type, search_order)
        
        if df is not None and not df.empty:
            df = df.sort_values(by="V/S Ratio", ascending=False)
            st.success(f"Found {len(df)} Viral Videos in {selected_region_name}!")
            
            for _, row in df.iterrows():
                with st.container():
                    col1, col2 = st.columns([1, 3])
                    with col1:
                        st.image(row['Thumbnail'], use_column_width=True)
                    with col2:
                        st.subheader(f"[{row['Title']}]({row['Link']})")
                        st.write(f"**Viral Score:** `{row['V/S Ratio']}` | **Views:** `{row['Views']}` | **Subs:** `{row['Subs']}`")
                        st.caption(f"Target: {row['Audience']}")
                        st.divider()
        else:
            st.error("No videos found. Filters might be too strict.")
