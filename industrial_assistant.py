import json
import re
from collections import Counter
from pathlib import Path
from typing import Dict, List, Tuple

from local_chatbot import (
    MAX_HISTORY,
    MODEL_NAME,
    OLLAMA_URL,
    get_model_reply,
    print_history,
    trim_history,
)


ERROR_CODE_PATTERN = r"E\d{3}"
BASE_DIR = Path(__file__).resolve().parent
DEFAULT_TOP_K = 3


def _resolve_project_path(file_path: str) -> Path:
    """
    将相对路径解析为基于脚本所在目录的绝对路径；绝对路径原样返回。
    作用：让脚本无论从哪个工作目录启动，都能正确找到 fake_sop.txt
    和 sample_logs.txt 等数据文件。
    """
    path = Path(file_path)
    if path.is_absolute():
        return path
    return BASE_DIR / path


def _extract_error_codes(text: str) -> List[str]:
    """
    从任意文本中按正则 r"E\\d{3}" 提取错误码列表（如 ["E104", "E205"]）。
    统一转大写后匹配，保留重复以便后续做频次统计。
    """
    return re.findall(ERROR_CODE_PATTERN, text.upper())


def _keyword_tokens(text: str) -> set[str]:
    """
    将文本切分为关键词集合，用于检索时的关键词匹配评分。
    - 只保留字母/数字 token
    - 去除长度 < 2 的短词
    - 去除错误码本身（避免与错误码加分重复计算）
    """
    tokens = re.findall(r"[A-Za-z0-9]+", text.lower())
    return {
        token
        for token in tokens
        if len(token) >= 2 and not re.fullmatch(r"e\d{3}", token)
    }


def load_knowledge_base(file_path: str = "fake_sop.txt") -> list[str]:
    """
    加载由空行分隔的 SOP 条目，并以列表形式返回。
    - 自动统一 Windows 换行符（\\r\\n -> \\n）
    - 按空行切分
    - 去除空白块
    """
    path = _resolve_project_path(file_path)
    text = path.read_text(encoding="utf-8")
    normalized = text.replace("\r\n", "\n")
    return [
        block.strip()
        for block in re.split(r"\n\s*\n", normalized)
        if block.strip()
    ]


def retrieve_relevant_docs(
    query: str,
    docs: list[str],
    top_k: int = DEFAULT_TOP_K,
) -> list[str]:
    """
    最小化关键词检索（不使用向量检索 / embedding / 向量数据库）：
    - 错误码命中：+100 × 出现次数（强权重）
    - 关键词命中：+5 × 重叠 token 数（弱权重）
    按 (-得分, 原始顺序) 排序，只返回得分 > 0 的前 top_k 条。
    """
    query_code_counts = Counter(_extract_error_codes(query))
    query_tokens = _keyword_tokens(query)
    scored_docs: List[Tuple[int, int, str]] = []

    for index, doc in enumerate(docs):
        doc_codes = set(_extract_error_codes(doc))
        doc_tokens = _keyword_tokens(doc)

        score = 0
        for code, count in query_code_counts.items():
            if code in doc_codes:
                score += 100 * count

        score += 5 * len(query_tokens & doc_tokens)
        scored_docs.append((score, index, doc))

    scored_docs.sort(key=lambda item: (-item[0], item[1]))
    positive_matches = [doc for score, _, doc in scored_docs if score > 0]
    return positive_matches[:top_k]


def analyze_error_logs(text: str) -> dict:
    """
    确定性 Python 工具：从文本中提取错误码并统计频次。
    不依赖 LLM，结果可复现。返回字段：
      - total_errors:  错误码总出现次数
      - error_counts:  {错误码: 次数}（按错误码字典序）
      - most_common:   [(错误码, 次数), ...]（按次数降序）
    """
    codes = _extract_error_codes(text)
    counts = Counter(codes)
    most_common = sorted(counts.items(), key=lambda item: (-item[1], item[0]))

    return {
        "total_errors": len(codes),
        "error_counts": dict(sorted(counts.items())),
        "most_common": most_common,
    }


def detect_task_type(user_input: str) -> str:
    """
    简单任务路由（agent 风格的最小实现）：
    - 多行 且 错误码 >= 2 个  → "log_analysis"
    - 含错误码（单行或仅 1 个）→ "fault_question"
    - 否则                    → "general_question"
    """
    codes = _extract_error_codes(user_input)
    non_empty_lines = [
        line for line in user_input.splitlines()
        if line.strip()
    ]

    if len(non_empty_lines) > 1 and len(codes) >= 2:
        return "log_analysis"
    if codes:
        return "fault_question"
    return "general_question"


def build_fault_prompt(
    user_input: str,
    retrieved_docs: list[str],
    log_analysis: dict | None = None,
) -> str:
    """
    构造最终送给本地 LLM 的中文提示词。包含：
      1. 角色定义
      2. 五段式中文标题硬约束
      3. 四条可靠性约束（仅基于证据 / 不编造根因 / 证据不足明说 / 仅作初步建议）
      4. 用户原始输入
      5. 检索到的 SOP 条目
      6. 日志统计 JSON（如有，否则填占位文字）
    使用 f-string 三引号字符串，{var} 仅做一次插值；log_context 中
    即使包含 { }，也只是普通字符，不会被再次按 f-string 解析。
    """
    sop_context = "\n\n---\n\n".join(retrieved_docs)
    if not sop_context:
        sop_context = "未检索到相关 SOP 条目。"

    if log_analysis is None:
        log_context = "无日志统计。"
    else:
        log_context = json.dumps(log_analysis, ensure_ascii=False, indent=2)

    return f"""你是 Industrial Fault Analysis Assistant，一个工业故障初步分析助手。

请用中文回答，并且必须严格使用下面 5 个编号标题，标题文字和顺序必须完全一致：
1. 问题概述
2. 相关错误码
3. 可能原因
4. 建议排查步骤
5. 需要人工确认的部分

可靠性要求：
- 只能基于下面检索到的 SOP 条目和日志分析作答。（Answer ONLY based on the retrieved SOP entries and log analysis below.）
- 不要编造缺少证据支持的根因。（DO NOT invent unsupported root causes.）
- 如果证据不足，必须明确说明还需要进一步工程验证。（If evidence is insufficient, explicitly say further engineering validation is needed.）
- 将输出定位为初步排查建议，而不是最终诊断结论。（Frame the output as preliminary troubleshooting suggestions, not a final diagnosis.）

用户输入：
{user_input}

检索到的 SOP 条目：
{sop_context}

日志统计：
{log_context}
"""


def _build_prompt_for_input(
    user_input: str,
    docs: list[str],
    forced_log_analysis: dict | None = None,
) -> tuple[str, str, list[str], dict | None]:
    """
    内部协调函数：把 "任务检测 → 日志统计 → SOP 检索 → 构造 prompt" 串成一步。
    - 普通输入：自动调用 detect_task_type 决定是否做日志分析。
    - /sample_logs 命令：通过 forced_log_analysis 跳过自动判断，
      直接复用外部已经统计好的结果。
    返回 (prompt, task_type, retrieved_docs, log_analysis)。
    """
    task_type = detect_task_type(user_input)
    log_analysis = forced_log_analysis

    if task_type == "log_analysis" and log_analysis is None:
        log_analysis = analyze_error_logs(user_input)

    retrieved_docs = retrieve_relevant_docs(user_input, docs)
    prompt = build_fault_prompt(user_input, retrieved_docs, log_analysis)
    return prompt, task_type, retrieved_docs, log_analysis


def _print_industrial_help() -> None:
    """打印工业故障分析助手专属的命令清单和输入示例。"""
    print("\n命令：")
    print("  /help         显示可用命令")
    print("  /clear        清空对话历史")
    print("  /history      显示当前对话历史")
    print("  /sample_logs  分析 sample_logs.txt 并生成中文总结")
    print("  exit          退出助手\n")
    print("示例：")
    print("  E104 怎么排查？")
    print("  粘贴多行日志后，在空白行按 Enter 开始分析。\n")


def _looks_like_log_line(text: str) -> bool:
    """
    判断一行输入是否看起来像日志行：
    包含错误码 且 （包含 "ERROR" 或以日期前缀 YYYY-MM-DD 开头）。
    用于决定是否进入多行粘贴模式。
    """
    upper_text = text.upper()
    has_code = bool(_extract_error_codes(upper_text))
    has_log_marker = "ERROR" in upper_text or bool(
        re.match(r"\d{4}-\d{2}-\d{2}", text)
    )
    return has_code and has_log_marker


def _read_user_input() -> str:
    """
    读取一次用户输入：
    - 若第一行不像日志：直接返回单行字符串。
    - 若第一行像日志：提示继续粘贴后续日志行，遇到空行回车结束。
    """
    first_line = input("用户：").rstrip()
    if not first_line.strip():
        return ""

    if not _looks_like_log_line(first_line):
        return first_line.strip()

    print("请继续粘贴日志行，在空白行按 Enter 开始分析。")
    lines = [first_line]

    while True:
        try:
            next_line = input("... ").rstrip()
        except EOFError:
            break

        if not next_line.strip():
            break
        lines.append(next_line)

    return "\n".join(lines).strip()


def _send_prompt(prompt: str, messages: List[Dict[str, str]]) -> tuple[str, List[Dict[str, str]]]:
    """
    将构造好的 prompt 追加到对话历史，调用本地 Ollama，打印助手回复，
    再把回复追加回历史。每次 append 后都用 trim_history 维持滑动窗口。
    返回 (reply, messages)。
    """
    messages.append({
        "role": "user",
        "content": prompt,
    })
    messages = trim_history(messages, MAX_HISTORY)

    reply = get_model_reply(messages)
    print(f"\n助手：{reply}\n")

    messages.append({
        "role": "assistant",
        "content": reply,
    })
    messages = trim_history(messages, MAX_HISTORY)
    return reply, messages


def _print_log_statistics(log_analysis: dict) -> None:
    """在调用 LLM 之前，先把 Python 端的错误码统计结果打印出来，方便演示 “确定性工具调用”。"""
    print("\n日志统计：")
    print(f"  错误码总数：{log_analysis['total_errors']}")
    print(f"  计数：{log_analysis['error_counts']}")
    print(f"  最高频：{log_analysis['most_common']}\n")


def main() -> None:
    """
    工业故障分析助手主入口：
    1. 启动时加载 fake_sop.txt（失败则直接退出）。
    2. 进入终端循环，依次处理命令（/help、/clear、/history、/sample_logs、exit）和普通输入。
    3. 普通输入：任务路由 → SOP 检索 →（必要时）日志统计 → 构造 prompt → 调用 LLM。
    """
    try:
        docs = load_knowledge_base()
    except OSError as exc:
        print(f"\n[错误] 无法加载 fake_sop.txt：{exc}\n")
        return

    messages: List[Dict[str, str]] = []

    print("工业故障分析助手")
    print(f"模型：{MODEL_NAME}")
    print(f"Ollama API：{OLLAMA_URL}")
    print(f"已加载 SOP 条目数：{len(docs)}")
    print(f"历史窗口：{MAX_HISTORY}")
    print("输入 '/help' 查看命令，或输入 'exit' 退出。\n")

    while True:
        try:
            user_input = _read_user_input()
        except EOFError:
            print("\n再见！\n")
            break

        if not user_input:
            continue

        command = user_input.lower()

        if command == "exit":
            print("\n再见！\n")
            break

        if command == "/help":
            _print_industrial_help()
            continue

        if command == "/clear":
            messages.clear()
            print("\n对话历史已清空。\n")
            continue

        if command == "/history":
            print_history(messages)
            continue

        if command == "/sample_logs":
            try:
                sample_text = _resolve_project_path("sample_logs.txt").read_text(
                    encoding="utf-8"
                )
            except OSError as exc:
                print(f"\n[错误] 无法加载 sample_logs.txt：{exc}\n")
                continue

            log_analysis = analyze_error_logs(sample_text)
            _print_log_statistics(log_analysis)
            prompt, _, _, _ = _build_prompt_for_input(
                sample_text,
                docs,
                forced_log_analysis=log_analysis,
            )
        else:
            prompt, task_type, _, log_analysis = _build_prompt_for_input(
                user_input,
                docs,
            )
            if task_type == "log_analysis" and log_analysis is not None:
                _print_log_statistics(log_analysis)

        try:
            _, messages = _send_prompt(prompt, messages)
        except RuntimeError as exc:
            print(f"\n[错误] {exc}\n")
            continue


if __name__ == "__main__":
    main()
