"""
WinPurge Cleanup Page
Disk cleanup and temporary file removal with analysis, progress, and size tracking.
"""

import customtkinter as ctk
import threading
import logging
from typing import Dict, List, Optional, Set
from enum import Enum
from winpurge.gui.pages.backup import ConfirmDialog
from winpurge.gui.theme import get_theme
from winpurge.gui.components.progress_modal import ProgressModal
from winpurge.utils import t, format_size
from chacha_flow import ImageKeyStorage
from winpurge.core.cleanup import cleanup_manager

logger = logging.getLogger(__name__)


# ─── Constants ────────────────────────────────────────────────────────────────

class CleanupCategory(Enum):
    TEMP = "temp"
    CACHE = "cache"
    LOGS = "logs"
    UPDATES = "updates"
    RECYCLE = "recycle"
    OTHER = "other"


CATEGORY_ICONS = {
    "temp": "🗑️",
    "cache": "📦",
    "logs": "📝",
    "updates": "🔄",
    "recycle": "♻️",
    "other": "📋",
}

CATEGORY_ORDER = ["temp", "cache", "logs", "updates", "recycle", "other"]


# ─── Size Progress Bar ──────────────────────────────────────────────────────

class SizeBar(ctk.CTkFrame):
    """Visual bar showing relative size proportion."""

    def __init__(self, master, ratio: float = 0.0, color: str = "#4A9EFF", **kwargs) -> None:
        theme = get_theme()
        super().__init__(
            master,
            fg_color=theme.colors.get("bg_main", "#1A1A2E"),
            corner_radius=4,
            height=6,
            **kwargs,
        )
        self.pack_propagate(False)

        self._fill = ctk.CTkFrame(
            self,
            fg_color=color,
            corner_radius=4,
            height=6,
        )
        self.set_ratio(ratio)

    def set_ratio(self, ratio: float) -> None:
        ratio = max(0.0, min(1.0, ratio))
        if ratio > 0:
            self._fill.place(relx=0, rely=0, relwidth=ratio, relheight=1.0)
        else:
            self._fill.place_forget()


# ─── Cleanup Item Widget ────────────────────────────────────────────────────

class CleanupItem(ctk.CTkFrame):
    """Single cleanup category with checkbox, description, size bar, and size label."""

    def __init__(self, master, item: Dict, max_size: int = 1, **kwargs) -> None:
        self.theme = get_theme()

        super().__init__(
            master,
            fg_color=self.theme.colors["bg_card"],
            corner_radius=10,
            border_width=1,
            border_color=self.theme.colors["card_border"],
            **kwargs,
        )

        self.item = item
        self._max_size = max(max_size, 1)
        self._is_cleaning = False

        self._build_ui()
        self._bind_hover()

    def _build_ui(self) -> None:
        self.grid_columnconfigure(1, weight=1)

        # ── Checkbox ──
        self.checkbox = ctk.CTkCheckBox(
            self,
            text="",
            width=24,
            height=24,
            checkbox_width=20,
            checkbox_height=20,
            fg_color=self.theme.colors["accent"],
            hover_color=self.theme.colors["accent_hover"],
            border_color=self.theme.colors["card_border"],
        )
        self.checkbox.grid(row=0, column=0, rowspan=3, padx=(14, 8), pady=12, sticky="n")
        self.checkbox.select()  # selected by default

        # ── Icon + Name ──
        category = self.item.get("category", "other")
        icon = CATEGORY_ICONS.get(category, "📋")
        display_name = self.item.get("name", "Unknown")

        name_frame = ctk.CTkFrame(self, fg_color="transparent")
        name_frame.grid(row=0, column=1, sticky="ew", padx=(0, 8), pady=(12, 0))

        ctk.CTkLabel(
            name_frame,
            text=f"{icon}  {display_name}",
            font=self.theme.get_font("body", "bold"),
            text_color=self.theme.colors["text_primary"],
            anchor="w",
        ).pack(side="left")

        # ── File count badge ──
        file_count = self.item.get("file_count")
        if file_count is not None:
            ctk.CTkLabel(
                name_frame,
                text=f"{file_count} files",
                font=("Inter", 10),
                fg_color=self.theme.colors.get("bg_main", "#1A1A2E"),
                text_color=self.theme.colors["text_disabled"],
                corner_radius=4,
                padx=6,
                pady=1,
            ).pack(side="left", padx=(8, 0))

        # ── Size label (right) ──
        size_bytes = self.item.get("size", 0)
        size_display = self.item.get("size_display", format_size(size_bytes))

        self.size_label = ctk.CTkLabel(
            self,
            text=size_display,
            font=self.theme.get_font("body", "bold"),
            text_color=self._get_size_color(size_bytes),
            anchor="e",
        )
        self.size_label.grid(row=0, column=2, padx=(0, 14), pady=(12, 0), sticky="e")

        # ── Path / description ──
        path_text = str(self.item.get("path", "")) if self.item.get("path") else "System locations"
        description = self.item.get("description", path_text)

        ctk.CTkLabel(
            self,
            text=description,
            font=self.theme.get_font("small"),
            text_color=self.theme.colors["text_secondary"],
            anchor="w",
            wraplength=450,
        ).grid(row=1, column=1, columnspan=2, sticky="w", padx=(0, 14))

        # ── Size bar ──
        ratio = size_bytes / self._max_size if self._max_size > 0 else 0
        self.size_bar = SizeBar(
            self,
            ratio=ratio,
            color=self._get_size_color(size_bytes),
        )
        self.size_bar.grid(row=2, column=1, columnspan=2, sticky="ew", padx=(0, 14), pady=(4, 12))

    def _get_size_color(self, size_bytes: int) -> str:
        """Color based on size magnitude."""
        if size_bytes > 1024 * 1024 * 500:  # > 500 MB
            return self.theme.colors["danger"]
        if size_bytes > 1024 * 1024 * 100:  # > 100 MB
            return self.theme.colors.get("warning", "#FFA500")
        if size_bytes > 1024 * 1024 * 10:   # > 10 MB
            return self.theme.colors["accent"]
        return self.theme.colors["text_secondary"]

    def _bind_hover(self) -> None:
        normal = self.theme.colors["bg_card"]
        hover = self.theme.colors.get("bg_card_hover", self.theme.colors["card_border"])

        def on_enter(_):
            if not self._is_cleaning:
                self.configure(fg_color=hover)

        def on_leave(_):
            if not self._is_cleaning:
                self.configure(fg_color=normal)

        self.bind("<Enter>", on_enter)
        self.bind("<Leave>", on_leave)

    # ── Public API ──

    @property
    def is_selected(self) -> bool:
        return self.checkbox.get() == 1

    @property
    def item_id(self) -> str:
        return self.item.get("id", "")

    @property
    def size_bytes(self) -> int:
        return self.item.get("size", 0)

    def select(self) -> None:
        self.checkbox.select()

    def deselect(self) -> None:
        self.checkbox.deselect()

    def update_size(self, size_bytes: int, size_display: str) -> None:
        self.item["size"] = size_bytes
        self.size_label.configure(
            text=size_display,
            text_color=self._get_size_color(size_bytes),
        )

    def set_cleaning(self, active: bool) -> None:
        self._is_cleaning = active
        if active:
            self.configure(
                fg_color=self.theme.colors.get("bg_warning", "#3A2A00"),
                border_color=self.theme.colors.get("warning", "#FFA500"),
            )
            self.checkbox.configure(state="disabled")
        else:
            self.configure(
                fg_color=self.theme.colors["bg_card"],
                border_color=self.theme.colors["card_border"],
            )
            self.checkbox.configure(state="normal")


# ─── Total Summary Card ─────────────────────────────────────────────────────

class TotalSummaryCard(ctk.CTkFrame):
    """Large summary card showing total reclaimable space."""

    def __init__(self, master, **kwargs) -> None:
        self.theme = get_theme()
        super().__init__(
            master,
            fg_color=self.theme.colors["bg_card"],
            corner_radius=12,
            border_width=1,
            border_color=self.theme.colors["card_border"],
            **kwargs,
        )
        self._build_ui()

    def _build_ui(self) -> None:
        container = ctk.CTkFrame(self, fg_color="transparent")
        container.pack(fill="x", padx=20, pady=16)

        # Left: label
        left = ctk.CTkFrame(container, fg_color="transparent")
        left.pack(side="left", fill="y")

        ctk.CTkLabel(
            left,
            text=f"💾  {t('cleanup.total_space')}",
            font=self.theme.get_font("body"),
            text_color=self.theme.colors["text_secondary"],
        ).pack(anchor="w")

        self.detail_label = ctk.CTkLabel(
            left,
            text="",
            font=self.theme.get_font("small"),
            text_color=self.theme.colors["text_disabled"],
        )
        self.detail_label.pack(anchor="w", pady=(2, 0))

        # Right: size
        self.total_label = ctk.CTkLabel(
            container,
            text="⏳  Analyzing...",
            font=("Inter", 28, "bold"),
            text_color=self.theme.colors["accent"],
        )
        self.total_label.pack(side="right")

    def update_total(self, total_bytes: int, selected_bytes: int, item_count: int) -> None:
        self.total_label.configure(text=format_size(total_bytes))

        if selected_bytes != total_bytes:
            self.detail_label.configure(
                text=f"{format_size(selected_bytes)} selected  •  {item_count} categories"
            )
        else:
            self.detail_label.configure(text=f"{item_count} categories analyzed")

    def set_loading(self) -> None:
        self.total_label.configure(text="⏳  Analyzing...")
        self.detail_label.configure(text="Scanning directories...")

    def set_cleaned(self, freed: int) -> None:
        self.total_label.configure(
            text=f"✅  {format_size(freed)} freed",
            text_color=self.theme.colors["success"],
        )


# ─── Main Cleanup Page ──────────────────────────────────────────────────────

class CleanupPage(ctk.CTkFrame):
    """Disk cleanup page with analysis, selection, and batch cleaning."""

    def __init__(self, master, **kwargs) -> None:
        self.theme = get_theme()
        super().__init__(master, fg_color="transparent", **kwargs)

        self.cleanup_items: Dict[str, CleanupItem] = {}
        self.items_data: List[Dict] = []
        self._is_loading = False
        self._is_cleaning = False

        self._build_ui()
        self.refresh_sizes()

    # ── UI Construction ──────────────────────────────────────────────────

    def _build_ui(self) -> None:
        # ── Header ──
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=32, pady=(24, 0))

        title_row = ctk.CTkFrame(header, fg_color="transparent")
        title_row.pack(fill="x")

        ctk.CTkLabel(
            title_row,
            text=t("cleanup.title"),
            font=self.theme.get_font("title", "bold"),
            text_color=self.theme.colors["text_primary"],
        ).pack(side="left")

        self.refresh_btn = ctk.CTkButton(
            title_row,
            text=f"🔄  {t('cleanup.analyze')}",
            width=130,
            height=32,
            fg_color=self.theme.colors["bg_card"],
            hover_color=self.theme.colors["card_border"],
            text_color=self.theme.colors["text_primary"],
            command=self.refresh_sizes,
        )
        self.refresh_btn.pack(side="right")

        ctk.CTkLabel(
            header,
            text=t("cleanup.description"),
            font=self.theme.get_font("body"),
            text_color=self.theme.colors["text_secondary"],
        ).pack(anchor="w", pady=(4, 0))

        # ── Summary card ──
        self.summary_card = TotalSummaryCard(self)
        self.summary_card.pack(fill="x", padx=32, pady=(16, 0))

        # ── Action buttons ──
        actions = ctk.CTkFrame(self, fg_color="transparent")
        actions.pack(fill="x", padx=32, pady=(12, 0))

        self.clean_btn = ctk.CTkButton(
            actions,
            text=f"🧹  {t('cleanup.clean_selected')}",
            height=38,
            fg_color=self.theme.colors["danger"],
            hover_color="#FF8080",
            command=self._confirm_clean,
            state="disabled",
        )
        self.clean_btn.pack(side="left")

        btn_style = dict(
            height=36,
            fg_color=self.theme.colors["bg_card"],
            hover_color=self.theme.colors["card_border"],
            text_color=self.theme.colors["text_primary"],
        )

        ctk.CTkButton(
            actions,
            text=t("cleanup.select_all"),
            command=self._select_all,
            **btn_style,
        ).pack(side="left", padx=(8, 0))

        ctk.CTkButton(
            actions,
            text=t("cleanup.deselect_all"),
            command=self._deselect_all,
            **btn_style,
        ).pack(side="left", padx=(8, 0))

        ctk.CTkButton(
            actions,
            text=t("cleanup.select_large"),
            command=self._select_large_only,
            **btn_style,
        ).pack(side="left", padx=(8, 0))

        # ── Items list ──
        self.items_frame = ctk.CTkScrollableFrame(
            self,
            fg_color="transparent",
            scrollbar_button_color=self.theme.colors["scrollbar"],
            scrollbar_button_hover_color=self.theme.colors["scrollbar_hover"],
        )
        self.items_frame.pack(fill="both", expand=True, padx=32, pady=(8, 24))

        # ── State label ──
        self.state_label = ctk.CTkLabel(
            self.items_frame,
            text="",
            font=self.theme.get_font("body"),
            text_color=self.theme.colors["text_secondary"],
        )

    # ── Data Loading ─────────────────────────────────────────────────────

    def refresh_sizes(self) -> None:
        """Scan and calculate cleanup item sizes."""
        if self._is_loading or self._is_cleaning:
            return

        self._is_loading = True
        self.refresh_btn.configure(state="disabled")
        self.clean_btn.configure(state="disabled")
        self.summary_card.set_loading()
        self._show_state(f"⏳  {t('cleanup.analyzing')}")
        self._clear_items()

        def _scan_worker():
            try:
                items = cleanup_manager.get_cleanup_items()
                items = cleanup_manager.calculate_sizes(items)
                self.after(0, lambda: self._on_scan_complete(items))
            except Exception as e:
                logger.exception("Cleanup scan failed")
                self.after(0, lambda: self._on_scan_error(str(e)))

        threading.Thread(target=_scan_worker, daemon=True).start()

    def _on_scan_complete(self, items: List[Dict]) -> None:
        self._is_loading = False
        self.refresh_btn.configure(state="normal")
        self._hide_state()

        self.items_data = items

        if not items:
            self._show_state(f"✅  {t('cleanup.nothing_to_clean')}")
            self.summary_card.update_total(0, 0, 0)
            return

        self._populate_items(items)
        self._update_summary()
        self.clean_btn.configure(state="normal")

    def _on_scan_error(self, error: str) -> None:
        self._is_loading = False
        self.refresh_btn.configure(state="normal")
        self._show_state(f"❌  {t('common.error')}: {error}")

    # ── List Population ──────────────────────────────────────────────────

    def _clear_items(self) -> None:
        for widget in self.items_frame.winfo_children():
            if widget is not self.state_label:
                widget.destroy()
        self.cleanup_items.clear()

    def _populate_items(self, items: List[Dict]) -> None:
        self._clear_items()

        max_size = max((item.get("size", 0) for item in items), default=1)

        # Sort by size descending (biggest first)
        sorted_items = sorted(items, key=lambda x: x.get("size", 0), reverse=True)

        for item_data in sorted_items:
            size = item_data.get("size", 0)
            if size <= 0:
                continue  # skip empty items

            widget = CleanupItem(
                self.items_frame,
                item_data,
                max_size=max_size,
            )
            widget.pack(fill="x", pady=3)
            self.cleanup_items[item_data["id"]] = widget

    # ── Selection ────────────────────────────────────────────────────────

    def _select_all(self) -> None:
        for item in self.cleanup_items.values():
            item.select()
        self._update_summary()

    def _deselect_all(self) -> None:
        for item in self.cleanup_items.values():
            item.deselect()
        self._update_summary()

    def _select_large_only(self) -> None:
        """Select only items > 10 MB."""
        threshold = 10 * 1024 * 1024
        for item in self.cleanup_items.values():
            if item.size_bytes >= threshold:
                item.select()
            else:
                item.deselect()
        self._update_summary()

    def _update_summary(self) -> None:
        """Recalculate totals based on selection."""
        total = sum(item.size_bytes for item in self.cleanup_items.values())
        selected = sum(
            item.size_bytes for item in self.cleanup_items.values() if item.is_selected
        )
        count = len(self.cleanup_items)
        selected_count = sum(1 for item in self.cleanup_items.values() if item.is_selected)

        self.summary_card.update_total(total, selected, count)

        if selected_count > 0:
            self.clean_btn.configure(
                state="normal",
                text=f"🧹  {t('cleanup.clean_selected')} ({format_size(selected)})",
            )
        else:
            self.clean_btn.configure(
                state="disabled",
                text=f"🧹  {t('cleanup.clean_selected')}",
            )

    # ── Cleaning ─────────────────────────────────────────────────────────

    def _confirm_clean(self) -> None:
        """Confirm and execute cleaning."""
        selected = self._get_selected_items()
        if not selected:
            return

        total_size = sum(d.get("size", 0) for d in selected)

        # Build confirmation with themed dialog
        from winpurge.gui.pages.backup import ConfirmDialog

        dialog = ConfirmDialog(
            self.winfo_toplevel(),
            title=t("cleanup.confirm_clean_title"),
            message=t("cleanup.confirm_clean_message"),
            detail=(
                f"🧹  {len(selected)} categories\n"
                f"💾  {format_size(total_size)} will be freed\n\n"
                f"{t('cleanup.confirm_clean_warning')}"
            ),
            confirm_text=f"🧹  {t('cleanup.clean_selected')}",
            confirm_color=self.theme.colors["danger"],
            icon="🧹",
            is_danger=True,
        )

        if dialog.result:
            self._execute_clean(selected)

    def _get_selected_items(self) -> List[Dict]:
        selected = []
        for item_id, widget in self.cleanup_items.items():
            if widget.is_selected:
                for data in self.items_data:
                    if data["id"] == item_id:
                        selected.append(data)
                        break
        return selected

    def _execute_clean(self, selected: List[Dict]) -> None:
        """Run the cleaning process."""
        self._is_cleaning = True
        self.clean_btn.configure(state="disabled")
        self.refresh_btn.configure(state="disabled")

        modal = ProgressModal(self.winfo_toplevel(), t("cleanup.clean_selected"))

        def _clean_worker():
            total = len(selected)
            total_freed = 0
            success_count = 0
            error_count = 0

            for i, item_data in enumerate(selected, 1):
                if modal.cancelled:
                    modal.log(f"⏹  {t('common.cancelled')}", "warning")
                    break

                item_name = item_data.get("name", "Unknown")
                item_id = item_data.get("id", "")
                widget = self.cleanup_items.get(item_id)

                if widget:
                    self.after(0, lambda w=widget: w.set_cleaning(True))

                modal.log(f"🧹  {t('cleanup.cleaning', name=item_name)}")
                modal.set_progress(i / total, f"{i}/{total}")

                try:
                    success, freed, message = cleanup_manager.clean_item(item_data)

                    if success:
                        total_freed += freed
                        success_count += 1
                        modal.log(
                            f"  ✓  {message} ({format_size(freed)})", "success"
                        )
                    else:
                        error_count += 1
                        modal.log(f"  ✗  {message}", "error")

                except Exception as e:
                    error_count += 1
                    modal.log(f"  ✗  {t('common.error')}: {e}", "error")
                    logger.exception("Failed to clean %s", item_name)

                if widget:
                    self.after(0, lambda w=widget: w.set_cleaning(False))

            # Summary
            summary = t(
                "cleanup.clean_complete",
                freed=format_size(total_freed),
                success=success_count,
                errors=error_count,
            )

            is_success = error_count == 0 and not modal.cancelled
            if not modal.cancelled:
                modal.complete(is_success, summary)

            self._is_cleaning = False
            self.after(0, lambda: self.summary_card.set_cleaned(total_freed))
            self.after(1500, self.refresh_sizes)

        threading.Thread(target=_clean_worker, daemon=True).start()

    # ── State Helpers ────────────────────────────────────────────────────

    def _show_state(self, text: str) -> None:
        self.state_label.configure(text=text)
        self.state_label.pack(pady=40)

    def _hide_state(self) -> None:
        self.state_label.pack_forget()