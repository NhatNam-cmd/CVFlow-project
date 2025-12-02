# test_ollama_local.py
from app.services.llm_engine import call_ollama
import os

# Giả lập môi trường (nếu chưa load .env)
os.environ["OLLAMA_BASE_URL"] = "http://localhost:11434"
os.environ["LLM_MODEL"] = "llama3"

if __name__ == "__main__":
    print("--- BẮT ĐẦU TEST OLLAMA ---")

    question = "Giải thích ngắn gọn: DevOps là gì trong 1 câu tiếng Việt?"

    print(f"Câu hỏi: {question}")
    answer = call_ollama(question)

    print("\n--- KẾT QUẢ TỪ AI ---")
    print(answer)
    print("---------------------")
