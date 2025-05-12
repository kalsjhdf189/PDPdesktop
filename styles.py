# styles.py

# Стили для главного окна (MainWindow)
MAIN_WINDOW_STYLE = """
    QMainWindow {
        background-color: #F5F5F5;
    }
    QPushButton {
        background-color: #800020;  /* Бордовый */
        color: white;
        font-family: Segoe UI;
        font-size: 14px;
        padding: 10px;
        border-radius: 5px;
        margin: 5px;
        border: none;
    }
    QPushButton:hover {
        background-color: #A52A2A;  /* Светлый бордовый */
    }
    QPushButton:pressed {
        background-color: #4A0000;  /* Тёмный бордовый */
    }
"""

# Стили для виджетов с таблицами (ProductWidget, MovementWidget, IncomingInvoiceWidget, OrderWidget)
TABLE_WIDGET_STYLE = """
    QWidget {
        background-color: #F5F5F5;
        font-family: Segoe UI;
    }
    QPushButton {
        background-color: #800020;  /* Бордовый */
        color: white;
        font-size: 14px;
        padding: 8px;
        border-radius: 5px;
        border: none;
    }
    QPushButton:hover {
        background-color: #A52A2A;  /* Светлый бордовый */
    }
    QPushButton:pressed {
        background-color: #4A0000;  /* Тёмный бордовый */
    }
    QTableWidget {
        background-color: white;
        border: 1px solid #BDC3C7;
        border-radius: 5px;
        font-size: 12px;
    }
    QTableWidget::item {
        padding: 5px;
    }
    QHeaderView::section {
        background-color: #800020;  /* Бордовый для заголовков таблицы */
        color: white;
        padding: 8px;
        border: none;
    }
    QLineEdit, QComboBox {
        padding: 6px;
        border: 1px solid #BDC3C7;
        border-radius: 4px;
        background-color: white;
    }
    QLabel {
        font-size: 14px;
        color: #333333;
    }
"""

# Стили для диалогов (AddProductDialog, EditMovementDialog, AddIncomingInvoiceDialog)
DIALOG_STYLE = """
    QDialog {
        background-color: #F5F5F5;
        font-family: Segoe UI;
    }
    QLineEdit, QComboBox, QDateTimeEdit {
        padding: 6px;
        border: 1px solid #BDC3C7;
        border-radius: 4px;
        background-color: white;
    }
    QPushButton {
        background-color: #800020;  /* Бордовый */
        color: white;
        font-size: 14px;
        padding: 8px;
        border-radius: 5px;
        border: none;
    }
    QPushButton:hover {
        background-color: #A52A2A;  /* Светлый бордовый */
    }
    QPushButton:pressed {
        background-color: #4A0000;  /* Тёмный бордовый */
    }
    QLabel {
        font-size: 14px;
        color: #333333;
    }
"""

CARD_STYLE = """
QFrame {
    background-color: #ffffff;
    border-radius: 8px;
    margin: 5px;
}
QFrame[selected="true"] {
    border: 2px solid #4CAF50;
}
QLabel {
    font-size: 12px;
}
"""

# Стили только для OrderWidget (без кнопок)
ORDER_WIDGET_STYLE = """
    QWidget {
        background-color: #F5F5F5;
        font-family: Segoe UI;
    }
    QTableWidget {
        background-color: white;
        border: 1px solid #BDC3C7;
        border-radius: 5px;
        font-size: 12px;
    }
    QTableWidget::item {
        padding: 5px;
    }
    QHeaderView::section {
        background-color: #800020;  /* Бордовый для заголовков таблицы */
        color: white;
        padding: 8px;
        border: none;
    }
"""

# Новый стиль для окна авторизации (LoginWindow)
LOGIN_WINDOW_STYLE = """
    QMainWindow {
        background-color: #F5F5F5;
    }
    QWidget {
        background-color: #F5F5F5;
        font-family: Segoe UI;
    }
    QPushButton {
        background-color: #800020;  /* Бордовый */
        color: white;
        font-size: 14px;
        padding: 8px;
        border-radius: 5px;
        border: none;
        margin: 5px;
    }
    QPushButton:hover {
        background-color: #A52A2A;  /* Светлый бордовый */
    }
    QPushButton:pressed {
        background-color: #4A0000;  /* Тёмный бордовый */
    }
    QLineEdit, QComboBox {
        padding: 6px;
        border: 1px solid #BDC3C7;
        border-radius: 4px;
        background-color: white;
    }
    QLabel {
        font-size: 14px;
        color: #333333;
    }
    QFormLayout {
        margin: 10px;
    }
"""

SIDEBAR_BUTTON_STYLE = """
QPushButton {
    background-color: #4A4A4A;  /* Серый */
    color: white;
    padding: 12px;
    border: none;
    border-radius: 5px;
    margin: 5px;
    font-size: 14px;
    text-align: left;
}
QPushButton:hover {
    background-color: #606060;  /* Светлый серый */
}
QPushButton:pressed {
    background-color: #383838;  /* Тёмный серый */
}
"""

SIDEBAR_BUTTON_ACTIVE_STYLE = """
QPushButton {
    background-color: #800020;  /* Бордовый */
    color: white;
    padding: 12px;
    border: none;
    border-radius: 5px;
    margin: 5px;
    font-size: 14px;
    text-align: left;
}
QPushButton:hover {
    background-color: #A52A2A;  /* Светлый бордовый */
}
QPushButton:pressed {
    background-color: #4A0000;  /* Тёмный бордовый */
}
"""

ICON_BUTTON_STYLE = """
QPushButton {
    background-color: transparent;
    border: none;
    padding: 5px;
}
QPushButton:hover {
    background-color: #e0e0e0;
}
QPushButton:pressed {
    background-color: #d0d0d0;
}
"""