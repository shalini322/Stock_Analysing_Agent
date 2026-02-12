import streamlit as st
import requests

API_URL = "http://127.0.0.1:8000"

st.set_page_config(page_title='Stock Analysis Agent', page_icon='📈', layout='wide')
st.title('AI Stock Analysis Agent')

# Sidebar Configuration
st.sidebar.header('⚙️ Configuration')
ticker = st.sidebar.text_input('Stock Ticker', value='NVDA').upper()
period = st.sidebar.radio('Financial Period', ['yearly', 'quarterly'])

if st.sidebar.button("🔍 Analyze Stock", type="primary", disabled=st.session_state.get("loading", False)):
    st.session_state.loading = True
    with st.spinner(f'🤖 AI Agent is analyzing {ticker}...'):
        try:
            response = requests.post(
                f"{API_URL}/analyze", 
                json={"ticker": ticker, "period": period},
                timeout=180
            )
            if response.status_code == 200:
                st.session_state.result = response.json()
                st.session_state.chat_history = []
            else:
                st.error(f"Backend Error: {response.json().get('detail', 'Unknown error')}")
        except requests.exceptions.ConnectionError:
            st.error("❌ Could not connect to Backend.")
        finally:
            st.session_state.loading = False  

if "result" in st.session_state:
    res = st.session_state.result
    
    # Render Tabs
    tab1, tab2, tab3, tab4 = st.tabs(['📊 Price Data', '💰 Financials', '🔍 Analysis', '💡 Recommendation'])
    
    # --- Price Data Tab ---
    with tab1:
        price_data = res.get('price_data', {})
        current_price = float(price_data.get('current_price', 0) or 0)
        fifty_two_week_avg = float(price_data.get('fifty_two_week_avg', 0) or 0)
        market_cap_price = float(price_data.get('market_cap', 0) or 0)

        st.subheader(f"{price_data.get('company_name', ticker)} Metrics")
        col1, col2, col3 = st.columns(3)
        col1.metric("Current Price", f"${current_price:.2f}")
        col2.metric("52-Week Range Avg", f"${fifty_two_week_avg:.2f}")
        col3.metric("Market Cap", f"${market_cap_price / 1e9:.2f}B")
    
    # --- Financials Tab ---
    with tab2:
        st.subheader("Financial Statements")
        f_data = res.get("financial_data", {})

        c1, c2, c3 = st.columns(3)
        with c1:
            st.write("**Balance Sheet (Yearly)**")
            st.write("_Values in USD Millions_")
            st.json(f_data.get("balance_sheet", {}))

        with c2:
            st.write("**Income Statement (Yearly)**")
            st.write("_Values in USD Millions_")
            st.json(f_data.get("income_statement", {}))

        with c3:
            st.write("**Cash Flow (Yearly)**")
            st.write("_Values in USD Millions_")
            st.json(f_data.get("cash_flow", {}))

        st.markdown("---")
        st.subheader("Key Metrics")

        profitability = res.get("profitability", {})
        valuation     = res.get("valuation", {})
        price_block   = res.get("price_data", {})

        gross_margin   = profitability.get("gross_margin")
        net_margin     = profitability.get("net_margin")
        eps            = profitability.get("eps")

        market_cap_val = valuation.get("market_cap")
        pe_ratio       = valuation.get("pe_ratio")
        forward_pe     = valuation.get("forward_pe")
        enterprise_val = valuation.get("enterprise_value")
        ps_ratio       = valuation.get("ps_ratio")

        current_px     = price_block.get("current_price")
        prev_close     = price_block.get("previous_close")

        m1, m2, m3, m4 = st.columns(4)

        with m1:
            if gross_margin is not None:
                st.metric("Gross margin", f"{gross_margin:.2f}%")
            if net_margin is not None:
                st.metric("Net margin", f"{net_margin:.2f}%")

        with m2:
            if eps is not None:
                st.metric("EPS", f"{eps:.4f}")
            if market_cap_val is not None:
                st.metric("Market cap", f"${market_cap_val:,.0f}")

        with m3:
            if pe_ratio is not None:
                st.metric("P/E ratio", f"{pe_ratio:.2f}")
            if forward_pe is not None:
                st.metric("Forward P/E", f"{forward_pe:.2f}")

        with m4:
            if current_px is not None:
                st.metric("Current price", f"${current_px:.2f}")
            if prev_close is not None:
                st.metric("Previous close", f"${prev_close:.2f}")
            # Optional extra metrics
            # if enterprise_val is not None:
            #     st.metric("Enterprise Value", f"${enterprise_val:,.0f}")
            # if ps_ratio is not None:
            #     st.metric("P/S ratio", f"{ps_ratio:.2f}")
    
    # --- Analysis Tab ---
    with tab3:
        st.subheader("🔍 AI Financial Analysis")
        st.markdown(res.get('analysis', "No analysis generated."))

    # --- Recommendation Tab ---
    with tab4:
        st.subheader("💡 Strategic Recommendation")
        st.markdown(res.get('recommendation', "No recommendation generated."))

    # --- Chat UI ---
    st.markdown("---")
    st.subheader(f"💬 Chat with {ticker} Analyst")

    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []

    for msg in st.session_state.chat_history:
        with st.chat_message(msg['role']):
            st.markdown(msg['content'])

    if prompt := st.chat_input("Ask a follow-up question..."):
        st.session_state.chat_history.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            chat_payload = {
                "context": res.get('analysis', ''),
                "history": "\n".join([f"{m['role']}: {m['content']}" for m in st.session_state.chat_history]),
                "prompt": prompt
            }
            try:
                chat_res = requests.post(f"{API_URL}/chat", json=chat_payload).json()
                response_text = chat_res.get('response', 'Sorry, I encountered an error.')
                st.markdown(response_text)
                st.session_state.chat_history.append({"role": "assistant", "content": response_text})
            except:
                st.error("Failed to get chat response.")
