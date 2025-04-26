# 📄 レポート：AIエンジニアリング実践講座2025 第2回 宿題

このレポートでは，【AIエンジニアリング実践講座2025】第2回の宿題（演習課題）の実施内容をまとめています．<br>
第2回の宿題では，AWSからFastAPIで立てたLLMにアクセスして回答を生成しています．<br>
ここでは，FastAPIで立てるLLMとしてモデルを変更しました．<br>

## 🙋 基本情報

- **Omnicampus アカウント名**：`taiga10969`  
- **名前**：増田大河

---

## 📌 実施内容（概要）

### 1. モデルの変更
AWSで作成するChatbotをコードに特化したChatbotに変更することを目標として，コードに特化したモデルの選択をしました．<br>
選択したモデルは，elyza社が作成し，Hugging Face上に公開している"elyza/ELYZA-japanese-CodeLlama-7b-instruct"とした．<br>
Codeに特化したLlamaモデルを更に日本語に対応させたモデルである．<br>
```
MODEL_NAME = "elyza/ELYZA-japanese-CodeLlama-7b-instruct"
```
しかし，この`MODEL_NAME`の変更では，Google Colaboratory上ではリソースの問題で実行できない．（無料版使用時）<br>
そこで，量子化したモデルとしてモデルをloadすることでリソースの問題を解決し，使用したいモデルを動作させました．

### 2. モデルの量子化

量子化とは，モデル内部の重みや演算を低精度（例：8bitや4bit）で表現することで，モデルサイズを縮小し，必要な計算資源（メモリ，計算量）を削減する手法です．  
今回のケースでは，`bitsandbytes`ライブラリを利用して，**4bit量子化**を行いモデルを読み込みました．  
これにより，従来の16bitや32bitでモデルをロードする場合に比べ，大幅にメモリ消費を抑えつつ，同じモデルを使用することが可能になりました．

以下が量子化により実施した変更点の概要です．

- `AutoModelForCausalLM.from_pretrained`で，`quantization_config`を設定し4bitで読み込み．
- トークナイザーは通常通り`AutoTokenizer.from_pretrained`を使用．
- モデルとトークナイザーを明示的に`pipeline`へ渡してテキスト生成パイプラインを構築．

具体的には，以下のようなコードを使用しました．

```python
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig, pipeline
import torch

model_id = "elyza/ELYZA-japanese-CodeLlama-7b-instruct"

# トークナイザーの読み込み
tokenizer = AutoTokenizer.from_pretrained(model_id)

# 4bit量子化の設定
bnb_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_use_double_quant=True,
    bnb_4bit_quant_type="nf4",
    bnb_4bit_compute_dtype=torch.float16,
)

# モデルの読み込み
model = AutoModelForCausalLM.from_pretrained(
    model_id,
    quantization_config=bnb_config,
    device_map="auto"
)

# Pipelineの作成
pipe = pipeline(
    "text-generation",
    model=model,
    tokenizer=tokenizer
)
```

これにより，Google Colaboratory（無料枠）でも`elyza/ELYZA-japanese-CodeLlama-7b-instruct`を動作させることに成功しました．  
また，APIサーバーにはFastAPIを使用しており，Colab環境上での公開には`ngrok`を利用してインターネット経由でアクセスできるように設定しました．

### 3. 実施結果

- 量子化モデルを使用することで，推論時のVRAM消費量を大幅に削減できました．
- 無料版Google Colab環境においても，エラーなくモデルのロードとテキスト生成が可能になりました．
- 生成結果も期待通り，日本語かつコード特化型の高品質な応答を得ることができました．
