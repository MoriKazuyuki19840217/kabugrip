import streamlit as st
import pandas as pd
import yfinance as yf
from datetime import datetime, date

st.set_page_config(page_title="株の握力測定", layout="centered")
st.title("💪 株の握力測定ソフト")
st.markdown("**保有期間をカレンダーで簡単入力**して、日本株・仮想通貨・インデックス全部の投資握力を診断！ 📱")

# セッションでデータ保持
if "portfolio" not in st.session_state:
    st.session_state.portfolio = pd.DataFrame(columns=["銘柄コード", "購入日", "保有期間(日)", "現在価格", "取得価格", "含み損率(%)"])

# ====================== 入力フォーム（仮想通貨・インデックス対応） ======================
with st.form("add_stock"):
    col1, col2 = st.columns([2, 1])
    
    ticker = col1.text_input(
        "銘柄コード",
        value="7203.T",
        help="日本株: 7203.T / 仮想通貨: BTC-USD / 指数: ^GSPC"
    ).strip().upper()
    
    purchase_date = col2.date_input("購入日", value=date(2024, 1, 1), min_value=date(2010, 1, 1))
    
    submitted = st.form_submit_button("✅ この銘柄を追加")

    # クイック追加ボタン
    st.markdown("**クイック追加（ワンタップ）**")
    qcol1, qcol2, qcol3, qcol4 = st.columns(4)
    if qcol1.button("🇺🇸 S&P500", use_container_width=True):
        ticker = "^GSPC"
        submitted = True
    if qcol2.button("₿ BTC", use_container_width=True):
        ticker = "BTC-USD"
        submitted = True
    if qcol3.button("Ξ ETH", use_container_width=True):
        ticker = "ETH-USD"
        submitted = True
    if qcol4.button("📈 NASDAQ", use_container_width=True):
        ticker = "^IXIC"
        submitted = True

# ====================== 銘柄追加処理 ======================
if submitted and ticker:
    try:
        stock = yf.Ticker(ticker)
        data = stock.history(period="5d")
        current_price = round(data['Close'].iloc[-1], 2) if not data.empty else None
        
        holding_days = (datetime.now().date() - purchase_date).days
        
        # 仮の取得価格（実際は後で手入力拡張可）
        assumed_buy_price = round(current_price * 0.95, 2) if current_price else 1000.0
        
        new_row = pd.DataFrame([{
            "銘柄コード": ticker,
            "購入日": purchase_date,
            "保有期間(日)": holding_days,
            "現在価格": current_price,
            "取得価格": assumed_buy_price,
            "含み損率(%)": round((current_price - assumed_buy_price) / assumed_buy_price * 100, 1) if current_price else None
        }])
        
        st.session_state.portfolio = pd.concat([st.session_state.portfolio, new_row], ignore_index=True)
        st.success(f"✅ {ticker} を追加！ 保有 {holding_days}日")
    except Exception as e:
        st.error(f"取得失敗: {ticker} が正しいか確認してね（例: BTC-USD / ^GSPC）")

# ====================== 保有株一覧 ======================
if not st.session_state.portfolio.empty:
    st.subheader("📋 あなたのポートフォリオ")
    st.dataframe(st.session_state.portfolio, use_container_width=True, hide_index=True)
    
    if st.button("🗑 最後の銘柄を削除"):
        st.session_state.portfolio = st.session_state.portfolio.iloc[:-1]
        st.rerun()

# ====================== 握力計算 ======================
if not st.session_state.portfolio.empty:
    df = st.session_state.portfolio.copy()
    
    df["握力貢献"] = (df["保有期間(日)"] / 30) + ((100 - df["含み損率(%)"].fillna(0).abs()) / 4)
    total_score = df["握力貢献"].sum() + (len(df) * 12)
    
    grip = max(10, min(100, int(total_score)))
    
    st.subheader("📊 あなたの総合株握力")
    st.progress(grip / 100.0)
    st.metric(label="握力", value=f"{grip} kg 💪")
    
    if grip >= 80:
        st.success("最強の握力！ グローバル分散の達人レベルです🔥")
    elif grip >= 60:
        st.info("なかなか強い握力。仮想通貨やS&P500も混ぜてさらに鍛えよう！")
    elif grip >= 40:
        st.warning("平均以上。保有期間を伸ばすと握力がグッと上がります")
    else:
        st.error("握力トレーニング中… 小さく始めて長期保有を習慣に！")
    
    # 保有期間グラフ
    st.bar_chart(df.set_index("銘柄コード")["保有期間(日)"], color="#00ccff")
else:
    st.info("まだ何も追加されていません。上のフォームで日本株・BTC・S&P500などを追加してみて！")

st.caption("※ yfinanceの価格は参考値です。仮想通貨・指数も対応済み。")
