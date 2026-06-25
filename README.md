# MentoHUST Win Modern

`MentoHUST Win Modern` 是一个面向 Windows 的锐捷有线 802.1X 认证客户端重制项目。仓库里同时保留了 OpenWrt 参考实现以及当前维护中的现代 GUI 版本，方便对照、兼容和后续开源整理。

使用 Codex App 辅助开发。

![image-20260625210041114](C:\Users\HL\Desktop\mentohust-win-modern\image-20260625210041114.png)

## 仓库结构

- `mentohust-modern/`：当前主力开发目录，包含 Python GUI、认证逻辑、测试和打包脚本。
- `MentoHUST-OpenWrt-ipk/`：[OpenWrt 版本源码](https://github.com/KyleRicardo/MentoHUST-OpenWrt-ipk)，主要作为协议与配置参考。
- `Ruijie Supplicant/`：锐捷官方客户端参考文件，仅用于兼容性分析和版本校验。

## 快速开始

安装开发环境：

```powershell
.\.venv\Scripts\python.exe -m pip install -e .\mentohust-modern
```

运行 GUI：

```powershell
.\.venv\Scripts\mentohust-win-modern.exe
```

运行测试：

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s .\mentohust-modern\tests -t .\mentohust-modern
```

**构建 Release 版本**

```powershell
.\mentohust-modern\tools\build_exe.ps1
```



## 关键配置说明

- `官方 8021x.exe`：填写锐捷官方客户端目录中的 `8021x.exe` 路径。
- `客户端版本`：填写 `8021x.exe` 的文件版本号，在文件属性里可以看到，例如 `5.00`。
- `DHCP 模式`：
  - `0`：不使用 DHCP 流程。
  - `1`：二次认证时执行 DHCP。
  - `2`：认证成功后执行 DHCP。
  - `3`：认证前先执行 DHCP。
- `DHCP 命令`：默认是 `ipconfig /renew`，也可以按校园网环境自行调整。

## 运行要求

- Windows 管理员权限
- 已安装 `Npcap`
- 可用的锐捷校园网账号
- 可访问的官方 `8021x.exe` 参考文件

## 其他说明

- 程序默认把配置和日志存放到 `%LOCALAPPDATA%\MentoHUST Win Modern\`。
- 已支持托盘最小化、自动保存配置、启动时自动连接、滚动日志。
- 本地账号配置、日志和构建产物已在 `.gitignore` 中排除。
