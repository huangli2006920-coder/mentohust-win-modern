# MentoHUST Win Modern 子项目说明

这个子项目是当前维护中的 Windows GUI 客户端实现。它复用了 `MentoHUST-OpenWrt-ipk` 的认证流程，使用 `Npcap + Scapy` 进行二层 EAPOL 抓发，并提供托盘、自动保存、日志和打包脚本。

## 开发与运行

安装可编辑包：

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e .\mentohust-modern[build]
```

从虚拟环境启动 GUI：

```powershell
.\.venv\Scripts\mentohust-win-modern.exe
```

运行测试：

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s .\mentohust-modern\tests -t .\mentohust-modern
```

## 打包

构建可分发版本：

```powershell
pwsh.exe -File .\mentohust-modern\tools\build_exe.ps1
```

默认输出目录：

```text
dist\MentoHUST Win Modern\
```

构建脚本会自动使用仓库根目录下独立的 `.build-venv/`；如果发现它不可用或引用了其他机器上的 Python，会自动重建后再执行打包。

## 配置说明

- `官方 8021x.exe`：应指向锐捷官方客户端安装目录中的 `8021x.exe`。
- `客户端版本`：填写对应 `8021x.exe` 的文件版本号，可在 Windows 文件属性中查看。
- `DHCP 模式`：
  - `0`：不使用 DHCP。
  - `1`：二次认证时执行 DHCP。
  - `2`：认证成功后执行 DHCP。
  - `3`：认证前执行 DHCP。

## 运行注意事项

- 程序启动时会请求管理员权限。
- 连接前需要先安装 `Npcap`。
- 官方 `Ruijie Supplicant\8021x.exe` 仅作为兼容性参考文件。
- 发布 `--onedir` 版本时，请分发整个 `dist\MentoHUST Win Modern\` 目录。
- 建议在一台未安装 Python 的 Windows 机器上验证发布包是否能正常启动。
- 像 `hlaccount.json`、`.venv/` 和 `.build-venv/` 这样的本地文件不应提交到仓库。
