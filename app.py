import streamlit as st
import pandas as pd
import yfinance as yf
from datetime import datetime, date
import plotly.express as px

# ====================== ページ設定 ======================
st.set_page_config(
    page_title="株の握力測定",
    layout="centered",
    page_icon="💪"
)

st.title("💪 株の握力測定ソフト")
st.markdown("**保有期間をカレンダーで簡単入力**して、日本株・仮想通貨・インデックス全部の**投資握力**を診断！ 📱")

# ====================== セッション状態初期化 ======================
if "portfolio" not in st.session_state:
    st.session_state.portfolio = pd.DataFrame(columns=[
        "銘柄コード", "購入日", "保有期間(日)", "保有数量", 
        "取得価格", "現在価格", "含み損益率(%)", "含み損益額", "評価額"
    ])

# ====================== データ取得関数（日本株対応強化） ======================
def get_current_price(ticker: str):
    try:
        # 日本株対応：数字のみ or 短いコードなら自動で .T を付与
        original_ticker = ticker.strip().upper()
        if original_ticker.replace(".", "").replace("-", "").isdigit() or len(original_ticker) <= 6:
            if not original_ticker.endswith(".T"):
                ticker = original_ticker + ".T"
        else:
            ticker = original_ticker

        stock = yf.Ticker(ticker)
        
        # fast_infoを優先（高速）
        try:
            price = stock.fast_info.get('lastPrice') or stock.fast_info.get('last_price')
            if price and price > 0:
                return round(float(price), 4)
        except:
            pass
        
        # フォールバック：history
        data = stock.history(period="5d")
        if not data.empty:
            return round(data['Close'].iloc[-1], 4)
        
        return None
    except Exception as e:
        st.warning(f"価格取得エラー: {ticker} → {e}")
        return None

# ====================== 銘柄追加フォーム ======================
with st.form("add_stock_form", clear_on_submit=True):
    st.subheader("🆕 新しい銘柄を握る")
    
    col1, col2 = st.columns(2)
    with col1:
        ticker = st.text_input("銘柄コード", placeholder="7203  or  BTC-USD  or  ^N225")
    with col2:
        purchase_date = st.date_input("購入日", value=date.today(), max_value=date.today())
    
    col3, col4 = st.columns(2)
    with col3:
        acquisition_price = st.number_input("取得価格（1単位あたり）", min_value=0.0001, format="%.4f", value=1000.0)
    with col4:
        shares = st.number_input("保有数量", min_value=0.0001, value=100.0, step=1.0)
    
    submitted = st.form_submit_button("💪 この銘柄をポートフォリオに追加")
    
    if submitted:
        if not ticker:
            st.error("銘柄コードを入力してください")
        else:
            current_price = get_current_price(ticker)
            
            if current_price is None:
                st.error(f"❌ {ticker} の価格を取得できませんでした。コードを確認してください。")
            else:
                days_held = (datetime.now().date() - purchase_date).days
                
                profit_rate = round((current_price - acquisition_price) / acquisition_price * 100, 2) if acquisition_price != 0 else 0
                profit_amount = round((current_price - acquisition_price) * shares, 0)
                valuation = round(current_price * shares, 0)
                
                new_row = pd.DataFrame([{
                    "銘柄コード": ticker.upper(),
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
                st.success(f"✅ {ticker} を追加しました！ 現在の握力：{days_held}日")

# ====================== ポートフォリオ表示 ======================
if not st.session_state.portfolio.empty:
    st.subheader("📊 あなたのポートフォリオ")
    
    # 合計値計算
    total_valuation = st.session_state.portfolio["評価額"].sum()
    total_profit = st.session_state.portfolio["含み損益額"].sum()
    total_profit_rate = round((total_profit / st.session_state.portfolio["取得価格"].sum() * st.session_state.portfolio["保有数量"].sum()) * 100, 2) if total_valuation > 0 else 0
    avg_days = round(st.session_state.portfolio["保有期間(日)"].mean(), 1)
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("総評価額", f"¥{total_valuation:,.0f}")
    col2.metric("総含み損益", f"¥{total_profit:,.0f}", delta=f"{total_profit_rate}%")
    col3.metric("平均保有期間", f"{avg_days}日")
    col4.metric("銘柄数", len(st.session_state.portfolio))
    
    # 握力ランク（遊び心）
    if avg_days >= 365:
        grip = "🦾 鉄の握力（伝説級）"
    elif avg_days >= 180:
        grip = "💪 強い握力（上級者）"
    elif avg_days >= 90:
        grip = "👍 普通の握力（中級者）"
    elif avg_days >= 30:
        grip = "👌 まだ握れてる（初心者脱却）"
    else:
        grip = "🤏 握力弱め（要注意）"
    
    st.info(f"**現在の総合握力：{grip}**（平均保有 {avg_days}日）")
    
    # データフレーム表示（色付け）
    def color_profit(val):
        if val > 0:
            return 'background-color: #d4edda; color: #155724'
        elif val < 0:
            return 'background-color: #f8d7da; color: #721c24'
        return ''
    
    styled_df = st.session_state.portfolio.style.format({
        "取得価格": "{:.2f}",
        "現在価格": "{:.2f}",
        "含み損益率(%)": "{:.2f}",
        "含み損益額": "{:.0f}",
        "評価額": "{:.0f}",
        "保有数量": "{:.2f}"
    }).applymap(color_profit, subset=["含み損益率(%)", "含み損益額"])
    
    st.dataframe(styled_df, use_container_width=True, hide_index=True)
    
    # 削除機能（簡易）
    if st.button("🗑️ ポートフォリオをリセット"):
        st.session_state.portfolio = pd.DataFrame(columns=st.session_state.portfolio.columns)
        st.rerun()
    
else:
    st.info("まだ銘柄が追加されていません。上記のフォームから「握る」銘柄を追加してください！")

# ====================== フッター ======================
st.caption("Made with 💪 & Streamlit | 日本株・仮想通貨対応 | 価格はYahoo Financeより取得")
