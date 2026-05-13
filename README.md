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

- **流式输出 + Stop 按钮**——边生成边显示，长输出可中途打断
- **三档模型切换**：Haiku 4.5（快/便宜）/ Sonnet 4.6（默认）/ Opus 4.7（最佳）
- **温度滑块**：0 死板 ↔ 1 发散
- **Markdown 渲染**：AI 返回的标题/列表/代码块直接美化（可关）
- **本地历史**：最近 10 条存在浏览器 localStorage，点击恢复
- **复制 + 下载 .md**、字数统计、**Ctrl/Cmd+Enter** 直接运行
- **暗色/亮色主题**，跟系统也行手动切
- **设置面板**：在 UI 里填自己的 Anthropic API key,带"Test"按钮验证 key 是否有效。Key 只存浏览器 localStorage,不上云

## 跑起来

```bash
pip install -r requirements.txt
python app.py
```

打开 `http://localhost:5000` → 点右上 **⚙ Settings** → 粘贴你的 Anthropic API key（[在这申请](https://console.anthropic.com/settings/keys)）→ Test → Save。

也可以走传统的环境变量方式（适合部署到 Heroku/Railway 的场景）：

```bash
export ANTHROPIC_API_KEY=你的key
python app.py
```

UI 会自动检测后端是否有环境变量 key,优先级是：**前端填的 key > 环境变量 key**。

## API

不止 Web UI，后端也能直接调：

所有 POST endpoint 都接受 `X-Api-Key: sk-ant-...` header（前端 UI 自动带）。不带就走服务器的 `ANTHROPIC_API_KEY` 环境变量。

**`POST /api/generate`** — 一次性返回

```bash
curl -X POST http://localhost:5000/api/generate \
  -H "Content-Type: application/json" \
  -H "X-Api-Key: sk-ant-xxx" \
  -d '{"task": "improve", "text": "这段话需要润色一下", "model": "claude-sonnet-4-6", "temperature": 0.7}'
```

**`POST /api/stream`** — SSE 流式

```bash
curl -N -X POST http://localhost:5000/api/stream \
  -H "Content-Type: application/json" \
  -H "X-Api-Key: sk-ant-xxx" \
  -d '{"task": "translate", "text": "你好世界", "target_language": "English"}'
```

每个 SSE event 是 `data: {"chunk": "..."}\n\n`，结束发 `data: {"done": true}\n\n`。错误发 `data: {"error": "..."}\n\n`。

**`POST /api/validate`** — 用一次廉价的 Haiku 调用验证 key 是否有效，前端的 Test 按钮就走这条。

```bash
curl -X POST http://localhost:5000/api/validate \
  -H "Content-Type: application/json" \
  -d '{"api_key": "sk-ant-xxx"}'
```

**`GET /api/health`** — 返回后端是否就绪 + 服务器有没有配 `ANTHROPIC_API_KEY`。

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

- **没做 rate limit**。如果你用环境变量 key 部署给所有人用,被刷会扣你账户余额。简单做法是 Cloudflare / nginx 加一层。如果是"BYO key"模式(用户自己填 key),那就是用户自己的账户,你不背锅。
- **localStorage 历史**最大 5MB,存多了浏览器会拒绝。我只留最近 10 条,正常用不到限制。
- **Key 存在浏览器 localStorage**: 同设备同浏览器的扩展/网页都能读,真正敏感的环境别用 BYO 模式,走环境变量。

## 协议

MIT。
