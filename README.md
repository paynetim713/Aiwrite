# Aiwrite

很小的写作助手 web app：粘一段文字进去，让 Claude 帮你润色、查语法、起标题、或者续写。

不是什么大项目，就是想要一个浏览器里能直接用的"调 Claude 改文字"的小工具。Flask + 一个模板页。

## 跑起来

```bash
pip install -r requirements.txt
export ANTHROPIC_API_KEY=你的key
python app.py
```

打开 `http://localhost:5000`。

## 四个动作

| 按钮 | 干什么 |
|---|---|
| Improve | 把段落改得更通顺 |
| Grammar | 列出语法错误 |
| Title | 根据内容生成 3 个标题 |
| Continue | 接着这段往下续写 |

prompt 都写在 `app.py` 里，想改改风格就直接改字符串。

## 部署

```
web: gunicorn app:app
```

Heroku / Railway / Render 任选，设置 `ANTHROPIC_API_KEY` 环境变量。

## 协议

MIT。
