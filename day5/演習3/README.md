# 📄 レポート：AIエンジニアリング実践講座2025 第5回 宿題

このレポートでは，【AIエンジニアリング実践講座2025】第5回の宿題（演習課題）の実施内容をまとめています．<br>
第5回の宿題では，講義で学んだMLOpsの概念とツールを用いて，機械学習モデルの運用・管理の
プロセスを実践的に体験した．<br>
ここでは，`モデルの推論速度と推論時間の検証`と`性能劣化を検証するテスト処理`を追加した．<br>

## 🙋 基本情報

- **Omnicampus アカウント名**：`taiga10969`  
- **名前**：増田大河

---
## 📌 実施内容（概要）

### 1. テスト関数を追加
`test_regression.py`を追加しました．

- 1. test_baseline_model_exists
```python
def test_baseline_model_exists():
    """ベースラインモデルが存在することを確認"""
    assert os.path.exists(
        BASELINE_MODEL_PATH
    ), f"ベースラインモデルが存在しません: {BASELINE_MODEL_PATH}"

```
目的: ベースラインモデルのファイルが存在するかを確認します．<br>
意義: テストを行うための前提条件のチェックです．

- 2. test_regression_accuracy
```python
def test_regression_accuracy():
    """現在モデルとベースラインモデルの精度を比較"""
    X_test, y_test = load_test_data()
    with open(CURRENT_MODEL_PATH, "rb") as f:
        current_model = pickle.load(f)
    with open(BASELINE_MODEL_PATH, "rb") as f:
        baseline_model = pickle.load(f)
    current_acc = accuracy_score(y_test, current_model.predict(X_test))
    baseline_acc = accuracy_score(y_test, baseline_model.predict(X_test))
    assert (
        current_acc >= baseline_acc
    ), f"モデルの精度が劣化しています: 現在={current_acc:.4f}, ベースライン={baseline_acc:.4f}"
```
目的: 現在のモデルの 精度（Accuracy） がベースラインモデル以上であるかを検証します．<br>
評価指標: sklearn.metrics.accuracy_score を用いた分類精度<br>
失敗条件: 現在のモデルが過去のモデルより精度が低い場合，テストは失敗します．<br>
意義: モデルの性能が劣化していないかを保証します．<br>

- 3. test_regression_inference_time
```python
def test_regression_inference_time():
    """現在モデルとベースラインモデルの推論時間を比較"""
    X_test, _ = load_test_data()
    with open(CURRENT_MODEL_PATH, "rb") as f:
        current_model = pickle.load(f)
    with open(BASELINE_MODEL_PATH, "rb") as f:
        baseline_model = pickle.load(f)
    start = time.time()
    current_model.predict(X_test)
    current_time = time.time() - start
    start = time.time()
    baseline_model.predict(X_test)
    baseline_time = time.time() - start
    # ベースラインより最大10%の遅延まで許容
    max_allowed_time = baseline_time * 1.1
    assert (
        current_time <= max_allowed_time
    ), f"推論時間が劣化しています: 現在={current_time:.4f}s, 許容時間={max_allowed_time:.4f}s"
```
目的: 現在のモデルの 推論速度（Inference Time） がベースラインモデル以上であるかを確認します．<br>
評価方法: time.time() を使って予測処理の経過時間を計測<br>
失敗条件: 現在のモデルの推論時間がベースラインより遅い場合にテスト失敗<br>
意義: モデルの処理効率が退化していないことを確認します．<br>

### 2. `test.yaml`への追加

```python
    # 追加: モデルの推論精度と推論時間を検証
    - name: Evaluate model performance
      run: |
        pytest day5/演習3/tests/test_model.py::test_model_accuracy -v
        pytest day5/演習3/tests/test_model.py::test_model_inference_time -v

    # 追加: 過去バージョンのモデルと比較して性能劣化がないか検証
    - name: Performance regression test
      run: |
        pytest day5/演習3/tests/test_regression.py -v
```