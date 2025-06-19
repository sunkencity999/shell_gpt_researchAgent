import sys
import os
from pathlib import Path
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QTextEdit, QPushButton, QFileDialog, QComboBox, QMenuBar, QAction, QMessageBox,
    QTabWidget, QListWidget, QSplitter, QSpinBox, QDoubleSpinBox, QGroupBox, QFormLayout
)
from PyQt5.QtGui import QFont, QIcon
from PyQt5.QtCore import Qt

# --- Configurable paths and constants ---
DOCUMENTS_DIR = Path(__file__).resolve().parent.parent / "documents"
DEFAULT_MODEL = "llama3"
APP_TITLE = "Shell GPT Research Agent GUI"

# --- Import backend ---
from sgptAgent.agent import ResearchAgent
import traceback
from PyQt5.QtCore import QThread, pyqtSignal, Qt

# --- Helper functions ---
def ensure_documents_dir():
    DOCUMENTS_DIR.mkdir(exist_ok=True)

# --- Main Window ---
class ResearchAgentGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(APP_TITLE)
        self.setMinimumSize(800, 600)
        # Set custom window icon
        icon_path = os.path.join(os.path.dirname(__file__), "Assets", "sgptRAicon.png")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        else:
            self.setWindowIcon(QIcon.fromTheme("applications-science"))
        self._init_ui()

    def toggle_theme(self):
        from PyQt5.QtGui import QPalette, QColor
        app = QApplication.instance()
        if not self.theme_is_dark:
            dark_palette = QPalette()
            dark_palette.setColor(QPalette.Window, QColor(30, 30, 30))
            dark_palette.setColor(QPalette.WindowText, QColor(220, 220, 220))
            dark_palette.setColor(QPalette.Base, QColor(24, 24, 24))
            dark_palette.setColor(QPalette.AlternateBase, QColor(40, 40, 40))
            dark_palette.setColor(QPalette.ToolTipBase, QColor(255, 255, 220))
            dark_palette.setColor(QPalette.ToolTipText, QColor(0, 0, 0))
            dark_palette.setColor(QPalette.Text, QColor(220, 220, 220))
            dark_palette.setColor(QPalette.Button, QColor(45, 45, 45))
            dark_palette.setColor(QPalette.ButtonText, QColor(220, 220, 220))
            dark_palette.setColor(QPalette.BrightText, QColor(255, 0, 0))
            dark_palette.setColor(QPalette.Link, QColor(42, 130, 218))
            dark_palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
            dark_palette.setColor(QPalette.HighlightedText, QColor(35, 35, 35))
            app.setPalette(dark_palette)
            self.theme_btn.setText("☀️ Light Mode")
            self.theme_is_dark = True
        else:
            app.setPalette(app.style().standardPalette())
            self.theme_btn.setText("🌙 Dark Mode")
            self.theme_is_dark = False

    def _init_ui(self):
        print("DEBUG: Entered _init_ui")
        from PyQt5.QtWidgets import QSizePolicy
        # Main splitter for responsive layout
        splitter = QSplitter(Qt.Horizontal)
        splitter.setChildrenCollapsible(False)

        # --- Left panel: Inputs & Controls ---
        print("DEBUG: Initializing left panel widgets")
        left_widget = QWidget()
        left_vbox = QVBoxLayout()
        left_vbox.setSpacing(16)
        left_vbox.setContentsMargins(24, 18, 12, 18)

        # Logo
        import os
        from PyQt5.QtGui import QPixmap
        logo_path = os.path.join(os.path.dirname(__file__), "Assets", "sgptRAicon.png")
        logo_label = QLabel()
        if os.path.exists(logo_path):
            pixmap = QPixmap(logo_path)
            logo_label.setPixmap(pixmap.scaled(104, 104, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        logo_label.setAlignment(Qt.AlignCenter)
        left_vbox.addWidget(logo_label)

        # Query input
        query_label = QLabel("Research Query:")
        query_label.setFont(QFont("Montserrat", 12, QFont.Bold))
        self.query_input = QTextEdit()
        self.query_input.setFont(QFont("Fira Mono", 12))
        self.query_input.setPlaceholderText("Enter your research question or topic...")
        self.query_input.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        left_vbox.addWidget(query_label)
        left_vbox.addWidget(self.query_input, 2)

        # Audience, Tone, Improvement fields
        extras_layout = QHBoxLayout()
        audience_label = QLabel("Audience:")
        audience_label.setFont(QFont("Montserrat", 11))
        self.audience_input = QLineEdit()
        self.audience_input.setFont(QFont("Fira Mono", 11))
        self.audience_input.setPlaceholderText("e.g., C-suite, technical, general")
        tone_label = QLabel("Tone:")
        tone_label.setFont(QFont("Montserrat", 11))
        self.tone_input = QLineEdit()
        self.tone_input.setFont(QFont("Fira Mono", 11))
        self.tone_input.setPlaceholderText("e.g., formal, technical, accessible")
        improvement_label = QLabel("Improvement:")
        improvement_label.setFont(QFont("Montserrat", 11))
        self.improvement_input = QLineEdit()
        self.improvement_input.setFont(QFont("Fira Mono", 11))
        self.improvement_input.setPlaceholderText("Anything to improve or focus on (optional)")
        extras_layout.addWidget(audience_label)
        extras_layout.addWidget(self.audience_input)
        extras_layout.addWidget(tone_label)
        extras_layout.addWidget(self.tone_input)
        extras_layout.addWidget(improvement_label)
        extras_layout.addWidget(self.improvement_input)
        left_vbox.addLayout(extras_layout)

        # Model selection
        model_layout = QHBoxLayout()
        model_label = QLabel("Ollama Model:")
        model_label.setFont(QFont("Montserrat", 11))
        self.model_combo = QComboBox()
        self.model_combo.setFont(QFont("Fira Mono", 11))
        # Dynamically populate model list
        import subprocess, re
        self.model_combo.setEditable(False)
        try:
            result = subprocess.run(['ollama', 'list'], capture_output=True, text=True, check=True)
            lines = result.stdout.strip().split('\n')
            models = []
            for line in lines[1:]:  # skip header
                fields = re.split(r'\s{2,}', line.strip())
                if len(fields) >= 3:
                    name = fields[0]
                    size = fields[2]
                    models.append({'name': name, 'size': size})
            if not models:
                self.model_combo.addItem(DEFAULT_MODEL)
            else:
                for m in models:
                    self.model_combo.addItem(f"{m['name']}  [size: {m['size']}]", m['name'])
        except Exception as e:
            self.model_combo.addItem(DEFAULT_MODEL)
            QMessageBox.warning(self, "Ollama Models Not Found", f"Could not list Ollama models. Defaulting to '{DEFAULT_MODEL}'.\nError: {e}")
        model_layout.addWidget(model_label)
        model_layout.addWidget(self.model_combo)
        left_vbox.addLayout(model_layout)

        # Number of web results
        from PyQt5.QtWidgets import QSpinBox, QDoubleSpinBox, QGroupBox, QFormLayout
        results_layout = QHBoxLayout()
        results_label = QLabel("Number of Web Results:")
        results_label.setFont(QFont("Montserrat", 11))
        self.results_spin = QSpinBox()
        self.results_spin.setRange(1, 20)
        self.results_spin.setValue(10)
        self.results_spin.setFont(QFont("Fira Mono", 11))
        results_layout.addWidget(results_label)
        results_layout.addWidget(self.results_spin)
        left_vbox.addLayout(results_layout)

        # Advanced LLM Settings
        adv_group = QGroupBox("Advanced LLM Settings")
        adv_form = QFormLayout()
        # Temperature
        self.temp_spin = QDoubleSpinBox()
        self.temp_spin.setRange(0.0, 1.5)
        self.temp_spin.setSingleStep(0.01)
        self.temp_spin.setValue(0.7)
        adv_form.addRow("Temperature:", self.temp_spin)
        # Max Tokens
        self.max_tokens_spin = QSpinBox()
        self.max_tokens_spin.setRange(128, 4096)
        self.max_tokens_spin.setValue(2048)
        adv_form.addRow("Max Tokens:", self.max_tokens_spin)
        # System Prompt
        self.system_prompt_input = QTextEdit()
        self.system_prompt_input.setPlaceholderText("Optional system prompt for the LLM")
        self.system_prompt_input.setFixedHeight(40)
        adv_form.addRow("System Prompt:", self.system_prompt_input)
        # Context Window
        self.ctx_window_spin = QSpinBox()
        self.ctx_window_spin.setRange(128, 8192)
        self.ctx_window_spin.setValue(2048)
        adv_form.addRow("Context Window:", self.ctx_window_spin)
        adv_group.setLayout(adv_form)
        left_vbox.addWidget(adv_group)

        # File name
        file_layout = QHBoxLayout()
        file_label = QLabel("Save Report As:")
        file_label.setFont(QFont("Montserrat", 11))
        self.file_input = QLineEdit()
        self.file_input.setFont(QFont("Fira Mono", 11))
        self.file_input.setPlaceholderText("research_report.txt")
        browse_btn = QPushButton("Browse…")
        browse_btn.clicked.connect(self.browse_file)
        file_layout.addWidget(file_label)
        file_layout.addWidget(self.file_input)
        file_layout.addWidget(browse_btn)
        left_vbox.addLayout(file_layout)

        # --- Progress/Status Panel ---
        from PyQt5.QtWidgets import QProgressBar
        progress_panel = QVBoxLayout()
        self.progress_label = QLabel("")
        self.progress_label.setFont(QFont("Montserrat", 11, QFont.Bold))
        self.progress_substep = QLabel("")
        self.progress_substep.setFont(QFont("Fira Mono", 10))
        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        self.progress_log = QTextEdit()
        self.progress_log.setFont(QFont("Fira Mono", 9))
        self.progress_log.setReadOnly(True)
        self.progress_log.setMaximumHeight(80)
        progress_panel.addWidget(self.progress_label)
        progress_panel.addWidget(self.progress_substep)
        progress_panel.addWidget(self.progress_bar)
        progress_panel.addWidget(self.progress_log)
        left_vbox.addLayout(progress_panel)

        # Theme toggle button
        self.theme_is_dark = False
        self.theme_btn = QPushButton("🌙 Dark Mode")
        self.theme_btn.setFont(QFont("Montserrat", 10))
        self.theme_btn.clicked.connect(self.toggle_theme)
        left_vbox.addWidget(self.theme_btn)

        # Run button
        self.run_btn = QPushButton("Run Research")
        self.run_btn.setFont(QFont("Montserrat", 13, QFont.Bold))
        self.run_btn.clicked.connect(self.run_research)
        left_vbox.addWidget(self.run_btn)

        # Clear button
        self.clear_btn = QPushButton("Clear")
        self.clear_btn.setFont(QFont("Montserrat", 11))
        self.clear_btn.clicked.connect(self.clear_fields)
        left_vbox.addWidget(self.clear_btn)

        # Citation style selector
        citation_layout = QHBoxLayout()
        citation_label = QLabel("Citation Style:")
        citation_label.setFont(QFont("Montserrat", 11))
        self.citation_combo = QComboBox()
        self.citation_combo.setFont(QFont("Fira Mono", 11))
        self.citation_combo.addItems(["APA", "MLA"])
        citation_layout.addWidget(citation_label)
        citation_layout.addWidget(self.citation_combo)
        citation_layout.addStretch()
        left_vbox.addLayout(citation_layout)

        left_widget.setLayout(left_vbox)
        print("DEBUG: Left panel widgets added and layout set")

        # --- Right panel: Output & Reports ---
        print("DEBUG: Initializing right panel widgets")
        right_panel = QWidget()
        right_vbox = QVBoxLayout()
        right_vbox.setSpacing(16)
        right_vbox.setContentsMargins(24, 18, 12, 18)

        # Output box
        self.output_box = QTextEdit()
        self.output_box.setFont(QFont("Fira Mono", 11))
        self.output_box.setReadOnly(True)
        right_vbox.addWidget(self.output_box)

        # Report list
        self.report_list = QListWidget()
        self.report_list.setFont(QFont("Fira Mono", 11))
        right_vbox.addWidget(self.report_list)

        # Report preview
        self.report_preview = QTextEdit()
        self.report_preview.setFont(QFont("Fira Mono", 11))
        self.report_preview.setReadOnly(True)
        right_vbox.addWidget(self.report_preview)

        # Report actions
        report_actions_layout = QHBoxLayout()
        open_report_btn = QPushButton("Open Report")
        open_report_btn.clicked.connect(self.open_report_in_current)
        report_actions_layout.addWidget(open_report_btn)
        refresh_reports_btn = QPushButton("Refresh Reports")
        refresh_reports_btn.clicked.connect(self.refresh_report_list)
        report_actions_layout.addWidget(refresh_reports_btn)
        right_vbox.addLayout(report_actions_layout)

        right_panel.setLayout(right_vbox)
        print("DEBUG: Right panel widgets added and layout set")

        splitter.addWidget(left_widget)
        splitter.addWidget(right_panel)
        splitter.setStretchFactor(0, 2)
        splitter.setStretchFactor(1, 3)
        splitter.setSizes([500, 700])

        self.setCentralWidget(splitter)
        print("DEBUG: Splitter and central widget set")

        # Menu bar setup (must be before any use of 'menu')
        print("DEBUG: Setting up menu bar")
        menu = self.menuBar()
        file_menu = menu.addMenu("File")
        save_action = QAction("Save Report", self)
        save_action.triggered.connect(self.save_report)
        file_menu.addAction(save_action)
        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        help_menu = menu.addMenu("Help")
        about_action = QAction("About", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
        print("DEBUG: Menu bar setup complete")

        # Ensure documents directory exists
        ensure_documents_dir()
        print("DEBUG: Finished _init_ui")

    def clear_fields(self):
        """Clear all input fields and output box to prepare for a new query."""
        self.query_input.clear()
        self.audience_input.clear()
        self.tone_input.clear()
        self.improvement_input.clear()
        self.file_input.clear()
        self.output_box.clear()
        self.progress_label.setText("")
        self.progress_substep.setText("")
        self.progress_bar.setValue(0)
        self.progress_log.clear()

    def browse_file(self):
        fname, _ = QFileDialog.getSaveFileName(self, "Save Research Report As", str(DOCUMENTS_DIR / "research_report.txt"), "Text/Markdown Files (*.txt *.md)")
        if fname:
            self.file_input.setText(fname)

    def run_research(self):
        query = self.query_input.toPlainText().strip()
        # If user selected from dropdown, extract model name (strip size info)
        model_data = self.model_combo.currentData()
        if model_data:
            model = model_data.strip()
        else:
            model = self.model_combo.currentText().split()[0].strip()
        filename = self.file_input.text().strip()
        # If blank, use default in DOCUMENTS_DIR
        if not filename:
            filename = str(DOCUMENTS_DIR / "research_report.txt")
        # If only a filename (no path), prepend DOCUMENTS_DIR
        elif not os.path.isabs(filename):
            filename = str(DOCUMENTS_DIR / filename)
        audience = self.audience_input.text().strip()
        tone = self.tone_input.text().strip()
        improvement = self.improvement_input.text().strip()
        if not query:
            QMessageBox.warning(self, "No Query", "Please enter a research question or topic.")
            return
        # Validate filename
        if not filename.lower().endswith(('.txt', '.md')):
            filename += '.txt'
        num_results = self.results_spin.value()
        temperature = self.temp_spin.value()
        max_tokens = self.max_tokens_spin.value()
        system_prompt = self.system_prompt_input.toPlainText().strip()
        ctx_window = self.ctx_window_spin.value()
        self.output_box.setPlainText("Running research... Please wait.")
        self.progress_label.setText("Initializing...")
        self.progress_substep.setText("")
        self.progress_bar.setValue(0)
        self.progress_log.clear()
        self.run_btn.setEnabled(False)
        # Start backend in a thread
        citation_style = self.citation_combo.currentText()
        self.worker = ResearchWorker(
            query, model, filename, audience, tone, improvement,
            num_results=num_results, temperature=temperature, max_tokens=max_tokens, system_prompt=system_prompt, ctx_window=ctx_window,
            citation_style=citation_style
        )
        self.worker.finished.connect(self.on_research_finished)
        self.worker.error.connect(self.on_research_error)
        self.worker.progress.connect(self.on_progress_update)
        self.worker.start()

    def on_progress_update(self, desc, bar, substep=None, percent=None, log=None):
        self.progress_label.setText(desc)
        if substep is not None:
            self.progress_substep.setText(substep)
        if percent is not None:
            self.progress_bar.setValue(percent)
        else:
            self.progress_bar.setValue(0)
        if log:
            self.append_log(log)

    def append_log(self, msg):
        self.progress_log.append(msg)
        self.progress_log.moveCursor(self.progress_log.textCursor().End)

    def on_research_finished(self, result, filename):
        # Only show the report if the filename matches what we expect (not README)
        if os.path.basename(filename).lower().startswith("readme"):
            self.output_box.setPlainText("[Error: Report file was not generated. Please check your save path and try again.]")
        else:
            # Try to render Markdown as HTML
            try:
                import markdown2
                html = markdown2.markdown(result)
                self.output_box.setHtml(html)
            except ImportError:
                self.output_box.setPlainText(result)
        self.run_btn.setEnabled(True)
        self.progress_label.setText("Done!")
        self.progress_substep.setText("")
        self.progress_bar.setValue(100)
        # Optionally clear or finalize log
        # Refresh previous reports list and select the new report
        self.refresh_report_list()
        # Try to select and preview the new report in the list
        for i in range(self.report_list.count()):
            item = self.report_list.item(i)
            if item.text() == os.path.basename(filename):
                self.report_list.setCurrentItem(item)
                self.load_selected_report(item)
                break
        QMessageBox.information(self, "Research Complete", f"Research report saved to:\n{filename}")

    def on_research_error(self, error_msg, tb):
        self.output_box.setPlainText(f"[Error]\n{error_msg}\n{tb}")
        self.run_btn.setEnabled(True)
        QMessageBox.critical(self, "Error", f"An error occurred:\n{error_msg}")

    def export_report(self):
        content = self.output_box.toPlainText()
        if not content.strip():
            QMessageBox.information(self, "Nothing to Export", "There is no research report to export.")
            return
        from PyQt5.QtWidgets import QFileDialog
        fname, selected_filter = QFileDialog.getSaveFileName(
            self, "Export Research Report", str(DOCUMENTS_DIR / "research_report"),
            "Markdown (*.md);;HTML (*.html);;PDF (*.pdf);;Word Document (*.docx);;Text (*.txt)")
        if not fname:
            return
        ext = os.path.splitext(fname)[1].lower()
        try:
            if ext == ".md":
                with open(fname, "w", encoding="utf-8") as f:
                    f.write(content)
            elif ext == ".html":
                try:
                    import markdown2
                    html = markdown2.markdown(content)
                except ImportError:
                    html = "<pre>" + content + "</pre>"
                with open(fname, "w", encoding="utf-8") as f:
                    f.write(html)
            elif ext == ".pdf":
                try:
                    from reportlab.lib.pagesizes import letter
                    from reportlab.pdfgen import canvas
                    c = canvas.Canvas(fname, pagesize=letter)
                    width, height = letter
                    lines = content.splitlines()
                    y = height - 40
                    for line in lines:
                        c.drawString(40, y, line[:120])
                        y -= 14
                        if y < 40:
                            c.showPage()
                            y = height - 40
                    c.save()
                except ImportError:
                    QMessageBox.warning(self, "PDF Export Error", "reportlab is not installed. Please install it for PDF export.")
                    return
            elif ext == ".docx":
                try:
                    from docx import Document
                    doc = Document()
                    for para in content.split('\n\n'):
                        doc.add_paragraph(para)
                    doc.save(fname)
                except ImportError:
                    QMessageBox.warning(self, "DOCX Export Error", "python-docx is not installed. Please install it for DOCX export.")
                    return
            else:
                with open(fname, "w", encoding="utf-8") as f:
                    f.write(content)
            QMessageBox.information(self, "Exported", f"Report exported to {fname}")
        except Exception as e:
            QMessageBox.critical(self, "Export Error", f"Could not export report:\n{e}")

    def save_report(self):
        content = self.output_box.toPlainText()
        if not content.strip():
            QMessageBox.information(self, "Nothing to Save", "There is no research report to save.")
            return
        fname, _ = QFileDialog.getSaveFileName(self, "Save Research Report", str(DOCUMENTS_DIR / "research_report.txt"), "Text Files (*.txt);;All Files (*)")
        if fname:
            with open(fname, "w", encoding="utf-8") as f:
                f.write(content)
            QMessageBox.information(self, "Saved", f"Report saved to {fname}")

    def use_output_as_query(self):
        """Copy the research report to the query box for further refinement."""
        report_text = self.output_box.toPlainText()
        self.query_input.setPlainText(report_text)

    # --- Report Viewer Functions ---
    def refresh_report_list(self):
        self.report_list.clear()
        files = []
        for ext in (".md", ".txt"):
            files += sorted(DOCUMENTS_DIR.glob(f"*{ext}"), key=os.path.getmtime, reverse=True)
        for file in files:
            self.report_list.addItem(str(file.name))

    def filter_report_list(self, text):
        for i in range(self.report_list.count()):
            item = self.report_list.item(i)
            item.setHidden(text.lower() not in item.text().lower())

    def load_selected_report(self, item):
        fname = DOCUMENTS_DIR / item.text()
        self._last_selected_report_path = str(fname)
        try:
            with open(fname, "r", encoding="utf-8") as f:
                content = f.read()
            self.report_preview.setPlainText(content)
        except Exception as e:
            self.report_preview.setPlainText(f"[Error loading report: {e}]")

    def open_report_in_current(self):
        """Load the selected previous report into the main output area for editing/refinement."""
        selected_items = self.report_list.selectedItems()
        if not selected_items:
            QMessageBox.information(self, "No Report Selected", "Please select a report to open.")
            return
        fname = DOCUMENTS_DIR / selected_items[0].text()
        try:
            with open(fname, "r", encoding="utf-8") as f:
                content = f.read()
            self.output_box.setPlainText(content)
            # Removed: self.tab_widget.setCurrentIndex(0)
        except Exception as e:
            QMessageBox.critical(self, "Open Report Error", f"Could not open report:\n{e}")

    def show_about(self):
        QMessageBox.about(self, "About Shell GPT Research Agent GUI",
            "<b>Shell GPT Research Agent GUI</b><br>"
            "A scientific, modern interface for research synthesis using local LLMs and web search.<br><br>"
            "Created by Christopher Bradford.<br>Inspired by Shell-GPT.<br>"
            "<a href='https://github.com/sunkencity999/shell_gpt_researchAgent'>Project Repository</a>")


def main():
    app = QApplication(sys.argv)
    app.setApplicationName(APP_TITLE)
    gui = ResearchAgentGUI()
    gui.show()
    sys.exit(app.exec_())

# --- Threaded backend worker ---
class ResearchWorker(QThread):
    finished = pyqtSignal(str, str)  # result, filename
    error = pyqtSignal(str, str)     # error_msg, traceback
    progress = pyqtSignal(str, str, object, object, object)  # desc, bar, substep, percent, log

    def __init__(self, query, model, filename, audience, tone, improvement,
                 num_results=10, temperature=0.7, max_tokens=2048, system_prompt="", ctx_window=2048, citation_style="APA"): 
        super().__init__()
        self.query = query
        self.model = model
        self.filename = filename
        self.audience = audience
        self.tone = tone
        self.improvement = improvement
        self.num_results = num_results
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.system_prompt = system_prompt
        self.ctx_window = ctx_window
        self.citation_style = citation_style

    def run(self):
        try:
            agent = ResearchAgent(model=self.model)
            def progress_callback(desc, bar, substep, percent, log):
                self.progress.emit(desc, bar, substep, percent, log)
            agent.run(
                self.query,
                audience=self.audience,
                tone=self.tone,
                improvement=self.improvement,
                num_results=self.num_results,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                system_prompt=self.system_prompt,
                ctx_window=self.ctx_window,
                citation_style=self.citation_style,
                filename=self.filename,
                progress_callback=progress_callback
            )
            with open(self.filename, "r", encoding="utf-8") as f:
                result = f.read()
            self.finished.emit(result, self.filename)
        except Exception as e:
            import traceback as tb
            self.error.emit(str(e), tb.format_exc())

    def _make_bar(self, frac):
        total = 20
        filled = int(frac * total)
        bar = "[" + "█" * filled + "-" * (total - filled) + f"] {int(frac*100)}%"
        return bar

if __name__ == "__main__":
    # --- Embedding model and dependency check ---
    import subprocess, sys, re
    from PyQt5.QtWidgets import QApplication, QMessageBox
    app = QApplication(sys.argv)
    # 1. Check for Ollama embedding model
    try:
        ollama_models = subprocess.run(['ollama', 'list'], capture_output=True, text=True, check=True).stdout.strip().split('\n')
        embedding_model_present = any('nomic-embed-text:latest' in line for line in ollama_models)
        if not embedding_model_present:
            QMessageBox.critical(None, "Embedding Model Missing", "Required embedding model 'nomic-embed-text:latest' not found in Ollama. Please run:\n\nollama pull nomic-embed-text:latest")
            sys.exit(1)
    except Exception as e:
        QMessageBox.critical(None, "Ollama Error", f"Could not check Ollama models: {e}")
        sys.exit(1)
    # 2. Check for Python embedding dependencies
    try:
        import sentence_transformers, torch, numpy
    except ImportError as e:
        QMessageBox.critical(None, "Python Embedding Dependencies Missing", "Required Python embedding dependencies missing. Please install with:\n\npip install sentence-transformers torch numpy")
        sys.exit(1)
    main()
