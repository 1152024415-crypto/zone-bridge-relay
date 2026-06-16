"""
黄区 HTTP Server - 供蓝区测试连通性
启动: python server.py [port]
默认端口: 8766

注意：这个服务器跑在黄区（公司内网），蓝区通过网关访问时会受到 50KB 限制
"""

import http.server
import socketserver
import sys
import json
from datetime import datetime

PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8766

class YellowZoneHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        # 基础健康检查 - 返回很小的响应
        if self.path == '/health':
            response = {
                'zone': 'yellow',
                'status': 'ok',
                'timestamp': datetime.now().isoformat(),
                'server': 'yellow-zone-test-server'
            }
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(response).encode('utf-8'))
        
        # 测试响应大小 - 用于验证 50KB 限制
        elif self.path.startswith('/size/'):
            try:
                kb = int(self.path.split('/')[2])
                data = 'y' * (kb * 1024)
                response = {
                    'zone': 'yellow',
                    'requested_size_kb': kb,
                    'data': data
                }
                body = json.dumps(response).encode('utf-8')
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.send_header('X-Actual-Size', str(len(body)))
                self.end_headers()
                self.wfile.write(body)
                print(f'  → 返回 {len(body)} bytes ({len(body)/1024:.1f} KB)')
            except (ValueError, IndexError):
                self.send_error(400, 'Invalid size parameter')
        
        # Agent 模拟端点 - 返回中等大小的数据
        elif self.path == '/agent/info':
            response = {
                'zone': 'yellow',
                'agent': 'yellow-zone-agent',
                'capabilities': ['code-review', 'internal-docs', 'build'],
                'description': '黄区内部 Agent，可访问公司内部资源',
                'timestamp': datetime.now().isoformat()
            }
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(response, ensure_ascii=False).encode('utf-8'))
        
        # 默认首页
        else:
            response = {
                'zone': 'yellow',
                'message': '黄区测试服务器已运行',
                'endpoints': [
                    '/health - 健康检查（小响应）',
                    '/size/<kb> - 返回指定 KB 大小的数据（测试限制）',
                    '/agent/info - Agent 信息',
                ],
                'timestamp': datetime.now().isoformat()
            }
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(response, ensure_ascii=False).encode('utf-8'))

    def do_POST(self):
        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length) if content_length > 0 else b''
        
        response = {
            'zone': 'yellow',
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
    with socketserver.TCPServer(('0.0.0.0', PORT), YellowZoneHandler) as httpd:
        print(f'黄区服务器启动在端口 {PORT}')
        print(f'访问 http://localhost:{PORT}/health 测试')
        httpd.serve_forever()
