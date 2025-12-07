# server.py

from flask import Flask, request, send_file, jsonify, render_template_string
from gevent.pywsgi import WSGIServer
from dotenv import load_dotenv
import os
import webbrowser
import threading
import time

from tts_handler import generate_speech, get_models, get_voices
from utils import require_api_key, AUDIO_FORMAT_MIME_TYPES

app = Flask(__name__)
load_dotenv()

API_KEY = os.getenv('API_KEY', 'sk')
PORT = int(os.getenv('PORT', 5050))

DEFAULT_VOICE = os.getenv('DEFAULT_VOICE', 'en-US-AndrewNeural')
DEFAULT_RESPONSE_FORMAT = os.getenv('DEFAULT_RESPONSE_FORMAT', 'mp3')
DEFAULT_SPEED = float(os.getenv('DEFAULT_SPEED', 1.0))

# DEFAULT_MODEL = os.getenv('DEFAULT_MODEL', 'tts-1')

# HTML文件路径
HTML_FILE = os.path.join(os.path.dirname(__file__), 'index.html')

# 添加一个完整的 HTML 测试页面（备用，如果文件不存在则使用）
HOME_TEMPLATE = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Edge TTS API 测试平台</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 12px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.2);
            overflow: hidden;
        }
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }
        .header h1 { font-size: 2em; margin-bottom: 10px; }
        .header p { opacity: 0.9; }
        .content { padding: 30px; }
        .section {
            margin-bottom: 40px;
            padding: 25px;
            background: #f8f9fa;
            border-radius: 8px;
            border-left: 4px solid #667eea;
        }
        .section h2 {
            color: #333;
            margin-bottom: 20px;
            font-size: 1.5em;
        }
        .form-group {
            margin-bottom: 15px;
        }
        .form-group label {
            display: block;
            margin-bottom: 5px;
            color: #555;
            font-weight: 500;
        }
        .form-group input,
        .form-group select,
        .form-group textarea {
            width: 100%;
            padding: 10px;
            border: 1px solid #ddd;
            border-radius: 6px;
            font-size: 14px;
            transition: border-color 0.3s;
        }
        .form-group input:focus,
        .form-group select:focus,
        .form-group textarea:focus {
            outline: none;
            border-color: #667eea;
        }
        .form-group textarea {
            min-height: 80px;
            resize: vertical;
        }
        .form-row {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 15px;
        }
        .btn {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            padding: 12px 24px;
            border-radius: 6px;
            cursor: pointer;
            font-size: 14px;
            font-weight: 500;
            transition: transform 0.2s, box-shadow 0.2s;
            margin-right: 10px;
            margin-top: 10px;
        }
        .btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
        }
        .btn:active {
            transform: translateY(0);
        }
        .btn-secondary {
            background: #6c757d;
        }
        .result {
            margin-top: 20px;
            padding: 15px;
            background: white;
            border-radius: 6px;
            border: 1px solid #ddd;
            display: none;
        }
        .result.show {
            display: block;
        }
        .result h3 {
            margin-bottom: 10px;
            color: #333;
        }
        .result pre {
            background: #f8f9fa;
            padding: 15px;
            border-radius: 6px;
            overflow-x: auto;
            font-size: 12px;
            line-height: 1.5;
        }
        .audio-player {
            margin-top: 15px;
            width: 100%;
        }
        .loading {
            display: none;
            text-align: center;
            padding: 20px;
            color: #667eea;
        }
        .loading.show {
            display: block;
        }
        .error {
            color: #dc3545;
            background: #f8d7da;
            padding: 10px;
            border-radius: 6px;
            margin-top: 10px;
        }
        .success {
            color: #155724;
            background: #d4edda;
            padding: 10px;
            border-radius: 6px;
            margin-top: 10px;
        }
        .voice-list {
            max-height: 300px;
            overflow-y: auto;
            margin-top: 10px;
        }
        .voice-item {
            padding: 8px;
            border-bottom: 1px solid #eee;
            cursor: pointer;
            transition: background 0.2s;
        }
        .voice-item:hover {
            background: #f0f0f0;
        }
        .method-selector {
            display: inline-block;
            margin-bottom: 15px;
        }
        .method-selector label {
            margin-right: 15px;
            cursor: pointer;
        }
        .method-selector input[type="radio"] {
            margin-right: 5px;
        }
        @media (max-width: 768px) {
            .form-row {
                grid-template-columns: 1fr;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎤 Edge TTS API 测试平台</h1>
            <p>基于微软 Edge TTS 的 OpenAI TTS API 替代品</p>
        </div>
        <div class="content">
            <!-- 普通TTS接口测试 -->
            <div class="section">
                <h2>📝 普通TTS接口 (/tts)</h2>
                <div class="method-selector">
                    <label><input type="radio" name="tts-method" value="GET" checked> GET</label>
                    <label><input type="radio" name="tts-method" value="POST"> POST</label>
                </div>
                <div class="form-group">
                    <label>API密钥 (key):</label>
                    <input type="text" id="tts-key" placeholder="输入API密钥" value="sk">
                </div>
                <div class="form-group">
                    <label>文本内容 (text):</label>
                    <textarea id="tts-text" placeholder="输入要合成的文本">Hello, this is a test of the TTS API.</textarea>
                </div>
                <div class="form-row">
                    <div class="form-group">
                        <label>说话人 (voice):</label>
                        <input type="text" id="tts-voice" placeholder="例如: en-US-AndrewNeural" value="en-US-AndrewNeural">
                    </div>
                    <div class="form-group">
                        <label>音频格式 (format):</label>
                        <select id="tts-format">
                            <option value="mp3">MP3</option>
                            <option value="wav">WAV</option>
                            <option value="opus">OPUS</option>
                            <option value="aac">AAC</option>
                            <option value="flac">FLAC</option>
                            <option value="pcm">PCM</option>
                        </select>
                    </div>
                </div>
                <div class="form-group">
                    <label>语速 (speed):</label>
                    <input type="number" id="tts-speed" step="0.1" min="0.5" max="2.0" value="1.0">
                </div>
                <button class="btn" onclick="testSimpleTTS()">🚀 测试TTS接口</button>
                <div class="loading" id="tts-loading">正在生成语音...</div>
                <div class="result" id="tts-result">
                    <h3>结果:</h3>
                    <audio id="tts-audio" class="audio-player" controls></audio>
                    <div id="tts-message"></div>
                </div>
            </div>

            <!-- OpenAI格式TTS接口测试 -->
            <div class="section">
                <h2>🎯 OpenAI格式TTS接口 (/v1/audio/speech)</h2>
                <div class="form-group">
                    <label>API密钥 (Bearer Token):</label>
                    <input type="text" id="openai-key" placeholder="输入API密钥" value="sk">
                </div>
                <div class="form-group">
                    <label>文本内容 (input):</label>
                    <textarea id="openai-input" placeholder="输入要合成的文本">Hello, this is a test of the OpenAI TTS API.</textarea>
                </div>
                <div class="form-row">
                    <div class="form-group">
                        <label>说话人 (voice):</label>
                        <input type="text" id="openai-voice" placeholder="例如: en-US-AndrewNeural" value="en-US-AndrewNeural">
                    </div>
                    <div class="form-group">
                        <label>音频格式 (response_format):</label>
                        <select id="openai-format">
                            <option value="mp3">MP3</option>
                            <option value="wav">WAV</option>
                            <option value="opus">OPUS</option>
                            <option value="aac">AAC</option>
                            <option value="flac">FLAC</option>
                            <option value="pcm">PCM</option>
                        </select>
                    </div>
                </div>
                <div class="form-group">
                    <label>语速 (speed):</label>
                    <input type="number" id="openai-speed" step="0.1" min="0.5" max="2.0" value="1.0">
                </div>
                <button class="btn" onclick="testOpenAITTS()">🚀 测试OpenAI TTS接口</button>
                <div class="loading" id="openai-loading">正在生成语音...</div>
                <div class="result" id="openai-result">
                    <h3>结果:</h3>
                    <audio id="openai-audio" class="audio-player" controls></audio>
                    <div id="openai-message"></div>
                </div>
            </div>

            <!-- 列出模型 -->
            <div class="section">
                <h2>📋 列出模型 (/v1/models)</h2>
                <div class="form-group">
                    <label>API密钥 (Bearer Token):</label>
                    <input type="text" id="models-key" placeholder="输入API密钥" value="sk">
                </div>
                <button class="btn" onclick="testListModels()">📋 获取模型列表</button>
                <div class="loading" id="models-loading">正在获取模型列表...</div>
                <div class="result" id="models-result">
                    <h3>结果:</h3>
                    <pre id="models-data"></pre>
                </div>
            </div>

            <!-- 列出语音 -->
            <div class="section">
                <h2>🗣️ 列出语音 (/v1/voices)</h2>
                <div class="form-group">
                    <label>API密钥 (Bearer Token):</label>
                    <input type="text" id="voices-key" placeholder="输入API密钥" value="sk">
                </div>
                <div class="form-group">
                    <label>语言代码 (language, 可选):</label>
                    <input type="text" id="voices-language" placeholder="例如: zh-CN, en-US (留空获取默认语言)">
                </div>
                <button class="btn" onclick="testListVoices()">🗣️ 获取语音列表</button>
                <div class="loading" id="voices-loading">正在获取语音列表...</div>
                <div class="result" id="voices-result">
                    <h3>结果:</h3>
                    <div class="voice-list" id="voices-data"></div>
                </div>
            </div>

            <!-- 列出所有语音 -->
            <div class="section">
                <h2>🌍 列出所有语音 (/v1/voices/all)</h2>
                <div class="form-group">
                    <label>API密钥 (Bearer Token):</label>
                    <input type="text" id="all-voices-key" placeholder="输入API密钥" value="sk">
                </div>
                <button class="btn" onclick="testListAllVoices()">🌍 获取所有语音</button>
                <div class="loading" id="all-voices-loading">正在获取所有语音列表...</div>
                <div class="result" id="all-voices-result">
                    <h3>结果:</h3>
                    <div class="voice-list" id="all-voices-data"></div>
                </div>
            </div>
        </div>
    </div>

    <script>
        const API_BASE = window.location.origin;

        // 普通TTS接口测试
        async function testSimpleTTS() {
            const method = document.querySelector('input[name="tts-method"]:checked').value;
            const key = document.getElementById('tts-key').value;
            const text = document.getElementById('tts-text').value;
            const voice = document.getElementById('tts-voice').value;
            const format = document.getElementById('tts-format').value;
            const speed = document.getElementById('tts-speed').value;

            if (!key || !text) {
                showMessage('tts-message', '请填写API密钥和文本内容', 'error');
                return;
            }

            const loading = document.getElementById('tts-loading');
            const result = document.getElementById('tts-result');
            const audio = document.getElementById('tts-audio');

            loading.classList.add('show');
            result.classList.remove('show');

            try {
                let url = `${API_BASE}/tts?key=${encodeURIComponent(key)}&text=${encodeURIComponent(text)}&voice=${encodeURIComponent(voice)}&format=${format}&speed=${speed}`;
                
                if (method === 'POST') {
                    const response = await fetch(`${API_BASE}/tts`, {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({ key, text, voice, format, speed })
                    });

                    if (response.ok) {
                        const blob = await response.blob();
                        const audioUrl = URL.createObjectURL(blob);
                        audio.src = audioUrl;
                        result.classList.add('show');
                        showMessage('tts-message', '语音生成成功！', 'success');
                    } else {
                        const error = await response.json();
                        showMessage('tts-message', `错误: ${error.error || '生成失败'}`, 'error');
                        result.classList.add('show');
                    }
                } else {
                    const response = await fetch(url);
                    if (response.ok) {
                        const blob = await response.blob();
                        const audioUrl = URL.createObjectURL(blob);
                        audio.src = audioUrl;
                        result.classList.add('show');
                        showMessage('tts-message', '语音生成成功！', 'success');
                    } else {
                        const error = await response.json();
                        showMessage('tts-message', `错误: ${error.error || '生成失败'}`, 'error');
                        result.classList.add('show');
                    }
                }
            } catch (error) {
                showMessage('tts-message', `请求失败: ${error.message}`, 'error');
                result.classList.add('show');
            } finally {
                loading.classList.remove('show');
            }
        }

        // OpenAI格式TTS接口测试
        async function testOpenAITTS() {
            const key = document.getElementById('openai-key').value;
            const input = document.getElementById('openai-input').value;
            const voice = document.getElementById('openai-voice').value;
            const format = document.getElementById('openai-format').value;
            const speed = document.getElementById('openai-speed').value;

            if (!key || !input) {
                showMessage('openai-message', '请填写API密钥和文本内容', 'error');
                return;
            }

            const loading = document.getElementById('openai-loading');
            const result = document.getElementById('openai-result');
            const audio = document.getElementById('openai-audio');

            loading.classList.add('show');
            result.classList.remove('show');

            try {
                const response = await fetch(`${API_BASE}/v1/audio/speech`, {
                    method: 'POST',
                    headers: {
                        'Authorization': `Bearer ${key}`,
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        input: input,
                        voice: voice,
                        response_format: format,
                        speed: parseFloat(speed)
                    })
                });

                if (response.ok) {
                    const blob = await response.blob();
                    const audioUrl = URL.createObjectURL(blob);
                    audio.src = audioUrl;
                    result.classList.add('show');
                    showMessage('openai-message', '语音生成成功！', 'success');
                } else {
                    const error = await response.json();
                    showMessage('openai-message', `错误: ${error.error || '生成失败'}`, 'error');
                    result.classList.add('show');
                }
            } catch (error) {
                showMessage('openai-message', `请求失败: ${error.message}`, 'error');
                result.classList.add('show');
            } finally {
                loading.classList.remove('show');
            }
        }

        // 列出模型
        async function testListModels() {
            const key = document.getElementById('models-key').value;
            if (!key) {
                alert('请填写API密钥');
                return;
            }

            const loading = document.getElementById('models-loading');
            const result = document.getElementById('models-result');
            const data = document.getElementById('models-data');

            loading.classList.add('show');
            result.classList.remove('show');

            try {
                const response = await fetch(`${API_BASE}/v1/models`, {
                    headers: {
                        'Authorization': `Bearer ${key}`
                    }
                });

                const json = await response.json();
                data.textContent = JSON.stringify(json, null, 2);
                result.classList.add('show');
            } catch (error) {
                data.textContent = `错误: ${error.message}`;
                result.classList.add('show');
            } finally {
                loading.classList.remove('show');
            }
        }

        // 列出语音
        async function testListVoices() {
            const key = document.getElementById('voices-key').value;
            const language = document.getElementById('voices-language').value;
            if (!key) {
                alert('请填写API密钥');
                return;
            }

            const loading = document.getElementById('voices-loading');
            const result = document.getElementById('voices-result');
            const data = document.getElementById('voices-data');

            loading.classList.add('show');
            result.classList.remove('show');

            try {
                let url = `${API_BASE}/v1/voices`;
                if (language) {
                    url += `?language=${encodeURIComponent(language)}`;
                }
                const response = await fetch(url, {
                    headers: {
                        'Authorization': `Bearer ${key}`
                    }
                });

                const json = await response.json();
                displayVoices(data, json.voices || []);
                result.classList.add('show');
            } catch (error) {
                data.innerHTML = `<div class="error">错误: ${error.message}</div>`;
                result.classList.add('show');
            } finally {
                loading.classList.remove('show');
            }
        }

        // 列出所有语音
        async function testListAllVoices() {
            const key = document.getElementById('all-voices-key').value;
            if (!key) {
                alert('请填写API密钥');
                return;
            }

            const loading = document.getElementById('all-voices-loading');
            const result = document.getElementById('all-voices-result');
            const data = document.getElementById('all-voices-data');

            loading.classList.add('show');
            result.classList.remove('show');

            try {
                const response = await fetch(`${API_BASE}/v1/voices/all`, {
                    headers: {
                        'Authorization': `Bearer ${key}`
                    }
                });

                const json = await response.json();
                displayVoices(data, json.voices || []);
                result.classList.add('show');
            } catch (error) {
                data.innerHTML = `<div class="error">错误: ${error.message}</div>`;
                result.classList.add('show');
            } finally {
                loading.classList.remove('show');
            }
        }

        // 显示语音列表
        function displayVoices(container, voices) {
            if (voices.length === 0) {
                container.innerHTML = '<div class="error">未找到语音</div>';
                return;
            }

            container.innerHTML = voices.map(voice => {
                return `<div class="voice-item" onclick="selectVoice('${voice.name}')">
                    <strong>${voice.name}</strong> - ${voice.gender} (${voice.language})
                </div>`;
            }).join('');
        }

        // 选择语音
        function selectVoice(voiceName) {
            document.getElementById('tts-voice').value = voiceName;
            document.getElementById('openai-voice').value = voiceName;
            alert(`已选择语音: ${voiceName}`);
        }

        // 显示消息
        function showMessage(elementId, message, type) {
            const element = document.getElementById(elementId);
            element.className = type;
            element.textContent = message;
        }
    </script>
</body>
</html>
"""

@app.route('/')
def home():
    # 尝试读取独立的HTML文件，如果不存在则使用模板
    if os.path.exists(HTML_FILE):
        with open(HTML_FILE, 'r', encoding='utf-8') as f:
            return f.read()
    else:
        return render_template_string(HOME_TEMPLATE, port=PORT)

@app.route('/v1/audio/speech', methods=['POST'])
@require_api_key
def text_to_speech():
    data = request.json
    if not data or 'input' not in data:
        return jsonify({"error": "Missing 'input' in request body"}), 400

    text = data.get('input')
    # model = data.get('model', DEFAULT_MODEL)
    voice = data.get('voice', DEFAULT_VOICE)

    response_format = data.get('response_format', DEFAULT_RESPONSE_FORMAT)
    speed = float(data.get('speed', DEFAULT_SPEED))
    
    mime_type = AUDIO_FORMAT_MIME_TYPES.get(response_format, "audio/mpeg")

    # Generate the audio file in the specified format with speed adjustment
    output_file_path = generate_speech(text, voice, response_format, speed)

    # Return the file with the correct MIME type
    return send_file(output_file_path, mimetype=mime_type, as_attachment=True, download_name=f"speech.{response_format}")

@app.route('/v1/models', methods=['GET', 'POST'])
@require_api_key
def list_models():
    return jsonify({"data": get_models()})

@app.route('/v1/voices', methods=['GET', 'POST'])
@require_api_key
def list_voices():
    specific_language = None

    data = request.args if request.method == 'GET' else request.json
    if data and ('language' in data or 'locale' in data):
        specific_language = data.get('language') if 'language' in data else data.get('locale')

    return jsonify({"voices": get_voices(specific_language)})

@app.route('/v1/voices/all', methods=['GET', 'POST'])
@require_api_key
def list_all_voices():
    return jsonify({"voices": get_voices('all')})

@app.route('/api/voices/chinese', methods=['GET'])
def list_chinese_voices():
    """获取中文语音列表，无需密钥验证，供前端使用"""
    try:
        # 获取所有中文语音（包括简体中文和繁体中文）
        all_voices = get_voices('all')
        chinese_voices = [
            v for v in all_voices 
            if v['language'].startswith('zh')
        ]
        return jsonify({"voices": chinese_voices})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/tts', methods=['GET', 'POST'])
def simple_tts():
    """
    普通TTS接口，支持GET和POST
    参数：
    - text: 文本内容（必需）
    - voice: 说话人（可选，默认使用DEFAULT_VOICE）
    - key: 密钥（必需）
    - format: 音频格式（可选，默认mp3）
    - speed: 语速（可选，默认1.0）
    """
    # 从GET参数或POST参数中获取数据
    if request.method == 'GET':
        data = request.args
    else:
        # POST请求支持JSON和form-data
        if request.is_json:
            data = request.json or {}
        else:
            data = request.form.to_dict()
    
    # 验证密钥
    api_key = data.get('key') or data.get('api_key')
    if not api_key or api_key != API_KEY:
        return jsonify({"error": "Invalid or missing API key"}), 401
    
    # 获取必需参数
    text = data.get('text') or data.get('input')
    if not text:
        return jsonify({"error": "Missing 'text' parameter"}), 400
    
    # 获取可选参数
    voice = data.get('voice', DEFAULT_VOICE)
    response_format = data.get('format') or data.get('response_format', DEFAULT_RESPONSE_FORMAT)
    speed = float(data.get('speed', DEFAULT_SPEED))
    
    mime_type = AUDIO_FORMAT_MIME_TYPES.get(response_format, "audio/mpeg")
    
    try:
        # 生成语音
        output_file_path = generate_speech(text, voice, response_format, speed)
        
        # 返回音频文件
        return send_file(output_file_path, mimetype=mime_type, as_attachment=True, download_name=f"speech.{response_format}")
    except Exception as e:
        return jsonify({"error": f"Failed to generate speech: {str(e)}"}), 500

print(f" Edge TTS (Free Azure TTS) Replacement for OpenAI's TTS API")
print(f" ")
print(f" * Serving OpenAI Edge TTS")
print(f" * Server running on http://localhost:{PORT}")
print(f" * TTS Endpoint: http://localhost:{PORT}/v1/audio/speech")
print(f" * Simple TTS Endpoint: http://localhost:{PORT}/tts")
print(f" ")

def open_browser():
    """延迟打开浏览器，等待服务器启动"""
    time.sleep(1.5)  # 等待服务器完全启动
    url = f"http://localhost:{PORT}"
    webbrowser.open(url)
    print(f" * Browser opened at {url}")

if __name__ == '__main__':
    http_server = WSGIServer(('0.0.0.0', PORT), app)
    
    # 在后台线程中打开浏览器
    browser_thread = threading.Thread(target=open_browser, daemon=True)
    browser_thread.start()
    
    http_server.serve_forever()
