from __future__ import annotations

import os
import queue
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext

from PIL import Image, ImageTk
import ttkbootstrap as ttk

from . import APP_VERSION
from .app_paths import APP_DIR_NAME, asset_path, default_log_path, default_profile_path, ensure_app_dirs
from .client import MentohustClient
from .config import MentohustConfig, default_client_exe
from .interfaces import has_active_wifi_connection, list_interfaces
from .logging_utils import get_logger
from .openwrt import load_openwrt_config_file
from .runtime_checks import validation_errors
from .tray import TrayController
from .windows import apply_window_icons, destroy_icon_handles


class MentohustApp(ttk.Window):
    def __init__(self) -> None:
        super().__init__(themename="flatly")
        ensure_app_dirs()
        self.title(APP_DIR_NAME)
        self.geometry("1120x880")
        self.minsize(1000, 760)
        self.logger = get_logger("gui")
        self.profile_path = default_profile_path()
        self.log_path = default_log_path()
        self.client: MentohustClient | None = None
        self.interfaces = []
        self._auto_save_job: str | None = None
        self._is_exiting = False
        self._has_hidden_notice = False
        self._auto_connect_requested = False
        self._password_visible = False
        self._native_icon_handles: list[int] = []
        self._window_icons: list[ImageTk.PhotoImage] = []
        self.ui_queue: queue.Queue[tuple[str, str]] = queue.Queue()
        self.status_var = tk.StringVar(value="未连接")
        self.form_vars = {
            "username": tk.StringVar(),
            "password": tk.StringVar(),
            "interface": tk.StringVar(),
            "ipaddr": tk.StringVar(value="0.0.0.0"),
            "gateway": tk.StringVar(value="0.0.0.0"),
            "mask": tk.StringVar(value="255.255.255.0"),
            "dns": tk.StringVar(value="0.0.0.0"),
            "ping": tk.StringVar(value="0.0.0.0"),
            "timeout": tk.StringVar(value="8"),
            "interval": tk.StringVar(value="30"),
            "wait": tk.StringVar(value="15"),
            "fail_number": tk.StringVar(value="0"),
            "multicast_address": tk.StringVar(value="1"),
            "dhcp_mode": tk.StringVar(value="2"),
            "dhcp_script": tk.StringVar(value="ipconfig /renew"),
            "version": tk.StringVar(value="5.00"),
            "client_exe": tk.StringVar(value=default_client_exe()),
        }
        self.enable_var = tk.BooleanVar(value=True)
        self.auto_connect_var = tk.BooleanVar(value=False)
        self.tray = TrayController(
            asset_path("app-icon.png"),
            app_name=APP_DIR_NAME,
            on_show=lambda: self.after(0, self._restore_from_tray),
            on_exit=lambda: self.after(0, self._exit_application),
        )
        self._build()
        self._set_window_icon()
        self._refresh_interfaces()
        self._bind_auto_save()
        self._load_default_profile()
        self.tray.start()
        self.after(100, self._drain_ui_queue)
        self.after(300, self._maybe_auto_connect)
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _build(self) -> None:
        root = ttk.Frame(self, padding=16)
        root.pack(fill=tk.BOTH, expand=True)

        header = ttk.Frame(root)
        header.pack(fill=tk.X, pady=(0, 12))
        title_group = ttk.Frame(header)
        title_group.pack(side=tk.LEFT)
        ttk.Label(title_group, text="MentoHUST Win Modern", font=("Segoe UI", 18, "bold")).pack(side=tk.LEFT)
        ttk.Label(title_group, text=f"V{APP_VERSION}", font=("Segoe UI", 11), bootstyle="secondary").pack(
            side=tk.LEFT,
            padx=(12, 0),
            pady=(8, 0),
        )
        ttk.Label(header, textvariable=self.status_var, bootstyle="info").pack(side=tk.RIGHT)

        form = ttk.Labelframe(root, text="连接配置", padding=12)
        form.pack(fill=tk.X)
        form.columnconfigure(1, weight=1)
        form.columnconfigure(3, weight=1)

        row = 0
        self._entry(form, row, 0, "用户名", "username")
        self.password_entry, self.password_toggle_button = self._entry_with_button(
            form,
            row,
            2,
            "密码",
            "password",
            show="*",
            button_text="显示",
            button_command=self._toggle_password_visibility,
        )
        row += 1
        self.interface_combo = self._entry(form, row, 0, "网卡", "interface", width=48, combo=True)
        self._entry_with_button(
            form,
            row,
            2,
            "官方 8021x.exe",
            "client_exe",
            width=42,
            button_text="浏览",
            button_command=self._browse_client_exe,
        )
        row += 1
        self._entry(form, row, 0, "IP", "ipaddr")
        self._entry(form, row, 2, "网关", "gateway")
        row += 1
        self._entry(form, row, 0, "掩码", "mask")
        self._entry(form, row, 2, "DNS", "dns")
        row += 1
        self._entry(form, row, 0, "Ping 主机", "ping")
        self._entry(form, row, 2, "DHCP 命令", "dhcp_script")
        row += 1
        self._entry(form, row, 0, "超时", "timeout")
        self._entry(form, row, 2, "心跳间隔", "interval")
        row += 1
        self._entry(form, row, 0, "重试等待", "wait")
        self._entry(form, row, 2, "失败上限", "fail_number")
        row += 1
        self._entry(form, row, 0, "组播地址(0/1/2)", "multicast_address")
        self._entry(form, row, 2, "DHCP 模式(0-3)", "dhcp_mode")
        row += 1
        self._entry(form, row, 0, "客户端版本", "version")
        toggles = ttk.Frame(form)
        toggles.grid(row=row, column=2, columnspan=2, sticky=tk.W, padx=12, pady=6)
        ttk.Checkbutton(toggles, text="启用配置", variable=self.enable_var, bootstyle="round-toggle").pack(side=tk.LEFT)
        ttk.Checkbutton(
            toggles,
            text="启动时自动连接",
            variable=self.auto_connect_var,
            bootstyle="round-toggle",
        ).pack(side=tk.LEFT, padx=(12, 0))
        ttk.Label(toggles, text="WiFi下不生效", bootstyle="secondary").pack(side=tk.LEFT, padx=(12, 0))

        buttons = ttk.Frame(root)
        buttons.pack(fill=tk.X, pady=12)
        ttk.Button(buttons, text="刷新网卡", command=self._refresh_interfaces).pack(side=tk.LEFT, padx=(0, 8))
        ttk.Button(buttons, text="导入 OpenWrt 配置", command=self._import_openwrt).pack(side=tk.LEFT, padx=(0, 8))
        ttk.Button(buttons, text="加载 JSON 配置", command=self._load_profile).pack(side=tk.LEFT, padx=(0, 8))
        ttk.Button(buttons, text="保存 JSON 配置", command=self._save_profile).pack(side=tk.LEFT, padx=(0, 8))
        ttk.Button(buttons, text="打开日志目录", command=self._open_log_dir).pack(side=tk.LEFT, padx=(0, 8))
        self.connect_button = ttk.Button(buttons, text="连接", bootstyle="success", command=self._connect)
        self.connect_button.pack(side=tk.RIGHT)
        self.disconnect_button = ttk.Button(
            buttons,
            text="断开",
            bootstyle="danger",
            command=self._disconnect,
            state=tk.DISABLED,
        )
        self.disconnect_button.pack(side=tk.RIGHT, padx=(0, 8))

        log_frame = ttk.Labelframe(root, text="运行日志", padding=8)
        log_frame.pack(fill=tk.BOTH, expand=True)
        self.log_widget = scrolledtext.ScrolledText(log_frame, font=("Consolas", 10), wrap=tk.WORD)
        self.log_widget.pack(fill=tk.BOTH, expand=True)
        self.log_widget.configure(state=tk.DISABLED)

    def _set_window_icon(self) -> None:
        png_path = asset_path("app-icon.png")
        ico_path = asset_path("app-icon.ico")
        if png_path.exists():
            with Image.open(png_path) as source:
                self._window_icons = [
                    ImageTk.PhotoImage(source.resize((size, size), Image.LANCZOS))
                    for size in (64, 48, 32, 24, 16)
                ]
            self.iconphoto(True, *self._window_icons)
        if ico_path.exists():
            try:
                self.iconbitmap(default=str(ico_path))
            except tk.TclError:
                self.logger.warning("无法加载 ICO 标题栏图标: %s", ico_path)
            else:
                self._native_icon_handles = apply_window_icons(self.winfo_id(), ico_path)
        self.after(200, self._refresh_window_icon)

    def _refresh_window_icon(self) -> None:
        if self._window_icons:
            self.iconphoto(True, *self._window_icons)

    def _entry(
        self,
        parent: tk.Misc,
        row: int,
        column: int,
        label: str,
        key: str,
        *,
        width: int = 24,
        show: str | None = None,
        combo: bool = False,
    ):
        label_column = column
        entry_column = column + 1
        ttk.Label(parent, text=label).grid(row=row, column=label_column, sticky=tk.W, padx=12, pady=6)
        widget_class = ttk.Combobox if combo else ttk.Entry
        widget = widget_class(parent, textvariable=self.form_vars[key], width=width)
        if show is not None and hasattr(widget, "configure"):
            widget.configure(show=show)
        widget.grid(row=row, column=entry_column, sticky=tk.EW, padx=12, pady=6)
        return widget

    def _entry_with_button(
        self,
        parent: tk.Misc,
        row: int,
        column: int,
        label: str,
        key: str,
        *,
        width: int = 24,
        show: str | None = None,
        button_text: str,
        button_command,
    ) -> tuple[ttk.Entry, ttk.Button]:
        label_column = column
        entry_column = column + 1
        ttk.Label(parent, text=label).grid(row=row, column=label_column, sticky=tk.W, padx=12, pady=6)
        container = ttk.Frame(parent)
        container.grid(row=row, column=entry_column, sticky=tk.EW, padx=12, pady=6)
        container.columnconfigure(0, weight=1)
        widget = ttk.Entry(container, textvariable=self.form_vars[key], width=width)
        if show is not None:
            widget.configure(show=show)
        widget.grid(row=0, column=0, sticky=tk.EW)
        button = ttk.Button(container, text=button_text, width=6, command=button_command)
        button.grid(row=0, column=1, padx=(8, 0))
        return widget, button

    def _toggle_password_visibility(self) -> None:
        self._password_visible = not self._password_visible
        self.password_entry.configure(show="" if self._password_visible else "*")
        self.password_toggle_button.configure(text="隐藏" if self._password_visible else "显示")

    def _browse_client_exe(self) -> None:
        path = filedialog.askopenfilename(
            title="选择官方 8021x.exe",
            filetypes=[("Executable", "*.exe"), ("All Files", "*.*")],
        )
        if path:
            self.form_vars["client_exe"].set(path)

    def _refresh_interfaces(self) -> None:
        self.interfaces = list_interfaces()
        values = [item.description for item in self.interfaces]
        self.interface_combo["values"] = values
        if values and not self.form_vars["interface"].get():
            self.form_vars["interface"].set(values[0])
        self._log(f"[界面] 发现 {len(values)} 个可用网卡。")

    def _append_log(self, message: str) -> None:
        self.log_widget.configure(state=tk.NORMAL)
        self.log_widget.insert(tk.END, f"{message}\n")
        self.log_widget.see(tk.END)
        self.log_widget.configure(state=tk.DISABLED)

    def _log(self, message: str) -> None:
        self.logger.info(message)
        self._append_log(message)

    def _bind_auto_save(self) -> None:
        for variable in self.form_vars.values():
            variable.trace_add("write", lambda *_: self._schedule_auto_save())
        self.enable_var.trace_add("write", lambda *_: self._schedule_auto_save())
        self.auto_connect_var.trace_add("write", lambda *_: self._schedule_auto_save())

    def _schedule_auto_save(self) -> None:
        if self._auto_save_job is not None:
            self.after_cancel(self._auto_save_job)
        self._auto_save_job = self.after(500, self._save_default_profile)

    def _load_default_profile(self) -> None:
        if self.profile_path.exists():
            self._apply_config(MentohustConfig.load_json(self.profile_path))
            self._log(f"[配置] 已加载默认配置: {self.profile_path}")
        else:
            self._save_default_profile()

    def _save_default_profile(self) -> None:
        self._auto_save_job = None
        self._collect_config().save_json(self.profile_path)
        self.logger.info("[配置] 自动保存到 %s", self.profile_path)

    def _import_openwrt(self) -> None:
        path = filedialog.askopenfilename(
            title="选择 OpenWrt /etc/config/mentohust",
            filetypes=[("Config", "*"), ("All Files", "*.*")],
        )
        if not path:
            return
        config = load_openwrt_config_file(path)
        self._apply_config(config)
        self._save_default_profile()
        self._log(f"[导入] 已导入 OpenWrt 配置: {path}")

    def _load_profile(self) -> None:
        path = filedialog.askopenfilename(title="选择 JSON 配置", filetypes=[("JSON", "*.json"), ("All Files", "*.*")])
        if not path:
            return
        self._apply_config(MentohustConfig.load_json(path))
        self._save_default_profile()
        self._log(f"[导入] 已加载 JSON 配置: {path}")

    def _save_profile(self) -> None:
        path = filedialog.asksaveasfilename(title="保存 JSON 配置", defaultextension=".json", filetypes=[("JSON", "*.json")])
        if not path:
            return
        self._collect_config().save_json(path)
        self._save_default_profile()
        self._log(f"[保存] 已写入 JSON 配置: {path}")

    def _open_log_dir(self) -> None:
        ensure_app_dirs()
        os.startfile(str(self.log_path.parent))

    def _apply_config(self, config: MentohustConfig) -> None:
        self.enable_var.set(config.enable)
        self.auto_connect_var.set(config.auto_connect)
        for key, value in config.to_dict().items():
            if key in {"enable", "auto_connect"}:
                continue
            if key == "interface_description":
                self.form_vars["interface"].set(str(value))
                continue
            if key in self.form_vars:
                self.form_vars[key].set(str(value))

    def _collect_config(self) -> MentohustConfig:
        selected_description = self.form_vars["interface"].get().strip()
        interface = next((item for item in self.interfaces if item.description == selected_description), None)
        return MentohustConfig(
            enable=self.enable_var.get(),
            auto_connect=self.auto_connect_var.get(),
            username=self.form_vars["username"].get().strip(),
            password=self.form_vars["password"].get(),
            interface_description=selected_description,
            interface_id=interface.network_name if interface else "",
            ipaddr=self.form_vars["ipaddr"].get().strip() or "0.0.0.0",
            gateway=self.form_vars["gateway"].get().strip() or "0.0.0.0",
            mask=self.form_vars["mask"].get().strip() or "0.0.0.0",
            ping=self.form_vars["ping"].get().strip() or "0.0.0.0",
            timeout=int(self.form_vars["timeout"].get() or "8"),
            interval=int(self.form_vars["interval"].get() or "30"),
            wait=int(self.form_vars["wait"].get() or "15"),
            fail_number=int(self.form_vars["fail_number"].get() or "0"),
            multicast_address=int(self.form_vars["multicast_address"].get() or "1"),
            dhcp_mode=int(self.form_vars["dhcp_mode"].get() or "2"),
            dhcp_script=self.form_vars["dhcp_script"].get().strip() or "ipconfig /renew",
            version=self.form_vars["version"].get().strip() or "5.00",
            dns=self.form_vars["dns"].get().strip() or "0.0.0.0",
            client_exe=self.form_vars["client_exe"].get().strip() or default_client_exe(),
        )

    def _connect(self) -> None:
        if self.client is not None:
            return
        try:
            config = self._collect_config()
        except ValueError as exc:
            messagebox.showerror("配置错误", str(exc), parent=self)
            return
        errors = validation_errors(config)
        if errors:
            messagebox.showerror("运行环境不完整", "\n".join(errors), parent=self)
            return
        self.client = MentohustClient(
            config,
            log_callback=lambda message: self.ui_queue.put(("log", message)),
            state_callback=lambda state: self.ui_queue.put(("state", state)),
        )
        self.client.start()
        self.connect_button.configure(state=tk.DISABLED)
        self.disconnect_button.configure(state=tk.NORMAL)
        self._save_default_profile()
        self._log("[界面] 已启动认证线程。")

    def _disconnect(self) -> None:
        if self.client is not None:
            self.client.stop()
            self.client = None
        self.connect_button.configure(state=tk.NORMAL)
        self.disconnect_button.configure(state=tk.DISABLED)
        self.status_var.set("未连接")
        self._save_default_profile()
        self._log("[界面] 已请求停止认证。")

    def _maybe_auto_connect(self) -> None:
        if self._auto_connect_requested:
            return
        if self.auto_connect_var.get() and self.enable_var.get():
            if has_active_wifi_connection():
                self._auto_connect_requested = True
                self._log("[界面] 检测到 WiFi 已连接，已跳过启动时自动连接。")
                return
            self._auto_connect_requested = True
            self._log("[界面] 启动时自动连接已启用。")
            self._connect()

    def _hide_to_tray(self) -> None:
        self.withdraw()
        self.tray.update_title(f"{APP_DIR_NAME} - {self.status_var.get()}")
        if not self._has_hidden_notice:
            self.tray.notify("程序已最小化到托盘，可右键图标显示主窗口或退出。")
            self._has_hidden_notice = True
        self.logger.info("[界面] 已隐藏到托盘。")

    def _restore_from_tray(self) -> None:
        self.deiconify()
        self.lift()
        self.focus_force()
        self.logger.info("[界面] 已从托盘恢复。")

    def _exit_application(self) -> None:
        self._is_exiting = True
        try:
            self._disconnect()
        finally:
            self.tray.stop()
            destroy_icon_handles(self._native_icon_handles)
            self.destroy()

    def _drain_ui_queue(self) -> None:
        while True:
            try:
                kind, payload = self.ui_queue.get_nowait()
            except queue.Empty:
                break
            if kind == "log":
                self.logger.info(payload)
                self._append_log(payload)
            elif kind == "state":
                self.status_var.set(payload)
                self.tray.update_title(f"{APP_DIR_NAME} - {payload}")
                if payload in {"已停止", "错误"}:
                    self.connect_button.configure(state=tk.NORMAL)
                    self.disconnect_button.configure(state=tk.DISABLED)
        self.after(100, self._drain_ui_queue)

    def _on_close(self) -> None:
        if self._is_exiting:
            self.destroy()
            return
        self._save_default_profile()
        self._hide_to_tray()
