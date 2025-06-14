
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QHBoxLayout, QScrollArea, QFrame, QLabel, QMessageBox
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon
from datebase import ProductOnWarehouse, Warehouse, Connect
from styles import TABLE_WIDGET_STYLE, ICON_BUTTON_STYLE, CARD_STYLE

def get_main_window(widget):
    """Ищет MainWindow среди родителей виджета."""
    parent = widget
    while parent is not None:
        if parent.__class__.__name__ == "MainWindow":
            return parent
        parent = parent.parent()
    return None

class ProductOnWarehouseCard(QFrame):
    def __init__(self, warehouse, products, session):
        super().__init__()
        self.setFrameShape(QFrame.Box)
        self.setLineWidth(1)
        self.setStyleSheet(CARD_STYLE)

        self.warehouse = warehouse
        self.products = products
        self.session = session

        
        layout = QVBoxLayout()

        
        warehouse_name = warehouse.Название if warehouse and warehouse.Название else "Не указан"
        layout.addWidget(QLabel(f"<b>Склад: {warehouse_name}</b>"))

        
        if not products:
            layout.addWidget(QLabel("Продукция отсутствует"))
        else:
            for product_stock in products:
                product_name = product_stock.продукция.Наименование if product_stock.продукция else "Не указан"
                quantity = product_stock.Количество if product_stock.Количество is not None else "Не указано"
                layout.addWidget(QLabel(f" - {product_name}: {quantity}"))
        
        self.setLayout(layout)

class ProductOnWarehouseWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.session = Connect.create_connection()
        self.setup_ui()

    def setup_ui(self):
        self.layout = QVBoxLayout(self)

        
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet("QScrollArea { border: none; }")

        self.cards_container = QWidget()
        self.cards_layout = QVBoxLayout(self.cards_container)
        self.cards_layout.setAlignment(Qt.AlignTop)
        self.cards_layout.setSpacing(10)
        self.cards_layout.setContentsMargins(10, 10, 10, 10)

        self.scroll_area.setWidget(self.cards_container)
        self.layout.addWidget(self.scroll_area)

        self.load_cards()
        self.setStyleSheet(TABLE_WIDGET_STYLE)

    def load_cards(self):
        
        for i in reversed(range(self.cards_layout.count())):
            widget = self.cards_layout.itemAt(i).widget()
            if widget is not None:
                widget.deleteLater()

        
        warehouses = self.session.query(Warehouse).all()

        
        for warehouse in warehouses:
            products = self.session.query(ProductOnWarehouse).filter_by(id_склада=warehouse.id).all()
            if products:  
                card = ProductOnWarehouseCard(warehouse, products, self.session)
                self.cards_layout.addWidget(card)

    def return_to_warehouses(self):
        
        main_window = get_main_window(self)
        if main_window is None:
            QMessageBox.critical(self, "Ошибка", "Не удалось найти главное окно приложения")
            return
        main_window.from_warehouse = False  
        main_window.toggle_warehouse_table()