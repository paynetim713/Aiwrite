from flask import Flask, render_template, request, jsonify
import anthropic
import os

app = Flask(__name__)

client = anthropic.Anthropic(
    api_key=os.environ.get("ANTHROPIC_API_KEY")
)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/improve', methods=['POST'])
def improve_text():
    try:
        data = request.json
        text = data['text']
        task = data['task']

        if task == 'improve':
            prompt = f"Please help me improve this text and make it smoother:\n{text}"
        elif task == 'grammar':
            prompt = f"Please check the grammar errors in this text:\n{text}"
        elif task == 'title':
            prompt = f"Please generate 3 titles for this content:\n{text}"
        else:
            prompt = f"Please continue writing this text:\n{text}"

        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=2000,
            temperature=1,
            messages=[{"role": "user", "content": prompt}]
        )

        result = message.content[0].text
        return jsonify({'success': True, 'result': result})

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

if __name__ == '__main__':
    app.run(debug=False)
