# 快速开始

## 当前状态
- ✅ 项目已创建: D:\proj\zone-bridge
- ✅ 蓝区服务器代码已就绪
- ✅ 黄区服务器代码已就绪  
- ✅ 测试客户端已就绪

## 实验步骤

### 实验 1: 黄区 → 蓝区 (应该没限制)

**1. 启动蓝区服务器 (在蓝区机器上运行):**
```bash
cd D:\proj\zone-bridge\blue_server
python server.py
```
服务器会启动在端口 8765

**2. 在黄区机器上测试:**
```bash
# 健康检查
python D:\proj\zone-bridge\client\test.py blue http://<蓝区IP>:8765/health

# 测试不同大小
python D:\proj\zone-bridge\client\test.py blue http://<蓝区IP>:8765/size/30
python D:\proj\zone-bridge\client\test.py blue http://<蓝区IP>:8765/size/100
```

### 实验 2: 蓝区 → 黄区 (验证 50KB 限制)

**1. 启动黄区服务器 (在黄区机器上运行):**
```bash
cd D:\proj\zone-bridge\yellow_server  
python server.py
```
服务器会启动在端口 8766

**2. 告诉我黄区的访问地址** (通过网关的 URL 或 IP:端口)

**3. 在蓝区测试:**
```bash
python D:\proj\zone-bridge\client\test_sizes.py http://<黄区地址>:8766
```

这会测试 1KB, 5KB, 10KB, ..., 100KB 等不同大小，找出真正的限制点。

## 文件说明

- `blue_server/server.py` - 蓝区服务器，端口 8765
- `yellow_server/server.py` - 黄区服务器，端口 8766
- `client/test.py` - 单次连通性测试
- `client/test_sizes.py` - 批量大小测试（验证 50KB 限制）

## 下一步

完成实验后，我们会知道：
1. 黄区能否访问蓝区 ✅
2. 蓝区能否访问黄区
3. 50KB 限制是否真实存在
4. 实际的临界点是多少 KB

然后我们可以设计真正的跨区 Agent 通信协议。
