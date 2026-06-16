"""
批量测试不同大小的响应 - 专门用于验证蓝区→黄区的 50KB 限制
用法: python test_sizes.py <base_url>

示例:
  python test_sizes.py http://黄区地址:8766
"""

import sys
import urllib.request
import urllib.error

def test_size(base_url, kb):
    url = f'{base_url}/size/{kb}'
    try:
        req = urllib.request.Request(url)
        response = urllib.request.urlopen(req, timeout=15)
        data = response.read()
        actual_kb = len(data) / 1024
        print(f'  ✅ {kb:3d} KB → 收到 {actual_kb:7.2f} KB')
        return True
    except urllib.error.HTTPError as e:
        print(f'  ❌ {kb:3d} KB → HTTP {e.code}')
        return False
    except urllib.error.URLError as e:
        print(f'  ❌ {kb:3d} KB → 连接失败: {e.reason}')
        return False
    except Exception as e:
        print(f'  ❌ {kb:3d} KB → {type(e).__name__}: {e}')
        return False

def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    
    base_url = sys.argv[1].rstrip('/')
    
    print(f'测试基础 URL: {base_url}')
    print(f'')
    print(f'测试不同响应大小:')
    
    sizes = [1, 5, 10, 20, 30, 40, 45, 48, 49, 50, 51, 52, 55, 60, 80, 100]
    
    results = []
    for kb in sizes:
        success = test_size(base_url, kb)
        results.append((kb, success))
    
    print(f'')
    print(f'结果汇总:')
    print(f'  成功: {sum(1 for _, s in results if s)}/{len(results)}')
    
    # 找到临界点
    failed = [kb for kb, s in results if not s]
    if failed:
        first_fail = min(failed)
        print(f'  首次失败: {first_fail} KB')
        success_before = [kb for kb, s in results if s and kb < first_fail]
        if success_before:
            print(f'  最大成功: {max(success_before)} KB')

if __name__ == '__main__':
    main()
