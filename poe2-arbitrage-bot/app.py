import streamlit as st
import requests
import pandas as pd

# This configures the webpage layout
st.set_page_config(page_title="PoE 2 Arbitrage Scanner", layout="wide")

st.title("Path of Exile 2: Arbitrage Scanner")
st.markdown("Automatically fetch live market data, filter high-volume trades, and calculate cross-currency arbitrage.")

# Sidebar UI Elements for you to interact with
st.sidebar.header("Scanner Settings")
league = st.sidebar.text_input("League", "Runes+of+Aldur")
min_volume = st.sidebar.number_input("Minimum Volume Filter", min_value=100, max_value=50000, value=1000, step=100)
gold_cost = st.sidebar.number_input("Gold Cost per Trade Unit", min_value=0, max_value=5000, value=250, step=10)

# The main action button
if st.button("Scan Market Now", type="primary"):
    with st.spinner("Fetching live data from API..."):
        url = f"https://poe.ninja/api/data/currencyoverview?league={league}&type=Currency"
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        
        try:
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                data = response.json()
                lines = data.get('lines', [])
                
                # Establish Baseline Rates from the live data
                rates = {'Chaos': 1.0, 'Divine': 0, 'Exalt': 0}
                for item in lines:
                    if item['currencyTypeName'] == 'Divine Orb':
                        rates['Divine'] = item.get('receive', {}).get('value', 0)
                    elif item['currencyTypeName'] == 'Exalted Orb':
                        rates['Exalt'] = item.get('receive', {}).get('value', 0)
                
                # Display the live base rates at the top
                st.success(f"**LIVE BASE RATES:** 1 Divine = {rates['Divine']} Chaos | 1 Exalt = {rates['Exalt']} Chaos")
                
                results = []
                
                # Scan every item and apply your logic
                for item in lines:
                    name = item.get('currencyTypeName')
                    receive = item.get('receive', {})
                    pay = item.get('pay', {})
                    
                    buy_vol = receive.get('count', 0)
                    sell_vol = pay.get('count', 0)
                    
                    # 1. Volume Filter
                    lowest_vol = min(buy_vol, sell_vol)
                    if lowest_vol >= min_volume:
                        
                        buy_price_chaos = receive.get('value', 0)
                        sell_price_chaos = pay.get('value', 0)
                        
                        # 2. Opportunity Calculation
                        if buy_price_chaos > 0 and sell_price_chaos > 0:
                            profit_chaos = sell_price_chaos - buy_price_chaos
                            
                            # We only care about positive arbitrage
                            if profit_chaos > 0:
                                results.append({
                                    "Item": name,
                                    "Volume": lowest_vol,
                                    "Buy Price (Chaos)": round(buy_price_chaos, 2),
                                    "Sell Price (Chaos)": round(sell_price_chaos, 2),
                                    "Est. Profit (Chaos)": round(profit_chaos, 2),
                                    "Total Gold Cost": gold_cost * 2
                                })
                
                # 3. Render the UI Table
                if results:
                    # Convert to a data table and sort by highest profit
                    df = pd.DataFrame(results).sort_values(by="Est. Profit (Chaos)", ascending=False)
                    st.dataframe(df, use_container_width=True, hide_index=True)
                else:
                    st.info(f"No profitable items found with a volume higher than {min_volume}.")
            else:
                st.error("Failed to fetch data from API. Please try again.")
        except Exception as e:
            st.error(f"An error occurred: {e}")