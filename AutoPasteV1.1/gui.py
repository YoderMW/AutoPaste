import os
import sys
import threading
import time

import ttkbootstrap as ttk
import keyboard
import pyperclip
from ttkbootstrap.scrolled import ScrolledText
from ttkbootstrap.constants import *

from version import __version__
from paths import resource_path
from settings import load_settings, save_settings
from updater import (
    is_frozen,
    get_latest_release,
    is_newer,
    download_exe,
    apply_update_and_restart,
)
from parsers.gfc_parser import parse_gfc
from parsers.mavin_parser import parse_mavin
from parsers.legacy_parser import parse_legacy
from parsers.mw_resi_parser import parse_mw_resi
from parsers.white_river_parser import parse_white_river
from parsers.schwartz_parser import parse_schwartz
from parsers.dean_parser import parse_dean
from parsers.dean_s4s_parser import parse_dean_s4s
from parsers.p_cabinetry_parser import parse_p_cabinetry
from PDF_Highlighter import build_pdf_highlighter_tab
from tkinterdnd2 import DND_FILES, TkinterDnD
from parsers.ruffino_box_parser import parse_ruffino_box



class App(TkinterDnD.Tk):
    def __init__(self):
        super().__init__()

        # Apply ttkbootstrap theme
        self.style = ttk.Style("superhero")

        self.title(f"AutoPaste v{__version__}")

        # Window / taskbar icon. Wrapped so a missing file (e.g. running from
        # source before the icon exists) never crashes startup.
        try:
            self.iconbitmap(resource_path("AutoPaste.ico"))
        except Exception:
            pass

        # Load persisted settings before building widgets (load_keywords reads
        # self.settings["keywords"] while the PDF tab is being constructed).
        self.settings = load_settings()

        # make_widgets() calls update_widget_visibility(), which rewrites
        # settings["selected_company"] from the default dropdown value, so grab
        # the saved company first.
        saved_company = self.settings["selected_company"]

        self.make_widgets()

        self.geometry("1052x665")

        # Restore the saved company / delay / extra-tabs into their widgets.
        self.company_selector.set(saved_company)
        self.auto_entry_speed.delete("1.0", "end")
        self.auto_entry_speed.insert("1.0", self.settings["delay"])
        self.auto_entry_tab_number.set(self.settings["extra_tabs"])
        self.update_widget_visibility()  # reflect the restored company

        self.clipboard_queue = []
        self.clipboard_index = 0

        self._autoentry_thread = None
        self._autoentry_stop = threading.Event()

        keyboard.add_hotkey('F2', lambda: self.after(10, self.paste_and_copy_next))
        keyboard.add_hotkey('F4', self.toggle_auto_entry)
        keyboard.add_hotkey('esc', self.stop_auto_entry)

        # Persist delay / extra-tabs / company when the window is closed.
        self.protocol("WM_DELETE_WINDOW", self.on_close)

        # Check GitHub for a newer release, in the background so a slow or
        # offline network never delays the window appearing. No-ops from source.
        self.after(500, self.start_update_check)

    def update_current_clipboard_display(self):
        if self.clipboard_queue:
            value = self.clipboard_queue[self.clipboard_index]
            self.current_clipboard_value.config(text=value)
        else:
            self.current_clipboard_value.config(text="")

    def make_widgets(self):

        ###################
        # TABS (NOTEBOOK) #
        ###################

        self.notebook = ttk.Notebook(self)
        self.notebook.grid(row=0, column=0)

        # Tab 1 - AutoPaste
        self.autopaste_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.autopaste_tab, text="AutoPaste")

        # Tab 2 - PDF Highlighter
        self.pdf_highlighter_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.pdf_highlighter_tab, text="PDF Highlighter")


        #######################
        # INPUT BUTTONS FRAME #
        #######################

        self.input_buttons_frame = ttk.Frame(
            self.autopaste_tab,
            borderwidth=5,
            #relief="solid",
        )
        self.input_buttons_frame.grid(row=2, column=0, padx=5, pady=5)

        ####################
        # AUTO ENTRY FRAME #
        ####################

        self.auto_entry_frame = ttk.Frame(
            self.input_buttons_frame,
            borderwidth=5,
            relief="solid",
        )
        self.auto_entry_frame.grid(row=0, column=1, padx=5, pady=5)

        ###############
        # ERROR FRAME #
        ###############

        self.error_frame = ttk.Frame(
            self.autopaste_tab,
            borderwidth=5,
            relief="solid",
            width=220,
            height=400,
        )
        self.error_frame.grid(row=1, column=2, padx=5, pady=35)
        self.error_frame.grid_propagate(False)

        ###############
        # ERROR LABEL #
        ###############

        self.error_label = ttk.Label(
            self.error_frame,
            text="",
            wraplength=210,
            justify=LEFT,
            font=("Helvetica", 16)
        )
        self.error_label.grid(row=0, column=0, padx=5, pady=5)

        ###############
        # INPUT FRAME #
        ###############

        self.input_frame = ttk.Frame(
            self.input_buttons_frame,
            borderwidth=5,
            relief="solid",
        )
        self.input_frame.grid(row=0, column=0, padx=5, pady=5)

        ####################
        # TAB NUMBER LABEL #
        ####################

        self.tab_number_label = ttk.Label(
            self.auto_entry_frame,
            text="Tab Number"
        )
        self.tab_number_label.grid(row=0, column=1, pady=0, padx=0)

        ####################
        # AUTO ENTRY SPEED #
        ####################

        self.delay_label = ttk.Label(
            self.auto_entry_frame,
            text="Delay"
        )
        self.delay_label.grid(row=0, column=2, pady=0, padx=0)

        #################
        # SUBMIT BUTTON #
        #################

        self.submit_button = ttk.Button(
            self.input_frame,
            text="Submit",
            command=self.on_submit
        )
        self.submit_button.grid(row=2, column=1, padx=10, pady=10)

        ###########################
        # Flip dimension checkbox #
        ###########################

        self.dimension_flipper_var = ttk.BooleanVar(value=False)
        self.dimension_flipper = ttk.Checkbutton(
            self.input_frame,
            text="Flip H x W",
            variable=self.dimension_flipper_var
        )
        self.dimension_flipper.grid(row=1, column=0, padx=10, pady=10)

        ############################
        # Company Select Drop Down #
        ############################

        self.company_selector = ttk.Combobox(
            self.input_frame,
            values=[
                "Greenfield/Corsi",
                "Mavin",
                "Legacy",
                "MW Residential",
                "White River Cabinetry",
                "Schwartz WW LLC",
                "Ruffino Boxes",
                "Dean Cabinetry",
                "Dean S4S",
                "Peters Cabinetry"
            ],
            state="readonly",
        )
        self.company_selector.current(0)
        self.company_selector.grid(row=2, column=0, padx=5, pady=5)
        self.company_selector.bind("<<ComboboxSelected>>", self.update_widget_visibility)

        ########################
        # AUTOENTRY TAB NUMBER #
        ########################

        self.auto_entry_tab_number = ttk.Spinbox(
            self.auto_entry_frame,
            from_=0,
            to=5,
            width=5,
            state="readonly"
        )
        self.auto_entry_tab_number.set(0)
        self.auto_entry_tab_number.grid(row=1, column=1, padx=5, pady=5)

        #######################
        # AUTOENTRY SPEED VAR #
        #######################

        self.auto_entry_speed = ttk.Text(
            self.auto_entry_frame,
            height=1,
            width=5,
        )
        self.auto_entry_speed.insert("1.0", "1")
        self.auto_entry_speed.grid(row=1, column=2, padx=5, pady=5,)

        #################
        # INPUT TEXTBOX #
        #################

        self.input_textbox = ScrolledText(
            self.autopaste_tab,
            wrap="none",
            width=60,
            height=30
        )
        self.input_textbox.grid(row=1, column=0, pady=20, padx=5)

        ##################
        # OUTPUT TEXTBOX #
        ##################

        self.output_textbox = ScrolledText(
            self.autopaste_tab,
            wrap="none",
            width=60,
            height=30,
            state="disabled"
        )
        self.output_textbox.grid(row=1, column=1, pady=20, padx=5)

        ###################
        # CLIPBOARD FRAME #
        ###################

        self.clipboard_frame = ttk.Frame(
            self.autopaste_tab,
            borderwidth=5,
            relief="solid",
        )
        self.clipboard_frame.grid(row=2, column=1, padx=0, pady=0)

        #############
        # -1 BUTTON #
        #############

        self.minus_button = ttk.Button(
            self.clipboard_frame,
            text="-1",
            command=self.move_back
        )
        self.minus_button.grid(row=1, column=0, pady=5, padx=5)

        #############
        # +1 BUTTON #
        #############

        self.plus_button = ttk.Button(
            self.clipboard_frame,
            text="+1",
            command=self.move_forward
        )
        self.plus_button.grid(row=1, column=2, pady=5, padx=5)

        ###################################
        # CURRENT CLIPBOARD VALUE DISPLAY #
        ###################################

        self.current_clipboard_value = ttk.Label(
            self.clipboard_frame,
            text=" "
        )
        self.current_clipboard_value.grid(row=1, column=1, pady=5, padx=5)

        #################################
        # CURRENT CLIPBOARD VALUE LABEL #
        #################################

        self.clipboard_label = ttk.Label(
            self.clipboard_frame,
            text="Current Clipboard Value"
        )
        self.clipboard_label.grid(row=0, column=1, pady=5, padx=5)

        #############################
        # REF ID OF CLIPBOARD VALUE #
        #############################

        # self.ref_id_label = ttk.Label(
        #     self.clipboard_frame,
        #     text="Reference ID: TEST"
        # )
        # self.ref_id_label.grid(row=3, column=1, pady=5, padx=5)

        ####################
        # RIGHT CLICK MENU #
        ####################

        self.input_textbox_menu = ttk.Menu(self, tearoff=0)

        self.input_textbox_menu.add_command(
            label="Paste",
            command=lambda: self.right_click_menu_paste(self.input_textbox)
        )

        self.input_textbox_menu.add_command(
            label="Clear",
            command=lambda: self.right_click_menu_clear(self.input_textbox)
        )

        self.input_textbox_menu.add_command(
            label="Reload",
            command=lambda: self.right_click_menu_reload(self.input_textbox)
        )

        self.input_textbox.text.bind(
            "<Button-3>",
            lambda event: self.input_textbox_menu.tk_popup(
                event.x_root, event.y_root
            )
        )

        ###########################
        # HIDE AUTO ENTRY WIDGETS #
        ###########################

        self.input_textbox.text.bind(
            "<Button-3>",
            lambda event: self.input_textbox_menu.tk_popup(
                event.x_root, event.y_root
            )
        )

        # Initialize widget visibility
        self.update_widget_visibility()

        ############################
        # BUILD PDF HIGHLIGHTER TAB #
        ############################

        build_pdf_highlighter_tab(self, self.pdf_highlighter_tab)

    def on_submit(self):
        self.last_raw_input = self.input_textbox.get("1.0", "end").strip()
        raw = self.last_raw_input

        # Clear previous UI state
        self.output_textbox.text.config(state="normal")
        self.output_textbox.text.delete("1.0", "end")
        self.error_label.config(text="")

        # Select parser
        company = self.company_selector.get()

        if company == "Greenfield/Corsi":
            status, result, message = parse_gfc(raw)
        elif company == "Mavin":
            status, result, message = parse_mavin(raw)
        elif company == "Legacy":
            status, result, message = parse_legacy(raw)
        elif company == "MW Residential":
            status, result, message = parse_mw_resi(raw)
        elif company == "White River Cabinetry":
            status, result, message = parse_white_river(raw)
        elif company == "Schwartz WW LLC":
            status, result, message = parse_schwartz(raw)
        elif company == "Ruffino Boxes":
            status, result, message = parse_ruffino_box(raw)
        elif company == "Dean Cabinetry":
            status, result, message = parse_dean(raw)
        elif company == "Dean S4S":
            status, result, message = parse_dean_s4s(raw)
        elif company == "P Cabinetry":
            status, result, message = parse_p_cabinetry(raw)
        else:
            status, result, message = "error", None, "Unknown company selected"

        # ---- ERROR ----
        if status == "error":
            self.error_label.config(text=message, foreground="red")
            self.output_textbox.text.config(state="disabled")
            return

        # Optional post-parse processing
        if self.dimension_flipper_var.get():
            result = self.flip_dimensions(result)

        # ---- VALIDATION (WARNING POSSIBLE) ----
        valid, result, warning_msg = self.validate_dimensions(result)

        if not valid:
            self.error_label.config(text=warning_msg, foreground="orange")
            self.output_textbox.text.insert("end", result)
            self.output_textbox.text.config(state="disabled")
            return

        # ---- SUCCESS ----
        self.output_textbox.text.insert("end", result)

        # Build clipboard queue
        self.clipboard_queue = []
        for line in result.splitlines():
            parts = line.split("\t")
            self.clipboard_queue.extend(parts)

        self.clipboard_index = 0

        if self.clipboard_queue:
            pyperclip.copy(self.clipboard_queue[0])
            self.update_current_clipboard_display()

        # Clear input ONLY on full success
        self.input_textbox.delete("1.0", "end")

        self.output_textbox.text.config(state="disabled")

        # Display Success Message
        self.show_error_status("Status: Success", "#7CFC98")

        # uncheck dimension flipper
        self.dimension_flipper_var.set(False)

    def flip_dimensions(self, result: str) -> str:
        """
        Flips height and width values in parsed output.
        Expects tab-separated values where columns 2 and 3 are height and width.

        For example:
        "2\t100\t50\t001" becomes "2\t50\t100\t001"
        """
        flipped_lines = []

        for line in result.splitlines():
            parts = line.split("\t")

            # Only flip if we have at least 3 tab-separated values (qty, height, width)
            if len(parts) >= 3:
                # Swap columns 2 and 3 (height and width)
                parts[1], parts[2] = parts[2], parts[1]

            flipped_lines.append("\t".join(parts))

        return "\n".join(flipped_lines)

    def toggle_auto_entry(self):
        """F4: start auto-entry when idle, stop it when running (mirrors AHK F4)."""
        if self._autoentry_thread and self._autoentry_thread.is_alive():
            self.stop_auto_entry()
            return

        if not self.clipboard_queue:
            return

        # Read speed (ms) and extra tabs at start time -- exactly like AHK read
        # them from parsed_data.txt when F4 was pressed.
        try:
            delay_ms = int(self.auto_entry_speed.get("1.0", "end").strip() or "0")
        except ValueError:
            delay_ms = 0
        try:
            extra_tabs = int(self.auto_entry_tab_number.get() or "0")
        except ValueError:
            extra_tabs = 0

        values = list(self.clipboard_queue)  # [qty, w, h, ref, qty, w, h, ref, ...]

        self._autoentry_stop.clear()
        self._autoentry_thread = threading.Thread(
            target=self._run_auto_entry,
            args=(values, delay_ms / 1000.0, extra_tabs),
            daemon=True,
        )
        self._autoentry_thread.start()

    def stop_auto_entry(self):
        """Esc, or F4 while running: signal the worker to stop."""
        self._autoentry_stop.set()

    def on_close(self):
        """Capture current delay / extra-tabs / company, save, then close."""
        self.settings["selected_company"] = self.company_selector.get()
        self.settings["delay"] = self.auto_entry_speed.get("1.0", "end").strip()
        self.settings["extra_tabs"] = self.auto_entry_tab_number.get()
        save_settings(self.settings)
        self.destroy()

    def start_update_check(self):
        """Kick off the GitHub release check on a daemon thread (non-blocking)."""
        if not is_frozen():
            return  # running from source: nothing to update
        threading.Thread(target=self._update_check_worker, daemon=True).start()

    def _update_check_worker(self):
        """
        Background: ask GitHub for the latest release. If it's newer, hand the
        result back to the UI thread to prompt (dialogs must run on the main
        thread). Silent on any failure (offline, no release, same version).
        """
        latest = get_latest_release()
        if not latest:
            return
        tag, asset_url = latest
        if is_newer(tag):
            self.after(0, lambda: self._prompt_update(tag, asset_url))

    def _prompt_update(self, tag, asset_url):
        """UI thread: 'Update available — install now?'. On Yes, do the swap."""
        from ttkbootstrap.dialogs import Messagebox

        answer = Messagebox.yesno(
            f"A new version ({tag}) of AutoPaste is available.\n"
            f"You're on v{__version__}.\n\nInstall it now?",
            "Update available",
            parent=self,
        )
        if answer != "Yes":
            return

        # Download beside the running exe so the .bat's move is same-drive/atomic.
        dest = os.path.join(os.path.dirname(sys.executable), "AutoPaste_new.exe")
        if not download_exe(asset_url, dest):
            Messagebox.show_error(
                "The update failed to download. Please try again later.",
                "Update failed",
                parent=self,
            )
            return

        if apply_update_and_restart(dest):
            # Persist settings, then quit so the helper can replace the exe.
            self.on_close()
        else:
            Messagebox.show_error(
                "The update could not be applied automatically.",
                "Update failed",
                parent=self,
            )

    def _run_auto_entry(self, values, delay, extra_tabs):
        """
        Worker thread: type each value then send Tab/Enter in a repeating
        4-value cycle (qty, width, height, cabinet), matching AutoEntry_V3.ahk.
        Sends into whatever window currently has focus.
        """
        last = len(values) - 1
        for i, value in enumerate(values):
            if self._autoentry_stop.is_set():
                break

            keyboard.write(value)              # AHK: SendText value
            time.sleep(delay)

            position = i % 4                   # 0=qty 1=width 2=height 3=cabinet
            if position in (0, 1):
                keyboard.press_and_release('tab')
                time.sleep(delay)
            elif position == 2:
                keyboard.press_and_release('tab')
                time.sleep(delay)
                for _ in range(extra_tabs):
                    keyboard.press_and_release('tab')
                    time.sleep(delay)
            elif position == 3:
                if i < last:                   # not the final row -> Tab, Tab, Enter
                    keyboard.press_and_release('tab')
                    time.sleep(delay)
                    keyboard.press_and_release('tab')
                    time.sleep(delay)
                    keyboard.press_and_release('enter')
                    time.sleep(delay)
                # final row: stop cleanly, no trailing keystrokes

    def paste_and_copy_next(self):
        """
        Paste current clipboard value, optionally press Tab (depending on company),
        then load next value into clipboard.
        """
        if not self.clipboard_queue:
            return

        # Paste
        keyboard.press_and_release('ctrl+v')
        self.after(50)

        # Check which company is selected
        company = self.company_selector.get()

        # Press Tab for all companies EXCEPT Mavin
        if company not in ["Mavin", "Schwartz WW LLC"]:
            keyboard.press_and_release('tab')

        # Load next value
        def load_next():
            if self.clipboard_index < len(self.clipboard_queue) - 1:
                self.clipboard_index += 1
                next_value = self.clipboard_queue[self.clipboard_index]
                pyperclip.copy(next_value)
                self.update_current_clipboard_display()
            else:
                # At end of queue
                pyperclip.copy("")  # optional
                # You can add a label to notify user

        self.after(100, load_next)

    def move_forward(self):
        """Move forward one item in the clipboard queue."""
        if not self.clipboard_queue:
            return

        # If currently showing the "Beginning" sentinel, go to the first real value
        if self.current_clipboard_value.cget("text") == "Beginning":
            self.clipboard_index = 0
            new_value = self.clipboard_queue[self.clipboard_index]
            pyperclip.copy(new_value)
            self.current_clipboard_value.config(text=new_value)
            return

        # If already at end
        if self.clipboard_index >= len(self.clipboard_queue) - 1:
            self.current_clipboard_value.config(text="End")
            pyperclip.copy("")  # optional: clear clipboard
            return

        # Move forward normally
        self.clipboard_index += 1
        new_value = self.clipboard_queue[self.clipboard_index]
        pyperclip.copy(new_value)
        self.current_clipboard_value.config(text=new_value)

    def move_back(self):
        """Move backward one item in the clipboard queue."""
        if not self.clipboard_queue:
            return

        # If currently showing the "End" sentinel, go to the last real value
        if self.current_clipboard_value.cget("text") == "End":
            self.clipboard_index = len(self.clipboard_queue) - 1
            new_value = self.clipboard_queue[self.clipboard_index]
            pyperclip.copy(new_value)
            self.current_clipboard_value.config(text=new_value)
            return

        # If already at beginning
        if self.clipboard_index <= 0:
            self.current_clipboard_value.config(text="Beginning")
            pyperclip.copy("")  # optional
            return

        # Move backward normally
        self.clipboard_index -= 1
        new_value = self.clipboard_queue[self.clipboard_index]
        pyperclip.copy(new_value)
        self.current_clipboard_value.config(text=new_value)

    def right_click_menu_paste(self, widget):
        """Paste clipboard contents into the given widget."""
        try:
            text = self.clipboard_get()
            widget.insert("insert", text)
        except Exception:
            pass

    def right_click_menu_clear(self, widget):
        """Clear all text from the given widget."""
        widget.delete("1.0", "end")

    def right_click_menu_reload(self, widget):
        """Reload last submitted raw input data"""
        if not hasattr(self, "last_raw_input"):
            return

        widget.delete("1.0", "end")
        widget.insert("1.0", self.last_raw_input)

    def update_widget_visibility(self, event=None):
        """Show/hide auto entry widgets based on selected company"""
        company = self.company_selector.get()
        self.settings["selected_company"] = company  # persist the choice

        # Companies that need auto-entry widgets
        show_autoentry = company in ["Greenfield/Corsi", "Legacy", "MW Residential", "Dean Cabinetry", "P Cabinetry"]

        if show_autoentry:
            # Show all widgets
            self.tab_number_label.grid()
            self.delay_label.grid()
            self.auto_entry_tab_number.grid()
            self.auto_entry_speed.grid()
        else:
            # Hide all widgets (but frame stays, taking up space)
            self.tab_number_label.grid_remove()
            self.delay_label.grid_remove()
            self.auto_entry_tab_number.grid_remove()
            self.auto_entry_speed.grid_remove()

    def validate_dimensions(self, result: str) -> tuple[bool, str, str | None]:
        """
        Validates that all dimensions are in 1/16th inch increments.

        Returns:
            (True, result, None) if all dimensions are valid
            (False, result, warning_message) if invalid dimensions found
        """
        lines = result.splitlines()

        for line_num, line in enumerate(lines, start=1):
            parts = line.split("\t")

            # Check each part to see if it's a dimension (contains a decimal point)
            for part in parts:
                try:
                    # Try to convert to float
                    value = float(part)

                    # Check if it's a 1/16th increment
                    multiplied = value * 16

                    # Use a small tolerance for floating point comparison
                    if abs(multiplied - round(multiplied)) > 0.01:
                        warning_msg = (
                            f"A non 1/16th inch increment dimension "
                            f"was found at line {line_num}.\n"
                            "Please verify the dimensions before continuing."
                        )
                        return False, result, warning_msg

                except ValueError:
                    # Not a number, skip it (could be text like ref_id)
                    continue

        # All dimensions are valid
        return True, result, None

    def show_error_status(self, text: str, color: str):
        self.error_label.config(text=text, foreground=color)