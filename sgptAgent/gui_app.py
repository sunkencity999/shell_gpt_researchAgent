import os
import sys
from pathlib import Path
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, QLabel, 
    QTextEdit, QLineEdit, QPushButton, QSplitter, QComboBox, QSpinBox, 
    QDoubleSpinBox, QGroupBox, QFormLayout, QListWidget, QProgressBar, 
    QMessageBox, QFileDialog, QAction, QMenuBar, QScrollArea, QSizePolicy
)
from PyQt5.QtCore import QThread, pyqtSignal, Qt, QTimer
from PyQt5.QtGui import QIcon, QFont, QPalette, QColor, QPixmap

# Import our modern styling system and components
from sgptAgent.gui_styles import (
    get_modern_stylesheet, get_font, apply_button_style, 
    create_dark_palette, create_light_palette, COLORS, SPACING, RADIUS
)
from sgptAgent.gui_components import (
    ModernCard, IconButton, ModernInput, ModernComboBox, ModernSpinBox,
    ModernProgressBar, StatusBadge, CollapsibleSection, create_form_row,
    create_button_row, ICONS
)

# --- Configurable paths and constants ---
DOCUMENTS_DIR = Path(__file__).resolve().parent.parent / "documents"
DEFAULT_MODEL = "llama3:latest"
APP_TITLE = "Shell GPT Research Agent GUI"

# --- Import backend ---
from sgptAgent.agent import ResearchAgent
import traceback

# --- Helper functions ---
def ensure_documents_dir():
    DOCUMENTS_DIR.mkdir(exist_ok=True)

# --- Main Window ---
class ResearchAgentGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        
        # Set window properties
        self.setWindowTitle(APP_TITLE)
        self.setMinimumSize(800, 600)  # Increased minimum size for better layout
        self.resize(1200, 800)
        
        # Set application icon
        icon_path = os.path.join(os.path.dirname(__file__), "Assets", "sgptRAicon.png")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        else:
            self.setWindowIcon(QIcon.fromTheme("applications-science"))
        
        # Apply modern styling
        self._apply_modern_styling()
        
        # Initialize UI
        self._init_ui()
        
        # Set up research stages for progress tracking
        self.research_stages = [
            {'name': 'Planning', 'icon': '🧠', 'color': 'blue'},
            {'name': 'Searching', 'icon': '🔍', 'color': 'orange'},
            {'name': 'Processing', 'icon': '⚙️', 'color': 'purple'},
            {'name': 'Synthesizing', 'icon': '📝', 'color': 'green'},
            {'name': 'Finalizing', 'icon': '✨', 'color': 'success'}
        ]
    
    def _apply_modern_styling(self):
        """Apply modern light theme styling to the application."""
        # Set application font
        app = QApplication.instance()
        app.setFont(get_font('body_md'))
        
        # Apply light theme stylesheet and palette
        stylesheet = get_modern_stylesheet(dark_mode=False)
        app.setStyleSheet(stylesheet)
        app.setPalette(create_light_palette())

    def clear_fields(self):
        """Clear all input fields and output box to prepare for a new query."""
        self.query_input.clear()
        self.audience_input.clear()
        self.tone_input.clear()
        self.improvement_input.clear()
        self.file_input.clear()
        self.system_prompt_input.clear()
        self.output_box.clear()
        self.progress_bar.setValue(0)
        self.progress_label.setText("")
        self.progress_substep.setText("")
        self.progress_log.clear()
        
        # Reset enhanced progress tracking
        self.progress_timer.stop()
        self.research_start_time = None
        self.total_results_found = 0
        self.successful_queries = 0
        self.total_queries = 0
        self.current_step_count = 0
        self.estimated_total_steps = 0
        self.time_label.setText("⏱️ Elapsed: 0:00")
        self.eta_label.setText("🎯 ETA: --:--")
        self.results_label.setText("📊 Results: 0")
        self.success_label.setText("✅ Success: 0%")
        
        self.run_btn.setEnabled(True)
    
    def browse_file(self):
        fname, _ = QFileDialog.getSaveFileName(self, "Save Research Report As", str(DOCUMENTS_DIR / "research_report.txt"), "Text/Markdown Files (*.txt *.md)")
        if fname:
            self.file_input.setText(fname)

    def run_research(self):
        """Start the research process in a separate thread."""
        # Get values from modern input components
        query = self.query_input.toPlainText().strip()
        audience = self.audience_input.text().strip()
        tone = self.tone_input.text().strip()
        improvement = self.improvement_input.text().strip()
        
        # Get model name from combo box
        model_text = self.model_combo.currentText()
        if '[' in model_text:
            model = self.model_combo.currentData() or model_text.split('[')[0].strip()
        else:
            model = model_text
        
        num_results = self.results_spin.value()
        temperature = self.temp_spin.value()
        max_tokens = self.max_tokens_spin.value()
        system_prompt = self.system_prompt_input.toPlainText().strip()
        ctx_window = self.ctx_window_spin.value()
        citation_style = self.citation_combo.currentText()
        filename = self.file_input.text().strip() or "research_report.txt"

        if not query:
            QMessageBox.warning(self, "Input Required", "Please enter a research query.")
            return

        # Disable the run button and clear output
        self.run_btn.setEnabled(False)
        self.output_box.clear()
        self.progress_bar.setValue(0)
        self.progress_label.setText("Initializing research...")
        self.progress_substep.setText("")
        
        # Initialize enhanced progress tracking
        import time
        self.research_start_time = time.time()
        self.total_results_found = 0
        self.successful_queries = 0
        self.total_queries = 0
        self.current_step_count = 0
        self.estimated_total_steps = 5  # Initial estimate, will be updated
        self.progress_timer.start()
        
        # Reset metrics display
        self.time_label.setText("⏱️ Elapsed: 0:00")
        self.eta_label.setText("🎯 ETA: Calculating...")
        self.results_label.setText("📊 Results: 0")
        self.success_label.setText("✅ Success: 0%")
        
        # Create and start the worker thread
        self.worker = ResearchWorker(
            query, audience, tone, improvement, model, num_results,
            temperature, max_tokens, system_prompt, ctx_window, citation_style, filename
        )
        self.worker.progress.connect(self.update_progress)
        self.worker.finished.connect(self.research_finished)
        self.worker.error.connect(self.research_error)
        self.worker.start()

    def update_progress(self, desc, bar, substep=None, percent=None, log=None):
        """Update progress display with enhanced metrics tracking."""
        if desc:
            self.progress_label.setText(desc)
        
        if bar:
            # Update progress bar with stage information
            if isinstance(bar, str) and bar.endswith('%'):
                try:
                    value = int(bar.replace('%', ''))
                    self.progress_bar.setValue(value)
                except ValueError:
                    pass
            else:
                self.progress_bar.setFormat(str(bar))
        
        if substep:
            self.progress_substep.setText(substep)
            # Track step progress for ETA calculation
            if "Step" in substep:
                try:
                    # Extract step numbers like "Step 3/7"
                    if "/" in substep:
                        parts = substep.split()
                        for part in parts:
                            if "/" in part:
                                current, total = part.split("/")
                                self.current_step_count = int(current)
                                self.estimated_total_steps = int(total)
                                break
                except (ValueError, IndexError):
                    pass
        
        if percent is not None:
            self.progress_bar.setValue(int(percent))
        
        if log:
            self.progress_log.append(log)
            
            # Track search metrics from log messages
            log_lower = log.lower()
            if "query:" in log_lower or "searching" in log_lower:
                self.total_queries += 1
            elif "found" in log_lower and "results" in log_lower:
                try:
                    # Extract result count from messages like "Found 5 results"
                    words = log.split()
                    for i, word in enumerate(words):
                        if word.lower() == "found" and i + 1 < len(words):
                            try:
                                count = int(words[i + 1])
                                self.total_results_found += count
                                if count > 0:
                                    self.successful_queries += 1
                                break
                            except ValueError:
                                continue
                except:
                    pass
            
            # Update results counter
            self.results_label.setText(f"📊 Results: {self.total_results_found}")
    
    def research_finished(self, result):
        """Handle research completion with enhanced metrics."""
        self.output_box.setPlainText(result)
        self.progress_label.setText("✅ Research completed successfully!")
        self.progress_substep.setText(f"Generated {len(result.split())} words from {self.total_results_found} sources")
        self.progress_bar.setValue(100)
        self.progress_timer.stop()
        self.eta_label.setText("🎯 Completed!")
        self.run_btn.setEnabled(True)
    
    def research_error(self, error_msg):
        """Handle research errors with enhanced feedback."""
        self.output_box.setPlainText(f"Research failed: {error_msg}")
        self.progress_label.setText("❌ Research failed")
        self.progress_substep.setText(error_msg)
        self.progress_bar.setValue(0)
        self.progress_timer.stop()
        self.eta_label.setText("🎯 Failed")
        self.run_btn.setEnabled(True)

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
        """Refresh the list of saved reports."""
        try:
            self.report_list.clear()
            files = []
            for ext in (".md", ".txt"):
                files += sorted(DOCUMENTS_DIR.glob(f"*{ext}"), key=os.path.getmtime, reverse=True)
            for file in files:
                self.report_list.addItem(str(file.name))
        except Exception as e:
            print(f"[WARNING] Error refreshing report list: {e}")
            # Continue gracefully even if refresh fails

    def filter_report_list(self, text):
        """Filter the report list based on search text."""
        try:
            for i in range(self.report_list.count()):
                item = self.report_list.item(i)
                if item:  # Check if item exists
                    item.setHidden(text.lower() not in item.text().lower())
        except Exception as e:
            print(f"[WARNING] Error filtering report list: {e}")

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

    def _init_ui(self):
        """Initialize the modern user interface."""
        # Set minimum and default window size
        self.setMinimumSize(800, 600)
        self.resize(1200, 800)
        
        # Main splitter for responsive layout
        splitter = QSplitter(Qt.Horizontal)
        splitter.setChildrenCollapsible(True)  # Allow collapsing for small screens

        # --- Left panel: Inputs & Controls ---
        left_widget = self._create_left_panel()
        left_widget.setMinimumWidth(300)  # Minimum width for usability
        
        # --- Right panel: Output & Reports ---
        right_widget = self._create_right_panel()
        right_widget.setMinimumWidth(400)  # Minimum width for readability

        splitter.addWidget(left_widget)
        splitter.addWidget(right_widget)
        splitter.setStretchFactor(0, 1)  # Left panel gets less space
        splitter.setStretchFactor(1, 2)  # Right panel gets more space
        
        # Set initial sizes with better proportions
        splitter.setSizes([400, 800])

        self.setCentralWidget(splitter)
        
        # Setup menu bar
        self._setup_menu_bar()
        
        # Ensure documents directory exists
        ensure_documents_dir()

    def _create_left_panel(self):
        """Create the modern left panel with input controls."""
        # Create scroll area for the left panel
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        left_widget = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(SPACING['md'])  # Reduced spacing for better fit
        layout.setContentsMargins(SPACING['lg'], SPACING['md'], SPACING['md'], SPACING['md'])
        
        # Logo section
        logo_card = ModernCard()
        logo_card.setStyleSheet(f"""
            ModernCard {{
                background: white;
                border: 1px solid #e5e7eb;
                border-radius: {RADIUS['lg']}px;
                margin: 4px;
            }}
        """)
        logo_layout = logo_card.setup_layout()
        
        logo_label = QLabel()
        # Load and display the actual logo
        logo_pixmap = QPixmap("sgptAgent/Assets/sgptRAicon.png")
        if not logo_pixmap.isNull():
            # Scale the logo to a large, prominent size while maintaining aspect ratio
            scaled_pixmap = logo_pixmap.scaled(160, 160, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            logo_label.setPixmap(scaled_pixmap)
        else:
            # Fallback to emoji if logo can't be loaded
            logo_label.setText("🔬")
            logo_label.setFont(QFont("Arial", 96))
        logo_label.setAlignment(Qt.AlignCenter)
        logo_label.setStyleSheet("padding: 20px;")
        
        logo_layout.addWidget(logo_label)
        layout.addWidget(logo_card)
        
        # Query input section
        query_card = ModernCard("Research Query")
        query_layout = query_card.setup_layout()
        
        self.query_input = ModernInput(
            placeholder="Enter your research question or topic...",
            multiline=True
        )
        query_layout.addWidget(self.query_input)
        layout.addWidget(query_card)
        
        # Research parameters section
        params_card = ModernCard("Research Parameters")
        params_layout = params_card.setup_layout()
        
        # Audience, Tone, Improvement in a grid
        row1_layout = QHBoxLayout()
        self.audience_input = ModernInput(placeholder="e.g., C-suite, technical, general")
        self.tone_input = ModernInput(placeholder="e.g., formal, technical, accessible")
        row1_layout.addWidget(create_form_row("Audience:", self.audience_input))
        row1_layout.addWidget(create_form_row("Tone:", self.tone_input))
        params_layout.addLayout(row1_layout)
        
        self.improvement_input = ModernInput(placeholder="Anything to improve or focus on (optional)")
        params_layout.addWidget(create_form_row("Improvement:", self.improvement_input))
        
        # Model and results count
        row2_layout = QHBoxLayout()
        self.model_combo = ModernComboBox()
        self._populate_model_list()
        
        self.results_spin = ModernSpinBox(1, 20, 10)
        row2_layout.addWidget(create_form_row("Model:", self.model_combo))
        row2_layout.addWidget(create_form_row("Web Results:", self.results_spin))
        params_layout.addLayout(row2_layout)
        
        layout.addWidget(params_card)
        
        # Advanced settings (collapsible)
        self.advanced_section = CollapsibleSection("Advanced LLM Settings")
        advanced_layout = QVBoxLayout()
        
        # Temperature and Max Tokens
        adv_row1 = QHBoxLayout()
        self.temp_spin = ModernSpinBox(0.0, 1.5, 0.7, is_double=True, step=0.01)
        self.max_tokens_spin = ModernSpinBox(128, 4096, 2048)
        adv_row1.addWidget(create_form_row("Temperature:", self.temp_spin))
        adv_row1.addWidget(create_form_row("Max Tokens:", self.max_tokens_spin))
        advanced_layout.addLayout(adv_row1)
        
        # System prompt and context window
        self.system_prompt_input = ModernInput(
            placeholder="Optional system prompt for the LLM",
            multiline=True
        )
        advanced_layout.addWidget(create_form_row("System Prompt:", self.system_prompt_input))
        
        self.ctx_window_spin = ModernSpinBox(128, 8192, 2048)
        advanced_layout.addWidget(create_form_row("Context Window:", self.ctx_window_spin))
        
        self.advanced_section.add_layout(advanced_layout)
        layout.addWidget(self.advanced_section)
        
        # File output section
        file_card = ModernCard("Output Settings")
        file_layout = file_card.setup_layout()
        
        file_row_widget = QWidget()
        file_row = QHBoxLayout()
        file_row.setContentsMargins(0, 0, 0, 0)
        self.file_input = ModernInput(placeholder="research_report.txt")
        browse_btn = IconButton("folder", "Browse", "secondary")
        browse_btn.clicked.connect(self.browse_file)
        file_row.addWidget(self.file_input, 1)
        file_row.addWidget(browse_btn)
        file_row_widget.setLayout(file_row)
        file_layout.addWidget(create_form_row("Save As:", file_row_widget))
        
        self.citation_combo = ModernComboBox()
        self.citation_combo.addItems(["APA", "MLA"])
        file_layout.addWidget(create_form_row("Citation Style:", self.citation_combo))
        
        layout.addWidget(file_card)
        
        # Progress section
        progress_card = ModernCard("Research Progress")
        progress_layout = progress_card.setup_layout()
        
        # Main progress label
        self.progress_label = QLabel("")
        self.progress_label.setFont(get_font('body_lg'))
        
        # Substep with enhanced formatting
        self.progress_substep = QLabel("")
        self.progress_substep.setFont(get_font('body_md'))
        self.progress_substep.setStyleSheet(f"color: {COLORS['text_secondary']}; margin-bottom: 8px;")
        
        # Enhanced progress bar with percentage display
        self.progress_bar = ModernProgressBar()
        self.progress_bar.setFormat("%p% - %v/%m steps")
        
        # Progress metrics row
        metrics_widget = QWidget()
        metrics_layout = QHBoxLayout(metrics_widget)
        metrics_layout.setContentsMargins(0, 8, 0, 8)
        
        # Time tracking
        self.time_label = QLabel("⏱️ Elapsed: 0:00")
        self.time_label.setFont(get_font('body_sm'))
        self.time_label.setStyleSheet(f"color: {COLORS['text_secondary']};")
        
        # ETA estimation
        self.eta_label = QLabel("🎯 ETA: --:--")
        self.eta_label.setFont(get_font('body_sm'))
        self.eta_label.setStyleSheet(f"color: {COLORS['text_secondary']};")
        
        # Search results counter
        self.results_label = QLabel("📊 Results: 0")
        self.results_label.setFont(get_font('body_sm'))
        self.results_label.setStyleSheet(f"color: {COLORS['text_secondary']};")
        
        # Query success rate
        self.success_label = QLabel("✅ Success: 0%")
        self.success_label.setFont(get_font('body_sm'))
        self.success_label.setStyleSheet(f"color: {COLORS['text_secondary']};")
        
        metrics_layout.addWidget(self.time_label)
        metrics_layout.addWidget(self.eta_label)
        metrics_layout.addWidget(self.results_label)
        metrics_layout.addWidget(self.success_label)
        metrics_layout.addStretch()
        
        # Detailed progress log with better formatting
        self.progress_log = QTextEdit()
        self.progress_log.setFont(get_font('code'))
        self.progress_log.setReadOnly(True)
        self.progress_log.setMaximumHeight(100)
        self.progress_log.setStyleSheet(f"""
            QTextEdit {{
                background-color: {COLORS['surface']};
                border: 1px solid {COLORS['border']};
                border-radius: 6px;
                padding: 8px;
            }}
        """)
        
        # Initialize progress tracking variables
        self.research_start_time = None
        self.total_results_found = 0
        self.successful_queries = 0
        self.total_queries = 0
        self.current_step_count = 0
        self.estimated_total_steps = 0
        
        # Progress timer for real-time updates
        self.progress_timer = QTimer()
        self.progress_timer.timeout.connect(self.update_time_display)
        self.progress_timer.setInterval(1000)  # Update every second
        
        progress_layout.addWidget(self.progress_label)
        progress_layout.addWidget(self.progress_substep)
        progress_layout.addWidget(self.progress_bar)
        progress_layout.addWidget(metrics_widget)
        progress_layout.addWidget(self.progress_log)
        layout.addWidget(progress_card)
        
        # Create action buttons
        self.clear_btn = IconButton(
            "clear", 
            "Clear",
            "secondary"
        )
        self.clear_btn.clicked.connect(self.clear_fields)
        
        self.run_btn = IconButton(
            "research", 
            "Start Research",
            "primary"
        )
        self.run_btn.clicked.connect(self.run_research)
        
        # Action buttons - use responsive button row
        action_buttons = create_button_row([self.clear_btn])
        layout.addWidget(action_buttons)
        
        # Run button - full width for prominence
        self.run_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        layout.addWidget(self.run_btn)
        
        layout.addStretch()
        
        left_widget.setLayout(layout)
        scroll_area.setWidget(left_widget)
        return scroll_area
    
    def _create_right_panel(self):
        """Create the modern right panel with output and reports."""
        right_widget = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(SPACING['lg'])
        layout.setContentsMargins(SPACING['md'], SPACING['lg'], SPACING['xl'], SPACING['lg'])
        
        # Output section
        output_card = ModernCard("Research Output")
        output_layout = output_card.setup_layout()
        
        self.output_box = QTextEdit()
        self.output_box.setFont(get_font('code'))
        self.output_box.setReadOnly(True)
        output_layout.addWidget(self.output_box)
        layout.addWidget(output_card, 2)
        
        # Reports section
        reports_card = ModernCard("Saved Reports")
        reports_layout = reports_card.setup_layout()
        
        self.report_list = QListWidget()
        self.report_list.setFont(get_font('body_md'))
        reports_layout.addWidget(self.report_list)
        
        # Report actions
        open_report_btn = IconButton("document", "Open Report", "secondary")
        open_report_btn.clicked.connect(self.open_report_in_current)
        
        refresh_reports_btn = IconButton("refresh", "Refresh", "secondary")
        refresh_reports_btn.clicked.connect(self.refresh_report_list)
        
        report_actions = create_button_row([open_report_btn, refresh_reports_btn])
        reports_layout.addWidget(report_actions)
        
        layout.addWidget(reports_card, 1)
        
        # Report preview
        preview_card = ModernCard("Report Preview")
        preview_layout = preview_card.setup_layout()
        
        self.report_preview = QTextEdit()
        self.report_preview.setFont(get_font('code'))
        self.report_preview.setReadOnly(True)
        preview_layout.addWidget(self.report_preview)
        layout.addWidget(preview_card, 1)
        
        right_widget.setLayout(layout)
        return right_widget
    
    def _populate_model_list(self):
        """Populate the model combo box with available Ollama models."""
        import subprocess
        import re
        
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
                    # Filter out embedding models that don't support text generation
                    if not any(embed_keyword in name.lower() for embed_keyword in ['embed', 'embedding', 'nomic-embed']):
                        models.append({'name': name, 'size': size})
            
            if not models:
                self.model_combo.addItem(DEFAULT_MODEL)
            else:
                for m in models:
                    self.model_combo.addItem(f"{m['name']}  [size: {m['size']}]", m['name'])
        except Exception as e:
            self.model_combo.addItem(DEFAULT_MODEL)
            QMessageBox.warning(
                self, 
                "Ollama Models Not Found", 
                f"Could not list Ollama models. Defaulting to '{DEFAULT_MODEL}'.\nError: {e}"
            )
    
    def _setup_menu_bar(self):
        """Setup the application menu bar."""
        menu = self.menuBar()
        
        # File menu
        file_menu = menu.addMenu("File")
        save_action = QAction("Save Report", self)
        save_action.triggered.connect(self.save_report)
        file_menu.addAction(save_action)
        
        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Help menu
        help_menu = menu.addMenu("Help")
        about_action = QAction("About", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)

    def update_time_display(self):
        """Update elapsed time and ETA estimation"""
        if self.research_start_time:
            import time
            elapsed = time.time() - self.research_start_time
            elapsed_str = f"{int(elapsed//60)}:{int(elapsed%60):02d}"
            self.time_label.setText(f"⏱️ Elapsed: {elapsed_str}")
            
            # Calculate ETA based on progress
            if self.current_step_count > 0 and self.estimated_total_steps > 0:
                progress_ratio = self.current_step_count / self.estimated_total_steps
                if progress_ratio > 0:
                    estimated_total_time = elapsed / progress_ratio
                    remaining_time = estimated_total_time - elapsed
                    if remaining_time > 0:
                        eta_str = f"{int(remaining_time//60)}:{int(remaining_time%60):02d}"
                        self.eta_label.setText(f"🎯 ETA: {eta_str}")
                    else:
                        self.eta_label.setText("🎯 ETA: Almost done!")
            
            # Update success rate
            if self.total_queries > 0:
                success_rate = (self.successful_queries / self.total_queries) * 100
                self.success_label.setText(f"✅ Success: {success_rate:.0f}%")

def main():
    app = QApplication(sys.argv)
    app.setApplicationName(APP_TITLE)
    gui = ResearchAgentGUI()
    gui.show()
    sys.exit(app.exec_())

# --- Threaded backend worker ---
class ResearchWorker(QThread):
    finished = pyqtSignal(str)  # result
    error = pyqtSignal(str, str)     # error_msg, traceback
    progress = pyqtSignal(str, str, object, object, object)  # desc, bar, substep, percent, log

    def __init__(self, query, audience, tone, improvement, model, num_results,
                 temperature, max_tokens, system_prompt, ctx_window, citation_style, filename): 
        super().__init__()
        self.query = query
        self.audience = audience
        self.tone = tone
        self.improvement = improvement
        self.model = model
        self.num_results = num_results
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.system_prompt = system_prompt
        self.ctx_window = ctx_window
        self.citation_style = citation_style
        self.filename = filename

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
            self.finished.emit(result)
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
