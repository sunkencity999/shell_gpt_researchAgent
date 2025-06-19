"""
Modern GUI Components for ResearchAgent
Custom styled components with icons, improved layouts, and enhanced UX.
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QLineEdit, 
    QTextEdit, QGroupBox, QFrame, QProgressBar, QComboBox, QSpinBox,
    QDoubleSpinBox, QFormLayout, QSizePolicy, QScrollArea, QStackedWidget
)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer, QPropertyAnimation, QEasingCurve
from PyQt5.QtGui import QFont, QPainter, QPen, QColor
from .gui_styles import get_font, apply_button_style, COLORS, SPACING, RADIUS

# =============================================================================
# ICON SYSTEM (Unicode symbols for cross-platform compatibility)
# =============================================================================

ICONS = {
    # Actions
    'search': '🔍',
    'settings': '⚙️',
    'export': '📤',
    'import': '📥',
    'save': '💾',
    'open': '📂',
    'refresh': '🔄',
    'clear': '🗑️',
    'copy': '📋',
    'edit': '✏️',
    'delete': '❌',
    'add': '➕',
    'remove': '➖',
    
    # Status
    'success': '✅',
    'warning': '⚠️',
    'error': '❌',
    'info': 'ℹ️',
    'loading': '⏳',
    'progress': '📊',
    
    # Navigation
    'back': '←',
    'forward': '→',
    'up': '↑',
    'down': '↓',
    'expand': '▼',
    'collapse': '▲',
    'menu': '☰',
    
    # Content
    'document': '📄',
    'report': '📋',
    'chart': '📊',
    'image': '🖼️',
    'link': '🔗',
    'tag': '🏷️',
    'bookmark': '🔖',
    
    # Research specific
    'research': '🔬',
    'analysis': '📈',
    'synthesis': '🧠',
    'query': '❓',
    'results': '📊',
    'sources': '📚',
    'citation': '📝',
    
    # Theme
    'light_mode': '☀️',
    'dark_mode': '🌙',
    'theme': '🎨',
}

# =============================================================================
# CUSTOM COMPONENTS
# =============================================================================

class ModernCard(QGroupBox):
    """
    A modern card component with proper styling and spacing.
    """
    
    def __init__(self, title="", parent=None):
        super().__init__(title, parent)
        self.setObjectName("modernCard")
        # Don't setup layout automatically - let caller set it
    
    def setup_layout(self):
        """Setup the card layout with responsive spacing."""
        layout = QVBoxLayout()
        layout.setSpacing(SPACING['md'])
        layout.setContentsMargins(SPACING['md'], SPACING['md'], SPACING['md'], SPACING['md'])
        self.setLayout(layout)
        
        # Set size policy for better responsiveness
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        
        return layout
    
    def add_widget(self, widget):
        """Add a widget to the card."""
        if self.layout():
            self.layout().addWidget(widget)
    
    def add_layout(self, layout):
        """Add a layout to the card."""
        if self.layout():
            self.layout().addLayout(layout)

class IconButton(QPushButton):
    """
    A button with an icon and optional text.
    """
    
    def __init__(self, icon_key="", text="", variant="primary", parent=None):
        icon_text = ICONS.get(icon_key, icon_key)
        display_text = f"{icon_text} {text}".strip() if text else icon_text
        super().__init__(display_text, parent)
        
        self.icon_key = icon_key
        self.variant = variant
        
        # Apply styling
        apply_button_style(self, variant)
        self.setFont(get_font('button'))
        
        # Set minimum size for better touch targets
        self.setMinimumHeight(36)
        if not text:  # Icon-only button
            self.setMinimumWidth(36)
            self.setMaximumWidth(36)

class ModernInput(QWidget):
    """
    A modern input field with label, validation, and helper text.
    """
    
    textChanged = pyqtSignal(str)
    
    def __init__(self, label="", placeholder="", helper_text="", input_type="line", multiline=False, parent=None):
        super().__init__(parent)
        self.label_text = label
        self.helper_text = helper_text
        self.has_error = False
        self.multiline = multiline
        
        self._setup_ui(placeholder, input_type)
    
    def _setup_ui(self, placeholder, input_type):
        """Setup the input widget UI."""
        layout = QVBoxLayout()
        layout.setSpacing(SPACING['xs'])
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Label
        if self.label_text:
            self.label = QLabel(self.label_text)
            self.label.setFont(get_font('body_md'))
            layout.addWidget(self.label)
        
        # Input widget
        if input_type == "text" or self.multiline:
            self.input = QTextEdit()
            self.input.setMaximumHeight(100 if not self.multiline else 200)
            self.input.setMinimumHeight(60 if not self.multiline else 100)
        else:
            self.input = QLineEdit()
            self.input.setMinimumHeight(32)
            
        self.input.setFont(get_font('body_md'))
        
        # Set size policy for better responsiveness
        self.input.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed if input_type != "text" and not self.multiline else QSizePolicy.Preferred)
        
        if placeholder:
            self.input.setPlaceholderText(placeholder)
        
        layout.addWidget(self.input)
        
        # Helper text
        if self.helper_text:
            self.helper_label = QLabel(self.helper_text)
            self.helper_label.setFont(get_font('caption'))
            self.helper_label.setStyleSheet(f"color: {COLORS['text_muted']};")
            self.helper_label.setWordWrap(True)  # Allow text wrapping
            layout.addWidget(self.helper_label)
        
        self.setLayout(layout)
    
    def text(self):
        """Get the current text value."""
        if hasattr(self.input, 'toPlainText'):
            return self.input.toPlainText()
        else:
            return self.input.text()
    
    def toPlainText(self):
        """Get the current text as plain text (for compatibility)."""
        return self.text()
    
    def setText(self, text):
        """Set the text value."""
        if hasattr(self.input, 'setPlainText'):
            self.input.setPlainText(text)
        else:
            self.input.setText(text)
    
    def setPlainText(self, text):
        """Set the plain text (for compatibility)."""
        self.setText(text)
    
    def clear(self):
        """Clear the input."""
        self.input.clear()
    
    def set_error(self, has_error, error_message=""):
        """Set error state for the input."""
        self.has_error = has_error
        
        # Update helper text to show error
        if hasattr(self, 'helper_label'):
            if has_error and error_message:
                self.helper_label.setText(error_message)
                self.helper_label.setStyleSheet(f"color: {COLORS['error']};")
            else:
                self.helper_label.setText(self.helper_text)
                self.helper_label.setStyleSheet(f"color: {COLORS['text_muted']};")
        
        # Apply error styling to input
        if has_error:
            self.input.setProperty('class', 'error')
        else:
            self.input.setProperty('class', '')
        self.input.style().unpolish(self.input)
        self.input.style().polish(self.input)

class ModernComboBox(QWidget):
    """
    A modern combo box with label and styling.
    """
    
    currentTextChanged = pyqtSignal(str)
    
    def __init__(self, label="", items=None, parent=None):
        super().__init__(parent)
        self.label_text = label
        self._setup_ui(items or [])
    
    def _setup_ui(self, items):
        """Setup the combo box UI."""
        layout = QVBoxLayout()
        layout.setSpacing(SPACING['xs'])
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Label
        if self.label_text:
            self.label = QLabel(self.label_text)
            self.label.setFont(get_font('body_md'))
            layout.addWidget(self.label)
        
        # Combo box
        self.combo = QComboBox()
        self.combo.setFont(get_font('body_md'))
        self.combo.addItems(items)
        self.combo.currentTextChanged.connect(self.currentTextChanged.emit)
        
        layout.addWidget(self.combo)
        self.setLayout(layout)
    
    def addItem(self, text, data=None):
        """Add an item to the combo box."""
        self.combo.addItem(text, data)
    
    def addItems(self, items):
        """Add multiple items to the combo box."""
        self.combo.addItems(items)
    
    def currentText(self):
        """Get current selected text."""
        return self.combo.currentText()
    
    def currentData(self):
        """Get current selected data."""
        return self.combo.currentData()
    
    def setCurrentText(self, text):
        """Set current selected text."""
        self.combo.setCurrentText(text)
    
    def setEditable(self, editable):
        """Set whether the combo box is editable."""
        self.combo.setEditable(editable)
    
    def clear(self):
        """Clear all items from the combo box."""
        self.combo.clear()

class ModernSpinBox(QWidget):
    """
    A modern spin box with label and styling.
    """
    
    valueChanged = pyqtSignal(int)
    
    def __init__(self, min_val=0, max_val=100, default_val=0, label="", is_double=False, step=1, parent=None):
        super().__init__(parent)
        self.label_text = label
        self.is_double = is_double
        self._setup_ui(min_val, max_val, default_val, step)
    
    def _setup_ui(self, min_val, max_val, default_val, step):
        """Setup the spin box UI."""
        layout = QVBoxLayout()
        layout.setSpacing(SPACING['xs'])
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Label
        if self.label_text:
            self.label = QLabel(self.label_text)
            self.label.setFont(get_font('body_md'))
            layout.addWidget(self.label)
        
        # Spin box
        if self.is_double:
            self.spin = QDoubleSpinBox()
            self.spin.setDecimals(2)
        else:
            self.spin = QSpinBox()
        
        self.spin.setRange(min_val, max_val)
        self.spin.setValue(default_val)
        self.spin.setSingleStep(step)
        self.spin.setFont(get_font('body_md'))
        self.spin.valueChanged.connect(self.valueChanged.emit)
        
        layout.addWidget(self.spin)
        self.setLayout(layout)
    
    def value(self):
        """Get current value."""
        return self.spin.value()
    
    def setValue(self, value):
        """Set current value."""
        self.spin.setValue(value)

class ModernProgressBar(QWidget):
    """
    A modern progress bar with stages and status indicators.
    """
    
    def __init__(self, stages=None, parent=None):
        super().__init__(parent)
        self.stages = stages or []
        self.current_stage = 0
        self.progress_value = 0
        
        self._setup_ui()
    
    def _setup_ui(self):
        """Setup the progress bar UI."""
        layout = QVBoxLayout()
        layout.setSpacing(SPACING['sm'])
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Stage indicators (if stages provided)
        if self.stages:
            self.stage_layout = QHBoxLayout()
            self.stage_indicators = []
            
            for i, stage in enumerate(self.stages):
                indicator = QLabel(f"{stage.get('icon', '●')} {stage['name']}")
                indicator.setFont(get_font('caption'))
                indicator.setAlignment(Qt.AlignCenter)
                indicator.setMinimumHeight(24)
                indicator.setStyleSheet(f"""
                    QLabel {{
                        background-color: {COLORS['surface_hover']};
                        color: {COLORS['text_muted']};
                        border-radius: {RADIUS['sm']}px;
                        padding: {SPACING['xs']}px {SPACING['sm']}px;
                    }}
                """)
                
                self.stage_indicators.append(indicator)
                self.stage_layout.addWidget(indicator)
            
            layout.addLayout(self.stage_layout)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setFont(get_font('caption'))
        
        layout.addWidget(self.progress_bar)
        
        # Status label
        self.status_label = QLabel("")
        self.status_label.setFont(get_font('body_sm'))
        self.status_label.setStyleSheet(f"color: {COLORS['text_secondary']};")
        layout.addWidget(self.status_label)
        
        self.setLayout(layout)
    
    def set_progress(self, value, status=""):
        """Set progress value and status."""
        self.progress_value = value
        self.progress_bar.setValue(value)
        
        if status:
            self.status_label.setText(status)
    
    def set_stage(self, stage_index):
        """Set current active stage."""
        if not self.stages or stage_index >= len(self.stages):
            return
        
        self.current_stage = stage_index
        
        # Update stage indicators
        for i, indicator in enumerate(self.stage_indicators):
            stage = self.stages[i]
            
            if i < stage_index:
                # Completed stage
                indicator.setStyleSheet(f"""
                    QLabel {{
                        background-color: {COLORS['success']};
                        color: {COLORS['text_inverse']};
                        border-radius: {RADIUS['sm']}px;
                        padding: {SPACING['xs']}px {SPACING['sm']}px;
                    }}
                """)
            elif i == stage_index:
                # Current stage
                indicator.setStyleSheet(f"""
                    QLabel {{
                        background-color: {COLORS['primary']};
                        color: {COLORS['text_inverse']};
                        border-radius: {RADIUS['sm']}px;
                        padding: {SPACING['xs']}px {SPACING['sm']}px;
                    }}
                """)
            else:
                # Future stage
                indicator.setStyleSheet(f"""
                    QLabel {{
                        background-color: {COLORS['surface_hover']};
                        color: {COLORS['text_muted']};
                        border-radius: {RADIUS['sm']}px;
                        padding: {SPACING['xs']}px {SPACING['sm']}px;
                    }}
                """)
    
    def setValue(self, value):
        """Set progress value (compatibility method)."""
        self.set_progress(value)
    
    def setFormat(self, format_str):
        """Set progress bar format (compatibility method)."""
        self.progress_bar.setFormat(format_str)
    
    def value(self):
        """Get current progress value."""
        return self.progress_value
    
    def setVisible(self, visible):
        """Set visibility."""
        super().setVisible(visible)

class StatusBadge(QLabel):
    """
    A status badge component for showing status with color coding.
    """
    
    def __init__(self, text="", status="info", parent=None):
        super().__init__(text, parent)
        self.status = status
        self._apply_styling()
    
    def _apply_styling(self):
        """Apply status-specific styling."""
        status_colors = {
            'success': (COLORS['success'], COLORS['text_inverse']),
            'warning': (COLORS['warning'], COLORS['text_inverse']),
            'error': (COLORS['error'], COLORS['text_inverse']),
            'info': (COLORS['info'], COLORS['text_inverse']),
            'default': (COLORS['secondary'], COLORS['text_inverse']),
        }
        
        bg_color, text_color = status_colors.get(self.status, status_colors['default'])
        
        self.setStyleSheet(f"""
            QLabel {{
                background-color: {bg_color};
                color: {text_color};
                border-radius: {RADIUS['sm']}px;
                padding: {SPACING['xs']}px {SPACING['sm']}px;
                font-weight: 500;
            }}
        """)
        self.setFont(get_font('caption'))
        self.setAlignment(Qt.AlignCenter)
    
    def set_status(self, status, text=None):
        """Update the badge status and optionally text."""
        self.status = status
        if text is not None:
            self.setText(text)
        self._apply_styling()

class CollapsibleSection(QWidget):
    """
    A collapsible section widget for organizing content.
    """
    
    def __init__(self, title="", collapsed=False, parent=None):
        super().__init__(parent)
        self.title = title
        self.collapsed = collapsed
        self._setup_ui()
    
    def _setup_ui(self):
        """Setup the collapsible section UI."""
        layout = QVBoxLayout()
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Header button
        self.header_btn = QPushButton()
        self.header_btn.setFont(get_font('heading_sm'))
        self.header_btn.clicked.connect(self.toggle_collapsed)
        self._update_header()
        
        # Apply header styling
        self.header_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['surface_hover']};
                color: {COLORS['text_primary']};
                border: 1px solid {COLORS['border']};
                border-radius: {RADIUS['sm']}px;
                padding: {SPACING['md']}px;
                text-align: left;
                font-weight: 600;
            }}
            QPushButton:hover {{
                background-color: {COLORS['primary_light']};
            }}
        """)
        
        layout.addWidget(self.header_btn)
        
        # Content area
        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout()
        self.content_layout.setContentsMargins(SPACING['md'], SPACING['md'], SPACING['md'], SPACING['md'])
        self.content_widget.setLayout(self.content_layout)
        
        # Content styling
        self.content_widget.setStyleSheet(f"""
            QWidget {{
                background-color: {COLORS['surface']};
                border: 1px solid {COLORS['border']};
                border-top: none;
                border-radius: 0 0 {RADIUS['sm']}px {RADIUS['sm']}px;
            }}
        """)
        
        layout.addWidget(self.content_widget)
        
        # Set initial state
        self.content_widget.setVisible(not self.collapsed)
        
        self.setLayout(layout)
    
    def _update_header(self):
        """Update header button text with collapse indicator."""
        icon = ICONS['collapse'] if not self.collapsed else ICONS['expand']
        self.header_btn.setText(f"{icon} {self.title}")
    
    def toggle_collapsed(self):
        """Toggle the collapsed state."""
        self.collapsed = not self.collapsed
        self.content_widget.setVisible(not self.collapsed)
        self._update_header()
    
    def add_widget(self, widget):
        """Add a widget to the content area."""
        self.content_layout.addWidget(widget)
    
    def add_layout(self, layout):
        """Add a layout to the content area."""
        self.content_layout.addLayout(layout)

# =============================================================================
# LAYOUT HELPERS
# =============================================================================

def create_form_row(label_text, widget, helper_text=""):
    """
    Create a form row with label and widget.
    
    Args:
        label_text (str): Label text
        widget: Widget to add
        helper_text (str): Optional helper text
        
    Returns:
        QWidget: Form row widget
    """
    row_widget = QWidget()
    layout = QVBoxLayout()
    layout.setSpacing(SPACING['xs'])
    layout.setContentsMargins(0, 0, 0, 0)
    
    # Label
    label = QLabel(label_text)
    label.setFont(get_font('body_md'))
    layout.addWidget(label)
    
    # Widget
    layout.addWidget(widget)
    
    # Helper text
    if helper_text:
        helper_label = QLabel(helper_text)
        helper_label.setFont(get_font('caption'))
        helper_label.setStyleSheet(f"color: {COLORS['text_muted']};")
        layout.addWidget(helper_label)
    
    row_widget.setLayout(layout)
    return row_widget

def create_button_row(buttons, alignment=Qt.AlignLeft):
    """Create a responsive horizontal layout for buttons that can wrap on small screens."""
    widget = QWidget()
    layout = QHBoxLayout()
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(SPACING['sm'])  # Reduced spacing for better fit
    
    if alignment == Qt.AlignRight:
        layout.addStretch()
    
    for button in buttons:
        # Set button size policy for better responsiveness
        button.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        layout.addWidget(button)
    
    if alignment == Qt.AlignLeft:
        layout.addStretch()
    elif alignment == Qt.AlignCenter:
        layout.insertStretch(0)
        layout.addStretch()
    
    widget.setLayout(layout)
    return widget
