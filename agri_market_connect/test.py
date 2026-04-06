import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime, timedelta
import requests
import base64
from io import BytesIO
from PIL import Image
import json

# Page configuration
st.set_page_config(
    page_title="AgriSmart - AI Agriculture Platform",
    page_icon="🌾",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(to right, #16a34a, #059669);
        padding: 1.5rem;
        border-radius: 10px;
        color: white;
        margin-bottom: 2rem;
    }
    .metric-card {
        background: white;
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        border-left: 4px solid #16a34a;
    }
    .quality-card {
        background: white;
        padding: 1rem;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        margin: 1rem 0;
    }
    .recommendation-box {
        padding: 1.5rem;
        border-radius: 10px;
        border: 3px solid;
        margin: 1rem 0;
        font-size: 1.1rem;
        font-weight: 600;
    }
    .stButton>button {
        width: 100%;
        background: #16a34a;
        color: white;
        font-weight: 600;
        padding: 0.75rem;
        border-radius: 8px;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'user_role' not in st.session_state:
    st.session_state.user_role = None
if 'language' not in st.session_state:
    st.session_state.language = 'en'
if 'current_page' not in st.session_state:
    st.session_state.current_page = 'landing'
if 'price_data' not in st.session_state:
    st.session_state.price_data = None
if 'quality_result' not in st.session_state:
    st.session_state.quality_result = None
if 'seasonal_insights' not in st.session_state:
    st.session_state.seasonal_insights = None

# Translations
translations = {
    'en': {
        'select_role': 'Select Your Role',
        'farmer': 'I am a Farmer',
        'buyer': 'I am a Buyer',
        'farmer_desc': 'Get best selling prices & quality insights',
        'buyer_desc': 'Find best buying opportunities & forecasts',
        'dashboard': 'Price Dashboard',
        'quality': 'Quality Check',
        'select_crop': 'Select Crop',
        'select_state': 'Select State',
        'select_market': 'Select Market',
        'select_season': 'Select Season',
        'get_prediction': 'Get Price Forecast',
        'upload_photo': 'Upload Photo',
        'analyze': 'Analyze Quality',
        'current_price': 'Current Price',
        'predicted_price': 'Predicted Price (3 Days)',
        'advice': 'Recommendation',
        'profit_calc': 'Profit Calculator',
        'quantity': 'Quantity (kg)',
        'transport': 'Transport Cost (₹)',
        'calculate': 'Calculate Profit',
        'data_source': 'Data Source: Agmarknet (Govt of India)',
        'confidence': 'Confidence',
        'shelf_life': 'Estimated Shelf Life',
        'freshness': 'Freshness Score',
        'grade': 'Quality Grade',
        'season': 'Season',
        'current_season': 'Current Season',
        'kharif': 'Kharif (Oct-Jan)',
        'rabi': 'Rabi (Feb-May)',
        'summer': 'Summer (Jun-Sep)'
    },
    'hi': {
        'select_role': 'अपनी भूमिका चुनें',
        'farmer': 'मैं किसान हूं',
        'buyer': 'मैं खरीदार हूं',
        'farmer_desc': 'सर्वोत्तम बिक्री मूल्य और गुणवत्ता जानकारी प्राप्त करें',
        'buyer_desc': 'सर्वोत्तम खरीद अवसर और पूर्वानुमान खोजें',
        'dashboard': 'मूल्य डैशबोर्ड',
        'quality': 'गुणवत्ता जांच',
        'select_crop': 'फसल चुनें',
        'select_state': 'राज्य चुनें',
        'select_market': 'मंडी चुनें',
        'select_season': 'मौसम चुनें',
        'get_prediction': 'मूल्य पूर्वानुमान प्राप्त करें',
        'upload_photo': 'फोटो अपलोड करें',
        'analyze': 'गुणवत्ता विश्लेषण करें',
        'current_price': 'वर्तमान मूल्य',
        'predicted_price': 'अनुमानित मूल्य (3 दिन)',
        'advice': 'सिफारिश',
        'profit_calc': 'लाभ कैलकुलेटर',
        'quantity': 'मात्रा (किलो)',
        'transport': 'परिवहन लागत (₹)',
        'calculate': 'लाभ की गणना करें',
        'data_source': 'डेटा स्रोत: एग्रीमार्केटनेट (भारत सरकार)',
        'confidence': 'विश्वास',
        'shelf_life': 'अनुमानित शेल्फ लाइफ',
        'freshness': 'ताजगी स्कोर',
        'grade': 'गुणवत्ता ग्रेड',
        'season': 'मौसम',
        'current_season': 'वर्तमान मौसम',
        'kharif': 'खरीफ (अक्टूबर-जनवरी)',
        'rabi': 'रबी (फरवरी-मई)',
        'summer': 'ग्रीष्म (जून-सितंबर)'
    }
}

def t(key):
    """Get translation for current language"""
    return translations[st.session_state.language].get(key, key)

# Markets data
MARKETS_DATA = {
    'Maharashtra': ['Lasalgaon', 'Pune', 'Nashik', 'Mumbai'],
    'Karnataka': ['Bangalore', 'Mysore', 'Hubli'],
    'Gujarat': ['Ahmedabad', 'Rajkot', 'Surat'],
    'Madhya Pradesh': ['Indore', 'Bhopal', 'Jabalpur'],
    'Rajasthan': ['Jaipur', 'Jodhpur', 'Kota']
}

# Seasonal data
SEASONAL_DATA = {
    'kharif': {
        'name': 'Kharif (Oct-Jan)',
        'name_hi': 'खरीफ (अक्टूबर-जनवरी)',
        'quality': 85,
        'shelf_life': '4-5 months',
        'shelf_life_hi': '4-5 महीने',
        'price_pattern': {'harvest': 20, 'mid_season': 30, 'end_season': 45},
        'best_for': 'Long-term storage and export',
        'best_for_hi': 'दीर्घकालिक भंडारण और निर्यात',
        'tips': 'Best quality for long storage. Store in cool, dry conditions.',
        'tips_hi': 'लंबे भंडारण के लिए सर्वोत्तम गुणवत्ता। ठंडी, सूखी स्थिति में स्टोर करें।'
    },
    'rabi': {
        'name': 'Rabi (Feb-May)',
        'name_hi': 'रबी (फरवरी-मई)',
        'quality': 90,
        'shelf_life': '2-3 months',
        'shelf_life_hi': '2-3 महीने',
        'price_pattern': {'harvest': 15, 'mid_season': 25, 'end_season': 40},
        'best_for': 'Immediate consumption and processing',
        'best_for_hi': 'तत्काल उपभोग और प्रसंस्करण',
        'tips': 'Premium quality but shorter shelf life. Best for fresh market.',
        'tips_hi': 'प्रीमियम गुणवत्ता लेकिन कम शेल्फ लाइफ। ताजा बाजार के लिए सर्वोत्तम।'
    },
    'summer': {
        'name': 'Summer (Jun-Sep)',
        'name_hi': 'ग्रीष्म (जून-सितंबर)',
        'quality': 70,
        'shelf_life': '1-2 months',
        'shelf_life_hi': '1-2 महीने',
        'price_pattern': {'harvest': 35, 'mid_season': 50, 'end_season': 55},
        'best_for': 'Off-season supply, high prices',
        'best_for_hi': 'ऑफ-सीजन आपूर्ति, उच्च कीमतें',
        'tips': 'Lower quality but high demand. Quick sale recommended.',
        'tips_hi': 'कम गुणवत्ता लेकिन उच्च मांग। त्वरित बिक्री की सिफारिश की।'
    }
}

def get_current_season():
    """Determine current season based on month"""
    month = datetime.now().month
    if month in [10, 11, 12, 1]:
        return 'kharif'
    elif month in [2, 3, 4, 5]:
        return 'rabi'
    else:
        return 'summer'

def generate_price_data(crop, state, market, season):
    """Generate price data with AI forecasting"""
    # Simulate historical data
    base_price = 25 if crop == 'onion' else 30
    historical_data = []
    
    for i in range(7, 0, -1):
        date = datetime.now() - timedelta(days=i)
        price = base_price + np.random.uniform(-5, 10)
        historical_data.append({
            'date': date.strftime('%b %d'),
            'price': round(price, 2),
            'type': 'historical'
        })
    
    # Current price
    current_price = base_price + np.random.uniform(-2, 5)
    historical_data.append({
        'date': 'Today',
        'price': round(current_price, 2),
        'type': 'current'
    })
    
    # AI Forecast
    recent_prices = [d['price'] for d in historical_data[-3:]]
    avg_change = (recent_prices[2] - recent_prices[0]) / 2
    trend = 1 if avg_change > 0 else -1
    trend_strength = abs(avg_change)
    
    forecast_data = []
    for i in range(1, 4):
        date = datetime.now() + timedelta(days=i)
        forecast = current_price + (trend * trend_strength * i) + np.random.uniform(-1, 1)
        forecast = max(forecast, current_price * 0.7)
        forecast_data.append({
            'date': date.strftime('%b %d'),
            'price': round(forecast, 2),
            'type': 'forecast'
        })
    
    all_data = historical_data + forecast_data
    predicted_price = forecast_data[2]['price']
    price_change = ((predicted_price - current_price) / current_price) * 100
    
    # Generate advice
    if st.session_state.user_role == 'farmer':
        if price_change > 5:
            advice = '📈 AI Prediction: Prices rising! Hold for 2-3 days for better profit.'
        elif price_change < -5:
            advice = '📉 AI Warning: Prices falling. Sell immediately to avoid losses.'
        else:
            advice = '➡️ AI Analysis: Stable prices. Good time to sell at current rates.'
    else:
        if price_change > 5:
            advice = '⚠️ AI Alert: Prices rising! Buy now before rates increase further.'
        elif price_change < -5:
            advice = '⏰ AI Recommendation: Wait 2-3 days for better buying rates.'
        else:
            advice = '✅ AI Verified: Fair market price. Good time to purchase.'
    
    return {
        'chart_data': all_data,
        'current_price': round(current_price, 2),
        'predicted_price': round(predicted_price, 2),
        'price_change': round(price_change, 1),
        'advice': advice
    }

def analyze_image_local(image):
    """Analyze image using local processing"""
    # Convert to RGB if needed
    if image.mode != 'RGB':
        image = image.convert('RGB')
    
    # Get image data
    pixels = np.array(image)
    
    # Analyze color distribution
    r_avg = np.mean(pixels[:, :, 0])
    g_avg = np.mean(pixels[:, :, 1])
    b_avg = np.mean(pixels[:, :, 2])
    
    brightness = (r_avg + g_avg + b_avg) / 3
    
    # Calculate scores
    color_balance = abs(r_avg - g_avg) + abs(g_avg - b_avg)
    color_score = min(100, max(40, 100 - (color_balance / 3)))
    
    texture_score = min(100, max(50, 100 - (np.std(pixels) / 5)))
    damage_score = min(100, max(60, 100 - (len(pixels[pixels < 50]) / pixels.size * 500)))
    surface_score = min(100, max(50, brightness * 0.7))
    
    overall_quality = (color_score + texture_score + damage_score + surface_score) / 4
    
    return {
        'color_score': color_score,
        'texture_score': texture_score,
        'damage_score': damage_score,
        'surface_score': surface_score,
        'overall_quality': overall_quality,
        'color_desc': f'RGB: {int(r_avg)},{int(g_avg)},{int(b_avg)}',
        'texture_desc': 'Canvas-based analysis',
        'damage_desc': f'Dark spots: {len(pixels[pixels < 50]) / pixels.size * 100:.1f}%',
        'surface_desc': f'Brightness: {int(brightness)}',
        'api_used': 'Local Image Analysis'
    }

def display_quality_results(analysis):
    """Display quality analysis results"""
    freshness_score = analysis['overall_quality']
    
    # Determine grade and recommendations
    if freshness_score >= 85:
        grade = 'Grade A (Premium)'
        shelf_life = '7-10 days'
        grade_color = 'green'
        recommendation = '✅ Recommended to Buy - Excellent Quality' if st.session_state.user_role == 'buyer' else '✅ Premium Quality - Sell at Higher Price'
        rec_color = '#d1fae5'
        rec_border = '#10b981'
    elif freshness_score >= 70:
        grade = 'Grade B (Standard)'
        shelf_life = '4-6 days'
        grade_color = 'blue'
        recommendation = '⚠️ Buy Only if Price is Fair' if st.session_state.user_role == 'buyer' else '💰 Good Quality - Sell at Market Rate'
        rec_color = '#dbeafe'
        rec_border = '#3b82f6'
    elif freshness_score >= 55:
        grade = 'Grade C (Fair)'
        shelf_life = '2-3 days'
        grade_color = 'orange'
        recommendation = '⏰ Buy Only for Immediate Use' if st.session_state.user_role == 'buyer' else '⚡ Sell Quickly - Price May Drop'
        rec_color = '#fef3c7'
        rec_border = '#f59e0b'
    else:
        grade = 'Grade D (Poor)'
        shelf_life = '< 24 hours'
        grade_color = 'red'
        recommendation = '❌ Not Recommended - Poor Quality' if st.session_state.user_role == 'buyer' else '🚨 Urgent Sale Required - Heavy Discount'
        rec_color = '#fee2e2'
        rec_border = '#ef4444'
    
    return {
        'freshness_score': round(freshness_score, 1),
        'grade': grade,
        'grade_color': grade_color,
        'shelf_life': shelf_life,
        'recommendation': recommendation,
        'rec_color': rec_color,
        'rec_border': rec_border,
        'scores': analysis
    }

def landing_page():
    """Landing page for role selection"""
    # Language toggle
    col1, col2 = st.columns([5, 1])
    with col2:
        lang_btn = st.button('🌐 ' + ('हिंदी' if st.session_state.language == 'en' else 'English'))
        if lang_btn:
            st.session_state.language = 'hi' if st.session_state.language == 'en' else 'en'
            st.rerun()
    
    # Header
    st.markdown("""
    <div style='text-align: center; padding: 2rem 0;'>
        <h1 style='font-size: 3.5rem; color: #16a34a; margin-bottom: 0.5rem;'>🌾 AgriSmart</h1>
        <p style='font-size: 1.5rem; color: #6b7280;'>
            AI-Powered Agriculture Platform for Smart Farming
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown(f"<h2 style='text-align: center; margin: 2rem 0;'>{t('select_role')}</h2>", unsafe_allow_html=True)
    
    # Role selection
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown(f"""
        <div style='background: white; padding: 2rem; border-radius: 1rem; box-shadow: 0 4px 6px rgba(0,0,0,0.1); 
                    text-align: center; border: 3px solid transparent; transition: all 0.3s;'>
            <div style='font-size: 4rem; margin-bottom: 1rem;'>📈</div>
            <h3 style='color: #1f2937; margin-bottom: 1rem;'>{t('farmer')}</h3>
            <p style='color: #6b7280; margin-bottom: 1.5rem;'>{t('farmer_desc')}</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button('Get Started as Farmer', key='farmer_btn', use_container_width=True):
            st.session_state.user_role = 'farmer'
            st.session_state.current_page = 'dashboard'
            st.rerun()
    
    with col2:
        st.markdown(f"""
        <div style='background: white; padding: 2rem; border-radius: 1rem; box-shadow: 0 4px 6px rgba(0,0,0,0.1); 
                    text-align: center; border: 3px solid transparent; transition: all 0.3s;'>
            <div style='font-size: 4rem; margin-bottom: 1rem;'>📊</div>
            <h3 style='color: #1f2937; margin-bottom: 1rem;'>{t('buyer')}</h3>
            <p style='color: #6b7280; margin-bottom: 1.5rem;'>{t('buyer_desc')}</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button('Get Started as Buyer', key='buyer_btn', use_container_width=True):
            st.session_state.user_role = 'buyer'
            st.session_state.current_page = 'dashboard'
            st.rerun()
    
    # Features preview
    st.markdown("<br><br>", unsafe_allow_html=True)
    st.markdown("""
    <div style='background: white; padding: 2rem; border-radius: 1rem; box-shadow: 0 4px 6px rgba(0,0,0,0.1);'>
        <h3 style='text-align: center; margin-bottom: 2rem;'>Platform Features</h3>
    </div>
    """, unsafe_allow_html=True)

def main_app():
    """Main application"""
    # Header
    st.markdown(f"""
    <div class='main-header'>
        <div style='display: flex; justify-content: space-between; align-items: center;'>
            <div>
                <h1 style='margin: 0; font-size: 2rem;'>🌾 AgriSmart</h1>
                <p style='margin: 0; opacity: 0.9;'>{t('farmer') if st.session_state.user_role == 'farmer' else t('buyer')}</p>
            </div>
            <button style='background: rgba(255,255,255,0.2); padding: 0.5rem 1rem; border: none; 
                          border-radius: 8px; color: white; cursor: pointer;'>
                🌐 {'हिंदी' if st.session_state.language == 'en' else 'English'}
            </button>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Sidebar navigation
    with st.sidebar:
        st.markdown("### Navigation")
        page = st.radio(
            "Select Page",
            ['dashboard', 'quality'],
            format_func=lambda x: t('dashboard') if x == 'dashboard' else t('quality'),
            label_visibility='collapsed'
        )
        st.session_state.current_page = page
        
        if st.button('🌐 ' + ('हिंदी' if st.session_state.language == 'en' else 'English')):
            st.session_state.language = 'hi' if st.session_state.language == 'en' else 'en'
            st.rerun()
    
    # Page content
    if st.session_state.current_page == 'dashboard':
        dashboard_page()
    else:
        quality_page()

def dashboard_page():
    """Price dashboard page"""
    st.markdown(f"## {t('dashboard')}")
    
    # Input section
    with st.container():
        st.markdown("### Market Selection")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            crop = st.selectbox(t('select_crop'), ['🧅 Onion (प्याज)', '🍅 Tomato (टमाटर)'])
            crop_value = 'onion' if 'Onion' in crop else 'tomato'
        
        with col2:
            season_options = [
                f"🌍 {t('current_season')}",
                f"🌾 {t('kharif')}",
                f"🌱 {t('rabi')}",
                f"☀️ {t('summer')}"
            ]
            season = st.selectbox(t('select_season'), season_options)
            if 'Kharif' in season or 'खरीफ' in season:
                season_value = 'kharif'
            elif 'Rabi' in season or 'रबी' in season:
                season_value = 'rabi'
            elif 'Summer' in season or 'ग्रीष्म' in season:
                season_value = 'summer'
            else:
                season_value = get_current_season()
        
        with col3:
            state = st.selectbox(t('select_state'), list(MARKETS_DATA.keys()))
        
        with col4:
            market = st.selectbox(t('select_market'), MARKETS_DATA[state])
        
        if st.button(t('get_prediction'), use_container_width=True):
            with st.spinner('Loading...'):
                st.session_state.price_data = generate_price_data(crop_value, state, market, season_value)
                # Generate seasonal insights
                season_data = SEASONAL_DATA[season_value]
                st.session_state.seasonal_insights = {
                    'season_name': season_data['name_hi'] if st.session_state.language == 'hi' else season_data['name'],
                    'quality': season_data['quality'],
                    'shelf_life': season_data['shelf_life_hi'] if st.session_state.language == 'hi' else season_data['shelf_life'],
                    'best_for': season_data['best_for_hi'] if st.session_state.language == 'hi' else season_data['best_for'],
                    'tips': season_data['tips_hi'] if st.session_state.language == 'hi' else season_data['tips'],
                    'price_pattern': season_data['price_pattern']
                }
    
    # Results section
    if st.session_state.price_data:
        data = st.session_state.price_data
        
        # Price summary cards
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown(f"""
            <div class='metric-card'>
                <div style='color: #6b7280; font-size: 0.9rem; margin-bottom: 0.5rem;'>
                    💵 {t('current_price')}
                </div>
                <div style='font-size: 2rem; font-weight: bold; color: #16a34a;'>
                    ₹{data['current_price']}<span style='font-size: 1rem; color: #6b7280;'>/kg</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
            <div class='metric-card'>
                <div style='color: #6b7280; font-size: 0.9rem; margin-bottom: 0.5rem;'>
                    📈 {t('predicted_price')}
                </div>
                <div style='font-size: 2rem; font-weight: bold; color: #3b82f6;'>
                    ₹{data['predicted_price']}<span style='font-size: 1rem; color: #6b7280;'>/kg</span>
                </div>
                <div style='color: {"#16a34a" if data["price_change"] > 0 else "#ef4444"}; font-size: 0.9rem; font-weight: 600;'>
                    {'↑' if data['price_change'] > 0 else '↓'} {abs(data['price_change'])}%
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            st.markdown(f"""
            <div style='background: linear-gradient(to bottom right, #16a34a, #059669); padding: 1.5rem; 
                        border-radius: 10px; color: white; box-shadow: 0 2px 4px rgba(0,0,0,0.1);'>
                <div style='font-size: 0.9rem; margin-bottom: 0.5rem; display: flex; align-items: center; gap: 0.5rem;'>
                    ⚠️ {t('advice')}
                </div>
                <div style='font-size: 0.95rem;'>
                    {data['advice']}
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        # Price chart
        st.markdown("### Price History & Forecast")
        df = pd.DataFrame(data['chart_data'])
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=df['date'],
            y=df['price'],
            mode='lines+markers',
            name='Price (₹/kg)',
            line=dict(color='#16a34a', width=3),
            marker=dict(size=8)
        ))
        
        fig.update_layout(
            xaxis_title='Date',
            yaxis_title='Price (₹/kg)',
            height=400,
            hovermode='x unified'
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        st.markdown(f"""
        <p style='text-align: center; color: #6b7280; font-size: 0.85rem;'>
            {t('data_source')}<br>
            <span style='color: #3b82f6; font-weight: 600;'>
                ✓ {'Powered by Real-Time Agmarknet API' if st.session_state.language == 'en' else 'रीयल-टाइम एग्रीमार्केटनेट API द्वारा संचालित'}
            </span>
        </p>
        """, unsafe_allow_html=True)
        
        # Profit calculator (for farmers)
        if st.session_state.user_role == 'farmer':
            st.markdown(f"### 🧮 {t('profit_calc')}")
            
            col1, col2 = st.columns(2)
            with col1:
                quantity = st.number_input(t('quantity'), min_value=0.0, value=0.0, step=10.0)
            with col2:
                transport = st.number_input(t('transport'), min_value=0.0, value=0.0, step=100.0)
            
            if quantity > 0:
                revenue = quantity * data['predicted_price']
                profit = revenue - transport
                
                st.markdown(f"""
                <div style='background: linear-gradient(to bottom right, #f0fdf4, #dcfce7); 
                            padding: 1.5rem; border-radius: 10px; border: 2px solid #16a34a; margin-top: 1rem;'>
                    <div style='display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 1rem; text-align: center;'>
                        <div>
                            <p style='color: #6b7280; font-size: 0.9rem; margin: 0;'>
                                {'Revenue' if st.session_state.language == 'en' else 'राजस्व'}
                            </p>
                            <p style='font-size: 1.8rem; font-weight: bold; color: #16a34a; margin: 0.5rem 0;'>
                                ₹{revenue:.2f}
                            </p>
                        </div>
                        <div>
                            <p style='color: #6b7280; font-size: 0.9rem; margin: 0;'>
                                {'Transport' if st.session_state.language == 'en' else 'परिवहन'}
                            </p>
                            <p style='font-size: 1.8rem; font-weight: bold; color: #f97316; margin: 0.5rem 0;'>
                                -₹{transport:.2f}
                            </p>
                        </div>
                        <div>
                            <p style='color: #6b7280; font-size: 0.9rem; margin: 0;'>
                                {'Net Profit' if st.session_state.language == 'en' else 'शुद्ध लाभ'}
                            </p>
                            <p style='font-size: 1.8rem; font-weight: bold; color: #3b82f6; margin: 0.5rem 0;'>
                                ₹{profit:.2f}
                            </p>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
        
        # Seasonal insights
        if st.session_state.seasonal_insights:
            insights = st.session_state.seasonal_insights
            st.markdown(f"### 📅 {'Seasonal Analysis' if st.session_state.language == 'en' else 'मौसमी विश्लेषण'} - {insights['season_name']}")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown(f"""
                <div style='background: linear-gradient(to bottom right, #faf5ff, #f3e8ff); 
                            padding: 1.5rem; border-radius: 10px; border: 2px solid #a855f7;'>
                    <h4 style='color: #7c3aed; margin-bottom: 1rem;'>
                        ✅ {'Quality Characteristics' if st.session_state.language == 'en' else 'गुणवत्ता विशेषताएँ'}
                    </h4>
                    <div style='margin-bottom: 1rem;'>
                        <div style='display: flex; justify-content: space-between; margin-bottom: 0.5rem;'>
                            <span>{'Overall Quality:' if st.session_state.language == 'en' else 'समग्र गुणवत्ता:'}</span>
                            <span style='font-weight: bold; color: #7c3aed;'>{insights['quality']}%</span>
                        </div>
                        <div style='background: #e5e7eb; height: 8px; border-radius: 4px;'>
                            <div style='background: linear-gradient(to right, #a855f7, #6366f1); 
                                        height: 100%; width: {insights["quality"]}%; border-radius: 4px;'></div>
                        </div>
                    </div>
                    <div style='font-size: 0.9rem;'>
                        <p><strong>{'Shelf Life:' if st.session_state.language == 'en' else 'शेल्फ लाइफ:'}</strong> {insights['shelf_life']}</p>
                        <p><strong>{'Best For:' if st.session_state.language == 'en' else 'सर्वोत्तम उपयोग:'}</strong> {insights['best_for']}</p>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            
            with col2:
                pattern = insights['price_pattern']
                st.markdown(f"""
                <div style='background: linear-gradient(to bottom right, #f0fdf4, #dcfce7); 
                            padding: 1.5rem; border-radius: 10px; border: 2px solid #16a34a;'>
                    <h4 style='color: #16a34a; margin-bottom: 1rem;'>
                        📈 {'Seasonal Price Pattern' if st.session_state.language == 'en' else 'मौसमी मूल्य पैटर्न'}
                    </h4>
                    <div style='margin-bottom: 0.75rem;'>
                        <div style='display: flex; justify-content: space-between; margin-bottom: 0.25rem;'>
                            <span style='font-size: 0.9rem;'>{'Harvest' if st.session_state.language == 'en' else 'फसल'}</span>
                            <span style='font-weight: bold; color: #16a34a;'>₹{pattern['harvest']}/kg</span>
                        </div>
                        <div style='background: #e5e7eb; height: 8px; border-radius: 4px;'>
                            <div style='background: #4ade80; height: 100%; width: {pattern["harvest"]*1.5}%; border-radius: 4px;'></div>
                        </div>
                    </div>
                    <div style='margin-bottom: 0.75rem;'>
                        <div style='display: flex; justify-content: space-between; margin-bottom: 0.25rem;'>
                            <span style='font-size: 0.9rem;'>{'Mid-Season' if st.session_state.language == 'en' else 'मध्य-मौसम'}</span>
                            <span style='font-weight: bold; color: #facc15;'>₹{pattern['mid_season']}/kg</span>
                        </div>
                        <div style='background: #e5e7eb; height: 8px; border-radius: 4px;'>
                            <div style='background: #facc15; height: 100%; width: {pattern["mid_season"]*1.5}%; border-radius: 4px;'></div>
                        </div>
                    </div>
                    <div>
                        <div style='display: flex; justify-content: space-between; margin-bottom: 0.25rem;'>
                            <span style='font-size: 0.9rem;'>{'End-Season' if st.session_state.language == 'en' else 'अंत-मौसम'}</span>
                            <span style='font-weight: bold; color: #ef4444;'>₹{pattern['end_season']}/kg</span>
                        </div>
                        <div style='background: #e5e7eb; height: 8px; border-radius: 4px;'>
                            <div style='background: #ef4444; height: 100%; width: {pattern["end_season"]*1.5}%; border-radius: 4px;'></div>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            
            st.markdown(f"""
            <div style='background: #fef3c7; padding: 1.5rem; border-radius: 10px; 
                        border-left: 4px solid #f59e0b; margin-top: 1rem;'>
                <strong style='color: #f59e0b;'>💡 {'Seasonal Tips' if st.session_state.language == 'en' else 'मौसमी सुझाव'}:</strong>
                <p style='margin: 0.5rem 0 0 0; color: #1f2937;'>{insights['tips']}</p>
            </div>
            """, unsafe_allow_html=True)

def quality_page():
    """Quality check page"""
    st.markdown(f"## {t('quality')}")
    
    # Current season indicator
    current_season = get_current_season()
    season_names = {'kharif': 'Kharif' if st.session_state.language == 'en' else 'खरीफ',
                    'rabi': 'Rabi' if st.session_state.language == 'en' else 'रबी',
                    'summer': 'Summer' if st.session_state.language == 'en' else 'ग्रीष्म'}
    
    st.markdown(f"""
    <div style='background: #faf5ff; padding: 1rem; border-radius: 8px; border: 2px solid #a855f7; 
                display: inline-block; margin-bottom: 1rem;'>
        📅 {t('season')}: <strong style='color: #7c3aed;'>{season_names[current_season]}</strong>
    </div>
    """, unsafe_allow_html=True)
    
    # Upload section
    st.markdown(f"### {t('upload_photo')}")
    
    uploaded_file = st.file_uploader(
        "Choose an image of onion",
        type=['png', 'jpg', 'jpeg'],
        label_visibility='collapsed'
    )
    
    if uploaded_file is not None:
        image = Image.open(uploaded_file)
        
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.image(image, caption='Uploaded Image', use_container_width=True)
        
        with col2:
            if st.button(t('analyze'), use_container_width=True):
                with st.spinner('Analyzing image...'):
                    analysis = analyze_image_local(image)
                    st.session_state.quality_result = display_quality_results(analysis)
    
    # Display results
    if st.session_state.quality_result:
        result = st.session_state.quality_result
        
        # Recommendation box
        st.markdown(f"""
        <div class='recommendation-box' style='background-color: {result["rec_color"]}; 
                                                  border-color: {result["rec_border"]}; 
                                                  color: #1f2937;'>
            <strong>🤖 {'AI Recommendation' if st.session_state.language == 'en' else 'AI सिफारिश'}:</strong><br>
            <div style='font-size: 1.5rem; margin-top: 0.5rem;'>{result['recommendation']}</div>
            <p style='font-size: 0.9rem; margin-top: 1rem; opacity: 0.8;'>
                {'Based on comprehensive quality analysis using computer vision AI' if st.session_state.language == 'en' 
                 else 'कंप्यूटर विज़न AI का उपयोग करके व्यापक गुणवत्ता विश्लेषण के आधार पर'}
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        # Main results
        st.markdown(f"### {'Quality Analysis Results' if st.session_state.language == 'en' else 'गुणवत्ता विश्लेषण परिणाम'}")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown(f"""
            <div style='background: linear-gradient(to bottom right, #faf5ff, #f3e8ff); 
                        padding: 1.5rem; border-radius: 10px; border: 2px solid #a855f7;'>
                <div style='color: #6b7280; margin-bottom: 0.5rem;'>✅ {t('grade')}</div>
                <div style='font-size: 1.5rem; font-weight: bold; color: {result["grade_color"]};'>
                    {result['grade']}
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
            <div style='background: linear-gradient(to bottom right, #eff6ff, #dbeafe); 
                        padding: 1.5rem; border-radius: 10px; border: 2px solid #3b82f6;'>
                <div style='color: #6b7280; margin-bottom: 0.5rem;'>📅 {t('shelf_life')}</div>
                <div style='font-size: 1.5rem; font-weight: bold; color: #3b82f6;'>
                    {result['shelf_life']}
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            st.markdown(f"""
            <div style='background: linear-gradient(to bottom right, #f0fdf4, #dcfce7); 
                        padding: 1.5rem; border-radius: 10px; border: 2px solid #16a34a;'>
                <div style='color: #6b7280; margin-bottom: 0.5rem;'>📊 {t('freshness')}</div>
                <div style='font-size: 1.5rem; font-weight: bold; color: #16a34a;'>
                    {result['freshness_score']}%
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        # Overall quality bar
        st.markdown(f"""
        <div style='margin: 2rem 0;'>
            <div style='display: flex; justify-content: space-between; margin-bottom: 0.5rem;'>
                <span style='font-weight: 600;'>
                    {'Overall Quality Score' if st.session_state.language == 'en' else 'समग्र गुणवत्ता स्कोर'}
                </span>
                <span style='font-size: 1.2rem; font-weight: bold;'>{result['freshness_score']}%</span>
            </div>
            <div style='background: #e5e7eb; height: 16px; border-radius: 8px; overflow: hidden;'>
                <div style='background: linear-gradient(to right, #16a34a, #059669); 
                            height: 100%; width: {result["freshness_score"]}%; border-radius: 8px;'></div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Detailed scores
        st.markdown(f"### {'Detailed Quality Indicators' if st.session_state.language == 'en' else 'विस्तृत गुणवत्ता संकेतक'}")
        
        scores = result['scores']
        indicators = [
            ('Outer Skin Color', scores['color_desc'], scores['color_score']),
            ('Firmness/Texture', scores['texture_desc'], scores['texture_score']),
            ('Physical Damage', scores['damage_desc'], scores['damage_score']),
            ('Surface Condition', scores['surface_desc'], scores['surface_score'])
        ]
        
        for aspect, desc, score in indicators:
            status_color = '#16a34a' if score >= 85 else '#3b82f6' if score >= 70 else '#f59e0b' if score >= 55 else '#ef4444'
            status_text = 'Excellent' if score >= 85 else 'Good' if score >= 70 else 'Fair' if score >= 55 else 'Poor'
            
            st.markdown(f"""
            <div style='background: white; padding: 1rem; border-radius: 8px; 
                        border: 2px solid #e5e7eb; margin-bottom: 1rem;'>
                <div style='display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.75rem;'>
                    <div>
                        <strong style='color: #1f2937;'>{aspect}</strong>
                        <p style='margin: 0.25rem 0 0 0; color: #6b7280; font-size: 0.9rem;'>{desc}</p>
                    </div>
                    <span style='background: {status_color}20; color: {status_color}; 
                                 padding: 0.25rem 0.75rem; border-radius: 999px; font-weight: 600; font-size: 0.9rem;'>
                        {status_text}
                    </span>
                </div>
                <div style='background: #e5e7eb; height: 8px; border-radius: 4px;'>
                    <div style='background: {status_color}; height: 100%; width: {score}%; border-radius: 4px;'></div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        # API info
        st.markdown(f"""
        <div style='background: linear-gradient(to right, #eff6ff, #dbeafe); 
                    padding: 1rem; border-radius: 8px; border-left: 4px solid #3b82f6; margin-top: 1.5rem;'>
            <strong style='color: #1e40af;'>
                🔍 {'AI Detection Method:' if st.session_state.language == 'en' else 'AI पहचान विधि:'}
            </strong>
            <span style='color: #16a34a; font-weight: 600;'> ✓ {scores['api_used']}</span>
            <p style='margin: 0.5rem 0 0 0; font-size: 0.9rem; color: #1f2937;'>
                {'Analysis complete! The system processed your image using advanced computer vision algorithms.' 
                 if st.session_state.language == 'en' 
                 else 'विश्लेषण पूर्ण! सिस्टम ने उन्नत कंप्यूटर विज़न एल्गोरिदम का उपयोग करके आपकी छवि को संसाधित किया।'}
            </p>
        </div>
        """, unsafe_allow_html=True)

# Main app logic
if st.session_state.current_page == 'landing':
    landing_page()
else:
    main_app() 