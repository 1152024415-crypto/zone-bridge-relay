"""
Zone Bridge Client - 跨区通信客户端
蓝区和黄区都用这个脚本，通过 GitHub 仓库做中继。

用法:
  python client.py send <to_zone> <message>     发送消息
  python client.py recv [from_zone]             接收消息
  python client.py ping                         发送 ping
  python client.py listen                       持续监听新消息
  python client.py status                       查看双方状态

环境变量:
  GITHUB_TOKEN  - GitHub Personal Access Token (必需)
  ZONE          - 本区标识: blue 或 yellow (必需)
"""

import os
import sys
import json
import base64
import time
import urllib.request
import urllib.error
from datetime import datetime

# ============ 配置 ============
REPO = '1152024415-crypto/zone-bridge-relay'
FILE_PATH = 'messages.json'
API_BASE = f'https://api.github.com/repos/{REPO}/contents/{FILE_PATH}'
# ==============================

def get_token():
    token = os.environ.get('GITHUB_TOKEN')
    if not token:
        print('错误: 请设置环境变量 GITHUB_TOKEN')
        sys.exit(1)
    return token

def get_zone():
    zone = os.environ.get('ZONE', '').lower()
    if zone not in ('blue', 'yellow'):
        print('错误: 请设置环境变量 ZONE=blue 或 ZONE=yellow')
        sys.exit(1)
    return zone

def api_request(url, token, method='GET', data=None):
    headers = {
        'Authorization': f'token {token}',
        'Accept': 'application/vnd.github.v3+json',
        'Content-Type': 'application/json'
    }
    req = urllib.request.Request(url, headers=headers, method=method, data=data)
    try:
        response = urllib.request.urlopen(req, timeout=30)
        return json.loads(response.read())
    except urllib.error.HTTPError as e:
        error_body = e.read().decode('utf-8', errors='replace')
        print(f'API 错误 {e.code}: {e.reason}')
        print(f'详情: {error_body[:200]}')
        sys.exit(1)

def read_messages(token):
    """读取当前消息文件"""
    file_data = api_request(API_BASE, token)
    sha = file_data['sha']
    content = base64.b64decode(file_data['content']).decode('utf-8')
    messages = json.loads(content)
    return messages, sha

def write_messages(token, messages, sha, commit_msg):
    """写入消息文件"""
    content = json.dumps(messages, indent=2, ensure_ascii=False)
    content_b64 = base64.b64encode(content.encode('utf-8')).decode('utf-8')
    body = json.dumps({
        "message": commit_msg,
        "content": content_b64,
        "sha": sha
    }).encode('utf-8')
    return api_request(API_BASE, token, method='PUT', data=body)

def cmd_send(token, zone, to_zone, message_text):
    """发送消息"""
    messages, sha = read_messages(token)
    
    # 更新本区状态
    messages['zones'][zone]['status'] = 'online'
    messages['zones'][zone]['last_seen'] = datetime.now().isoformat()
    
    # 添加消息
    msg_id = max((m.get('id', 0) for m in messages['messages']), default=0) + 1
    messages['messages'].append({
        "id": msg_id,
        "from": zone,
        "to": to_zone,
        "type": "message",
        "data": message_text,
        "timestamp": datetime.now().isoformat()
    })
    
    write_messages(token, messages, sha, f'{zone} → {to_zone}: {message_text[:30]}')
    print(f'✅ 消息已发送 (id={msg_id})')

def cmd_recv(token, zone, from_zone=None):
    """接收消息"""
    messages, _ = read_messages(token)
    
    # 过滤发给本区的消息
    my_messages = [m for m in messages['messages'] if m.get('to') == zone]
    if from_zone:
        my_messages = [m for m in my_messages if m.get('from') == from_zone]
    
    if not my_messages:
        print('没有新消息')
        return
    
    print(f'收到 {len(my_messages)} 条消息:\n')
    for m in my_messages:
        ts = m.get('timestamp', '?')[:19]
        print(f'  [{ts}] {m["from"]} → {m["to"]} ({m["type"]}):')
        print(f'    {m["data"]}')
        print()

def cmd_ping(token, zone):
    """发送 ping"""
    messages, sha = read_messages(token)
    
    messages['zones'][zone]['status'] = 'online'
    messages['zones'][zone]['last_seen'] = datetime.now().isoformat()
    
    msg_id = max((m.get('id', 0) for m in messages['messages']), default=0) + 1
    messages['messages'].append({
        "id": msg_id,
        "from": zone,
        "to": "all",
        "type": "ping",
        "data": f'{zone} zone is alive',
        "timestamp": datetime.now().isoformat()
    })
    
    write_messages(token, messages, sha, f'{zone}: ping')
    print(f'🏓 Ping 已发送!')

def cmd_status(token, zone):
    """查看状态"""
    messages, _ = read_messages(token)
    
    print('Zone Bridge 状态:')
    print('=' * 40)
    for z, info in messages['zones'].items():
        marker = ' ← 本区' if z == zone else ''
        status = info.get('status', 'unknown')
        last = info.get('last_seen', 'never')
        if last and last != 'None':
            last = last[:19]
        print(f'  {z:8s} | {status:8s} | last seen: {last}{marker}')
    
    print(f'\n消息总数: {len(messages["messages"])}')

def cmd_listen(token, zone, interval=5):
    """持续监听"""
    print(f'开始监听 (每 {interval} 秒轮询)... Ctrl+C 退出\n')
    last_count = 0
    try:
        while True:
            messages, _ = read_messages(token)
            my_messages = [m for m in messages['messages'] if m.get('to') in (zone, 'all')]
            
            new_messages = my_messages[last_count:]
            if new_messages:
                for m in new_messages:
                    ts = m.get('timestamp', '?')[:19]
                    print(f'[{ts}] {m["from"]} ({m["type"]}): {m["data"]}')
                last_count = len(my_messages)
            
            time.sleep(interval)
    except KeyboardInterrupt:
        print('\n停止监听')

def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    
    token = get_token()
    zone = get_zone()
    cmd = sys.argv[1].lower()
    
    if cmd == 'send':
        if len(sys.argv) < 4:
            print('用法: client.py send <to_zone> <message>')
            sys.exit(1)
        cmd_send(token, zone, sys.argv[2], sys.argv[3])
    
    elif cmd == 'recv':
        from_zone = sys.argv[2] if len(sys.argv) > 2 else None
        cmd_recv(token, zone, from_zone)
    
    elif cmd == 'ping':
        cmd_ping(token, zone)
    
    elif cmd == 'status':
        cmd_status(token, zone)
    
    elif cmd == 'listen':
        interval = int(sys.argv[2]) if len(sys.argv) > 2 else 5
        cmd_listen(token, zone, interval)
    
    else:
        print(f'未知命令: {cmd}')
        print(__doc__)
        sys.exit(1)

if __name__ == '__main__':
    main()
