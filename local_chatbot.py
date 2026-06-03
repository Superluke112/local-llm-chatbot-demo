import requests
from typing import List, Dict


OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL_NAME = "gemma3"
MAX_HISTORY = 6
REQUEST_TIMEOUT = 60


def trim_history(messages: List[Dict[str, str]], max_history: int) -> List[Dict[str, str]]:
    """
    只保留最近的若干轮对话。
    """
    if len(messages) <= max_history:
        return messages
    return messages[-max_history:]


def build_payload(messages: List[Dict[str, str]]) -> Dict:
    """
    构建发送给 Ollama Chat API 的请求体。
    """
    return {
        "model": MODEL_NAME,
        "messages": messages,
        "stream": False
    }


def get_model_reply(messages: List[Dict[str, str]]) -> str:
    """
    将对话发送给 Ollama，并返回助手回复。
    """
    payload = build_payload(messages)

    try:
        response = requests.post(
            OLLAMA_URL,
            json=payload,
            timeout=REQUEST_TIMEOUT
        )
        response.raise_for_status()
    except requests.exceptions.ConnectionError:
        raise RuntimeError(
            "无法连接到 Ollama。"
            "请确认 Ollama 已运行，并且 API 地址正确。"
        )
    except requests.exceptions.Timeout:
        raise RuntimeError(
            f"请求在 {REQUEST_TIMEOUT} 秒后超时。"
        )
    except requests.exceptions.HTTPError as e:
        raise RuntimeError(f"HTTP 错误：{e}")
    except requests.exceptions.RequestException as e:
        raise RuntimeError(f"请求失败：{e}")

    try:
        data = response.json()
    except ValueError:
        raise RuntimeError("响应不是有效的 JSON。")

    try:
        reply = data["message"]["content"].strip()
    except (KeyError, TypeError):
        raise RuntimeError(
            f"响应格式不符合预期：{data}"
        )

    return reply


def print_help() -> None:
    print("\n命令：")
    print("  /help     显示可用命令")
    print("  /clear    清空对话历史")
    print("  /history  显示当前对话历史")
    print("  exit      退出聊天机器人\n")


def print_history(messages: List[Dict[str, str]]) -> None:
    if not messages:
        print("\n[历史记录为空]\n")
        return

    print("\n对话历史：")
    for i, msg in enumerate(messages, start=1):
        role = msg.get("role", "unknown").capitalize()
        content = msg.get("content", "")
        print(f"{i}. {role}: {content}")
    print()


def main() -> None:
    messages: List[Dict[str, str]] = []

    print("本地聊天机器人演示")
    print(f"模型：{MODEL_NAME}")
    print(f"历史窗口：{MAX_HISTORY}")
    print("输入 '/help' 查看命令，或输入 'exit' 退出。\n")

    while True:
        user_input = input("用户：").strip()

        if not user_input:
            continue

        if user_input.lower() == "exit":
            print("\n再见！\n")
            break

        if user_input == "/help":
            print_help()
            continue

        if user_input == "/clear":
            messages.clear()
            print("\n对话历史已清空。\n")
            continue

        if user_input == "/history":
            print_history(messages)
            continue

        messages.append({
            "role": "user",
            "content": user_input
        })

        messages = trim_history(messages, MAX_HISTORY)

        try:
            reply = get_model_reply(messages)
        except RuntimeError as e:
            print(f"\n[错误] {e}\n")
            continue

        print(f"\n助手：{reply}\n")

        messages.append({
            "role": "assistant",
            "content": reply
        })

        messages = trim_history(messages, MAX_HISTORY)


if __name__ == "__main__":
    main()
