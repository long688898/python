import os
import re
import shutil
import subprocess
import http.server
import socketserver
import threading
import requests
from flask import Flask
import json
import time
import base64
import logging
import socket

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)

# 设置环境变量
FILE_PATH = os.environ.get('FILE_PATH', './temp')
PROJECT_URL = os.environ.get('URL', '')
INTERVAL_SECONDS = int(os.environ.get("TIME", 120))
UUID = os.environ.get('UUID', 'abe2f2de-13ae-4f1f-bea5-d6c881ce6888')
NEZHA_SERVER = os.environ.get('NEZHA_SERVER', '')
NEZHA_PORT = os.environ.get('NEZHA_PORT', '')
NEZHA_KEY = os.environ.get('NEZHA_KEY', '')
ARGO_DOMAIN = os.environ.get('ARGO_DOMAIN', '')
ARGO_AUTH = os.environ.get('ARGO_AUTH', '')
CFIP = os.environ.get('CFIP', 'ip.sb')
NAME = os.environ.get('NAME', 'Vls')
ARGO_PORT = int(os.environ.get('ARGO_PORT', 8008))
CFPORT = int(os.environ.get('CFPORT', 443))

# 动态获取可用端口
def get_free_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('', 0))
        return s.getsockname()[1]

PORT = get_free_port()

# 创建目录
if not os.path.exists(FILE_PATH):
    os.makedirs(FILE_PATH)
    logger.info(f"{FILE_PATH} has been created")
else:
    logger.info(f"{FILE_PATH} already exists")

# 清理旧文件
paths_to_delete = ['boot.log', 'list.txt', 'sub.txt', 'npm', 'web', 'bot', 'tunnel.yml', 'tunnel.json']
for file in paths_to_delete:
    file_path = os.path.join(FILE_PATH, file)
    try:
        os.unlink(file_path)
        logger.info(f"{file_path} has been deleted")
    except Exception as e:
        logger.info(f"Skip Delete {file_path}: {e}")

# HTTP服务器
class MyHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, format, *args):
        pass

    def do_GET(self):
        if self.path == '/':
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b'Hello, world')
        elif self.path == '/sub':
            try:
                with open(os.path.join(FILE_PATH, 'sub.txt'), 'rb') as file:
                    content = file.read()
                self.send_response(200)
                self.send_header('Content-Type', 'text/plain; charset=utf-8')
                self.end_headers()
                self.wfile.write(content)
            except FileNotFoundError:
                self.send_response(500)
                self.end_headers()
                self.wfile.write(b'Error reading file')
        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b'Not found')

def start_http_server():
    try:
        httpd = socketserver.TCPServer(('', PORT), MyHandler)
        logger.info(f"Serving on port {PORT}")
        server_thread = threading.Thread(target=httpd.serve_forever)
        server_thread.daemon = True
        server_thread.start()
    except Exception as e:
        logger.error(f"Failed to start HTTP server: {e}")
        raise

# 生成xr-ay配置文件
def generate_config():
    config = {"log":{"access":"/dev/null","error":"/dev/null","loglevel":"none",},"inbounds":[{"port":ARGO_PORT ,"protocol":"vless","settings":{"clients":[{"id":UUID ,"flow":"xtls-rprx-vision",},],"decryption":"none","fallbacks":[{"dest":3001 },{"path":"/vless","dest":3002 },{"path":"/vmess","dest":3003 },{"path":"/trojan","dest":3004 },],},"streamSettings":{"network":"tcp",},},{"port":3001 ,"listen":"127.0.0.1","protocol":"vless","settings":{"clients":[{"id":UUID },],"decryption":"none"},"streamSettings":{"network":"ws","security":"none"}},{"port":3002 ,"listen":"127.0.0.1","protocol":"vless","settings":{"clients":[{"id":UUID ,"level":0 }],"decryption":"none"},"streamSettings":{"network":"ws","security":"none","wsSettings":{"path":"/vless"}},"sniffing":{"enabled":True ,"destOverride":["http","tls","quic"],"metadataOnly":False }},{"port":3003 ,"listen":"127.0.0.1","protocol":"vmess","settings":{"clients":[{"id":UUID ,"alterId":0 }]},"streamSettings":{"network":"ws","wsSettings":{"path":"/vmess"}},"sniffing":{"enabled":True ,"destOverride":["http","tls","quic"],"metadataOnly":False }},{"port":3004 ,"listen":"127.0.0.1","protocol":"trojan","settings":{"clients":[{"password":UUID },]},"streamSettings":{"network":"ws","security":"none","wsSettings":{"path":"/trojan"}},"sniffing":{"enabled":True ,"destOverride":["http","tls","quic"],"metadataOnly":False }},],"dns":{"servers":["https+local://8.8.8.8/dns-query"]},"outbounds":[{"protocol":"freedom"},{"tag":"WARP","protocol":"wireguard","settings":{"secretKey":"YFYOAdbw1bKTHlNNi+aEjBM3BO7unuFC5rOkMRAz9XY=","address":["172.16.0.2/32","2606:4700:110:8a36:df92:102a:9602:fa18/128"],"peers":[{"publicKey":"bmXOC+F1FxEMF9dyiK2H5/1SUtzH0JuVo51h2wPfgyo=","allowedIPs":["0.0.0.0/0","::/0"],"endpoint":"162.159.193.10:2408"}],"reserved":[78 ,135 ,76 ],"mtu":1280 }},],"routing":{"domainStrategy":"AsIs","rules":[{"type":"field","domain":["domain:openai.com","domain:ai.com"],"outboundTag":"WARP"},]}}
    with open(os.path.join(FILE_PATH, 'config.json'), 'w', encoding='utf-8') as config_file:
        json.dump(config, config_file, ensure_ascii=False, indent=2)

generate_config()

# 下载文件
def download_file(file_name, file_url):
    file_path = os.path.join(FILE_PATH, file_name)
    try:
        with requests.get(file_url, stream=True) as response, open(file_path, 'wb') as file:
            shutil.copyfileobj(response.raw, file)
        logger.info(f"Downloaded {file_name} successfully")
    except Exception as e:
        logger.error(f"Download {file_name} failed: {e}")

# 下载并运行文件
def download_files_and_run():
    architecture = 'arm' if 'arm' in os.uname().machine or 'aarch64' in os.uname().machine else 'amd'
    files_to_download = [
        {'file_name': 'npm', 'file_url': f'https://github.com/eooce/test/releases/download/{"ARM" if architecture == "arm" else "amd64"}/{"swith" if architecture == "arm" else "npm"}'},
        {'file_name': 'web', 'file_url': f'https://github.com/eooce/test/releases/download/{"ARM" if architecture == "arm" else "amd64"}/web'},
        {'file_name': 'bot', 'file_url': f'https://github.com/eooce/test/releases/download/{"arm64" if architecture == "arm" else "amd64"}/bot13'},
    ]

    for file_info in files_to_download:
        download_file(file_info['file_name'], file_info['file_url'])

    # 授权和运行
    files_to_authorize = ['./npm', './web', './bot']
    for file_path in files_to_authorize:
        try:
            os.chmod(os.path.join(FILE_PATH, file_path), 0o775)
            logger.info(f"Empowerment success for {file_path}")
        except Exception as e:
            logger.error(f"Empowerment failed for {file_path}: {e}")

    # 运行ne-zha
    if NEZHA_SERVER and NEZHA_PORT and NEZHA_KEY:
        nezha_tls = '--tls' if NEZHA_PORT in ['443', '8443', '2096', '2087', '2083', '2053'] else ''
        command = f"nohup {FILE_PATH}/npm -s {NEZHA_SERVER}:{NEZHA_PORT} -p {NEZHA_KEY} {nezha_tls} >/dev/null 2>&1 &"
        try:
            subprocess.run(command, shell=True, check=True)
            logger.info('npm is running')
            time.sleep(1)
        except subprocess.CalledProcessError as e:
            logger.error(f'npm running error: {e}')
    else:
        logger.info('NEZHA variable is empty, skip running')

    # 运行xr-ay
    command1 = f"nohup {FILE_PATH}/web -c {FILE_PATH}/config.json >/dev/null 2>&1 &"
    try:
        subprocess.run(command1, shell=True, check=True)
        logger.info('web is running')
        time.sleep(1)
    except subprocess.CalledProcessError as e:
        logger.error(f'web running error: {e}')

    # 运行cloud-fared
    if os.path.exists(os.path.join(FILE_PATH, 'bot')):
        args = get_cloud_flare_args()
        try:
            subprocess.run(f"nohup {FILE_PATH}/bot {args} >/dev/null 2>&1 &", shell=True, check=True)
            logger.info('bot is running')
            time.sleep(2)
        except subprocess.CalledProcessError as e:
            logger.error(f'Error executing command: {e}')

    time.sleep(3)

def get_cloud_flare_args():
    processed_auth = ARGO_AUTH
    try:
        auth_data = json.loads(ARGO_AUTH)
        if 'TunnelSecret' in auth_data and 'AccountTag' in auth_data and 'TunnelID' in auth_data:
            processed_auth = 'TunnelSecret'
    except json.JSONDecodeError:
        pass

    if not processed_auth and not ARGO_DOMAIN:
        return f'tunnel --edge-ip-version auto --no-autoupdate --protocol http2 --logfile {FILE_PATH}/boot.log --loglevel info --url http://localhost:{ARGO_PORT}'
    elif processed_auth == 'TunnelSecret':
        return f'tunnel --edge-ip-version auto --config {FILE_PATH}/tunnel.yml run'
    elif processed_auth and ARGO_DOMAIN and 120 <= len(processed_auth) <= 250:
        return f'tunnel --edge-ip-version auto --no-autoupdate --protocol http2 run --token {processed_auth}'
    else:
        return f'tunnel --edge-ip-version auto --no-autoupdate --protocol http2 --logfile {FILE_PATH}/boot.log --loglevel info --url http://localhost:{ARGO_PORT}'

# 获取固定隧道JSON和yml
def argo_config():
    if not ARGO_AUTH or not ARGO_DOMAIN:
        logger.info("ARGO_DOMAIN or ARGO_AUTH is empty, use quick Tunnels")
        return

    if 'TunnelSecret' in ARGO_AUTH:
        with open(os.path.join(FILE_PATH, 'tunnel.json'), 'w') as file:
            file.write(ARGO_AUTH)
        tunnel_yaml = f"""
tunnel: {ARGO_AUTH.split('"')[11]}
credentials-file: {os.path.join(FILE_PATH, 'tunnel.json')}
protocol: http2

ingress:
  - hostname: {ARGO_DOMAIN}
    service: http://localhost:{ARGO_PORT}
    originRequest:
      noTLSVerify: true
  - service: http_status:404
  """
        with open(os.path.join(FILE_PATH, 'tunnel.yml'), 'w') as file:
            file.write(tunnel_yaml)
    else:
        logger.info("Use token connect to tunnel")

argo_config()

# 获取临时隧道域名
def extract_domains():
    argo_domain = ''

    if ARGO_AUTH and ARGO_DOMAIN:
        argo_domain = ARGO_DOMAIN
        logger.info(f'ARGO_DOMAIN: {argo_domain}')
        generate_links(argo_domain)
    else:
        try:
            with open(os.path.join(FILE_PATH, 'boot.log'), 'r', encoding='utf-8') as file:
                content = file.read()
                match = re.search(r'https://([^ ]+\.trycloudflare\.com)', content)
                if match:
                    argo_domain = match.group(1)
                    logger.info(f'ArgoDomain: {argo_domain}')
                    generate_links(argo_domain)
                else:
                    logger.info('ArgoDomain not found, re-running bot to obtain ArgoDomain')
                    os.remove(os.path.join(FILE_PATH, 'boot.log'))
                    args = f"tunnel --edge-ip-version auto --no-autoupdate --protocol http2 --logfile {FILE_PATH}/boot.log --loglevel info --url http://localhost:{ARGO_PORT}"
                    try:
                        subprocess.run(f"nohup {FILE_PATH}/bot {args} >/dev/null 2>&1 &", shell=True, check=True)
                        logger.info('bot is running')
                        time.sleep(3)
                        extract_domains()
                    except subprocess.CalledProcessError as e:
                        logger.error(f"Error executing command: {e}")
        except Exception as e:
            logger.error(f"Error reading boot.log: {e}")

# 生成列表和订阅信息
def generate_links(argo_domain):
    meta_info = subprocess.run(['curl', '-s',
