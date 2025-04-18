# app.py
import streamlit as st
import ui                   # UIモジュール
import llm                  # LLMモジュール
import database             # データベースモジュール
import metrics              # 評価指標モジュール
import data                 # データモジュール
import torch
from transformers import pipeline
from config import MODEL_NAME
from huggingface_hub import HfFolder

# --- アプリケーション設定 ---
st.set_page_config(page_title="Gemma Chatbot", layout="wide")

# --- 初期化処理 ---
# NLTKデータのダウンロード（初回起動時など）
metrics.initialize_nltk()

# データベースの初期化（テーブルが存在しない場合、作成）
database.init_db()

# データベースが空ならサンプルデータを投入
data.ensure_initial_data()

# LLMモデルのロード（キャッシュを利用）
# モデルをキャッシュして再利用
#@st.cache_resource
#def load_model():
#    """LLMモデルをロードする"""
#    try:
#        device = "cuda" if torch.cuda.is_available() else "cpu"
#        st.info(f"Using device: {device}") # 使用デバイスを表示
#        pipe = pipeline(
#            "text-generation",
#            model=MODEL_NAME,
#            model_kwargs={"torch_dtype": torch.bfloat16},
#            device=device
#        )
#        st.success(f"モデル '{MODEL_NAME}' の読み込みに成功しました。")
#        return pipe
#    except Exception as e:
#        st.error(f"モデル '{MODEL_NAME}' の読み込みに失敗しました: {e}")
#        st.error("GPUメモリ不足の可能性があります。不要なプロセスを終了するか、より小さいモデルの使用を検討してください。")
#        return None

# --- Streamlit アプリケーション ---
st.image("ai-engineering_chatbot_icon.png", width=1000)
st.title("🤖 Gemma 2 Chatbot with Feedback")
st.write("Gemmaモデルを使用したチャットボットです。回答に対してフィードバックを行えます。")
st.markdown("---")

# --- サイドバー ---
st.sidebar.title("ナビゲーション")
# セッション状態を使用して選択ページを保持
if 'page' not in st.session_state:
    st.session_state.page = "チャット" # デフォルトページ


## モデル候補
model_options = [
    "モデルを選択してください",
    "google/gemma-2b", 
    "google/gemma-2-2b-jpn-it",
]

## モデル選択（セッションに保持）
#if "selected_model" not in st.session_state:
#    st.session_state.selected_model = MODEL_NAME

# 初期選択を「モデルを選択してください」にする
if "selected_model" not in st.session_state:
    st.session_state.selected_model = "モデルを選択してください"

selected_model = st.sidebar.selectbox(
    "使用するモデルを選択",
    model_options,
    index=model_options.index(st.session_state.selected_model) if st.session_state.selected_model in model_options else 0,
    on_change=lambda: st.session_state.update(selected_model=st.session_state.selected_model_selector),
    key="selected_model_selector"
)


page = st.sidebar.radio(
    "ページ選択",
    ["チャット", "履歴閲覧", "サンプルデータ管理", "レポート"],
    key="page_selector",
    index=["チャット", "履歴閲覧", "サンプルデータ管理", "レポート"].index(st.session_state.page), # 現在のページを選択状態にする
    on_change=lambda: setattr(st.session_state, 'page', st.session_state.page_selector) # 選択変更時に状態を更新
)

## モデル読み込み
# LLMモデルのロード（キャッシュを利用）
# モデルをキャッシュして再利用
@st.cache_resource
def load_model(model_name):
    """LLMモデルをロードする"""
    try:
        device = "cuda" if torch.cuda.is_available() else "cpu"
        st.info(f"Using device: {device}") # 使用デバイスを表示
        pipe = pipeline(
            "text-generation",
            model=model_name,
            model_kwargs={"torch_dtype": torch.bfloat16},
            device=device
        )
        st.success(f"モデル '{model_name}' の読み込みに成功しました。")
        return pipe
    except Exception as e:
        st.error(f"モデル '{model_name}' の読み込みに失敗しました: {e}")
        st.error("GPUメモリ不足の可能性があります。不要なプロセスを終了するか、より小さいモデルの使用を検討してください。")
        return None
pipe = load_model(st.session_state.selected_model)

# --- メインコンテンツ ---
if st.session_state.page == "チャット":
    if pipe:
        ui.display_chat_page(pipe)
    else:
        st.error("チャット機能を利用できません。モデルの読み込みに失敗しました。")
elif st.session_state.page == "履歴閲覧":
    ui.display_history_page()
elif st.session_state.page == "サンプルデータ管理":
    ui.display_data_page()
elif st.session_state.page == "レポート":
    ui.display_report_page()

# --- フッターなど（任意） ---
st.sidebar.markdown("---")
st.sidebar.info("開発者: Taiga MASUDA")
