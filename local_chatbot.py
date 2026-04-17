import requests
from typing import List, Dict


OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL_NAME = "gemma3"
MAX_HISTORY = 6
REQUEST_TIMEOUT = 60


def trim_history(messages: List[Dict[str, str]], max_history: int) -> List[Dict[str, str]]:
    """
    Keep only the most recent conversation turns.
    """
    if len(messages) <= max_history:
        return messages
    return messages[-max_history:]


def build_payload(messages: List[Dict[str, str]]) -> Dict:
    """
    Build request payload for Ollama chat API.
    """
    return {
        "model": MODEL_NAME,
        "messages": messages,
        "stream": False
    }


def get_model_reply(messages: List[Dict[str, str]]) -> str:
    """
    Send the conversation to Ollama and return the assistant reply.
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
            "Could not connect to Ollama. "
            "Make sure Ollama is running and the API URL is correct."
        )
    except requests.exceptions.Timeout:
        raise RuntimeError(
            f"Request timed out after {REQUEST_TIMEOUT} seconds."
        )
    except requests.exceptions.HTTPError as e:
        raise RuntimeError(f"HTTP error: {e}")
    except requests.exceptions.RequestException as e:
        raise RuntimeError(f"Request failed: {e}")

    try:
        data = response.json()
    except ValueError:
        raise RuntimeError("The response is not valid JSON.")

    try:
        reply = data["message"]["content"].strip()
    except (KeyError, TypeError):
        raise RuntimeError(
            f"Unexpected response format: {data}"
        )

    return reply


def print_help() -> None:
    print("\nCommands:")
    print("  /help     Show available commands")
    print("  /clear    Clear conversation history")
    print("  /history  Show current conversation history")
    print("  exit      Quit the chatbot\n")


def print_history(messages: List[Dict[str, str]]) -> None:
    if not messages:
        print("\n[History is empty]\n")
        return

    print("\nConversation History:")
    for i, msg in enumerate(messages, start=1):
        role = msg.get("role", "unknown").capitalize()
        content = msg.get("content", "")
        print(f"{i}. {role}: {content}")
    print()


def main() -> None:
    messages: List[Dict[str, str]] = []

    print("Local Chatbot Demo")
    print(f"Model: {MODEL_NAME}")
    print(f"History window: {MAX_HISTORY}")
    print("Type '/help' for commands or 'exit' to quit.\n")

    while True:
        user_input = input("User: ").strip()

        if not user_input:
            continue

        if user_input.lower() == "exit":
            print("\nGoodbye!\n")
            break

        if user_input == "/help":
            print_help()
            continue

        if user_input == "/clear":
            messages.clear()
            print("\nConversation history cleared.\n")
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
            print(f"\n[Error] {e}\n")
            continue

        print(f"\nAssistant: {reply}\n")

        messages.append({
            "role": "assistant",
            "content": reply
        })

        messages = trim_history(messages, MAX_HISTORY)


if __name__ == "__main__":
    main()