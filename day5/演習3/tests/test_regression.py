import os
import pickle
import time
import pytest
import pandas as pd
from sklearn.metrics import accuracy_score
from sklearn.model_selection import train_test_split

# モデルとデータのパスを定義
CURRENT_MODEL_PATH = os.path.join(
    os.path.dirname(__file__), "../models/titanic_model.pkl"
)
BASELINE_MODEL_PATH = os.path.join(
    os.path.dirname(__file__), "../models/titanic_model_baseline.pkl"
)
DATA_PATH = os.path.join(os.path.dirname(__file__), "../data/Titanic.csv")


def load_test_data():
    """テスト用のデータセット（テスト分割）を読み込む"""
    df = pd.read_csv(DATA_PATH)
    X = df.drop("Survived", axis=1)
    y = df["Survived"].astype(int)
    _, X_test, _, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    return X_test, y_test


def test_baseline_model_exists():
    """ベースラインモデルが存在することを確認"""
    assert os.path.exists(
        BASELINE_MODEL_PATH
    ), f"ベースラインモデルが存在しません: {BASELINE_MODEL_PATH}"


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
    assert (
        current_time <= baseline_time
    ), f"推論時間が劣化しています: 現在={current_time:.4f}s, ベースライン={baseline_time:.4f}s"
