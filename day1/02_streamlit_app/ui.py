# ui.py
import streamlit as st
import pandas as pd
import time
from database import save_to_db, get_chat_history, get_db_count, clear_db
from llm import generate_response
from data import create_sample_evaluation_data
from metrics import get_metrics_descriptions

# --- チャットページのUI ---
def display_chat_page(pipe):
    """チャットページのUIを表示する"""
    st.subheader("質問を入力してください")
    user_question = st.text_area("質問", key="question_input", height=100, value=st.session_state.get("current_question", ""))
    submit_button = st.button("質問を送信")

    # セッション状態の初期化（安全のため）
    if "current_question" not in st.session_state:
        st.session_state.current_question = ""
    if "current_answer" not in st.session_state:
        st.session_state.current_answer = ""
    if "response_time" not in st.session_state:
        st.session_state.response_time = 0.0
    if "feedback_given" not in st.session_state:
        st.session_state.feedback_given = False

    # 質問が送信された場合
    if submit_button and user_question:
        st.session_state.current_question = user_question
        st.session_state.current_answer = "" # 回答をリセット
        st.session_state.feedback_given = False # フィードバック状態もリセット

        with st.spinner("モデルが回答を生成中..."):
            answer, response_time = generate_response(pipe, user_question)
            st.session_state.current_answer = answer
            st.session_state.response_time = response_time
            # ここでrerunすると回答とフィードバックが一度に表示される
            st.rerun()

    # 回答が表示されるべきか判断 (質問があり、回答が生成済みで、まだフィードバックされていない)
    if st.session_state.current_question and st.session_state.current_answer:
        st.subheader("回答:")
        st.markdown(st.session_state.current_answer) # Markdownで表示
        st.info(f"応答時間: {st.session_state.response_time:.2f}秒")

        # フィードバックフォームを表示 (まだフィードバックされていない場合)
        if not st.session_state.feedback_given:
            display_feedback_form()
        else:
             # フィードバック送信済みの場合、次の質問を促すか、リセットする
             if st.button("次の質問へ"):
                  # 状態をリセット
                  st.session_state.current_question = ""
                  st.session_state.current_answer = ""
                  st.session_state.response_time = 0.0
                  st.session_state.feedback_given = False
                  st.rerun() # 画面をクリア


def display_feedback_form():
    """フィードバック入力フォームを表示する"""
    with st.form("feedback_form"):
        st.subheader("フィードバック")
        feedback_options = ["正確", "部分的に正確", "不正確"]
        # label_visibility='collapsed' でラベルを隠す
        feedback = st.radio("回答の評価", feedback_options, key="feedback_radio", label_visibility='collapsed', horizontal=True)
        correct_answer = st.text_area("より正確な回答（任意）", key="correct_answer_input", height=100)
        feedback_comment = st.text_area("コメント（任意）", key="feedback_comment_input", height=100)
        submitted = st.form_submit_button("フィードバックを送信")
        if submitted:
            # フィードバックをデータベースに保存
            is_correct = 1.0 if feedback == "正確" else (0.5 if feedback == "部分的に正確" else 0.0)
            # コメントがない場合でも '正確' などの評価はfeedbackに含まれるようにする
            combined_feedback = f"{feedback}"
            if feedback_comment:
                combined_feedback += f": {feedback_comment}"

            save_to_db(
                st.session_state.current_question,
                st.session_state.current_answer,
                combined_feedback,
                correct_answer,
                is_correct,
                st.session_state.response_time
            )
            st.session_state.feedback_given = True
            st.success("フィードバックが保存されました！")
            # フォーム送信後に状態をリセットしない方が、ユーザーは結果を確認しやすいかも
            # 必要ならここでリセットして st.rerun()
            st.rerun() # フィードバックフォームを消すために再実行

# --- 履歴閲覧ページのUI ---
def display_history_page():
    """履歴閲覧ページのUIを表示する"""
    st.subheader("チャット履歴と評価指標")
    history_df = get_chat_history()

    if history_df.empty:
        st.info("まだチャット履歴がありません。")
        return

    # タブでセクションを分ける
    tab1, tab2 = st.tabs(["履歴閲覧", "評価指標分析"])

    with tab1:
        display_history_list(history_df)

    with tab2:
        display_metrics_analysis(history_df)

def display_history_list(history_df):
    """履歴リストを表示する"""
    st.write("#### 履歴リスト")
    # 表示オプション
    filter_options = {
        "すべて表示": None,
        "正確なもののみ": 1.0,
        "部分的に正確なもののみ": 0.5,
        "不正確なもののみ": 0.0
    }
    display_option = st.radio(
        "表示フィルタ",
        options=filter_options.keys(),
        horizontal=True,
        label_visibility="collapsed" # ラベル非表示
    )

    filter_value = filter_options[display_option]
    if filter_value is not None:
        # is_correctがNaNの場合を考慮
        filtered_df = history_df[history_df["is_correct"].notna() & (history_df["is_correct"] == filter_value)]
    else:
        filtered_df = history_df

    if filtered_df.empty:
        st.info("選択した条件に一致する履歴はありません。")
        return

    # ページネーション
    items_per_page = 5
    total_items = len(filtered_df)
    total_pages = (total_items + items_per_page - 1) // items_per_page
    current_page = st.number_input('ページ', min_value=1, max_value=total_pages, value=1, step=1)

    start_idx = (current_page - 1) * items_per_page
    end_idx = start_idx + items_per_page
    paginated_df = filtered_df.iloc[start_idx:end_idx]


    for i, row in paginated_df.iterrows():
        with st.expander(f"{row['timestamp']} - Q: {row['question'][:50] if row['question'] else 'N/A'}..."):
            st.markdown(f"**Q:** {row['question']}")
            st.markdown(f"**A:** {row['answer']}")
            st.markdown(f"**Feedback:** {row['feedback']}")
            if row['correct_answer']:
                st.markdown(f"**Correct A:** {row['correct_answer']}")

            # 評価指標の表示
            st.markdown("---")
            cols = st.columns(3)
            cols[0].metric("正確性スコア", f"{row['is_correct']:.1f}")
            cols[1].metric("応答時間(秒)", f"{row['response_time']:.2f}")
            cols[2].metric("単語数", f"{row['word_count']}")

            cols = st.columns(3)
            # NaNの場合はハイフン表示
            cols[0].metric("BLEU", f"{row['bleu_score']:.4f}" if pd.notna(row['bleu_score']) else "-")
            cols[1].metric("類似度", f"{row['similarity_score']:.4f}" if pd.notna(row['similarity_score']) else "-")
            cols[2].metric("関連性", f"{row['relevance_score']:.4f}" if pd.notna(row['relevance_score']) else "-")

    st.caption(f"{total_items} 件中 {start_idx+1} - {min(end_idx, total_items)} 件を表示")


def display_metrics_analysis(history_df):
    """評価指標の分析結果を表示する"""
    st.write("#### 評価指標の分析")

    # is_correct が NaN のレコードを除外して分析
    analysis_df = history_df.dropna(subset=['is_correct'])
    if analysis_df.empty:
        st.warning("分析可能な評価データがありません。")
        return

    accuracy_labels = {1.0: '正確', 0.5: '部分的に正確', 0.0: '不正確'}
    analysis_df['正確性'] = analysis_df['is_correct'].map(accuracy_labels)

    # 正確性の分布
    st.write("##### 正確性の分布")
    accuracy_counts = analysis_df['正確性'].value_counts()
    if not accuracy_counts.empty:
        st.bar_chart(accuracy_counts)
    else:
        st.info("正確性データがありません。")

    # 応答時間と他の指標の関係
    st.write("##### 応答時間とその他の指標の関係")
    metric_options = ["bleu_score", "similarity_score", "relevance_score", "word_count"]
    # 利用可能な指標のみ選択肢に含める
    valid_metric_options = [m for m in metric_options if m in analysis_df.columns and analysis_df[m].notna().any()]

    if valid_metric_options:
        metric_option = st.selectbox(
            "比較する評価指標を選択",
            valid_metric_options,
            key="metric_select"
        )

        chart_data = analysis_df[['response_time', metric_option, '正確性']].dropna() # NaNを除外
        if not chart_data.empty:
             st.scatter_chart(
                chart_data,
                x='response_time',
                y=metric_option,
                color='正確性',
            )
        else:
            st.info(f"選択された指標 ({metric_option}) と応答時間の有効なデータがありません。")

    else:
        st.info("応答時間と比較できる指標データがありません。")


    # 全体の評価指標の統計
    st.write("##### 評価指標の統計")
    stats_cols = ['response_time', 'bleu_score', 'similarity_score', 'word_count', 'relevance_score']
    valid_stats_cols = [c for c in stats_cols if c in analysis_df.columns and analysis_df[c].notna().any()]
    if valid_stats_cols:
        metrics_stats = analysis_df[valid_stats_cols].describe()
        st.dataframe(metrics_stats)
    else:
        st.info("統計情報を計算できる評価指標データがありません。")

    # 正確性レベル別の平均スコア
    st.write("##### 正確性レベル別の平均スコア")
    if valid_stats_cols and '正確性' in analysis_df.columns:
        try:
            accuracy_groups = analysis_df.groupby('正確性')[valid_stats_cols].mean()
            st.dataframe(accuracy_groups)
        except Exception as e:
            st.warning(f"正確性別スコアの集計中にエラーが発生しました: {e}")
    else:
         st.info("正確性レベル別の平均スコアを計算できるデータがありません。")


    # カスタム評価指標：効率性スコア
    st.write("##### 効率性スコア (正確性 / (応答時間 + 0.1))")
    if 'response_time' in analysis_df.columns and analysis_df['response_time'].notna().any():
        # ゼロ除算を避けるために0.1を追加
        analysis_df['efficiency_score'] = analysis_df['is_correct'] / (analysis_df['response_time'].fillna(0) + 0.1)
        # IDカラムが存在するか確認
        if 'id' in analysis_df.columns:
            # 上位10件を表示
            top_efficiency = analysis_df.sort_values('efficiency_score', ascending=False).head(10)
            # id をインデックスにする前に存在確認
            if not top_efficiency.empty:
                st.bar_chart(top_efficiency.set_index('id')['efficiency_score'])
            else:
                st.info("効率性スコアデータがありません。")
        else:
            # IDがない場合は単純にスコアを表示
             st.bar_chart(analysis_df.sort_values('efficiency_score', ascending=False).head(10)['efficiency_score'])

    else:
        st.info("効率性スコアを計算するための応答時間データがありません。")


# --- サンプルデータ管理ページのUI ---
def display_data_page():
    """サンプルデータ管理ページのUIを表示する"""
    st.subheader("サンプル評価データの管理")
    count = get_db_count()
    st.write(f"現在のデータベースには {count} 件のレコードがあります。")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("サンプルデータを追加", key="create_samples"):
            create_sample_evaluation_data()
            st.rerun() # 件数表示を更新

    with col2:
        # 確認ステップ付きのクリアボタン
        if st.button("データベースをクリア", key="clear_db_button"):
            if clear_db(): # clear_db内で確認と実行を行う
                st.rerun() # クリア後に件数表示を更新

    # 評価指標に関する解説
    st.subheader("評価指標の説明")
    metrics_info = get_metrics_descriptions()
    for metric, description in metrics_info.items():
        with st.expander(f"{metric}"):
            st.write(description)

# --- レポートページのUI ---
def display_report_page():
    """レポートページのUIを表示する"""
    st.subheader("📄 レポート")

    st.markdown("""
    このページでは、【AIエンジニアリング実践講座2025】第1回の宿題（演習課題）の実施内容を記述しています。

    ### 🙋
    Omnicampus アカウント名：taiga10969

    名前：増田大河

    ### 📌 実施内容<概要>
    #### 1. UIの改良
    - ページのタイトル表示部分にicon（イラスト）を追加。
    - タイトルと氏名などの文字も含めて1つの画像ファイル`ai-engineering_chatbot_icon.png`として作成して読み込み・表示。
    #### 2. モデル選択の改良
    - チャットボットに使用するgemmaモデルを選択できるように改良。
    - gemmaの中には、日本語テキスト向けに微調整されたモデルも公開。
    - これらの複数のモデルの中からユーザーが使用したいモデルを選択できるように改良。
    #### 3. レポートページの追加
    - 本演習のレポートページを作成・追加。
    - アプリ上で、ページ選択でレポートページを選択することでUI上にレポートを表示させるように改良。

    ### ⚙️ 実装方法
    #### 1. UIの改良
    `app.py`に画像を表示させるプログラムを追加""")
    with st.expander("プログラムを見る"):
        st.code("""            
                   - # --- Streamlit アプリケーション ---
                   + st.image("ai-engineering_chatbot_icon.png", width=1000)
                   - st.title("🤖 Gemma 2 Chatbot with Feedback")
                   - st.write("Gemmaモデルを使用したチャットボットです。回答に対してフィードバックを行えます。")
                   - st.markdown("---")
                """, language="python")
    st.markdown("""
    #### 2. モデル選択の改良
    app.pyのサイドバー設定部分にモデル選択のプログラムを追加


    最初にモデルが選択されている状態だと、appアクセス時にモデルの読み込みが始まってしまうため、初めはモデルを選択して下さいを選択。""")
    with st.expander("プログラムを見る (モデル選択部分)"):
        st.code("""  
                    - # --- サイドバー ---
                    - st.sidebar.title("ナビゲーション")
                    - # セッション状態を使用して選択ページを保持
                    - if 'page' not in st.session_state:
                    -     st.session_state.page = "チャット" # デフォルトページ
                    - 
                    - 
                    + ## モデル候補
                    + model_options = [
                    +     "モデルを選択してください",
                    +     "google/gemma-2b", 
                    +     "google/gemma-2-2b-jpn-it",
                    + ]
                    + 
                    + ## モデル選択（セッションに保持）
                    + #if "selected_model" not in st.session_state:
                    + #    st.session_state.selected_model = MODEL_NAME
                    + 
                    + # 初期選択を「モデルを選択してください」にする
                    + if "selected_model" not in st.session_state:
                    +     st.session_state.selected_model = "モデルを選択してください"
                    + 
                    + selected_model = st.sidebar.selectbox(
                    +     "使用するモデルを選択",
                    +     model_options,
                    +     index=model_options.index(st.session_state.selected_model) if st.session_state.selected_model in model_options else 0,
                    +     on_change=lambda: st.session_state.update(selected_model=st.session_state.selected_model_selector),
                    +     key="selected_model_selector"
                    + )
                    + 
                    + page = st.sidebar.radio(
                    +     "ページ選択",
                    +     ["チャット", "履歴閲覧", "サンプルデータ管理", "レポート"],
                    +     key="page_selector",
                    +     index=["チャット", "履歴閲覧", "サンプルデータ管理", "レポート"].index(st.session_state.page), # 現在のページを選択状態にする
                    +     on_change=lambda: setattr(st.session_state, 'page', st.session_state.page_selector) # 選択変更時に状態を更新
                    + )
                """, language="python")
    st.markdown("""
    さらに、`app.py`上でモデルをloadする部分を引数でモデル名を受け取って実行できるように変更する。""")
    with st.expander("プログラムを見る (モデルロード部分)"):
        st.code("""  
                    - #LLMモデルのロード（キャッシュを利用）
                    - #モデルをキャッシュして再利用
                    - @st.cache_resource
                    - def load_model():
                    -     #LLMモデルをロードする
                    -     try:
                    -         device = "cuda" if torch.cuda.is_available() else "cpu"
                    -         st.info(f"Using device: {device}") # 使用デバイスを表示
                    -         pipe = pipeline(
                    -             "text-generation",
                    -             model=MODEL_NAME,
                    -             model_kwargs={"torch_dtype": torch.bfloat16},
                    -             device=device
                    -         )
                    -         st.success(f"モデル '{MODEL_NAME}' の読み込みに成功しました。")
                    -         return pipe
                    -     except Exception as e:
                    -         st.error(f"モデル '{MODEL_NAME}' の読み込みに失敗しました: {e}")
                    -         st.error("GPUメモリ不足の可能性があります。不要なプロセスを終了するか、より小さいモデルの使用を検討してください。")
                    -         return None
                    - pipe = load_model()

                    + ## モデル読み込み
                    + # LLMモデルのロード（キャッシュを利用）
                    + # モデルをキャッシュして再利用
                    + @st.cache_resource
                    + def load_model(model_name):
                    +     #LLMモデルをロードする
                    +     try:
                    +         device = "cuda" if torch.cuda.is_available() else "cpu"
                    +         st.info(f"Using device: {device}") # 使用デバイスを表示
                    +         pipe = pipeline(
                    +             "text-generation",
                    +             model=model_name,
                    +             model_kwargs={"torch_dtype": torch.bfloat16},
                    +             device=device
                    +         )
                    +         st.success(f"モデル '{model_name}' の読み込みに成功しました。")
                    +         return pipe
                    +     except Exception as e:
                    +         st.error(f"モデル '{model_name}' の読み込みに失敗しました: {e}")
                    +         st.error("GPUメモリ不足の可能性があります。不要なプロセスを終了するか、より小さいモデルの使用を検討してください。")
                    +         return None
                    + pipe = load_model(st.session_state.selected_model)
                """, language="python")
    st.markdown("""
    今回選択可能にしたモデルはデフォルトモデルに1つ追加した。
    - モデル: `gemma-2b` / `gemma-2-2b-jpn-it`

    #### 3. レポートページの追加
    `app.py`のサイドバー設定部分にモデル選択のプログラムを追加""")
    with st.expander("プログラムを見る"):
        st.code("""            
                    - # --- メインコンテンツ ---
                    - if st.session_state.page == "チャット":
                    -     if pipe:
                    -         ui.display_chat_page(pipe)
                    -     else:
                    -         st.error("チャット機能を利用できません。モデルの読み込みに失敗しました。")
                    - elif st.session_state.page == "履歴閲覧":
                    -     ui.display_history_page()
                    - elif st.session_state.page == "サンプルデータ管理":
                    -     ui.display_data_page()
                    + elif st.session_state.page == "レポート":
                    +     ui.display_report_page()
                """, language="python")
    st.markdown("""
    その他、レポートを表示させる部分は`ui.py`に`display_report_page()`を定義している。

    ### 🤗 モデルの変更に伴う出力結果の変化
    質問文：「桃太郎についておしえてください」
    - `gemma-2b`
    - `gemma-2-2b-jpn-it`
    ```
    #桃太郎について
    桃太郎は、日本の民間伝承であり、子供たちに親しみやすい物語です。
    ##あらすじ
    - 桃の樹と、桃太郎の誕生: 桃太郎は、ある村の物語に登場する主人公です。
    - 悪鬼の襲撃: 村を襲う悪鬼は、桃を奪い、人々を苦しめます。
    - 桃太郎の活躍: 桃太郎は、悪鬼と戦い、桃を奪い、村を救います。
    - 勝利と伝説: 桃太郎の活躍は、村の人々に希望を与え、その伝説は世代を超えて語り継がれています。
    ##特徴
    - 子供向け: 桃太郎は、子供たちに親しみやすい、単純明快な物語です。
    - 勇敢さ、正義感: 桃太郎は、勇敢で正義感あふれる主人公です。
    - 伝統的な日本の物語: 桃太郎は、日本の伝統的な物語の一例です。
    - 様々な解釈: 桃太郎は、様々な解釈で表現されており、現代においても人気があります。
    ##桃太郎の文化的な影響
    - 絵画、彫刻、文学: 桃太郎は、日本の美術や文学に大きな影響を与えました。
    - 演劇、アニメ、漫画: 桃太郎は、多くの演劇、アニメ、漫画で描かれ、現代でも広く知られています。
    - 祭り: 桃太郎節や、桃太郎祭りなど、様々な祭りが開催され、桃太郎の文化が伝わる機会があります。
    ```

    ---
    Omnicampus アカウント名：taiga10969

    名前：増田大河
    """)