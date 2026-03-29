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

# ====================== データ取得関数 ======================
def get_current_price(ticker: str):
    try:
        original_ticker = ticker.strip().upper()
        if original_ticker.replace(".", "").replace("-", "").isdigit() or len(original_ticker) <= 6:
            if not original_ticker.endswith(".T"):
                ticker = original_ticker + ".T"
        else:
            ticker = original_ticker

        stock = yf.Ticker(ticker)
        
        try:
            price = stock.fast_info.get('lastPrice') or stock.fast_info.get('last_price')
            if price and price > 0:
                return round(float(price), 4)
        except:
            pass
        
        data = stock.history(period="5d")
        if not data.empty:
            return round(data['Close'].iloc[-1], 4)
        
        return None
    except Exception:
        return None

# ====================== メインUIをタブ化 ======================
tab1, tab2, tab3 = st.tabs([
    "🆕 銘柄を握る", 
    "📊 ポートフォリオ一覧", 
    "📈 握力分析"
])

# ====================== タブ1：銘柄追加 ======================
with tab1:
    st.subheader("🆕 新しい銘柄を握る")
    with st.form("add_stock_form", clear_on_submit=True):
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

# ====================== タブ2：ポートフォリオ一覧（クリックでツリー表示） ======================
with tab2:
    if not st.session_state.portfolio.empty:
        st.subheader("📊 あなたのポートフォリオ")
        
        # 合計値計算
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
        
        # 握力ランク
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
        
        # ====================== クリック対応データフレーム ======================
        event = st.dataframe(
            st.session_state.portfolio,
            use_container_width=True,
            hide_index=True,
            selection_mode="single-row",   # 行をクリックで選択（端っこタップでも反応）
            on_select="rerun",
            column_config={
                "銘柄コード": st.column_config.TextColumn(
                    "銘柄コード",
                    help="タップ/クリックで詳細ツリーを表示",
                    width="medium"
                ),
                "取得価格": st.column_config.NumberColumn("取得価格", format="¥%.2f"),
                "現在価格": st.column_config.NumberColumn("現在価格", format="¥%.2f"),
                "含み損益率(%)": st.column_config.NumberColumn("含み損益率(%)", format="%.2f%%"),
                "含み損益額": st.column_config.NumberColumn("含み損益額", format="¥%.0f"),
                "評価額": st.column_config.NumberColumn("評価額", format="¥%.0f"),
                "保有数量": st.column_config.NumberColumn("保有数量", format="%.2f"),
            }
        )

        # 選択された行があれば詳細ツリーを表示
        if event and len(event.selection.get("rows", [])) > 0:
            selected_idx = event.selection["rows"][0]
            row = st.session_state.portfolio.iloc[selected_idx]
            
            st.success(f"📌 選択中: **{row['銘柄コード']}**")
            
            # ====================== ツリー風詳細表示 ======================
            with st.expander("🔍 銘柄詳細ツリー", expanded=True):
                st.write(f"### {row['銘柄コード']} の握力詳細")
                
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("保有期間（握力）", f"{row['保有期間(日)']} 日")
                    st.metric("購入日", row['購入日'].strftime('%Y-%m-%d'))
                    st.metric("保有数量", f"{row['保有数量']:.2f}")
                
                with col2:
                    st.metric("取得価格", f"¥{row['取得価格']:,.2f}")
                    st.metric("現在価格", f"¥{row['現在価格']:,.2f}")
                    profit_color = "🟢 利益" if row['含み損益額'] >= 0 else "🔴 損失"
                    st.metric("含み損益額", f"¥{row['含み損益額']:,.0f}", delta=f"{row['含み損益率(%)']:.2f}%")
                    st.metric("評価額", f"¥{row['評価額']:,.0f}")
                
                st.divider()
                
                # 握力ランク（個別銘柄用）
                days = row['保有期間(日)']
                if days >= 365:
                    rank = "🦾 鉄の握力（伝説級）"
                elif days >= 180:
                    rank = "💪 強い握力（上級者）"
                elif days >= 90:
                    rank = "👍 普通の握力（中級者）"
                elif days >= 30:
                    rank = "👌 まだ握れてる（初心者脱却）"
                else:
                    rank = "🤏 握力弱め（要注意）"
                
                st.info(f"**この銘柄の握力ランク：{rank}**")
                
                # さらに詳細を追加したい場合はここに書く（例：簡単なチャートなど）

        # リセットボタン
        if st.button("🗑️ ポートフォリオをリセット"):
            st.session_state.portfolio = pd.DataFrame(columns=st.session_state.portfolio.columns)
            st.rerun()

    else:
        st.info("まだ銘柄が追加されていません。左のタブ「🆕 銘柄を握る」から追加してください！")

# ====================== タブ3：握力分析 ======================
with tab3:
    if not st.session_state.portfolio.empty:
        st.subheader("📈 握力分析")
        
        fig_pie = px.pie(
            st.session_state.portfolio,
            values="評価額",
            names="銘柄コード",
            title="評価額構成比",
            color_discrete_sequence=px.colors.sequential.Blues_r
        )
        st.plotly_chart(fig_pie, use_container_width=True)
        
        fig_bar = px.bar(
            st.session_state.portfolio,
            x="銘柄コード",
            y="保有期間(日)",
            title="銘柄ごとの保有期間（握力）",
            color="保有期間(日)",
            color_continuous_scale="Viridis"
        )
        st.plotly_chart(fig_bar, use_container_width=True)
        
        fig_scatter = px.scatter(
            st.session_state.portfolio,
            x="保有期間(日)",
            y="含み損益率(%)",
            size="評価額",
            color="銘柄コード",
            title="保有期間 vs 含み損益率（点の大きさ＝評価額）",
            hover_data=["銘柄コード"]
        )
        st.plotly_chart(fig_scatter, use_container_width=True)
        
    else:
        st.info("グラフは銘柄を追加すると表示されます。まずはタブ1で銘柄を握ってみてください！")

# ====================== フッター ======================
st.caption("Made with 💪 & Streamlit | 日本株・仮想通貨対応 | 価格はYahoo Financeより取得")
