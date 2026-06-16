"""
蓝区 HTTP Server - 供黄区测试连通性
启动: python server.py [port]
默认端口: 8765
"""

import http.server
import socketserver
import sys
import json
from datetime import datetime

PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8765

class BlueZoneHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        # 基础健康检查
        if self.path == '/health':
            response = {
                'zone': 'blue',
                'status': 'ok',
                'timestamp': datetime.now().isoformat(),
                'server': 'blue-zone-test-server'
            }
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(response).encode('utf-8'))
        
        # 测试响应大小 - 返回指定 KB 的数据
        elif self.path.startswith('/size/'):
            try:
                kb = int(self.path.split('/')[2])
                # 生成指定大小的文本数据
                data = 'x' * (kb * 1024)
                response = {
                    'zone': 'blue',
                    'size_kb': kb,
                    'data': data
                }
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps(response).encode('utf-8'))
            except (ValueError, IndexError):
                self.send_error(400, 'Invalid size parameter')
        
        # 默认首页
        else:
            response = {
                'zone': 'blue',
                'message': '蓝区测试服务器已运行',
                'endpoints': [
                    '/health - 健康检查',
                    '/size/<kb> - 返回指定 KB 大小的数据',
                ],
                'timestamp': datetime.now().isoformat()
            }
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(response, ensure_ascii=False).encode('utf-8'))

    def do_POST(self):
        # 接收数据并回显
        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length) if content_length > 0 else b''
        
        response = {
            'zone': 'blue',
            'received_bytes': len(post_data),
            'received_size_kb': len(post_data) / 1024,
            'timestamp': datetime.now().isoformat()
        }
        
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(response).encode('utf-8'))

if __name__ == '__main__':
    with socketserver.TCPServer(('0.0.0.0', PORT), BlueZoneHandler) as httpd:
        print(f'蓝区服务器启动在端口 {PORT}')
        print(f'访问 http://localhost:{PORT}/health 测试')
        httpd.serve_forever()
