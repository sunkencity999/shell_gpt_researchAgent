"""
Modern GUI Styling System for ResearchAgent
Implements a comprehensive design system with semantic colors, typography, and component styles.
"""

from PyQt5.QtGui import QFont, QPalette, QColor
from PyQt5.QtCore import Qt

# =============================================================================
# DESIGN SYSTEM CONSTANTS
# =============================================================================

# Modern Color Palette with Semantic Meaning
COLORS = {
    # Primary Brand Colors
    'primary': '#2563eb',           # Blue - primary actions, links
    'primary_hover': '#1d4ed8',     # Darker blue for hover states
    'primary_light': '#dbeafe',     # Light blue for backgrounds
    
    # Secondary Colors
    'secondary': '#64748b',         # Gray for secondary elements
    'secondary_hover': '#475569',   # Darker gray for hover
    'secondary_light': '#f1f5f9',   # Light gray backgrounds
    
    # Status Colors
    'success': '#10b981',           # Green for success states
    'success_light': '#d1fae5',     # Light green backgrounds
    'warning': '#f59e0b',           # Amber for warnings
    'warning_light': '#fef3c7',     # Light amber backgrounds
    'error': '#ef4444',             # Red for errors
    'error_light': '#fee2e2',       # Light red backgrounds
    'info': '#3b82f6',              # Blue for information
    'info_light': '#dbeafe',        # Light blue for info backgrounds
    
    # Neutral Colors
    'background': '#f8fafc',        # Main background
    'surface': '#ffffff',           # Cards, panels, inputs
    'surface_hover': '#f1f5f9',     # Hover state for surfaces
    'border': '#e2e8f0',            # Default borders
    'border_focus': '#2563eb',      # Focused element borders
    'border_error': '#ef4444',      # Error state borders
    
    # Text Colors
    'text_primary': '#1e293b',      # Primary text
    'text_secondary': '#64748b',    # Secondary text
    'text_muted': '#94a3b8',        # Muted text
    'text_inverse': '#ffffff',      # White text for dark backgrounds
    
    # Dark Theme Colors
    'dark_background': '#0f172a',   # Dark main background
    'dark_surface': '#1e293b',      # Dark cards/panels
    'dark_surface_hover': '#334155', # Dark hover states
    'dark_border': '#334155',       # Dark borders
    'dark_text_primary': '#f1f5f9', # Dark theme primary text
    'dark_text_secondary': '#cbd5e1', # Dark theme secondary text
}

# Typography Scale
TYPOGRAPHY = {
    'heading_xl': ('Inter', 24, QFont.Bold),      # Main headings
    'heading_lg': ('Inter', 20, QFont.Bold),      # Section headings
    'heading_md': ('Inter', 16, QFont.Bold),      # Subsection headings
    'heading_sm': ('Inter', 14, QFont.Bold),      # Small headings
    'body_lg': ('Inter', 14, QFont.Normal),       # Large body text
    'body_md': ('Inter', 12, QFont.Normal),       # Default body text
    'body_sm': ('Inter', 11, QFont.Normal),       # Small body text
    'code': ('JetBrains Mono', 12, QFont.Normal), # Code/monospace
    'button': ('Inter', 12, QFont.Medium),        # Button text
    'caption': ('Inter', 10, QFont.Normal),       # Captions, labels
}

# Spacing Scale (consistent spacing throughout the app)
SPACING = {
    'xs': 4,    # 4px
    'sm': 8,    # 8px
    'md': 12,   # 12px
    'lg': 16,   # 16px
    'xl': 20,   # 20px
    'xxl': 24,  # 24px
    'xxxl': 32, # 32px
}

# Border Radius
RADIUS = {
    'xs': 2,    # Extra small radius for subtle elements
    'sm': 4,    # Small radius for inputs
    'md': 8,    # Medium radius for buttons
    'lg': 12,   # Large radius for cards
    'xl': 16,   # Extra large radius
    'full': 9999, # Fully rounded (pills)
}

# Shadow Definitions
SHADOWS = {
    'sm': '0 1px 2px 0 rgba(0, 0, 0, 0.05)',
    'md': '0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)',
    'lg': '0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05)',
    'xl': '0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)',
}

# =============================================================================
# QSS STYLE SHEETS
# =============================================================================

def get_modern_stylesheet(dark_mode=False):
    """
    Generate comprehensive QSS stylesheet for modern UI design.
    
    Args:
        dark_mode (bool): Whether to use dark theme colors
        
    Returns:
        str: Complete QSS stylesheet
    """
    
    # Select color scheme based on theme
    if dark_mode:
        bg = COLORS['dark_background']
        surface = COLORS['dark_surface']
        surface_hover = COLORS['dark_surface_hover']
        border = COLORS['dark_border']
        text_primary = COLORS['dark_text_primary']
        text_secondary = COLORS['dark_text_secondary']
        text_muted = COLORS['dark_text_secondary']
    else:
        bg = COLORS['background']
        surface = COLORS['surface']
        surface_hover = COLORS['surface_hover']
        border = COLORS['border']
        text_primary = COLORS['text_primary']
        text_secondary = COLORS['text_secondary']
        text_muted = COLORS['text_muted']
    
    return f"""
    /* =============================================================================
       GLOBAL STYLES
       ============================================================================= */
    
    QMainWindow {{
        background-color: {bg};
        color: {text_primary};
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        font-size: 12px;
    }}
    
    /* =============================================================================
       BUTTONS
       ============================================================================= */
    
    QPushButton {{
        background-color: {COLORS['primary']};
        color: {COLORS['text_inverse']};
        border: none;
        border-radius: {RADIUS['md']}px;
        padding: {SPACING['md']}px {SPACING['xl']}px;
        font-family: 'Inter';
        font-size: 12px;
        font-weight: 500;
        min-height: 20px;
        outline: none;
    }}
    
    QPushButton:hover {{
        background-color: {COLORS['primary_hover']};
    }}
    
    QPushButton:pressed {{
        background-color: {COLORS['primary_hover']};
    }}
    
    QPushButton:disabled {{
        background-color: {text_muted};
        color: {surface};
    }}
    
    /* Secondary Button Variant */
    QPushButton[class="secondary"] {{
        background-color: {surface};
        color: {text_primary};
        border: 1px solid {border};
    }}
    
    QPushButton[class="secondary"]:hover {{
        background-color: {surface_hover};
        border-color: {COLORS['primary']};
    }}
    
    /* Danger Button Variant */
    QPushButton[class="danger"] {{
        background-color: {COLORS['error']};
        color: {COLORS['text_inverse']};
    }}
    
    QPushButton[class="danger"]:hover {{
        background-color: #dc2626;
    }}
    
    /* Success Button Variant */
    QPushButton[class="success"] {{
        background-color: {COLORS['success']};
        color: {COLORS['text_inverse']};
    }}
    
    QPushButton[class="success"]:hover {{
        background-color: #059669;
    }}
    
    /* =============================================================================
       INPUT FIELDS
       ============================================================================= */
    
    QLineEdit, QTextEdit, QPlainTextEdit {{
        background-color: {surface};
        color: {text_primary};
        border: 2px solid {border};
        border-radius: {RADIUS['sm']}px;
        padding: {SPACING['sm']}px {SPACING['md']}px;
        font-family: 'Inter';
        font-size: 12px;
        selection-background-color: {COLORS['primary_light']};
        selection-color: {text_primary};
    }}
    
    QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {{
        border-color: {COLORS['border_focus']};
        outline: none;
    }}
    
    QLineEdit:disabled, QTextEdit:disabled, QPlainTextEdit:disabled {{
        background-color: {surface_hover};
        color: {text_muted};
        border-color: {border};
    }}
    
    /* Error State */
    QLineEdit[class="error"], QTextEdit[class="error"] {{
        border-color: {COLORS['border_error']};
        background-color: {COLORS['error_light']};
    }}
    
    /* =============================================================================
       COMBO BOXES
       ============================================================================= */
    
    QComboBox {{
        background-color: {surface};
        color: {text_primary};
        border: 2px solid {border};
        border-radius: {RADIUS['sm']}px;
        padding: {SPACING['sm']}px {SPACING['md']}px;
        font-family: 'Inter';
        font-size: 12px;
        min-height: 20px;
    }}
    
    QComboBox:focus {{
        border-color: {COLORS['border_focus']};
    }}
    
    QComboBox::drop-down {{
        border: none;
        width: 20px;
    }}
    
    QComboBox::down-arrow {{
        image: none;
        border-left: 5px solid transparent;
        border-right: 5px solid transparent;
        border-top: 5px solid {text_secondary};
        margin-right: 5px;
    }}
    
    QComboBox QAbstractItemView {{
        background-color: {surface};
        color: {text_primary};
        border: 1px solid {border};
        border-radius: {RADIUS['sm']}px;
        selection-background-color: {COLORS['primary_light']};
        selection-color: {text_primary};
        padding: {SPACING['xs']}px;
    }}
    
    /* =============================================================================
       SPIN BOXES
       ============================================================================= */
    
    QSpinBox, QDoubleSpinBox {{
        background-color: {surface};
        color: {text_primary};
        border: 2px solid {border};
        border-radius: {RADIUS['sm']}px;
        padding: {SPACING['sm']}px {SPACING['md']}px;
        font-family: 'Inter';
        font-size: 12px;
        min-height: 20px;
    }}
    
    QSpinBox:focus, QDoubleSpinBox:focus {{
        border-color: {COLORS['border_focus']};
    }}
    
    QSpinBox::up-button, QDoubleSpinBox::up-button,
    QSpinBox::down-button, QDoubleSpinBox::down-button {{
        background-color: {surface_hover};
        border: none;
        width: 20px;
        border-radius: {RADIUS['xs']}px;
    }}
    
    QSpinBox::up-button:hover, QDoubleSpinBox::up-button:hover,
    QSpinBox::down-button:hover, QDoubleSpinBox::down-button:hover {{
        background-color: {COLORS['primary_light']};
    }}
    
    /* =============================================================================
       LABELS
       ============================================================================= */
    
    QLabel {{
        color: {text_primary};
        font-family: 'Inter';
        font-size: 12px;
        font-weight: 500;
    }}
    
    QLabel[class="heading"] {{
        font-size: 16px;
        font-weight: 600;
        color: {text_primary};
        margin-bottom: {SPACING['sm']}px;
    }}
    
    QLabel[class="subheading"] {{
        font-size: 14px;
        font-weight: 500;
        color: {text_secondary};
    }}
    
    QLabel[class="caption"] {{
        font-size: 10px;
        color: {text_muted};
    }}
    
    /* =============================================================================
       GROUP BOXES (CARDS)
       ============================================================================= */
    
    QGroupBox {{
        background-color: {surface};
        border: 1px solid {border};
        border-radius: {RADIUS['lg']}px;
        margin-top: {SPACING['md']}px;
        padding-top: {SPACING['lg']}px;
        font-family: 'Inter';
        font-size: 12px;
        font-weight: 600;
        color: {text_primary};
    }}
    
    QGroupBox::title {{
        subcontrol-origin: margin;
        subcontrol-position: top left;
        padding: 0 {SPACING['sm']}px;
        background-color: {surface};
        color: {text_primary};
        border: none;
        margin-left: {SPACING['md']}px;
    }}
    
    /* =============================================================================
       PROGRESS BARS
       ============================================================================= */
    
    QProgressBar {{
        background-color: {surface_hover};
        border: 1px solid {border};
        border-radius: {RADIUS['md']}px;
        text-align: center;
        font-family: 'Inter';
        font-size: 11px;
        font-weight: 500;
        color: {text_primary};
        height: 20px;
    }}
    
    QProgressBar::chunk {{
        background-color: {COLORS['primary']};
        border-radius: {RADIUS['sm']}px;
        margin: 2px;
    }}
    
    /* Success Progress Bar */
    QProgressBar[class="success"]::chunk {{
        background-color: {COLORS['success']};
    }}
    
    /* Warning Progress Bar */
    QProgressBar[class="warning"]::chunk {{
        background-color: {COLORS['warning']};
    }}
    
    /* =============================================================================
       LIST WIDGETS
       ============================================================================= */
    
    QListWidget {{
        background-color: {surface};
        color: {text_primary};
        border: 1px solid {border};
        border-radius: {RADIUS['sm']}px;
        font-family: 'Inter';
        font-size: 12px;
        outline: none;
        padding: {SPACING['xs']}px;
    }}
    
    QListWidget::item {{
        padding: {SPACING['sm']}px {SPACING['md']}px;
        border-radius: {RADIUS['xs']}px;
        margin: 1px;
    }}
    
    QListWidget::item:selected {{
        background-color: {COLORS['primary_light']};
        color: {text_primary};
    }}
    
    QListWidget::item:hover {{
        background-color: {surface_hover};
    }}
    
    /* =============================================================================
       SPLITTER
       ============================================================================= */
    
    QSplitter::handle {{
        background-color: {border};
        width: 2px;
        height: 2px;
    }}
    
    QSplitter::handle:hover {{
        background-color: {COLORS['primary']};
    }}
    
    /* =============================================================================
       MENU BAR
       ============================================================================= */
    
    QMenuBar {{
        background-color: {surface};
        color: {text_primary};
        border-bottom: 1px solid {border};
        font-family: 'Inter';
        font-size: 12px;
        padding: {SPACING['xs']}px;
    }}
    
    QMenuBar::item {{
        background-color: transparent;
        padding: {SPACING['sm']}px {SPACING['md']}px;
        border-radius: {RADIUS['xs']}px;
    }}
    
    QMenuBar::item:selected {{
        background-color: {surface_hover};
    }}
    
    QMenu {{
        background-color: {surface};
        color: {text_primary};
        border: 1px solid {border};
        border-radius: {RADIUS['sm']}px;
        padding: {SPACING['xs']}px;
    }}
    
    QMenu::item {{
        padding: {SPACING['sm']}px {SPACING['md']}px;
        border-radius: {RADIUS['xs']}px;
    }}
    
    QMenu::item:selected {{
        background-color: {COLORS['primary_light']};
    }}
    
    /* =============================================================================
       SCROLL BARS
       ============================================================================= */
    
    QScrollBar:vertical {{
        background-color: {surface_hover};
        width: 12px;
        border-radius: 6px;
        margin: 0;
    }}
    
    QScrollBar::handle:vertical {{
        background-color: {text_muted};
        border-radius: 6px;
        min-height: 20px;
        margin: 2px;
    }}
    
    QScrollBar::handle:vertical:hover {{
        background-color: {text_secondary};
    }}
    
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
        height: 0;
    }}
    
    QScrollBar:horizontal {{
        background-color: {surface_hover};
        height: 12px;
        border-radius: 6px;
        margin: 0;
    }}
    
    QScrollBar::handle:horizontal {{
        background-color: {text_muted};
        border-radius: 6px;
        min-width: 20px;
        margin: 2px;
    }}
    
    QScrollBar::handle:horizontal:hover {{
        background-color: {text_secondary};
    }}
    
    QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
        width: 0;
    }}
    
    /* =============================================================================
       MESSAGE BOXES
       ============================================================================= */
    
    QMessageBox {{
        background-color: {surface};
        color: {text_primary};
        font-family: 'Inter';
    }}
    
    QMessageBox QPushButton {{
        min-width: 80px;
        padding: {SPACING['sm']}px {SPACING['lg']}px;
    }}
    
    /* =============================================================================
       TOOLTIPS
       ============================================================================= */
    
    QToolTip {{
        background-color: {text_primary};
        color: {surface};
        border: 1px solid {border};
        border-radius: {RADIUS['sm']}px;
        padding: {SPACING['sm']}px {SPACING['md']}px;
        font-family: 'Inter';
        font-size: 11px;
    }}
    """

def get_font(font_key):
    """
    Get a QFont object for the specified typography key.
    
    Args:
        font_key (str): Key from TYPOGRAPHY dictionary
        
    Returns:
        QFont: Configured font object
    """
    if font_key not in TYPOGRAPHY:
        font_key = 'body_md'  # Default fallback
    
    family, size, weight = TYPOGRAPHY[font_key]
    font = QFont(family, size, weight)
    font.setStyleHint(QFont.SansSerif)
    return font

def create_dark_palette():
    """
    Create a dark theme QPalette for the application.
    
    Returns:
        QPalette: Dark theme palette
    """
    palette = QPalette()
    
    # Window colors
    palette.setColor(QPalette.Window, QColor(COLORS['dark_background']))
    palette.setColor(QPalette.WindowText, QColor(COLORS['dark_text_primary']))
    
    # Base colors (input backgrounds)
    palette.setColor(QPalette.Base, QColor(COLORS['dark_surface']))
    palette.setColor(QPalette.AlternateBase, QColor(COLORS['dark_surface_hover']))
    
    # Text colors
    palette.setColor(QPalette.Text, QColor(COLORS['dark_text_primary']))
    palette.setColor(QPalette.BrightText, QColor(COLORS['text_inverse']))
    
    # Button colors
    palette.setColor(QPalette.Button, QColor(COLORS['dark_surface']))
    palette.setColor(QPalette.ButtonText, QColor(COLORS['dark_text_primary']))
    
    # Highlight colors
    palette.setColor(QPalette.Highlight, QColor(COLORS['primary']))
    palette.setColor(QPalette.HighlightedText, QColor(COLORS['text_inverse']))
    
    # Link colors
    palette.setColor(QPalette.Link, QColor(COLORS['primary']))
    palette.setColor(QPalette.LinkVisited, QColor(COLORS['secondary']))
    
    return palette

def create_light_palette():
    """
    Create a light theme QPalette for the application.
    
    Returns:
        QPalette: Light theme palette
    """
    palette = QPalette()
    
    # Window colors
    palette.setColor(QPalette.Window, QColor(COLORS['background']))
    palette.setColor(QPalette.WindowText, QColor(COLORS['text_primary']))
    
    # Base colors (input backgrounds)
    palette.setColor(QPalette.Base, QColor(COLORS['surface']))
    palette.setColor(QPalette.AlternateBase, QColor(COLORS['surface_hover']))
    
    # Text colors
    palette.setColor(QPalette.Text, QColor(COLORS['text_primary']))
    palette.setColor(QPalette.BrightText, QColor(COLORS['text_inverse']))
    
    # Button colors
    palette.setColor(QPalette.Button, QColor(COLORS['surface']))
    palette.setColor(QPalette.ButtonText, QColor(COLORS['text_primary']))
    
    # Highlight colors
    palette.setColor(QPalette.Highlight, QColor(COLORS['primary']))
    palette.setColor(QPalette.HighlightedText, QColor(COLORS['text_inverse']))
    
    # Link colors
    palette.setColor(QPalette.Link, QColor(COLORS['primary']))
    palette.setColor(QPalette.LinkVisited, QColor(COLORS['secondary']))
    
    return palette

# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def apply_button_style(button, variant='primary'):
    """
    Apply a specific button style variant.
    
    Args:
        button (QPushButton): Button to style
        variant (str): Style variant ('primary', 'secondary', 'danger', 'success')
    """
    button.setProperty('class', variant)
    button.style().unpolish(button)
    button.style().polish(button)

def apply_input_error_style(widget, has_error=True):
    """
    Apply error styling to input widgets.
    
    Args:
        widget: Input widget to style
        has_error (bool): Whether to show error state
    """
    if has_error:
        widget.setProperty('class', 'error')
    else:
        widget.setProperty('class', '')
    widget.style().unpolish(widget)
    widget.style().polish(widget)

def set_widget_font(widget, font_key):
    """
    Set font for a widget using typography scale.
    
    Args:
        widget: Widget to apply font to
        font_key (str): Key from TYPOGRAPHY dictionary
    """
    widget.setFont(get_font(font_key))
