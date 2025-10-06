# -*- coding: utf-8 -*-
# Qdrant FAQ Data Uploader (Native Client + Azure Embedding)
# Author: Reiyu + ChatGPT
# Version: Cleaned & Fixed for SK 1.14+

import os
import asyncio
from pathlib import Path
from typing import List
from dotenv import load_dotenv
from qdrant_client import AsyncQdrantClient, models
from semantic_kernel.connectors.ai.open_ai import AzureTextEmbedding

# ========= 載入環境變數 =========
load_dotenv()

# ========= 全域設定 =========
COLLECTION_NAME = "faq"
CHUNK_SIZE = 1000

# ========= 初始化 =========
client = AsyncQdrantClient(host="localhost", port=6333)

embeddings = AzureTextEmbedding(
    deployment_name=os.getenv("AZURE_EMBED_DEPLOYMENT"),
    endpoint=os.getenv("AZURE_ENDPOINT", ""),
    api_key=os.getenv("AZURE_API_KEY", ""),
    api_version=os.getenv("AZURE_EMBED_API_VERSION"),
)


# ========= 建立或重建 collection =========
async def setup_collection():
    collections = await client.get_collections()
    names = [c.name for c in collections.collections]
    if COLLECTION_NAME not in names:
        print(f"⚙️ 建立新的 Qdrant collection: {COLLECTION_NAME}")
        await client.recreate_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=models.VectorParams(
                size=embeddings.dimensions,  # 自動偵測 embedding 維度
                distance=models.Distance.COSINE,
            ),
        )
    else:
        print(f"✅ Collection '{COLLECTION_NAME}' 已存在，直接使用")


# ========= 文字轉向量 =========
async def embed_text(text: str) -> List[float]:
    """呼叫 Azure Embedding 並回傳向量"""
    vectors = await embeddings.generate_embeddings([text])
    return vectors[0]


# ========= 上傳資料夾 =========
async def upload_folder(folder_path: str):
    folder = Path(folder_path)
    files = list(folder.glob("**/*.txt"))
    if not files:
        print(f"❌ 資料夾 {folder_path} 沒有任何 .txt 文件")
        return

    points = []
    idx = 0

    for f in files:
        print(f"📄 處理 {f.name}")
        text = f.read_text(encoding="utf-8")
        chunks = [text[i:i + CHUNK_SIZE] for i in range(0, len(text), CHUNK_SIZE)]

        for j, chunk in enumerate(chunks):
            emb = await embed_text(chunk)
            points.append(
                models.PointStruct(
                    id=idx,
                    vector=emb,
                    payload={"file": f.name, "chunk": j, "text": chunk},
                )
            )
            idx += 1

    await client.upsert(collection_name=COLLECTION_NAME, points=points)
    print(f"✅ 已上傳 {len(points)} 筆資料至 collection: {COLLECTION_NAME}")


# ========= 搜尋測試 =========
async def search(query: str, k: int = 3):
    print(f"\n🔎 測試搜尋: {query}")
    vector = await embed_text(query)

    results = await client.query_points(
        collection_name=COLLECTION_NAME,
        query=vector,
        limit=k,
        with_payload=True,
    )

    if not results or not results.points:
        print("❌ 沒有找到相關結果")
        return

    for hit in results.points:
        payload = hit.payload or {}
        text = payload.get("text", "")[:150].replace("\n", " ")
        file = payload.get("file", "未知檔案")
        score = round(hit.score, 3)
        print(f"📘 {file} (score={score}) → {text}...")

# ========= 主程式入口 =========
async def main():
    current_dir = Path(__file__).parent
    docs_dir = current_dir / "docs"

    await setup_collection()
    await upload_folder(docs_dir)
    await search("quantum entanglement", k=3)


if __name__ == "__main__":
    asyncio.run(main())





# # -*- coding: utf-8 -*-
# # Qdrant FAQ Data Uploader for Semantic Kernel
# # Author: Reiyu + ChatGPT
# # Version: Unified with RagQdrantPlugin
# # -------------------------------------------

# import os
# import asyncio
# from pathlib import Path
# from typing import List
# from dotenv import load_dotenv
# from qdrant_client import AsyncQdrantClient, models
# from semantic_kernel.connectors.ai.open_ai import AzureTextEmbedding
# from semantic_kernel.connectors.qdrant import QdrantStore

# # ========= 載入環境變數 =========
# load_dotenv()

# # ========= 全域設定 =========
# COLLECTION_NAME = "faq"
# CHUNK_SIZE = 1000

# # ========= 初始化 =========
# client = AsyncQdrantClient(host="localhost", port=6333)
# vector_store = QdrantStore(client=client)

# embeddings = AzureTextEmbedding(
#     deployment_name=os.getenv("AZURE_DEPLOYMENT", "text-embedding-ada-002"),
#     endpoint=os.getenv("AZURE_ENDPOINT", ""),
#     api_key=os.getenv("AZURE_API_KEY", ""),
#     api_version=os.getenv("AZURE_API_VERSION", "2023-05-15"),
# )

# # ========= 建立或重建 collection =========
# async def setup_collection():
#     collections = await client.get_collections()
#     names = [c.name for c in collections.collections]
#     if COLLECTION_NAME not in names:
#         print(f"⚙️ 建立新的 Qdrant collection: {COLLECTION_NAME}")
#         await client.recreate_collection(
#             collection_name=COLLECTION_NAME,
#             vectors_config=models.VectorParams(
#                 size=embeddings.dimensions,  # 自動偵測 embedding 維度
#                 distance=models.Distance.COSINE
#             )
#         )
#     else:
#         print(f"✅ Collection '{COLLECTION_NAME}' 已存在，直接使用")


# # ========= 文字轉向量 =========
# async def embed_text(text: str) -> List[float]:
#     return await embeddings.generate_embeddings_async([text])[0]


# # ========= 上傳資料夾 =========
# async def upload_folder(folder_path: str):
#     folder = Path(folder_path)
#     files = list(folder.glob("**/*.txt"))
#     if not files:
#         print(f"❌ 資料夾 {folder_path} 沒有任何 .txt 文件")
#         return

#     points = []
#     idx = 0

#     for f in files:
#         print(f"📄 處理 {f.name}")
#         text = f.read_text(encoding="utf-8")
#         chunks = [text[i:i + CHUNK_SIZE] for i in range(0, len(text), CHUNK_SIZE)]

#         for j, chunk in enumerate(chunks):
#             emb = await embeddings.generate_embeddings_async([chunk])
#             points.append(
#                 models.PointStruct(
#                     id=idx,
#                     vector=emb[0],
#                     payload={"file": f.name, "chunk": j, "text": chunk}
#                 )
#             )
#             idx += 1

#     await client.upsert(collection_name=COLLECTION_NAME, points=points)
#     print(f"✅ 已上傳 {len(points)} 筆資料至 collection: {COLLECTION_NAME}")


# # ========= 搜尋測試 =========
# async def search(query: str, k: int = 3):
#     print(f"\n🔎 測試搜尋: {query}")
#     vector = await embeddings.generate_embeddings_async([query])
#     results = await vector_store.search(
#         collection_name=COLLECTION_NAME,
#         query=query,
#         embeddings=embeddings,
#         limit=k
#     )

#     if not results:
#         print("❌ 沒有找到相關結果")
#         return

#     for hit in results:
#         text = hit.text[:150].replace("\n", " ")
#         score = round(hit.score, 3)
#         print(f"📘 {hit.metadata.get('file', '未知檔案')} (score={score}) → {text}...")


# # ========= 主程式入口 =========
# async def main():
#     current_dir = Path(__file__).parent
#     docs_dir = current_dir / "docs"

#     await setup_collection()
#     await upload_folder(docs_dir)
#     await search("quantum entanglement", k=3)


# if __name__ == "__main__":
#     asyncio.run(main())
