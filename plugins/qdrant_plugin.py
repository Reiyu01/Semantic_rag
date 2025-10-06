# -*- coding: utf-8 -*-
# Qdrant Plugin (Native client version)
# Author: Reiyu + ChatGPT

import os
import anyio
from dotenv import load_dotenv
from qdrant_client import QdrantClient
from qdrant_client.http import models
from openai import AzureOpenAI
from semantic_kernel import Kernel
from semantic_kernel.functions import kernel_function
from mcp.server.stdio import stdio_server

load_dotenv()


class RagQdrantPlugin:
    def __init__(self):
        # === 初始化 Qdrant ===
        self.client = QdrantClient(host="localhost", port=6333)
        self.collection_name = os.getenv("QDRANT_COLLECTION", "faq")

        # === 初始化 Azure OpenAI Embedding ===
        self.embed_client = AzureOpenAI(
            api_key=os.getenv("AZURE_API_KEY"),
            azure_endpoint=os.getenv("AZURE_ENDPOINT"),
            api_version=os.getenv("AZURE_EMBED_API_VERSION", ),
        )
        self.embed_model = os.getenv("AZURE_EMBED_DEPLOYMENT")

    def embed(self, text: str):
        """直接呼叫 Azure OpenAI 取得向量"""
        resp = self.embed_client.embeddings.create(model=self.embed_model, input=text)
        return resp.data[0].embedding

    @kernel_function(
        name="faq_lookup",
        description="從 Qdrant 向量資料庫中查詢最相關的內容，並回傳摘要。"
    )
    async def faq_lookup(self, input: str) -> str:
        try:
            query_vector = self.embed(input)
            results = self.client.query_points(
                collection_name=self.collection_name,
                query=query_vector,
                limit=5,
                with_payload=True,
            )

            if not results or not results.points:
                return "❌ 沒找到相關結果。"

            output = []
            for i, hit in enumerate(results.points):
                payload = hit.payload or {}
                text = payload.get("text", "(無內容)")
                source = payload.get("file", "未知檔案")
                output.append(f"{i+1}. 📘 來源：{source}\n{text[:300]}...\n(score={hit.score:.3f})")

            return "\n\n".join(output)
        except Exception as e:
            return f"(RAG 查詢失敗: {e})"


# === MCP 啟動函數（可選）===
def run() -> None:
    kernel = Kernel()
    plugin = RagQdrantPlugin()
    kernel.add_plugin(plugin, plugin_name="qdrant_faq")

    server = kernel.as_mcp_server(server_name="faq_lookup")

    async def handle_stdin():
        print("✅ Qdrant FAQ MCP Server 啟動")
        async with stdio_server() as (r, w):
            await server.run(r, w, server.create_initialization_options())

    anyio.run(handle_stdin)


# # -*- coding: utf-8 -*-
# # Semantic Kernel Qdrant RAG Plugin Example (Revised)
# # Author: Reiyu + ChatGPT
# # Ref: https://learn.microsoft.com/zh-tw/semantic-kernel/concepts/vector-store-connectors/out-of-the-box-connectors/qdrant-connector

# import os
# import anyio
# from dotenv import load_dotenv
# from mcp.server.stdio import stdio_server
# from semantic_kernel import Kernel
# from semantic_kernel.functions import kernel_function
# from semantic_kernel.connectors.qdrant import QdrantStore
# from qdrant_client import AsyncQdrantClient
# from semantic_kernel.connectors.ai.open_ai import AzureTextEmbedding


# # Load environment variables
# load_dotenv()


# class RagQdrantPlugin:
#     """
#     Qdrant + Azure Embedding 的簡易 RAG Plugin，
#     可用於查詢 FAQ 類知識庫。
#     """

#     def __init__(self):
#         # === Qdrant 設定 ===
#         self.collection_name = "faq"
#         self.client = AsyncQdrantClient(host="localhost", port=6333)
#         self.vector_store = QdrantStore(client=self.client)

#         # === Azure OpenAI Embedding 設定 ===
#         self.embeddings = AzureTextEmbedding(
#             deployment_name=os.getenv("AZURE_DEPLOYMENT", "text-embedding-ada-002"),
#             endpoint=os.getenv("AZURE_ENDPOINT", ""),
#             api_key=os.getenv("AZURE_API_KEY", ""),
#             api_version=os.getenv("AZURE_API_VERSION", "2023-05-15"),
#         )

#     @kernel_function(
#         name="faq_lookup",
#         description="根據問題向量比對常見問題資料庫並回傳最相關的回答"
#     )
#     async def faq_lookup(self, question: str) -> str:
#         """
#         用戶輸入問題後，會執行向量比對並輸出最相似的 FAQ。
#         """
#         try:
#             # 查詢相似文件（k=5）
#             results = await self.vector_store.search(
#                 collection_name=self.collection_name,
#                 query=question,
#                 embeddings=self.embeddings,
#                 limit=5,
#             )

#             if not results:
#                 return "❌ 沒有找到相關的常見問題。"

#             output_lines = []
#             for idx, r in enumerate(results):
#                 meta = r.metadata or {}
#                 q = meta.get("question", "未知問題")
#                 a = r.text or "（無回答內容）"
#                 score = round(r.score, 3) if hasattr(r, "score") else "N/A"
#                 output_lines.append(f"{idx+1}. ❓ {q}\n📘 {a}\n🔹 相似度: {score}")

#             return "\n\n".join(output_lines)

#         except Exception as e:
#             return f"⚠️ RAG 查詢發生錯誤: {type(e).__name__}: {e}"


# def run() -> None:
#     """
#     啟動為 MCP Plugin Server，可供 Semantic Kernel 或外部代理呼叫。
#     """
#     kernel = Kernel()
#     plugin = RagQdrantPlugin()
#     kernel.add_plugin(plugin, plugin_name="qdrant_faq")

#     async def handle_stdin():
#         print("✅ Qdrant FAQ MCP Server 正在啟動...")
#         async with stdio_server() as (read_stream, write_stream):
#             await kernel.run_as_mcp_server(
#                 read_stream,
#                 write_stream,
#                 server_name="qdrant_faq_server",
#             )

#     anyio.run(handle_stdin)


# if __name__ == "__main__":
#     run()









# # plugins/qdrant_faq_plugin.py

# import anyio
# from mcp.server.stdio import stdio_server
# from semantic_kernel import Kernel
# from semantic_kernel.functions import kernel_function
# from qdrant_client import QdrantClient
# from langchain_openai import AzureOpenAIEmbeddings
# from langchain_qdrant import QdrantVectorStore
# import os
# from dotenv import load_dotenv

# # Load environment variables from .env if present
# load_dotenv()


# class RagQdrantPlugin:
#     def __init__(self):
#         # Qdrant 設定
#         qdrant_url = "http://localhost:6333"
#         collection_name = "faq"

#         # Azure OpenAI 的參數（從環境變數讀取）
#         api_key = os.environ.get("AZURE_API_KEY", "")
#         azure_endpoint = os.environ.get("AZURE_ENDPOINT", "")
#         azure_deployment = os.environ.get("AZURE_DEPLOYMENT", "text-embedding-ada-002")
#         api_version = os.environ.get("AZURE_API_VERSION", "2023-05-15")

#         # 初始化 Qdrant + Azure Embeddings
#         self.client = QdrantClient(url=qdrant_url)
#         self.embeddings = AzureOpenAIEmbeddings(
#             azure_endpoint=azure_endpoint,
#             deployment=azure_deployment,
#             api_version=api_version,
#             api_key=api_key,
#         )
#         self.vector_db = QdrantVectorStore(
#             client=self.client,
#             collection_name=collection_name,
#             embedding=self.embeddings,
#         )

#     @kernel_function(
#         name="faq_lookup",
#         description="根據問題向量比對常見問題資料庫並回傳最相關的回答"
#     )
#     async def faq_lookup(self, input: str) -> str:
#         try:
#             # 包成非同步避免阻塞
#             results = await anyio.to_thread.run_sync(
#                 lambda: self.vector_db.similarity_search(input, k=5)
#             )
#             if not results:
#                 return "(❌ 沒有找到相關的常見問題)"

#             output = []
#             for idx, doc in enumerate(results):
#                 meta = doc.metadata or {}
#                 question = meta.get("question", "未知問題")
#                 output.append(f"{idx+1}. ❓ {question}\n📘 {doc.page_content}")

#             return "\n\n".join(output)
#         except Exception as e:
#             return f"(RAG 搜尋失敗: {e})"


# def run() -> None:
#     kernel = Kernel()
#     faq_plugin = QdrantFAQ()
#     kernel.add_function("faq", faq_plugin.faq_lookup)

#     server = kernel.as_mcp_server(server_name="faq_lookup")

#     async def handle_stdin():
#         print("✅ Qdrant FAQ MCP Server 正在啟動...")
#         async with stdio_server() as (read_stream, write_stream):
#             await server.run(read_stream, write_stream, server.create_initialization_options())

#     anyio.run(handle_stdin)


# if __name__ == "__main__":
#     run()
