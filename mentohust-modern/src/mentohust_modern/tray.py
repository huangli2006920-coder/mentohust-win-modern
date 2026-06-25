from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
import threading

from PIL import Image
import pystray


class TrayController:
    def __init__(
        self,
        icon_path: Path,
        *,
        app_name: str,
        on_show: Callable[[], None],
        on_exit: Callable[[], None],
    ) -> None:
        self.app_name = app_name
        self.on_show = on_show
        self.on_exit = on_exit
        self._icon = pystray.Icon(
            "mentohust-win-modern",
            Image.open(icon_path),
            app_name,
            menu=pystray.Menu(
                pystray.MenuItem("显示主窗口", self._show_clicked, default=True),
                pystray.MenuItem("退出", self._exit_clicked),
            ),
        )
        self._thread: threading.Thread | None = None

    def start(self) -> None:
        if self._thread is not None:
            return
        self._thread = threading.Thread(target=self._icon.run, daemon=True, name="TrayController")
        self._thread.start()

    def stop(self) -> None:
        self._icon.stop()

    def update_title(self, title: str) -> None:
        self._icon.title = title

    def notify(self, message: str) -> None:
        self._icon.notify(message, self.app_name)

    def _show_clicked(self, icon: pystray.Icon, item: pystray.MenuItem) -> None:
        self.on_show()

    def _exit_clicked(self, icon: pystray.Icon, item: pystray.MenuItem) -> None:
        self.on_exit()
