# 本地 LLM 聊天机器人演示
# Local LLM chatbot demo

## English Version

This repository keeps the original terminal chatbot in `local_chatbot.py` and adds a small prototype called **Industrial Fault Analysis Assistant** in `industrial_assistant.py`.

### What This Prototype Does

The industrial assistant demonstrates a minimal RAG-style workflow for fault analysis:

- Loads fake SOP and failure-case entries from `fake_sop.txt`.
- Retrieves relevant SOP entries with simple error-code and keyword matching.
- Uses a deterministic Python function to count error codes in pasted logs.
- Sends the retrieved evidence and log statistics to a local Ollama model for a structured Chinese troubleshooting summary.

Please note: this is a prototype, **not** a production diagnostic system. It uses fake SOP data only and a minimal keyword retriever. The local LLM is mainly used for structured summary generation, not for authoritative diagnosis.

### Difference From `local_chatbot.py`

`local_chatbot.py` is a general-purpose local terminal chatbot. It calls the Ollama Chat API, maintains conversation history, trims history with a sliding window, and supports `/help`, `/clear`, `/history`, and `exit`.

`industrial_assistant.py` reuses those base capabilities and adds industrial fault-analysis behavior:

- Detects fault questions such as `E104 怎么排查？`.
- Detects multi-line log input and counts error codes through `analyze_error_logs()`.
- Retrieves related SOP entries from `fake_sop.txt` before calling the model.
- Builds a fixed five-section Chinese troubleshooting prompt.
- Provides `/sample_logs` for a built-in log-analysis demo.

The original chatbot is still kept and should continue to work normally.

### Requirements

- Python 3.10 or newer
- `requests`
- Ollama running locally
- Ollama model `gemma3` pulled and available

Install the only extra Python dependency:

```bash
pip install requests
```

Make sure the Ollama model is available:

```bash
ollama pull gemma3
```

The project reuses this Ollama configuration:

```python
OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL_NAME = "gemma3"
```

### How To Run

Run the original chatbot:

```bash
python local_chatbot.py
```

Run the industrial fault assistant:

```bash
python industrial_assistant.py
```

### Test Fault-Question Mode

Start the industrial assistant and enter:

```text
E104 怎么排查？
```

Expected behavior: the program retrieves the E104 SOP entry and asks the local LLM to answer in Chinese with this fixed five-section structure:

```text
1. 问题概述
2. 相关错误码
3. 可能原因
4. 建议排查步骤
5. 需要人工确认的部分
```

### Test Log-Analysis Mode

Paste multiple log lines, then press Enter on a blank line to start analysis:

```text
2026-06-01 10:01:22 ERROR E104 Motor temperature high
2026-06-01 10:03:11 ERROR E104 Retry failed
2026-06-01 10:04:05 ERROR E205 Communication timeout
2026-06-01 10:05:30 ERROR E104 Thermal warning
```

Expected behavior: the Python logic detects log-analysis mode, counts error codes, identifies E104 as the most frequent code, retrieves the E104 and E205 SOP entries, and asks the LLM to generate a structured Chinese summary and troubleshooting plan.

You can also enter:

```text
/sample_logs
```

This command loads `sample_logs.txt`, runs deterministic error-code statistics, retrieves related SOP entries, and generates a structured Chinese summary.

### Limitations

- This is a prototype and is not suitable for real industrial diagnostics.
- SOP entries are fake and intentionally small.
- Retrieval is keyword-based, not semantic.
- It does not use LangChain, LlamaIndex, FAISS, Chroma, vector databases, or external embedding models.
- The LLM can still make mistakes, so the prompt asks it not to invent unsupported root causes and to call out insufficient evidence.
- Log analysis only extracts error-code frequencies with the regex `E\d{3}`.

### Possible Future Improvements

- Replace fake SOP entries with engineering-reviewed real documentation.
- Add unit tests for retrieval, log statistics, and prompt construction.
- Improve log parsing with timestamps, severity levels, and subsystem fields.
- Add confidence scores and source references for each recommendation.
- Add evaluation examples for common fault scenarios.

---

## 中文版

本项目保留原有的终端聊天机器人 `local_chatbot.py`，并新增一个小型原型 **Industrial Fault Analysis Assistant（工业故障分析助手）**，入口文件为 `industrial_assistant.py`。

### 这个原型做什么

工业故障分析助手演示了一个最小化的 RAG 风格流程：

- 从 `fake_sop.txt` 加载模拟 SOP / 故障案例条目。
- 通过错误码和关键词匹配检索相关 SOP。
- 使用确定性的 Python 函数统计日志中的错误码频次。
- 将检索证据和日志统计结果交给本地 Ollama 模型，生成中文结构化排查总结。

请注意：这是一个原型，**不是**生产级诊断系统。项目只使用模拟 SOP 数据，检索方式也是最小化的关键词匹配；本地 LLM 主要用于结构化总结生成，而不是给出权威诊断结论。

### 与 `local_chatbot.py` 的区别

`local_chatbot.py` 是一个通用本地终端聊天机器人。它负责调用 Ollama Chat API、维护对话历史、通过滑动窗口裁剪历史，并支持 `/help`、`/clear`、`/history` 和 `exit`。

`industrial_assistant.py` 复用了原项目的这些基础能力，并增加了工业故障分析逻辑：

- 识别类似 `E104 怎么排查？` 的故障问题。
- 识别多行日志输入，并通过 `analyze_error_logs()` 统计错误码。
- 在调用模型前，从 `fake_sop.txt` 检索相关 SOP 条目。
- 构建固定五段式中文排查提示词。
- 通过 `/sample_logs` 运行内置日志分析示例。

原有聊天机器人仍然保留，并应继续正常工作。

### 运行要求

- Python 3.10 或更高版本
- `requests`
- 本地 Ollama 服务正在运行
- 已拉取并可使用 Ollama 模型 `gemma3`

安装唯一额外 Python 依赖：

```bash
pip install requests
```

确认 Ollama 模型可用：

```bash
ollama pull gemma3
```

项目复用的 Ollama 配置如下：

```python
OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL_NAME = "gemma3"
```

### 如何运行

运行原始聊天机器人：

```bash
python local_chatbot.py
```

运行工业故障分析助手：

```bash
python industrial_assistant.py
```

### 测试故障问答模式

启动工业故障分析助手后输入：

```text
E104 怎么排查？
```

预期行为：程序检索到 E104 对应的 SOP 条目，并要求本地 LLM 使用中文五段式结构回答：

```text
1. 问题概述
2. 相关错误码
3. 可能原因
4. 建议排查步骤
5. 需要人工确认的部分
```

### 测试日志分析模式

粘贴多行日志后，在空白行按 Enter 开始分析：

```text
2026-06-01 10:01:22 ERROR E104 Motor temperature high
2026-06-01 10:03:11 ERROR E104 Retry failed
2026-06-01 10:04:05 ERROR E205 Communication timeout
2026-06-01 10:05:30 ERROR E104 Thermal warning
```

预期行为：Python 逻辑会识别日志分析模式，统计错误码，确认 E104 是最高频错误码，检索 E104 和 E205 相关 SOP，并让 LLM 生成中文结构化总结和排查计划。

也可以直接输入：

```text
/sample_logs
```

该命令会加载 `sample_logs.txt`，运行确定性的错误码统计，检索相关 SOP 条目，并生成中文结构化总结。

### 局限性

- 这是原型，不适合用于真实工业诊断。
- SOP 条目是模拟数据，覆盖范围很小。
- 检索方式是关键词匹配，不是语义检索。
- 未使用 LangChain、LlamaIndex、FAISS、Chroma、向量数据库或外部 embedding 模型。
- LLM 仍可能出错，因此提示词要求它避免编造无证据根因，并在证据不足时明确说明需要工程验证。
- 日志分析只使用正则表达式 `E\d{3}` 提取错误码频次。

### 后续可改进方向

- 将模拟 SOP 替换为经过工程审核的真实文档。
- 为检索、日志统计和提示词构建添加单元测试。
- 增强日志解析能力，例如时间戳、严重级别和子系统字段。
- 为每条建议增加置信度和来源引用。
- 增加常见故障场景的评估样例。

---

