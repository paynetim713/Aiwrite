# Aiwrite

浏览器里直接用的 AI 写作助手，Flask + Claude，12 种文字处理任务 + 流式输出 + 历史记录 + 暗色模式。

写这个的契机：日常需要快速润色一段话或者切换语气，每次开 ChatGPT/Claude 网页都要先打一遍 prompt 太烦，所以做了一个一键操作的小工具。

## 功能

12 个任务，按钮直接切：

| 任务 | 做什么 |
|---|---|
| Improve | 润色：通顺、紧凑、不啰嗦 |
| Grammar | 列出语法 / 拼写 / 标点问题，每条带解释 |
| Title | 5 个候选标题，风格混合 |
| Continue | 接着写下去，保持原风格 |
| Summarize | 压成一段精简版 |
| Expand | 扩写，加细节、加例子 |
| Paraphrase | 同义改写，意思一样、措辞不同 |
| Translate | 翻译，下拉选目标语言（中英日韩法西德马来 9 种） |
| Tone | 改语气，8 种（professional / casual / formal / friendly / academic / persuasive / humorous / concise） |
| Simplify | 白话化，砍 jargon |
| Outline | 生成大纲 |
| Custom | 自定义 prompt，比如"用鲁迅风格改写" |

UX：

- **流式输出**——边生成边显示，几个字就开始看到结果，不用等完整响应
- **三档模型切换**：Haiku 4.5（快/便宜）/ Sonnet 4.6（默认）/ Opus 4.7（最佳）
- **温度滑块**：0 死板 ↔ 1 发散
- **本地历史**：最近 10 条存在浏览器 localStorage，点击恢复
- **复制按钮**、**字数统计**、**Ctrl/Cmd+Enter** 直接运行
- **暗色/亮色主题**，跟系统也行手动切

## 跑起来

```bash
pip install -r requirements.txt
export ANTHROPIC_API_KEY=你的key
python app.py
```

key 在 https://console.anthropic.com/settings/keys 申请。

打开 `http://localhost:5000`，粘段文字，选任务，跑。

## API

不止 Web UI，后端也能直接调：

**`POST /api/generate`** — 一次性返回

```bash
curl -X POST http://localhost:5000/api/generate \
  -H "Content-Type: application/json" \
  -d '{"task": "improve", "text": "这段话需要润色一下", "model": "claude-sonnet-4-6", "temperature": 0.7}'
```

**`POST /api/stream`** — SSE 流式

```bash
curl -N -X POST http://localhost:5000/api/stream \
  -H "Content-Type: application/json" \
  -d '{"task": "translate", "text": "你好世界", "target_language": "English"}'
```

每个 SSE event 是 `data: {"chunk": "..."}\n\n`，结束发 `data: {"done": true}\n\n`。错误发 `data: {"error": "..."}\n\n`。

**`GET /api/health`** — 检查后端 + key 是否就绪。

## 部署

```
web: gunicorn app:app
```

Heroku / Railway / Render 都行，环境变量设 `ANTHROPIC_API_KEY` 就行。

注意流式部署：

- **Heroku**：Router 默认 30 秒超时，长输出会被截断。要么换 Sonnet/Haiku（输出快），要么关掉 Stream toggle 走非流式。
- **Cloudflare 系**：默认 100 秒 worker 上限，一般够用。
- **Railway**：没有这层超时，最舒服。

## 改起来

新加一个任务很简单，在 `app.py` 的 `TASKS` 字典里加一项：

```python
def _your_task(text, **_):
    return (
        "你的 system prompt",
        text,
    )

TASKS["your_task"] = {"label": "Your Task", "fn": _your_task}
```

前端 `index.html` 的 `<div class="task-row">` 是用 Jinja 循环生成的，自动会显示新任务，不用动 HTML。

## 已知问题

- **没做 rate limit**。部署到公网随便给人用的话，被刷会扣你账户余额。简单做法是上 Cloudflare 或在 nginx 层加限流。
- **localStorage 历史**最大 5MB，存多了浏览器会拒绝。我只留最近 10 条，正常用不到限制。
- **API key 在后端**，前端拿不到——所以这个工具不能做成"用户带自己的 key"的形态，部署者承担费用。

## 协议

MIT。
