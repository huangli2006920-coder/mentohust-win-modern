from mentohust_modern import APP_VERSION
from mentohust_modern.elevation import ensure_admin
from mentohust_modern.gui import MentohustApp
from mentohust_modern.logging_utils import configure_logging
from mentohust_modern.windows import enable_high_dpi_awareness, set_current_process_app_id


def main() -> None:
    if ensure_admin():
        return
    enable_high_dpi_awareness()
    set_current_process_app_id(f"MentoHUSTModern.{APP_VERSION}")
    configure_logging()
    app = MentohustApp()
    app.mainloop()


if __name__ == "__main__":
    main()
