import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from ttkbootstrap.scrolled import ScrolledText
from tkinter import colorchooser, filedialog
import os
import fitz  # PyMuPDF library for PDF manipulation
import json
from tkinterdnd2 import DND_FILES, TkinterDnD
from settings import save_settings

############################
# PDF HIGHLIGHTER TAB GUI #
############################

def build_pdf_highlighter_tab(app, parent):
    """
    Builds the PDF Highlighter tab UI.

    app    -> Main App instance (shared state & callbacks)
    parent -> The PDF Highlighter tab frame
    """

    # Initialize data storage on app instance.
    # keywords_list IS the list inside the shared settings dict, so editing it
    # and saving settings keeps keywords, company and delay in one file.
    app.keywords_list = app.settings["keywords"]
    app.pdf_files_list = []
    app.selected_color = "#FFFF00"  # Default yellow
    app.create_copy_var = ttk.BooleanVar(value=True)  # Default to creating a copy

    ###########################
    # KEYWORD INPUT FRAME #
    ###########################

    app.keyword_input_frame = ttk.Frame(
        parent,
        borderwidth=5,
        relief="solid",
        width=500,
        height=200,
    )
    app.keyword_input_frame.grid(row=0, column=0, padx=10, pady=5, sticky="nw")
    app.keyword_input_frame.grid_propagate(False)

    # Section Title
    app.keyword_section_title = ttk.Label(
        app.keyword_input_frame,
        text="Keyword Management",
        font=("Helvetica", 12, "bold")
    )
    app.keyword_section_title.grid(row=0, column=0, columnspan=2, pady=10)

    # Keyword Entry Label
    app.keyword_entry_label = ttk.Label(
        app.keyword_input_frame,
        text="Keyword:"
    )
    app.keyword_entry_label.grid(row=1, column=0, padx=5, pady=5, sticky="e")

    # Keyword Entry Field
    app.keyword_entry = ttk.Entry(
        app.keyword_input_frame,
        width=30
    )
    app.keyword_entry.grid(row=1, column=1, padx=5, pady=5, columnspan=2)

    # Color Selector Label
    app.color_selector_label = ttk.Label(
        app.keyword_input_frame,
        text="Highlight Color:"
    )
    app.color_selector_label.grid(row=2, column=0, padx=5, pady=5, sticky="e")

    # Color Display Frame
    app.color_display_frame = ttk.Frame(
        app.keyword_input_frame,
        width=30,
        height=30,
        relief="solid",
        borderwidth=2
    )
    app.color_display_frame.grid(row=2, column=2, padx=5, pady=5, sticky="w")
    app.color_display_frame.grid_propagate(False)

    # Configure the color display background
    app.color_display_label = ttk.Label(
        app.color_display_frame,
        text="",
        background=app.selected_color
    )
    app.color_display_label.place(relx=0, rely=0, relwidth=1, relheight=1)

    # Color Picker Button
    app.color_picker_button = ttk.Button(
        app.keyword_input_frame,
        text="Choose Color",
        command=lambda: choose_color(app)
    )
    app.color_picker_button.grid(row=2, column=1, padx=5, pady=5, sticky="w")

    # Submit Button
    app.submit_keyword_button = ttk.Button(
        app.keyword_input_frame,
        text="Add Keyword",
        bootstyle="success",
        command=lambda: add_keyword(app)
    )
    app.submit_keyword_button.grid(row=4, column=1, columnspan=1, padx=5, pady=5, sticky="w")

    ###########################
    # DRAG & DROP AREA FRAME #
    ###########################

    app.drag_drop_frame = ttk.Frame(
        parent,
        borderwidth=5,
        relief="solid",
        width=500,
        height=200
    )
    app.drag_drop_frame.grid(row=0, column=1, padx=10, pady=5, sticky="nsew")
    app.drag_drop_frame.grid_propagate(False)
    app.drag_drop_frame.drop_target_register(DND_FILES)
    app.drag_drop_frame.dnd_bind(
        "<<DragEnter>>",
        lambda event: app.drag_drop_frame.config(bootstyle="success")
    )

    app.drag_drop_frame.dnd_bind(
        "<<DragLeave>>",
        lambda event: app.drag_drop_frame.config(bootstyle="")
    )

    app.drag_drop_frame.dnd_bind(
        "<<Drop>>",
        lambda event: handle_pdf_drop(event, app)
    )

    # Container frame for centered content
    app.drag_drop_content_frame = ttk.Frame(app.drag_drop_frame)
    app.drag_drop_content_frame.place(relx=0.5, rely=0.5, anchor="center")

    # Instructions Label
    app.drag_drop_instructions = ttk.Label(
        app.drag_drop_content_frame,
        text="Drop PDF Files Here",
        font=("Helvetica", 14, "bold"),
        foreground="gray"
    )
    app.drag_drop_instructions.grid(row=0, column=0, pady=10)

    # "or" Label
    app.drag_drop_or_label = ttk.Label(
        app.drag_drop_content_frame,
        text="or",
        font=("Helvetica", 10),
        foreground="gray"
    )
    app.drag_drop_or_label.grid(row=1, column=0, pady=5)

    # Browse Button
    app.browse_files_button = ttk.Button(
        app.drag_drop_content_frame,
        text="Browse Files",
        bootstyle="primary",
        command=lambda: load_pdfs_browse(app)
    )
    app.browse_files_button.grid(row=2, column=0, pady=10)

    ######################
    # KEYWORD LIST FRAME #
    ######################

    app.keyword_list_frame = ttk.Frame(
        parent,
        borderwidth=5,
        relief="solid"
    )
    app.keyword_list_frame.grid(row=1, column=0, padx=5, pady=5, sticky="nsew")

    # Section Title
    app.keyword_list_title = ttk.Label(
        app.keyword_list_frame,
        text="Saved Keywords",
        font=("Helvetica", 12, "bold")
    )
    app.keyword_list_title.grid(row=0, column=0, pady=10, sticky="w", padx=10)

    # Scrollable Frame for Keywords
    app.keyword_display_canvas = ttk.Canvas(
        app.keyword_list_frame,
        height=280,
        width=150,
    )
    app.keyword_display_canvas.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
    app.keyword_display_canvas.grid_propagate(False)

    # Scrollbar for canvas
    app.keyword_scrollbar = ttk.Scrollbar(
        app.keyword_list_frame,
        orient="vertical",
        command=app.keyword_display_canvas.yview
    )
    app.keyword_scrollbar.grid(row=1, column=1, sticky="ns")

    app.keyword_display_canvas.configure(yscrollcommand=app.keyword_scrollbar.set)

    # Frame inside canvas to hold keyword entries
    app.keyword_entries_frame = ttk.Frame(app.keyword_display_canvas)
    app.keyword_canvas_window = app.keyword_display_canvas.create_window(
        (0, 0),
        window=app.keyword_entries_frame,
        anchor="nw"
    )

    # Bind canvas resize
    app.keyword_entries_frame.bind(
        "<Configure>",
        lambda e: app.keyword_display_canvas.configure(
            scrollregion=app.keyword_display_canvas.bbox("all")
        )
    )

    # Configure grid weights for proper resizing
    app.keyword_list_frame.grid_rowconfigure(1, weight=1)
    app.keyword_list_frame.grid_columnconfigure(0, weight=1)

    ###########################
    # PDF LIST FRAME #
    ###########################

    app.pdf_list_frame = ttk.Frame(
        parent,
        borderwidth=5,
        relief="solid"
    )
    app.pdf_list_frame.grid(row=1, column=1, padx=5, pady=5, sticky="nsew")

    # Section Title
    app.pdf_list_title = ttk.Label(
        app.pdf_list_frame,
        text="Loaded PDF Files",
        font=("Helvetica", 12, "bold")
    )
    app.pdf_list_title.grid(row=0, column=0, pady=10, sticky="w", padx=10)

    # Scrolled Text for PDF list
    app.pdf_list_display = ScrolledText(
        app.pdf_list_frame,
        wrap="word",
        height=10,
        width=50,
        state="disabled"
    )
    app.pdf_list_display.grid(row=1, column=0, padx=5, pady=5, sticky="nsew")

    # Configure grid weights
    app.pdf_list_frame.grid_rowconfigure(1, weight=1)
    app.pdf_list_frame.grid_columnconfigure(0, weight=1)

    # Clear All PDFs Button
    app.clear_pdfs_button = ttk.Button(
        app.pdf_list_frame,
        text="Clear All PDFs",
        bootstyle="danger-outline",
        command=lambda: clear_all_pdfs(app)
    )
    app.clear_pdfs_button.grid(row=2, column=0, pady=10)

    #############################
    # ACTION BUTTONS FRAME #
    #############################

    app.action_buttons_frame = ttk.Frame(parent)
    app.action_buttons_frame.grid(row=2, column=0, columnspan=2, padx=5, pady=10, sticky="ew")

    # Frame to hold checkbox and button together
    app.highlight_control_frame = ttk.Frame(app.action_buttons_frame)
    app.highlight_control_frame.pack(side="right", padx=10)

    # Highlight PDFs Button
    app.highlight_button = ttk.Button(
        app.highlight_control_frame,
        text="Highlight PDFs",
        bootstyle="success",
        command=lambda: highlight_pdfs(app)
    )
    app.highlight_button.pack(side="right", padx=5)

    # Checkbox for create copy option
    app.create_copy_checkbox = ttk.Checkbutton(
        app.highlight_control_frame,
        text="Create copy",
        variable=app.create_copy_var,
        bootstyle="round-toggle"
    )
    app.create_copy_checkbox.pack(side="right", padx=5)

    # Status Label
    app.status_label = ttk.Label(
        app.action_buttons_frame,
        text="Ready",
        font=("Helvetica", 10),
        foreground="gray"
    )
    app.status_label.pack(side="left", padx=20)

    # Configure grid weights for the parent
    parent.grid_rowconfigure(1, weight=1)
    parent.grid_columnconfigure(0, weight=1)
    parent.grid_columnconfigure(1, weight=1)

    # Load saved keywords on startup
    load_keywords(app)

############################
# CALLBACK FUNCTIONS #
############################

def choose_color(app):
    """Opens color picker dialog"""
    color = colorchooser.askcolor(
        initialcolor=app.selected_color,
        title="Choose Highlight Color"
    )

    if color[1]:  # color[1] is the hex value
        app.selected_color = color[1]
        app.color_display_label.config(background=app.selected_color)

def add_keyword(app):
    """Adds a new keyword to the list"""
    keyword = app.keyword_entry.get().strip()

    if not keyword:
        show_status(app, "Please enter a keyword", "orange")
        return

    # Check for duplicates
    for item in app.keywords_list:
        if item['keyword'].lower() == keyword.lower():
            show_status(app, "Keyword already exists", "orange")
            return

    # Add to list
    keyword_data = {
        'keyword': keyword,
        'color': app.selected_color
    }
    app.keywords_list.append(keyword_data)

    # Update display
    update_keyword_display(app)

    # Clear entry
    app.keyword_entry.delete(0, 'end')

    # Save to file
    save_keywords(app)

    # Show status
    show_status(app, f"Added keyword: {keyword}", "green")

def delete_keyword(app, index):
    """Deletes a keyword from the list"""
    if 0 <= index < len(app.keywords_list):
        deleted_keyword = app.keywords_list[index]['keyword']
        del app.keywords_list[index]
        update_keyword_display(app)
        save_keywords(app)
        show_status(app, f"Deleted keyword: {deleted_keyword}", "orange")

def update_keyword_display(app):
    """Updates the keyword list display"""
    # Clear existing widgets
    for widget in app.keyword_entries_frame.winfo_children():
        widget.destroy()

    # Create a row for each keyword
    for index, keyword_data in enumerate(app.keywords_list):
        # Create a frame for this keyword row
        row_frame = ttk.Frame(app.keyword_entries_frame)
        row_frame.grid(row=index, column=0, sticky="ew", pady=2)

        # Keyword label
        keyword_label = ttk.Label(
            row_frame,
            text=keyword_data['keyword'],
            font=("Helvetica", 10)
        )
        keyword_label.grid(row=0, column=0, padx=10, pady=5, sticky="w")

        # Color block
        color_block = ttk.Frame(
            row_frame,
            width=30,
            height=20,
            relief="solid",
            borderwidth=1
        )
        color_block.grid(row=0, column=1, padx=10, pady=5)
        color_block.grid_propagate(False)

        # Color display label
        color_label = ttk.Label(
            color_block,
            text="",
            background=keyword_data['color']
        )
        color_label.place(relx=0, rely=0, relwidth=1, relheight=1)

        # Delete button
        delete_button = ttk.Button(
            row_frame,
            text="Delete",
            bootstyle="danger-outline",
            command=lambda idx=index: delete_keyword(app, idx),
            width=10
        )
        delete_button.grid(row=0, column=2, padx=10, pady=5)

        # Configure row frame columns
        row_frame.grid_columnconfigure(0, weight=1)

    # Configure keyword entries frame
    app.keyword_entries_frame.grid_columnconfigure(0, weight=1)

def load_pdfs_browse(app):
    """Opens file dialog to select PDF files"""
    filenames = filedialog.askopenfilenames(
        title="Select PDF Files",
        filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")]
    )

    if filenames:
        # Add new files to list (avoid duplicates)
        for filename in filenames:
            if filename not in app.pdf_files_list:
                app.pdf_files_list.append(filename)

        # Update display
        update_pdf_display(app)
        show_status(app, f"{len(app.pdf_files_list)} PDF(s) loaded", "green")

def update_pdf_display(app):
    """Updates the PDF list frame to show loaded files"""
    if app.pdf_files_list:
        # Update the PDF list display in the bottom right frame
        app.pdf_list_display.text.config(state="normal")
        app.pdf_list_display.text.delete("1.0", "end")

        for i, filepath in enumerate(app.pdf_files_list, 1):
            filename = os.path.basename(filepath)
            app.pdf_list_display.text.insert("end", f"{i}. {filename}\n")

        app.pdf_list_display.text.config(state="disabled")
    else:
        # Clear the display
        app.pdf_list_display.text.config(state="normal")
        app.pdf_list_display.text.delete("1.0", "end")
        app.pdf_list_display.text.insert("end", "No PDF files loaded yet.")
        app.pdf_list_display.text.config(state="disabled")

def clear_all_pdfs(app):
    """Clears all loaded PDFs from the list"""
    if app.pdf_files_list:
        app.pdf_files_list.clear()
        update_pdf_display(app)
        show_status(app, "All PDFs cleared", "orange")
    else:
        show_status(app, "No PDFs to clear", "gray")

def highlight_pdfs(app):
    """
    Processes PDF files and highlights all instances of saved keywords.
    Creates new PDF files with "_highlighted" appended to the original filename
    if create_copy_var is True, otherwise modifies the original file.
    """

    # ===================================================================
    # STEP 1: VALIDATION - Make sure we have keywords and PDFs to process
    # ===================================================================

    if not app.keywords_list:
        show_status(app, "Error: No keywords defined", "red")
        return

    if not app.pdf_files_list:
        show_status(app, "Error: No PDF files loaded", "red")
        return

    # ===================================================================
    # STEP 2: SETUP - Prepare variables to track our progress
    # ===================================================================

    processed_count = 0
    total_highlights = 0
    create_copy = app.create_copy_var.get()
    total_pdfs = len(app.pdf_files_list)

    # ===================================================================
    # STEP 3: PROCESS EACH PDF - Loop through all loaded PDF files
    # ===================================================================

    for pdf_path in app.pdf_files_list:

        try:
            # Show progress status
            filename = os.path.basename(pdf_path)
            show_status(app, f"Processing {processed_count + 1}/{total_pdfs}: {filename}...", "white")
            app.update_idletasks()  # Force UI update to show status immediately

            # Open the PDF file
            pdf_document = fitz.open(pdf_path)

            # Count highlights for this specific PDF
            pdf_highlight_count = 0

            # Process each page in the PDF
            for page_num in range(len(pdf_document)):

                # Get the specific page
                page = pdf_document[page_num]

                # Search for each keyword on this page
                for keyword_data in app.keywords_list:

                    keyword = keyword_data['keyword']
                    hex_color = keyword_data['color']

                    # Convert hex color to RGB format (0-1 range)
                    hex_color = hex_color.lstrip('#')
                    rgb_color = tuple(
                        int(hex_color[i:i + 2], 16) / 255.0
                        for i in (0, 2, 4)
                    )

                    # Search for the keyword on the page
                    text_instances = page.search_for(keyword, quads=True)

                    # Highlight each instance
                    for inst in text_instances:
                        highlight = page.add_highlight_annot(inst)
                        highlight.set_colors(stroke=rgb_color)
                        highlight.update()
                        pdf_highlight_count += 1

            # Determine the output path based on checkbox state
            if create_copy:
                # Create a new file with "_highlighted" suffix
                directory = os.path.dirname(pdf_path)
                filename = os.path.basename(pdf_path)
                name, extension = os.path.splitext(filename)
                new_filename = f"{name}_highlighted{extension}"
                output_path = os.path.join(directory, new_filename)

                # Save the highlighted PDF
                pdf_document.save(output_path)
                pdf_document.close()
            else:
                # Modify the original file
                # Save to a temporary file first, then replace the original
                directory = os.path.dirname(pdf_path)
                filename = os.path.basename(pdf_path)
                name, extension = os.path.splitext(filename)
                temp_filename = f"{name}_temp{extension}"
                temp_path = os.path.join(directory, temp_filename)

                # Save to temp file
                pdf_document.save(temp_path)
                pdf_document.close()

                # Replace the original file with the temp file
                import shutil
                shutil.move(temp_path, pdf_path)

            # Update progress counters
            processed_count += 1
            total_highlights += pdf_highlight_count

        except Exception as e:
            # Error handling
            filename = os.path.basename(pdf_path)
            show_status(
                app,
                f"Error processing {filename}: {str(e)}",
                "red"
            )
            continue

    # Show success message
    if create_copy:
        show_status(
            app,
            f"Success! Processed {processed_count} PDF(s) with {total_highlights} highlight(s) - Copies created",
            "green"
        )
    else:
        show_status(
            app,
            f"Success! Processed {processed_count} PDF(s) with {total_highlights} highlight(s) - Originals modified",
            "green"
        )

def show_status(app, message, color):
    """Updates the status label with a message and color"""
    app.status_label.config(text=message, foreground=color)

def save_keywords(app):
    """
    Persist the keyword list. Keywords live inside the shared settings dict,
    so this writes the whole settings.json (keywords + company + delay).
    """
    save_settings(app.settings)

def load_keywords(app):
    """
    Refresh the keyword display from the already-loaded settings.

    The keywords were loaded from settings.json at startup (app.keywords_list
    is the same list object as app.settings["keywords"]), so there is no file
    to read here -- just show what's in memory.
    """
    try:
        update_keyword_display(app)
        if app.keywords_list:
            show_status(app, f"Loaded {len(app.keywords_list)} saved keyword(s)", "green")
    except Exception as e:
        # If something goes wrong, show an error (but don't crash)
        print(f"Error loading keywords: {e}")

def handle_pdf_drop(event, app):
    """
    Handles files dropped into the drag_drop_frame.
    Accepts one or multiple PDF files.
    """

    # event.data contains file paths as a single string
    files = app.tk.splitlist(event.data)

    added_count = 0

    for file_path in files:
        # Only accept .pdf files
        if file_path.lower().endswith(".pdf"):
            if file_path not in app.pdf_files_list:
                app.pdf_files_list.append(file_path)
                added_count += 1

    if added_count > 0:
        update_pdf_display(app)
        show_status(app, f"{added_count} PDF(s) added via drag & drop", "green")
    else:
        show_status(app, "No new PDF files added", "orange")