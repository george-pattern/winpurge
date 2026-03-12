"""
WinPurge Main Entry Point
Application entry point with admin check and initialization.
"""

import sys
import ctypes
from pathlib import Path

# Ensure we can import from the package
if __name__ == "__main__":
    package_dir = Path(__file__).parent.parent
    if str(package_dir) not in sys.path:
        sys.path.insert(0, str(package_dir))


def check_windows() -> bool:
    """
    Check if running on Windows.
    
    Returns:
        True if on Windows, False otherwise.
    """
    return sys.platform == "win32"


def show_admin_required_dialog() -> bool:
    """
    Show a dialog indicating admin privileges are required.
    
    Returns:
        True if user wants to restart as admin, False otherwise.
    """
    try:
        import customtkinter as ctk
        from winpurge.gui.theme import get_theme
        from winpurge.utils import t, get_locale
        
        # Load locale
        get_locale().load_locale("en")
        
        # Create dialog
        root = ctk.CTk()
        root.withdraw()
        
        theme = get_theme()
        
        dialog = ctk.CTkToplevel(root)
        dialog.title("WinPurge")
        dialog.geometry("450x200")
        dialog.resizable(False, False)
        dialog.configure(fg_color=theme.colors["bg_main"])
        
        # Center dialog
        dialog.update_idletasks()
        screen_width = dialog.winfo_screenwidth()
        screen_height = dialog.winfo_screenheight()
        x = (screen_width - 450) // 2
        y = (screen_height - 200) // 2
        dialog.geometry(f"+{x}+{y}")
        
        result = [False]
        
        # Icon
        ctk.CTkLabel(
            dialog,
            text="🛡️",
            font=("Segoe UI Emoji", 48),
        ).pack(pady=(20, 10))
        
        # Title
        ctk.CTkLabel(
            dialog,
            text=t("common.admin_required"),
            font=theme.get_font("header", "bold"),
            text_color=theme.colors["text_primary"],
        ).pack()
        
        # Description
        ctk.CTkLabel(
            dialog,
            text=t("common.admin_required_desc"),
            font=theme.get_font("body"),
            text_color=theme.colors["text_secondary"],
            wraplength=400,
        ).pack(pady=(8, 16))
        
        # Buttons
        btn_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        btn_frame.pack()
        
        def on_restart():
            result[0] = True
            dialog.destroy()
            root.destroy()
        
        def on_cancel():
            dialog.destroy()
            root.destroy()
        
        ctk.CTkButton(
            btn_frame,
            text=t("common.restart_as_admin"),
            fg_color=theme.colors["accent"],
            hover_color=theme.colors["accent_hover"],
            command=on_restart,
        ).pack(side="left", padx=(0, 8))
        
        ctk.CTkButton(
            btn_frame,
            text=t("common.cancel"),
            fg_color=theme.colors["bg_card"],
            hover_color=theme.colors["card_border"],
            text_color=theme.colors["text_primary"],
            command=on_cancel,
        ).pack(side="left")
        
        # Handle close button
        dialog.protocol("WM_DELETE_WINDOW", on_cancel)
        
        # Make dialog modal
        dialog.transient(root)
        dialog.grab_set()
        
        dialog.wait_window()
        
        return result[0]
        
    except Exception as e:
        # Fallback to simple message box
        try:
            result = ctypes.windll.user32.MessageBoxW(
                0,
                "WinPurge requires administrator privileges to modify system settings.\n\n"
                "Click OK to restart with elevated privileges, or Cancel to exit.",
                "Administrator Required",
                0x31  # MB_OKCANCEL | MB_ICONWARNING
            )
            return result == 1  # IDOK
        except Exception:
            print("Error: Administrator privileges required.")
            return False


def main() -> None:
    """Main entry point."""
    # Check if running on Windows
    if not check_windows():
        print("Error: WinPurge only runs on Windows.")
        sys.exit(1)
    
    # Import utilities
    from winpurge.utils import is_admin, run_as_admin, logger, get_locale, load_config
    
    # Check for admin privileges
    if not is_admin():
        logger.warning("Not running as administrator")
        
        if show_admin_required_dialog():
            logger.info("Restarting with admin privileges")
            run_as_admin()
        else:
            logger.info("User cancelled admin restart")
            sys.exit(0)
        
        return
    
    logger.info("Starting WinPurge with admin privileges")
    
    # Load configuration
    config = load_config()
    
    # Load locale
    locale = get_locale()
    locale.load_locale(config.get("language", "en"))
    
    # Create and run application
    try:
        from winpurge.gui.app import WinPurgeApp
        
        app = WinPurgeApp()
        app.run()
        
    except Exception as e:
        logger.error(f"Application error: {e}", exc_info=True)
        
        # Show error dialog
        try:
            ctypes.windll.user32.MessageBoxW(
                0,
                f"An error occurred:\n\n{str(e)}\n\nCheck the log file for details.",
                "WinPurge Error",
                0x10  # MB_ICONERROR
            )
        except Exception:
            print(f"Error: {e}")
        
        sys.exit(1)
    
    logger.info("WinPurge closed")


if __name__ == "__main__":
    main()