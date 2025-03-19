# -*- coding: utf-8 -*-
import serial
import time
import threading

from http.server import BaseHTTPRequestHandler, HTTPServer
import urllib


frames = [0,0,0,0,0,0,0]
"""
=============================
ここでポート変更
↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓
=============================
"""
class Serial:
    def __init__(self):
        global frames;
        self.port = input("ポート名を入力してください")
        self.baudrate = 119200
        self.ser = serial.Serial(self.port, self.baudrate, timeout=1)
        if self.ser.is_open:
            print(f'{self.port} is open.')
        else:
            print("SerialCantConnect!")
            exit()
    def run(self):
        global frames;
        while(True):
            time.sleep(0.15)
            txt = ""
            for i in range(7):
                txt = txt + format(frames[i], '02x')[-2:]
                if (i < 6):
                    txt = txt + ","
            txt+="\r\n"
            print("                                                                      " + txt)
            self.ser.write(txt.encode())

serial_comm = Serial()
"""
サーバー待ち受け
"""
is_safety = True
class RequestHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        global is_safety, frames;
        parsed_path = urllib.parse.urlparse(self.path)
        path = parsed_path.path
        if path == '/key':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length).decode('utf-8')
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b'Key data received')
            print
            values = list(map(int, post_data.split(',')))
            for i in range(7):
                frames[i] = values[i]
    def do_GET(self):
        global is_safety, frames;
        parsed_path = urllib.parse.urlparse(self.path)
        path = parsed_path.path
        if path == '/':
            self.send_response(200)
            self.end_headers()
            response = """
            <!DOCTYPE html><html><head><meta charset="UTF-8"><title>Safety Control</title><style>body {font-family: Arial, sans-serif;text-align: center;margin-top: 50px;}#output {margin-top: 20px;font-size: 1.5em;}.button {padding: 15px 30px;font-size: 16px;margin: 10px;border: none;color: white;cursor: pointer;transition: transform 0.3s;}.button:active {transform: scale(0.95);}#emergencyButton {background-color: red;}#resetButton {background-color: green;}#epb_button {background-color: #c60000;color: #fff;border: 4px solid #7a0000;border-radius: 50%;width: 150px;height: 150px;font-size: 1.2rem;font-weight: bold;cursor: pointer;box-shadow: 0 4px 0 #7a0000, 0 8px 15px rgba(0, 0, 0, 0.5);transition: transform 0.1s, box-shadow 0.1s;}#epb_button:hover {background-color: #e00000;}#epb_button:active {transform: translateY(4px);box-shadow: 0 0 0 #7a0000, 0 4px 8px rgba(0, 0, 0, 0.4);}/* 激しく点滅するアニメーション */@keyframes epb_flash {0%, 100% { background-color: #c60000; }50% { background-color: #ff4444; }}/* data-epb="t" の時、点滅させる */#epb_button[data-epb="t"] {animation: epb_flash 0.3s infinite;}/* リセットボタン */#epb_reset {background-color: #0058a8;        /* 深い青 */color: #fff;border: 4px solid #003f7d;        /* 濃いめの縁取り */border-radius: 50%;width: 150px;height: 150px;font-size: 1.2rem;font-weight: bold;cursor: pointer;box-shadow: 0 4px 0 #003f7d, 0 8px 15px rgba(0, 0, 0, 0.5);transition: transform 0.1s, box-shadow 0.1s;}#epb_reset:hover {background-color: #0070d1;        /* ホバーで少し明るく */}#epb_reset:active {transform: translateY(4px);box-shadow: 0 0 0 #003f7d, 0 4px 8px rgba(0, 0, 0, 0.4);}</style></head><body><button id="epb_button">非常停止<br>長押し解除</button><h1>入力モニタ</h1><div id="safety">非常停止解除</div><div id="output">マウスX:, キーコード: [0, 0, 0]</div><div id="pad">接続先：未接続</div><script>let last_safety = true;const epbButton = document.getElementById('epb_button');let longPressTimer = null;/* 押した瞬間の処理 */epbButton.addEventListener('mousedown', () => {/* とりあえず非常停止 */last_safety = false;epbButton.setAttribute('data-epb', 't');longPressTimer = setTimeout(() => {/* 長押し成功 → 解除 */epbButton.setAttribute('data-epb', '');last_safety = true;longPressTimer = null;}, 3000); /* 2秒以上で解除 */});/* 離した瞬間の処理 */epbButton.addEventListener('mouseup', () => {if (longPressTimer) {clearTimeout(longPressTimer);/* 2秒以内なら非常停止発動 */if (epbButton.getAttribute('data-epb') !== 't') {epbButton.setAttribute('data-epb', 't');last_safety = false;}}});/* 万が一マウスが外れた時の保険 */epbButton.addEventListener('mouseleave', () => {if (longPressTimer) clearTimeout(longPressTimer);});</script><script>/* 設定配列は軸番号 */function getParamAxis(config, name, index){const params = new URLSearchParams(window.location.search);const query = params.get(name);if (query === null) return;config[index] = parseInt(query);}/* 設定配列はボタン番号 */function getParamButton(config, name, index){const params = new URLSearchParams(window.location.search);const query = params.get(name);if (query === null) return;config[index] = parseInt(query);}/* 検出数値初期化 */let leftMouseDown = false;let rightMouseDown = false;let pad_idx = -1;let lastMouseX = 127;let last_pad = Array(4);last_pad.fill(127);let last_button = Array(8);last_button.fill(false);/* ボタン設定取得 */button_config = {};for (let i = 0; i < 8; i++){getParamButton(button_config, "k"+i, i);}/* 軸設定取得 */axis_config = {};for (let i = 0; i < 4; i++){getParamAxis(axis_config, "a"+i, i);}/* マウスイベントトリガ */document.addEventListener("mousemove", (event) => {lastMouseX = Math.round((event.clientX / window.innerWidth) * 255);updateDisplay();});/* パッドイベントトリガ */window.addEventListener("gamepadconnected", (event) => {pad_idx = event.gamepad.index;updateDisplay();});/* キーイベントトリガ */document.addEventListener("keydown", (event) => {const idx = button_config[event.key];if(event.key === 'Escape'){epbButton.setAttribute('data-epb', 't');last_safety = false;console.error("EPB by key");}updateDisplay();});/* マウスイベントトリガ */document.addEventListener('mousedown', (event) => {if (event.button === 0) leftMouseDown = true;if (event.button === 2) rightMouseDown = true;updateDisplay();});document.addEventListener('mouseup', (event) => {if (event.button === 0) leftMouseDown = false;if (event.button === 2) rightMouseDown = false;updateDisplay();});document.addEventListener('mouseleave', () => {leftMouseDown = false;rightMouseDown = false;updateDisplay();});window.addEventListener('blur', () => {leftMouseDown = false;rightMouseDown = false;updateDisplay();});function updateDisplay() {const gamepads = navigator.getGamepads();document.getElementById("safety").textContent = last_safety ?  `動作可能` : "非常停止状態";document.getElementById("output").innerHTML = `マウス: ${lastMouseX},${leftMouseDown}, ${rightMouseDown}, <br>ボタン: [${last_button.join(", ")}]<br>軸: [${last_pad.join(", ")}]`;if (pad_idx < 0){document.getElementById("pad").textContent = `接続先：未接続`;}else{document.getElementById("pad").textContent = `接続先：${gamepads[pad_idx].id}`;}}function sendData() {/* ボタン前処理 */let key_bin = 0;for (let i = 0; i < 8; i++){key_bin = (key_bin << 1) + (last_button[i] ? 1 : 0);}/* ゲームパッド情報取得 */getGamepadData();/* 非常停止、マウスクリック */let epb_click = 0;if (last_safety) epb_click += 1;if (leftMouseDown) epb_click += 2;if (rightMouseDown) epb_click += 4;let data = `${epb_click},${lastMouseX},${last_pad.join(",")},${key_bin}`;fetch("/key", {method: "POST",headers: { "Content-Type": "text/plain" },body: data}).catch(err => console.error("送信エラー: ", err));console.log(data)}function getGamepadData() {const gamepads = navigator.getGamepads();if (pad_idx == -1) return;if (!gamepads || !gamepads[pad_idx]){pad_idx = -1;return;}const axes = gamepads[pad_idx].axes;for(let i = 0 ; i < 4; i++){last_pad[i] = Math.round(axes[axis_config[i]] * 126 + 127)}const buttons = gamepads[pad_idx].buttons;for(let i = 0 ; i < 8; i++){last_button[i] = buttons[button_config[i]].pressed;}updateDisplay();}setInterval(sendData, 100)</script></body></html>
            """
            self.wfile.write(response.encode())
        elif path == '/config':
            self.send_response(200)
            self.end_headers()
            response = """
            <!DOCTYPE html><html lang="ja"><head><meta charset="UTF-8"><title>クエリ生成ページ</title><style>body {font-family: 'Arial', sans-serif;background-color: #f4f4f4;color: #333;padding: 20px;margin: 0;height: 100vh;}h1 {text-align: center;font-size: 32px;margin-bottom: 20px;color: #444;}.container {display: grid;grid-template-columns: 1fr 1fr;gap: 30px;max-width: 1200px;margin: 0 auto;}.section {background-color: #fff;padding: 20px;border-radius: 8px;box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);}.section h2 {text-align: center;font-size: 24px;color: #444;margin-bottom: 15px;}label {display: inline-block;width: 100px;font-size: 16px;color: #555;}input {width: 100px;padding: 8px;background-color: #f9f9f9;color: #333;border: 1px solid #ccc;border-radius: 5px;font-size: 16px;margin-bottom: 10px;}input:focus {outline: none;border-color: #888;}button {display: block;width: 220px;margin: 30px auto;padding: 12px;background-color: #4CAF50;color: #fff;border: none;border-radius: 8px;font-size: 18px;cursor: pointer;transition: background-color 0.3s ease;}button:hover {background-color: #45a049;}button:active {background-color: #388e3c;}.input-group {display: flex;justify-content: space-between;margin-bottom: 15px;}.input-group label {width: 100px;text-align: left;}.input-group input {width: 80px;text-align: center;}.footer {text-align: center;margin-top: 30px;color: #777;}/* スマートフォン等の小さい画面で1カラムにする */@media (max-width: 768px) {.container {grid-template-columns: 1fr;}}</style></head><body><h1>クエリ生成ページ</h1><div class="container"><div class="section"><h2>ボタン設定 (ボタン0〜ボタン7)</h2><div id="buttons"><!-- ボタン入力エリア --><div class="input-group"><label>ボタン0:</label><input type="number" id="k0" value="0"></div><div class="input-group"><label>ボタン1:</label><input type="number" id="k1" value="0"></div><div class="input-group"><label>ボタン2:</label><input type="number" id="k2" value="0"></div><div class="input-group"><label>ボタン3:</label><input type="number" id="k3" value="0"></div><div class="input-group"><label>ボタン4:</label><input type="number" id="k4" value="0"></div><div class="input-group"><label>ボタン5:</label><input type="number" id="k5" value="0"></div><div class="input-group"><label>ボタン6:</label><input type="number" id="k6" value="0"></div><div class="input-group"><label>ボタン7:</label><input type="number" id="k7" value="0"></div></div></div><div class="section"><h2>軸設定 (軸0〜軸3)</h2><div id="axes"><!-- 軸入力エリア --><div class="input-group"><label>軸0:</label><input type="number" id="a0" value="0"></div><div class="input-group"><label>軸1:</label><input type="number" id="a1" value="0"></div><div class="input-group"><label>軸2:</label><input type="number" id="a2" value="0"></div><div class="input-group"><label>軸3:</label><input type="number" id="a3" value="0"></div></div></div></div><button onclick="generateQuery()">送信する</button><div class="footer"><p>&copy; 2025 設定ページ</p></div><script>/*ページ読み込み時にローカルストレージから値を取得して表示*/window.onload = function() {for (let i = 0; i < 8; i++) {const savedButtonValue = localStorage.getItem(`k${i}`);if (savedButtonValue !== null) {document.getElementById(`k${i}`).value = savedButtonValue;}}for (let i = 0; i < 4; i++) {const savedAxisValue = localStorage.getItem(`a${i}`);if (savedAxisValue !== null) {document.getElementById(`a${i}`).value = savedAxisValue;}}};/* クエリ生成とローカルストレージに保存する処理*/function generateQuery() {const params = new URLSearchParams();/* ボタンパラメータとローカルストレージへの保存*/for (let i = 0; i < 8; i++) {const value = document.getElementById(`k${i}`).value;params.append(`k${i}`, value);localStorage.setItem(`k${i}`, value);}/* 軸パラメータとローカルストレージへの保存 */for (let i = 0; i < 4; i++) {const value = document.getElementById(`a${i}`).value;params.append(`a${i}`, value);localStorage.setItem(`a${i}`, value);}/* 遷移*/window.location.href = "/?" + params.toString();}</script></body></html>
            """
            self.wfile.write(response.encode())
        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b'Not found')
def run_server(server_class=HTTPServer, handler_class=RequestHandler, host='0.0.0.0', port=8000):
    server_address = (host, port)
    httpd = server_class(server_address, handler_class)
    print(f'Starting httpd server on {host}:{port}')
    httpd.serve_forever()
server_thread = threading.Thread(target=run_server)
server_thread.daemon = True
server_thread.start()
serial_thread = threading.Thread(target=serial_comm.run)
serial_thread.daemon = True
serial_thread.start()
while(1):
    time.sleep(1)