import streamlit as st
import cloudscraper
import pandas as pd
import requests

# Set up a wider, modern gaming dashboard layout
st.set_page_config(page_title="PoE 2 Live Arbitrage Scanner", page_icon="🪙", layout="wide")

# Inject Custom CSS
st.markdown("""
<style>
    .metric-container { display: flex; justify-content: space-between; gap: 15px; margin-bottom: 25px; }
    .metric-card { background-color: #1A1D24; border: 1px solid #2E323D; border-radius: 8px; padding: 15px 20px; flex: 1; box-shadow: 0 4px 6px rgba(0,0,0,0.2); border-top: 3px solid #D4AF37; }
    .metric-card h4 { margin: 0; color: #8C92A4; font-size: 0.9rem; text-transform: uppercase; letter-spacing: 1px; }
    .metric-card h2 { margin: 10px 0 0 0; color: #F5F6F8; font-size: 1.8rem; }
</style>
""", unsafe_allow_html=True)

st.title("🪙 Path of Exile 2: Live Arbitrage Dashboard")
st.markdown("Algorithmic scanner utilizing live API feeds.")

# Sidebar Navigation & Settings
st.sidebar.title("⚙️ Scanner Settings")
league = st.sidebar.text_input("Active League Name", "Runes+of+Aldur")
min_volume = st.sidebar.number_input("Minimum Volume Filter (Trades/hr)", min_value=100, max_value=50000, value=1000, step=100)

# Main Execution Trigger
if st.button("🚀 Intercept Live Market Data", type="primary", use_container_width=True):
    with st.spinner("Bypassing Cloudflare and connecting to live API..."):
        
        api_url = f"https://poe.ninja/poe2/api/economy/exchange/current/overview?league={league}&type=Currency"
        
        try:
            # Attempt 1: Use cloudscraper to bypass bot protection
            scraper = cloudscraper.create_scraper(browser={'browser': 'chrome', 'platform': 'windows', 'desktop': True})
            response = scraper.get(api_url)
            
            # Attempt 2: If poe.ninja's Cloudflare still blocks the cloud IP, route through a proxy
            if response.status_code in [401, 403]:
                proxy_url = f"https://api.allorigins.win/raw?url={api_url}"
                response = requests.get(proxy_url)
                
            if response.status_code == 200:
                data = response.json()
                lines = data.get('lines', [])
                
                divine_price = 0.0
                exalt_price = 0.0
                
                # Sift for baseline live orb values directly from the API
                for item in lines:
                    name = item.get('currencyTypeName', '')
                    if name == 'Divine Orb':
                        divine_price = item.get('chaosEquivalent', 0.0) 
                    elif name == 'Exalted Orb':
                        exalt_price = item.get('chaosEquivalent', 0.0)
                
                # Render top visual metric cards
                st.markdown(f"""
                <div class="metric-container">
                    <div class="metric-card" style="border-top-color: #A0AEC0;">
                        <h4>Base Currency</h4>
                        <h2>1.0 Chaos Orb</h2>
                    </div>
                    <div class="metric-card" style="border-top-color: #F6E05E;">
                        <h4>Live Divine Orb Rate</h4>
                        <h2>{divine_price:,.2f} Chaos</h2>
                    </div>
                    <div class="metric-card" style="border-top-color: #E2E8F0;">
                        <h4>Live Exalted Orb Rate</h4>
                        <h2>{exalt_price:,.2f} Chaos</h2>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                # Calculate Arbitrage Opportunities
                opportunities = []
                for item in lines:
                    name = item.get('currencyTypeName', 'Unknown Item')
                    receive = item.get('receive', {}) # Buy side
                    pay = item.get('pay', {})         # Sell side
                    
                    buy_vol = receive.get('count', 0)
                    sell_vol = pay.get('count', 0)
                    
                    # Apply Strict Volume Filter
                    lowest_vol = min(buy_vol, sell_vol)
                    if lowest_vol >= min_volume:
                        
                        buy_rate = receive.get('value', 0.0)
                        sell_rate = pay.get('value', 0.0)
                        
                        if buy_rate > 0 and sell_rate > 0:
                            profit = sell_rate - buy_rate
                            
                            if profit > 0:
                                opportunities.append({
                                    "Item Name": name,
                                    "Active Listings": f"{lowest_vol:,}",
                                    "Market Buy Rate": f"{buy_rate:,.2f} c",
                                    "Market Sell Rate": f"{sell_rate:,.2f} c",
                                    "Net Profit (Chaos Eq.)": profit
                                })
                
                # Display Polished Data Table
                if opportunities:
                    df = pd.DataFrame(opportunities).sort_values(by="Net Profit (Chaos Eq.)", ascending=False)
                    df["Net Profit (Chaos Eq.)"] = df["Net Profit (Chaos Eq.)"].apply(lambda x: f"+{x:,.2f} Chaos equivalents")
                    st.dataframe(df, use_container_width=True, hide_index=True)
                else:
                    st.info(f"No positive arbitrage opportunities found that meet the strict {min_volume:,} hourly volume threshold.")
                    
            else:
                st.error(f"API Failed (HTTP {response.status_code}). Please verify the league name '{league}' is currently active.")
                
        except Exception as e:
            st.error(f"Failed to communicate with the raw data API: {e}")
