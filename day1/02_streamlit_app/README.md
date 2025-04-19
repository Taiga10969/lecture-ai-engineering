# 📄 レポート：AIエンジニアリング実践講座2025 第1回 宿題

このレポートでは、【AIエンジニアリング実践講座2025】第1回の宿題（演習課題）の実施内容をまとめています。

## 🙋 基本情報

- **Omnicampus アカウント名**：`taiga10969`  
- **名前**：増田大河

---

## 📌 実施内容（概要）

### 1. UIの改良
- タイトル表示にイラストアイコンを追加。
- `ai-engineering_chatbot_icon.png` を作成し、タイトル・氏名情報とともに一枚の画像として表示。

### 2. モデル選択の改良
- Gemmaモデル（`gemma-2b`, `gemma-2-2b-jpn-it`）をUI上で選択可能に。
- モデル未選択時はロードされないように初期値を「モデルを選択してください」に設定。

### 3. レポートページの追加
- アプリに「レポート」ページを追加し、実装内容をStreamlit上に表示可能に。
  ※レポートの内容はこのREADMEの内容と同様．



## ⚙️ 実装方法

### 1. UIの改良
`app.py` に以下のように画像表示処理を追加：

```python
st.image("ai-engineering_chatbot_icon.png", width=1000)
```



### 2. モデル選択の改良

#### サイドバーでのモデル選択処理（`app.py`）

```python
model_options = [
    "モデルを選択してください",
    "google/gemma-2b", 
    "google/gemma-2-2b-jpn-it",
]

if "selected_model" not in st.session_state:
    st.session_state.selected_model = "モデルを選択してください"

selected_model = st.sidebar.selectbox(
    "使用するモデルを選択",
    model_options,
    index=model_options.index(st.session_state.selected_model) if st.session_state.selected_model in model_options else 0,
    on_change=lambda: st.session_state.update(selected_model=st.session_state.selected_model_selector),
    key="selected_model_selector"
)
```

#### モデル読み込み関数（`app.py`）

```python
@st.cache_resource
def load_model(model_name):
    try:
        device = "cuda" if torch.cuda.is_available() else "cpu"
        st.info(f"Using device: {device}")
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
        return None

pipe = load_model(st.session_state.selected_model)
```

#### モデルによる入力形式の分岐（`llm.py`）

```python
def generate_response(pipe, user_question):
    if pipe is None:
        return "モデルがロードされていないため、回答を生成できません。", 0

    try:
        if st.session_state.selected_model == "google/gemma-2b":
            inputs = user_question
        elif st.session_state.selected_model == "google/gemma-2-2b-jpn-it":
            inputs = [{"role": "user", "content": user_question}]
        
        outputs = pipe(inputs, max_new_tokens=512, do_sample=True, temperature=0.7, top_p=0.9)
        # 出力処理はモデル仕様に応じて調整
        ...
```



### 3. レポートページの追加

#### `app.py` 内でのページ分岐追加：

```python
elif st.session_state.page == "レポート":
    ui.display_report_page()
```

#### `ui.py` 内に `display_report_page()` を定義し、本文表示を実装。



## 🤗 モデル出力結果の比較

### 質問：桃太郎についておしえてください

#### `gemma-2b` の出力（繰り返し文）：

```
桃太郎は、桃を100個も食べることができた。（以下繰り返し）
```

#### `gemma-2-2b-jpn-it` の出力（構造化された内容）：

```
#桃太郎について
桃太郎は、日本の民間伝承であり、子供たちに親しみやすい物語です。

##あらすじ
- 桃の樹と、桃太郎の誕生
- 悪鬼の襲撃
- 桃太郎の活躍
- 勝利と伝説

##特徴
- 子供向け、勇敢さ、正義感、伝統
- 現代でも人気

##文化的な影響
- 絵画、アニメ、祭りなどに派生
```

### 考察
- `gemma-2-2b-jpn-it` モデルは日本語に特化しているため、構造化された正確な回答が得られる。
- `gemma-2b` モデルは汎用性はあるが、日本語対応の精度に劣るため繰り返し文などが出力されやすい。


## 📎 補足

- 本レポートページは Streamlit アプリ内に追加されており、UIから選択して確認可能です。
- モデル追加や拡張も今後簡単に行える設計になっています。

---

## 実行結果
実行したときのスクリーンショットを添付します。
![](https://raw.githubusercontent.com/Taiga10969/lecture-ai-engineering/refs/heads/master/day1/02_streamlit_app/results_image/%E3%82%B9%E3%82%AF%E3%83%AA%E3%83%BC%E3%83%B3%E3%82%B7%E3%83%A7%E3%83%83%E3%83%88%202025-04-19%200.58.02.png)
![](https://raw.githubusercontent.com/Taiga10969/lecture-ai-engineering/refs/heads/master/day1/02_streamlit_app/results_image/%E3%82%B9%E3%82%AF%E3%83%AA%E3%83%BC%E3%83%B3%E3%82%B7%E3%83%A7%E3%83%83%E3%83%88%202025-04-19%201.23.17.png)
![](https://raw.githubusercontent.com/Taiga10969/lecture-ai-engineering/refs/heads/master/day1/02_streamlit_app/results_image/%E3%82%B9%E3%82%AF%E3%83%AA%E3%83%BC%E3%83%B3%E3%82%B7%E3%83%A7%E3%83%83%E3%83%88%202025-04-19%201.23.58.png)

Omnicampus アカウント名：`taiga10969`  
名前：増田大河
