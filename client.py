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
        self.port = 'COM18'
        self.baudrate = 119200
        self.ser = serial.Serial(port, baudrate, timeout=1)
        if self.ser.is_open:
            print(f'{self.port} is open.')
        else:
            print("SerialCantConnect!")
            exit()
    def run():
        global frames, is_safety;
        while(True):
            time.sleep(0.05)
            if (is_safety):
                frames[0] = 1;
            else:
                frames[0] = 0;
            txt = ""
            for i in range(7):
                txt = txt + format(frames[i], '02x')[-2:]
                if (i < 6):
                    txt = txt + ","
            txt+="\r\n"
            print(txt)
            self.ser.write(txt.encode())



"""
サーバー待ち受け
"""
is_safety = True
class RequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        global is_safety, frames;
        parsed_path = urllib.parse.urlparse(self.path)
        path = parsed_path.path
        
        if path == '/emergency':
            is_safety = False
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b'State set to emergency')
        elif path == '/reset':
            is_safety = True
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b'State reset to safety')
        elif path == '/is_safety':
            self.send_response(200)
            self.end_headers()
            response = f'Is safety: {is_safety}'
            self.wfile.write(response.encode())
        if path == '/key':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length).decode('utf-8')
            serial_comm.update_frame(post_data)
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b'Key data received')
            values = list(map(int, post_data.split(',')))
            for i in range(6):
                frames[i+ 1] = values[i]
        elif path == '/':
            self.send_response(200)
            self.end_headers()
            response = """
            <!DOCTYPE html><html><head><title>Safety Control</title><style>body {font-family: Arial, sans-serif;text-align: center;margin-top: 50px;}#output {margin-top: 20px;font-size: 1.5em;}.button {padding: 15px 30px;font-size: 16px;margin: 10px;border: none;color: white;cursor: pointer;transition: transform 0.3s;}.button:active {transform: scale(0.95);}#emergencyButton {background-color: red;}#resetButton {background-color: green;}</style></head><body><h1>Safety Control</h1><button id="emergencyButton" class="button" onclick="sendEmergency()">Emergency Stop</button><button id="resetButton" class="button" onclick="sendReset()">Reset</button><p id="status">Loading...</p><h1>マウス位置 & キー入力モニタ</h1><div id="output">マウスX: 127, キーコード: [0, 0, 0]</div><script>async function sendEmergency() {const response = await fetch('/emergency');}async function sendReset() {const response = await fetch('/reset');}async function fetchSafetyStatus() {const response = await fetch('/is_safety');if (response.ok) {const text = await response.text();document.getElementById('status').innerText = text;}}setInterval(fetchSafetyStatus, 100); // 3秒ごとに状態を取得fetchSafetyStatus(); // 初回取得</script><script>let allKeys = [];let lastMouseX = 127;const params = new URLSearchParams(window.location.search);let stickIndex = [0,1,2];if (params.has('s1')) {stickIndex[0] = parseInt(params.get('s1'));}if (params.has('s2')) {stickIndex[1] = parseInt(params.get('s2'));}if (params.has('s3')) {stickIndex[2] = parseInt(params.get('s3'));}document.addEventListener("mousemove", (event) => {lastMouseX = Math.round((event.clientX / window.innerWidth) * 255);updateDisplay();});document.addEventListener("keydown", (event) => {if (!allKeys.includes(event.keyCode)) {allKeys.push(event.keyCode);}updateDisplay();});document.addEventListener("keyup", (event) => {allKeys = allKeys.filter(k => k !== event.keyCode);updateDisplay();});function updateDisplay() {let keysArray = allKeys.slice(0, 3);while (keysArray.length < 3) {keysArray.push(0);}console.log(`マウスX: ${lastMouseX}`);console.log(`キーコード: [${keysArray.join(", ")}]`);document.getElementById("output").textContent = `マウスX: ${lastMouseX}, キーコード: [${keysArray.join(", ")}]`;}function sendData() {let keysArray = allKeys.slice(0, 3);while (keysArray.length < 3) {keysArray.push(0);}getGamepadData();let data = `${lastMouseX},${last_pad.join(",")},${keysArray.join(",")}`;fetch("/key", {method: "POST",headers: { "Content-Type": "text/plain" },body: data}).catch(err => console.error("送信エラー: ", err));console.log(data)}let pad_idx = -1;let last_pad = [127, 127, 127]window.addEventListener("gamepadconnected", (event) => {pad_idx = event.gamepad.index;});function getGamepadData() {const gamepads = navigator.getGamepads();if (pad_idx == -1) return;if (!gamepads || !gamepads[pad_idx]){pad_idx = -1;return;}const axes = gamepads[pad_idx].axes;last_pad = [Math.round(axes[stickIndex[0]] * 126 + 127),Math.round(axes[stickIndex[1]] * 126 + 127),Math.round(axes[stickIndex[2]] * 126 + 127)];}setInterval(sendData, 100);</script></body></html>
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
while(1):
    time.sleep(1)