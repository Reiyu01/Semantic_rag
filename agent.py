# -*- coding: utf-8 -*-
# Semantic Kernel + Azure OpenAI + Qdrant RAG Interactive CLI (Auto Function Mode)
# Author: Reiyu + ChatGPT

import asyncio
import os
from dotenv import load_dotenv
from semantic_kernel import Kernel
from semantic_kernel.connectors.ai.open_ai import (
    AzureChatCompletion,
    AzureChatPromptExecutionSettings,
)
from semantic_kernel.connectors.ai import FunctionChoiceBehavior
from semantic_kernel.contents import ChatHistory, ChatMessageContent
from plugins.qdrant_plugin import RagQdrantPlugin

# === 載入環境變數 ===
load_dotenv()


async def main():
    print("🚀 Azure + Qdrant RAG 聊天系統啟動中...")
    print("輸入問題開始對話（輸入 exit 離開）\n")

    # === 初始化 Kernel ===
    kernel = Kernel()

    # === 設定 Azure OpenAI 聊天模型 ===
    chat_completion = AzureChatCompletion(
        service_id="azure-gpt",
        deployment_name=os.getenv("AZURE_DEPLOYMENT"),
        endpoint=os.getenv("AZURE_ENDPOINT"),
        api_key=os.getenv("AZURE_API_KEY"),
        api_version=os.getenv("AZURE_API_VERSION", "2024-02-15-preview"),
    )
    kernel.add_service(chat_completion)

    # === 掛載 Qdrant RAG Plugin ===
    rag_plugin = RagQdrantPlugin()
    kernel.add_plugin(rag_plugin, plugin_name="qdrant_faq")

    # === 初始化對話歷史 ===
    history = ChatHistory()
    print("✅ 載入完成，請輸入問題。")

    # === 互動主循環 ===
    while True:
        query = input("\nYou > ").strip()
        if query.lower() in ["exit", "quit", "bye"]:
            print("👋 再見！")
            break

        # === 加入使用者訊息 ===
        history.add_user_message(query)

        # === 呼叫模型 (Auto Function Mode) ===
        result = await chat_completion.get_chat_message_contents(
            chat_history=history,
            settings=AzureChatPromptExecutionSettings(
                function_choice_behavior=FunctionChoiceBehavior.Auto(),
            ),
            kernel=kernel,  # 👈 核心：讓模型能自動調用 plugin
        )

        # === 提取模型回覆 ===
        reply = str(result[0]).strip()

        print(f"Assistant > {reply}")

        # === 把模型回覆存進歷史 ===
        history.add_message(ChatMessageContent(role="assistant", content=reply))


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 手動中止。")
