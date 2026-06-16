"""
Zone Bridge Client - 跨区通信客户端（简化版）
蓝区和黄区都用这个脚本，通过 GitHub 仓库做中继。

用法:
  python client.py send <to_zone> <message>     发送消息
  python client.py recv [from_zone]             接收消息（读公开仓库，不需要 token）
  python client.py ping                         发送 ping
  python client.py listen                       持续监听新消息
  python client.py status                       查看双方状态

配置文件:
  首次运行时会自动创建 config.json，你只需要填 zone 和 token。
  token 只在 send/ping/listen 时需要，recv/status 读公开仓库不需要。
"""

import os
import sys
import json
import base64
import time
import urllib.request
import urllib.error
from datetime import datetime
from pathlib import Path

# ============ 默认配置 ============
DEFAULT_CONFIG = {
    "repo": "1152024415-crypto/zone-bridge-relay",
    "zone": "yellow",
    "token": ""
}

CONFIG_FILE = Path(__file__).parent / "config.json"
# ==================================

def load_config():
    """加载配置，首次运行自动创建"""
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            config = json.load(f)
    else:
        config = DEFAULT_CONFIG.copy()
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        print(f'首次运行，已创建配置文件: {CONFIG_FILE}')
        print(f'请编辑 config.json，设置你的 zone (blue/yellow) 和 token')
        print(f'recv 不需要 token，可以先用 recv 测试')
    return config

def get_config():
    config = load_config()
    return config

def api_get(url, token=None):
    """GET 请求（公开仓库不需要 token）"""
    headers = {'Accept': 'application/vnd.github.v3+json'}
    if token:
        headers['Authorization'] = f'token {token}'
    req = urllib.request.Request(url, headers=headers)
    try:
        response = urllib.request.urlopen(req, timeout=30)
        return json.loads(response.read())
    except urllib.error.HTTPError as e:
        error_body = e.read().decode('utf-8', errors='replace')[:200]
        print(f'API 错误 {e.code}: {e.reason}')
        print(f'详情: {error_body}')
        sys.exit(1)

def api_put(url, token, data):
    """PUT 请求（需要 token）"""
    if not token:
        print('错误: 发送消息需要 token，请在 config.json 中设置 token')
        sys.exit(1)
    headers = {
        'Authorization': f'token {token}',
        'Accept': 'application/vnd.github.v3+json',
        'Content-Type': 'application/json'
    }
    req = urllib.request.Request(url, headers=headers, method='PUT', data=data)
    try:
        response = urllib.request.urlopen(req, timeout=30)
        return json.loads(response.read())
    except urllib.error.HTTPError as e:
        error_body = e.read().decode('utf-8', errors='replace')[:200]
        print(f'API 错误 {e.code}: {e.reason}')
        print(f'详情: {error_body}')
        sys.exit(1)

def read_messages(config):
    """读取消息文件（不需要 token）"""
    url = f'https://api.github.com/repos/{config["repo"]}/contents/messages.json'
    file_data = api_get(url, config.get('token'))
    sha = file_data['sha']
    content = base64.b64decode(file_data['content']).decode('utf-8')
    messages = json.loads(content)
    return messages, sha

def write_messages(config, messages, sha, commit_msg):
    """写入消息文件（需要 token）"""
    url = f'https://api.github.com/repos/{config["repo"]}/contents/messages.json'
    content = json.dumps(messages, indent=2, ensure_ascii=False)
    content_b64 = base64.b64encode(content.encode('utf-8')).decode('utf-8')
    body = json.dumps({
        "message": commit_msg,
        "content": content_b64,
        "sha": sha
    }).encode('utf-8')
    return api_put(url, config.get('token'), body)

def cmd_send(config, to_zone, message_text):
    """发送消息"""
    zone = config['zone']
    messages, sha = read_messages(config)
    
    messages['zones'][zone]['status'] = 'online'
    messages['zones'][zone]['last_seen'] = datetime.now().isoformat()
    
    msg_id = max((m.get('id', 0) for m in messages['messages']), default=0) + 1
    messages['messages'].append({
        "id": msg_id,
        "from": zone,
        "to": to_zone,
        "type": "message",
        "data": message_text,
        "timestamp": datetime.now().isoformat()
    })
    
    write_messages(config, messages, sha, f'{zone} → {to_zone}: {message_text[:30]}')
    print(f'✅ 消息已发送 (id={msg_id})')

def cmd_recv(config, from_zone=None):
    """接收消息（不需要 token）"""
    zone = config['zone']
    messages, _ = read_messages(config)
    
    my_messages = [m for m in messages['messages'] if m.get('to') in (zone, 'all')]
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

def cmd_ping(config):
    """发送 ping"""
    zone = config['zone']
    messages, sha = read_messages(config)
    
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
    
    write_messages(config, messages, sha, f'{zone}: ping')
    print(f'🏓 Ping 已发送!')

def cmd_status(config):
    """查看状态（不需要 token）"""
    messages, _ = read_messages(config)
    zone = config['zone']
    
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

def cmd_listen(config, interval=5):
    """持续监听（不需要 token）"""
    zone = config['zone']
    print(f'开始监听 (每 {interval} 秒轮询)... Ctrl+C 退出\n')
    last_count = 0
    try:
        while True:
            messages, _ = read_messages(config)
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
    
    config = get_config()
    cmd = sys.argv[1].lower()
    
    if cmd == 'send':
        if len(sys.argv) < 4:
            print('用法: client.py send <to_zone> <message>')
            sys.exit(1)
        cmd_send(config, sys.argv[2], sys.argv[3])
    
    elif cmd == 'recv':
        from_zone = sys.argv[2] if len(sys.argv) > 2 else None
        cmd_recv(config, from_zone)
    
    elif cmd == 'ping':
        cmd_ping(config)
    
    elif cmd == 'status':
        cmd_status(config)
    
    elif cmd == 'listen':
        interval = int(sys.argv[2]) if len(sys.argv) > 2 else 5
        cmd_listen(config, interval)
    
    else:
        print(f'未知命令: {cmd}')
        print(__doc__)
        sys.exit(1)

if __name__ == '__main__':
    main()
