# Tiger SigLIP + Qdrant 物件辨識

這是一個以 **SigLIP**、**Qdrant Local Mode** 與 **FastAPI** 建立的輕量級影像／物件辨識 API。

本專案會將 `rawpics/` 下每一個第一層資料夾視為一個類別（class）或物件 ID，使用 SigLIP 將每張參考圖片轉換為向量，經 L2 normalization 後存入 Qdrant，並透過 cosine similarity 搜尋來辨識新的圖片。


## 🚀 無需訓練模型，即可進行物件辨識。
>
> 將參考圖片放入 `rawpics/`，執行建庫程式，即可建立向量資料庫並開始辨識。
>
> **不需要自行訓練神經網路模型。**

>
> 將參考圖片放入 `rawpics/`，執行建庫程式，即可建立向量資料庫並開始辨識。


## 🚀 使用chatgpt(pro-USD100)，未使用codex、claude code、copilot等。

> https://chatgpt.com/share/6aa72439-c484-83e8-86a4-d9e791556e1d

## 系統架構

```text
參考圖片
rawpics/<class_name>/*
        |
        v
      SigLIP
        |
        v
L2-normalized 768 維向量
        |
        v
Qdrant Local Mode
        |
        v
FastAPI /api/v1/recognize
```

## 功能特色

- 使用 `google/siglip-base-patch16-224`
- 自動偵測 GPU，若無可用 GPU 則回退至 CPU
- 使用持久化的 Qdrant Local Mode
- 從 `rawpics/` 批次建立圖片向量索引
- 由資料夾名稱自動產生 class / object ID
- 支援 Top-K 候選搜尋
- 支援 `MATCH`、`LOW_SIMILARITY`、`AMBIGUOUS`、`EMPTY_INDEX` 判定
- FastAPI Swagger / OpenAPI 介面
- 提供 Windows PowerShell 輔助腳本

## 系統需求

- Python 3.11+
- Windows PowerShell（若要使用專案內附的 `.ps1` 腳本）
- 可選：NVIDIA GPU 與相容的 PyTorch / CUDA 環境

## 快速開始

### 1. 建立並啟用 Python 虛擬環境

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

如果你已經有相容的 Python 虛擬環境，也可以直接啟用既有環境。

### 2. 安裝相依套件

```powershell
.\scripts\setup.ps1
```

## Qdrant 設定

本專案使用 **Qdrant Local Mode**，透過 Python 套件 `qdrant-client` 直接在本機建立與讀取向量資料庫。

因此：

- 不需要安裝獨立的 Qdrant Server
- 不需要 Docker
- 不需要另外啟動 Qdrant 服務

安裝專案相依套件後，只要執行：

```powershell
.\scripts\build_index.ps1
```

程式就會自動建立 Qdrant Local 資料庫。

預設資料庫位置：

```text
data\qdrant\
```

預設 collection 名稱：

```text
object_images
```

可以使用以下指令確認 Qdrant 索引狀態：

```powershell
.\scripts\status.ps1
```

成功建立後，輸出會類似：

```json
{
  "collection_name": "object_images",
  "collection_exists": true,
  "vector_count": 260
}
```

如果要重新建立向量資料庫，請先停止 FastAPI，再執行：

```powershell
.\scripts\build_index.ps1
```

程式會依照 `rawpics/` 目前的圖片內容重新建立 collection。

> `rawpics/` 是參考圖片的來源；Qdrant 則保存由 SigLIP 產生的向量索引。

### 3. 加入參考圖片

建議使用「一個資料夾代表一個類別」的方式：

```text
rawpics\
  tiger\
    tiger_01.jpg
    tiger_02.jpg
  eagle\
    eagle_01.jpg
    eagle_02.jpg
```

`rawpics` 下的第一層資料夾名稱會成為 class / object ID。

資料夾名稱會正規化為小寫 snake_case。

例如：

```text
German Shepherd
```

會被正規化為：

```text
german_shepherd
```

另外也支援平面命名方式：

```text
rawpics\tiger__01.jpg
rawpics\tiger__02.jpg
```

雙底線 `__` 前面的文字會被視為 object ID。

### 4. 驗證圖片資料集

```powershell
.\scripts\validate_rawpics.ps1
```

這個指令會檢查：

- 圖片總數
- 類別數量
- 每個類別的圖片數
- 圖片格式
- 圖片尺寸
- 是否存在損壞圖片

### 5. 建立或重建 Qdrant 向量索引

請先停止 FastAPI，再執行：

```powershell
.\scripts\build_index.ps1
```

第一次執行時會下載 SigLIP 模型，模型 cache 預設存放於：

```text
models\hf_cache\
```

建立索引的流程：

```text
rawpics/
   |
   v
讀取參考圖片
   |
   v
SigLIP embedding
   |
   v
L2 normalization
   |
   v
Qdrant Cosine Vector Index
   |
   v
data/qdrant/
```

### 6. 檢查索引狀態

```powershell
.\scripts\status.ps1
```

### 7. 啟動 FastAPI

```powershell
.\scripts\start.ps1
```

Swagger UI：

```text
http://127.0.0.1:18080/docs
```

## API

目前提供：

```text
GET  /health
GET  /api/v1/index/status
POST /api/v1/recognize
```

### 辨識圖片範例

```bash
curl -X POST "http://127.0.0.1:18080/api/v1/recognize?top_k=5" \
  -H "accept: application/json" \
  -F "file=@test.jpg;type=image/jpeg"
```

回傳範例：

```json
{
  "recognized": true,
  "decision": "MATCH",
  "object_id": "tiger",
  "object_name": "tiger",
  "score": 0.94
}
```

> SigLIP 的 cosine similarity score 是「相似度」，不是機率。  
> `0.94` 不代表 94% 的分類機率。

## 設定

請先將：

```text
.env.example
```

複製成：

```text
.env
```

再依需求修改。

重要設定：

```env
SIGLIP_MODEL_ID=google/siglip-base-patch16-224
SIGLIP_DEVICE=auto
QDRANT_COLLECTION=object_images
MATCH_THRESHOLD=0.80
AMBIGUITY_MARGIN=0.03
INDEX_BATCH_SIZE=16
```

### `SIGLIP_DEVICE`

```env
SIGLIP_DEVICE=auto
```

`auto` 會在 CUDA 可用時自動使用 GPU，否則使用 CPU。

### `MATCH_THRESHOLD`

```env
MATCH_THRESHOLD=0.80
```

Top-1 similarity score 低於此門檻時，系統可以回傳：

```text
LOW_SIMILARITY
```

### `AMBIGUITY_MARGIN`

```env
AMBIGUITY_MARGIN=0.03
```

當 Top-1 與 Top-2 分數過於接近時，可判定為：

```text
AMBIGUOUS
```

`MATCH_THRESHOLD` 與 `AMBIGUITY_MARGIN` 都應依實際資料集重新校正，建議同時使用：

- 正樣本
- 未見過的新圖片
- Unknown / Negative 圖片

進行測試。

## 資料與產生檔案

Public GitHub repository 預設不追蹤以下內容：

- `.env`
- `rawpics/` 內的實際圖片資料集
- `data/qdrant/`
- `data/index_manifest.json`
- `models/hf_cache/`
- Python virtual environment

這樣可以：

- 避免公開本機設定
- 避免把大型圖片資料集提交到 Git
- 避免把 Qdrant Local DB 提交到 Git
- 避免把 Hugging Face 模型 cache 提交到 Git
- 保持 repository 精簡

`rawpics/README.txt` 會保留在 repository 中，用來說明資料夾用途。

## 目前適用範圍

這個實作最適合：

- 一般物件辨識
- 動物類別辨識
- 商品／零件類別辨識
- 已知類別的圖片相似度搜尋
- Semantic / Category Image Recognition

目前使用的是通用 SigLIP image embedding。

如果要辨識：

```text
特定人物 A
vs
其他長相相似人物
```

這屬於「人物身份辨識（identity recognition）」問題，通常應改用專門的人臉／身份 embedding model，而不是只依賴通用 SigLIP embedding。

## License

本專案採用 **MIT License**。

詳細內容請參閱 [LICENSE](LICENSE)。
