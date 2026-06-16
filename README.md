# Zone Bridge

跨区通信工具，通过 GitHub 仓库做中继，绕过蓝区→黄区的 50KB 限制。

## 文件说明

- `client.py` - 通信客户端（蓝区黄区都用同一个）
- `config.json` - 配置文件（两边 zone 不同）

## 使用方法

### 黄区

```bash
git clone https://github.com/1152024415-crypto/zone-bridge-relay.git
cd zone-bridge-relay

# config.json 已经是 zone=yellow，直接用
python client.py recv          # 读消息（不需要 token）
python client.py status        # 查看状态

# 发消息需要 token，编辑 config.json 填上
python client.py send blue "黄区收到！"
```

### 蓝区

```bash
# 编辑 config.json，把 zone 改成 "blue"
# 填上 token

python client.py recv
python client.py send yellow "蓝区发消息"
```

## 命令

- `recv` - 接收消息（不需要 token）
- `send <zone> <msg>` - 发送消息（需要 token）
- `status` - 查看状态（不需要 token）
- `ping` - 发送 ping（需要 token）
- `listen` - 持续监听（不需要 token）
