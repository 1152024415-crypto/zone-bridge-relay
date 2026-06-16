"""
跨区连通性测试客户端
用法: python test.py <zone> <url> [size_kb]

示例:
  python test.py blue http://localhost:8765/health        # 测试黄区→蓝区
  python test.py yellow http://内网地址:8766/health       # 测试蓝区→黄区
  python test.py yellow http://内网地址:8766/size/30      # 测试蓝区→黄区 30KB
  python test.py yellow http://内网地址:8766/size/60      # 测试蓝区→黄区 60KB（应该超限）
"""

import sys
import urllib.request
import urllib.error
import time
import json

def test_connectivity(zone, url, size_kb=None):
    """测试连通性"""
    print(f'{"="*60}')
    print(f'测试方向: 本区 → {zone}区')
    print(f'目标 URL: {url}')
    if size_kb:
        print(f'请求大小: {size_kb} KB')
    print(f'{"="*60}')
    
    start = time.time()
    try:
        req = urllib.request.Request(url)
        req.add_header('User-Agent', 'ZoneBridge-Test/1.0')
        
        response = urllib.request.urlopen(req, timeout=10)
        elapsed = time.time() - start
        
        # 读取响应
        data = response.read()
        content_type = response.headers.get('Content-Type', 'unknown')
        
        print(f'')
        print(f'✅ 连接成功!')
        print(f'  HTTP 状态: {response.status}')
        print(f'  Content-Type: {content_type}')
        print(f'  响应大小: {len(data)} bytes ({len(data)/1024:.2f} KB)')
        print(f'  耗时: {elapsed*1000:.0f} ms')
        print(f'')
        
        # 尝试解析 JSON
        try:
            json_data = json.loads(data)
            print(f'  响应内容 (JSON):')
            # 如果 data 字段太大，截断显示
            if 'data' in json_data and len(json_data.get('data', '')) > 100:
                json_data['data'] = json_data['data'][:50] + '...[截断]'
            print(f'    {json.dumps(json_data, ensure_ascii=False, indent=2)}')
        except json.JSONDecodeError:
            # 显示前 200 字符
            text = data.decode('utf-8', errors='replace')
            if len(text) > 200:
                text = text[:200] + '...[截断]'
            print(f'  响应内容 (Text): {text}')
        
        return True
        
    except urllib.error.HTTPError as e:
        elapsed = time.time() - start
        print(f'')
        print(f'❌ HTTP 错误!')
        print(f'  状态码: {e.code}')
        print(f'  原因: {e.reason}')
        print(f'  耗时: {elapsed*1000:.0f} ms')
        return False
        
    except urllib.error.URLError as e:
        elapsed = time.time() - start
        print(f'')
        print(f'❌ 连接失败!')
        print(f'  错误: {e.reason}')
        print(f'  耗时: {elapsed*1000:.0f} ms')
        print(f'')
        print(f'可能原因:')
        print(f'  - 目标服务器未启动')
        print(f'  - 防火墙阻止连接')
        print(f'  - URL 地址错误')
        print(f'  - 网关/代理未配置')
        return False
        
    except Exception as e:
        elapsed = time.time() - start
        print(f'')
        print(f'❌ 未知错误!')
        print(f'  {type(e).__name__}: {e}')
        print(f'  耗时: {elapsed*1000:.0f} ms')
        return False

def main():
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)
    
    zone = sys.argv[1].lower()
    url = sys.argv[2]
    size_kb = int(sys.argv[3]) if len(sys.argv) > 3 else None
    
    if zone not in ('blue', 'yellow'):
        print(f'错误: zone 必须是 blue 或 yellow，当前: {zone}')
        sys.exit(1)
    
    test_connectivity(zone, url, size_kb)

if __name__ == '__main__':
    main()
