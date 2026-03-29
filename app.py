import streamlit as st
import pandas as pd
import yfinance as yf
from datetime import datetime, date
import plotly.express as px
import time

# ====================== ページ設定 ======================
st.set_page_config(
    page_title="株の握力測定",
    layout="centered",
    page_icon="💪",
    initial_sidebar_state="collapsed"
)

st.title("💪 株の握力測定ソフト")
st.markdown("**保有期間をカレンダーで簡単入力**して、**日本株・米国株・仮想通貨・ミームコイン・インデックス**の**投資握力**を診断！ 📱")

# ====================== セッション状態 ======================
if "portfolio" not in st.session_state:
    st.session_state.portfolio = pd.DataFrame(columns=[
        "銘柄コード", "銘柄名", "購入日", "保有期間(日)", "保有数量", 
        "取得価格", "現在価格", "含み損益率(%)", "含み損益額", "評価額"
    ])

# ====================== データ取得関数（強化版） ======================
def get_current_price(ticker: str):
    try:
        original = ticker.strip().upper()
        if original.replace(".", "").replace("-", "").isdigit() or len(original) <= 6:
            if not original.endswith(".T"):
                ticker = original + ".T"
        else:
            ticker = original

        stock = yf.Ticker(ticker)
        
        for attempt in range(3):
            try:
                price = stock.fast_info.get('lastPrice') or stock.fast_info.get('last_price')
                if price and price > 0:
                    return round(float(price), 4)
            except:
                pass
            
            data = stock.history(period="5d")
            if not data.empty:
                return round(data['Close'].iloc[-1], 4)
            
            time.sleep(0.8)
        
        return None
    except Exception:
        return None

# ====================== 握力ランク ======================
def get_grip_rank(days: int):
    if days >= 365:
        return "🦾 鉄の握力（伝説級）"
    elif days >= 180:
        return "💪 強い握力（上級者）"
    elif days >= 90:
        return "👍 普通の握力（中級者）"
    elif days >= 30:
        return "👌 まだ握れてる（初心者脱却）"
    else:
        return "🤏 握力弱め（要注意）"

# ====================== 銘柄リスト（名前＋コード） ======================
TICKER_DICT = {
    # 日本株
    "トヨタ自動車 (7203.T)": "7203.T",
    "ソフトバンクグループ (9984.T)": "9984.T",
    "ソニーグループ (6758.T)": "6758.T",
    "NTT (9432.T)": "9432.T",
    "ソフトバンク (9434.T)": "9434.T",
    "三菱UFJフィナンシャル (8306.T)": "8306.T",
    "ファストリテイリング (9983.T)": "9983.T",
    "東京エレクトロン (8035.T)": "8035.T",

    # 米国株
    "アップル (AAPL)": "AAPL",
    "マイクロソフト (MSFT)": "MSFT",
    "エヌビディア (NVDA)": "NVDA",
    "テスラ (TSLA)": "TSLA",
    "アマゾン (AMZN)": "AMZN",
    "アルファベット (GOOGL)": "GOOGL",
    "メタ・プラットフォームズ (META)": "META",
    "バークシャー・ハサウェイ (BRK-B)": "BRK-B",

    # インデックス
    "S&P500 (^GSPC)": "^GSPC",
    "ダウ平均 (^DJI)": "^DJI",
    "ナスダック (^IXIC)": "^IXIC",
    "日経平均 (^N225)": "^N225",
    "東証プライム (^TOPX)": "^TOPX",

    # 主要仮想通貨
    "ビットコイン (BTC-USD)": "BTC-USD",
    "イーサリアム (ETH-USD)": "ETH-USD",
    "XRP (XRP-USD)": "XRP-USD",
    "ソラナ (SOL-USD)": "SOL-USD",
    "カルダノ (ADA-USD)": "ADA-USD",
    "アバランチ (AVAX-USD)": "AVAX-USD",
    "BNB (BNB-USD)": "BNB-USD",

    # ミームコイン
    "ドージコイン (DOGE-USD)": "DOGE-USD",
    "柴犬コイン (SHIB-USD)": "SHIB-USD",
    "ペペ (PEPE-USD)": "PEPE-USD",
    "フロキ (FLOKI-USD)": "FLOKI-USD",
    "ボンク (BONK-USD)": "BONK-USD",
    "ドッグウィフハット (WIF-USD)": "WIF-USD",

    "その他（手入力）": "その他"
}

ticker_options = list(TICKER_DICT.keys())

# ====================== タブ ======================
tab1, tab2, tab3 = st.tabs(["🆕 銘柄を握る", "📊 ポートフォリオ一覧", "📈 握力分析"])

# ====================== タブ1：銘柄追加 ======================
with tab1:
    st.subheader("🆕 新しい銘柄を握る")
    
    with st.form("add_stock_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            selected_name = st.selectbox(
                "銘柄を選択（検索可能）",
                options=ticker_options,
                help="ミームコイン（DOGE、SHIB、PEPEなど）も名前で選べます！"
            )
            
            if selected_name == "その他（手入力）":
                ticker = st.text_input("銘柄コードを手入力", placeholder="DOGE-USD  or  PEPE-USD  or  AAPL")
                display_name = ticker.upper() if ticker else ""
            else:
                ticker = TICKER_DICT[selected_name]
                display_name = selected_name
        
        with col2:
            purchase_date = st.date_input("購入日", value=date.today(), max_value=date.today())
        
        col3, col4 = st.columns(2)
        with col3:
            acquisition_price = st.number_input("取得価格（1単位あたり）", min_value=0.0001, format="%.4f", value=1000.0)
        with col4:
            shares = st.number_input("保有数量", min_value=0.0001, value=100.0, step=1.0)
        
        submitted = st.form_submit_button("💪 この銘柄をポートフォリオに追加")
        
        if submitted:
            if not ticker or ticker.strip() == "":
                st.error("銘柄を選択または入力してください")
            else:
                current_price = get_current_price(ticker)
                
                if current_price is None:
                    st.error(f"❌ {display_name} の価格を取得できませんでした。少し待ってからもう一度試してください。")
                else:
                    days_held = (datetime.now().date() - purchase_date).days
                    profit_rate = round((current_price - acquisition_price) / acquisition_price * 100, 2) if acquisition_price != 0 else 0
                    profit_amount = round((current_price - acquisition_price) * shares, 0)
                    valuation = round(current_price * shares, 0)
                    
                    new_row = pd.DataFrame([{
                        "銘柄コード": ticker.upper(),
                        "銘柄名": display_name,
                        "購入日": purchase_date,
                        "保有期間(日)": days_held,
                        "保有数量": shares,
                        "取得価格": round(acquisition_price, 4),
                        "現在価格": current_price,
                        "含み損益率(%)": profit_rate,
                        "含み損益額": profit_amount,
                        "評価額": valuation
                    }])
                    
                    st.session_state.portfolio = pd.concat([st.session_state.portfolio, new_row], ignore_index=True)
                    st.success(f"✅ {display_name} を追加しました！ 握力：{days_held}日")

# ====================== タブ2：ポートフォリオ一覧 ======================
with tab2:
    if not st.session_state.portfolio.empty:
        st.subheader("📊 あなたのポートフォリオ")
        
        total_valuation = st.session_state.portfolio["評価額"].sum()
        total_profit = st.session_state.portfolio["含み損益額"].sum()
        total_cost = (st.session_state.portfolio["取得価格"] * st.session_state.portfolio["保有数量"]).sum()
        total_profit_rate = round((total_profit / total_cost * 100), 2) if total_cost > 0 else 0
        avg_days = round(st.session_state.portfolio["保有期間(日)"].mean(), 1)
        
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("総評価額", f"¥{total_valuation:,.0f}")
        col2.metric("総含み損益", f"¥{total_profit:,.0f}", delta=f"{total_profit_rate}%")
        col3.metric("平均保有期間", f"{avg_days}日")
        col4.metric("銘柄数", len(st.session_state.portfolio))
        
        st.info(f"**総合握力：{get_grip_rank(avg_days)}**（平均 {avg_days}日）")
        
        event = st.dataframe(
            st.session_state.portfolio,
            use_container_width=True,
            hide_index=True,
            selection_mode="single-row",
            on_select="rerun",
            column_config={
                "銘柄名": st.column_config.TextColumn("銘柄名", width="large"),
                "銘柄コード": st.column_config.TextColumn("コード"),
                "取得価格": st.column_config.NumberColumn("取得価格", format="¥%.2f"),
                "現在価格": st.column_config.NumberColumn("現在価格", format="¥%.2f"),
                "含み損益率(%)": st.column_config.NumberColumn("損益率(%)", format="%.2f%%"),
                "含み損益額": st.column_config.NumberColumn("損益額", format="¥%.0f"),
                "評価額": st.column_config.NumberColumn("評価額", format="¥%.0f"),
            }
        )
        
        if event and len(event.selection.get("rows", [])) > 0:
            idx = event.selection["rows"][0]
            row = st.session_state.portfolio.iloc[idx]
            
            with st.expander(f"🔍 {row['銘柄名']} の詳細", expanded=True):
                col_a, col_b = st.columns(2)
                with col_a:
                    st.metric("保有期間", f"{row['保有期間(日)']} 日")
                    st.metric("購入日", row['購入日'].strftime('%Y-%m-%d'))
                    st.metric("保有数量", f"{row['保有数量']:.2f}")
                with col_b:
                    st.metric("取得価格", f"¥{row['取得価格']:,.2f}")
                    st.metric("現在価格", f"¥{row['現在価格']:,.2f}")
                    st.metric("含み損益額", f"¥{row['含み損益額']:,.0f}", delta=f"{row['含み損益率(%)']:.2f}%")
                    st.metric("評価額", f"¥{row['評価額']:,.0f}")
                
                st.info(f"**握力ランク：{get_grip_rank(row['保有期間(日)'])}**")
        
        if st.button("🗑️ ポートフォリオをリセット"):
            st.session_state.portfolio = pd.DataFrame(columns=st.session_state.portfolio.columns)
            st.rerun()
    else:
        st.info("まだ銘柄がありません。「銘柄を握る」タブから追加してください！")

# ====================== タブ3：握力分析 ======================
with tab3:
    if not st.session_state.portfolio.empty:
        st.subheader("📈 握力分析")
        
        fig_pie = px.pie(st.session_state.portfolio, values="評価額", names="銘柄名", title="評価額構成比")
        st.plotly_chart(fig_pie, use_container_width=True)
        
        fig_bar = px.bar(st.session_state.portfolio, x="銘柄名", y="保有期間(日)",
                         title="銘柄ごとの保有期間（握力）", color="保有期間(日)")
        st.plotly_chart(fig_bar, use_container_width=True)
        
        fig_scatter = px.scatter(st.session_state.portfolio, x="保有期間(日)", y="含み損益率(%)",
                                 size="評価額", color="銘柄名", title="保有期間 vs 含み損益率")
        st.plotly_chart(fig_scatter, use_container_width=True)
    else:
        st.info("銘柄を追加するとグラフが表示されます。")

st.caption("Made with 💪 & Streamlit | 日本株・米国株・仮想通貨・ミームコイン・インデックス対応 | Yahoo Financeより価格取得")
