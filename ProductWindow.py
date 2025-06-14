
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QHBoxLayout, QLabel, QComboBox, 
    QMessageBox, QScrollArea, QFrame, QDialog, QLineEdit
)
from PySide6.QtGui import QIcon
from PySide6.QtCore import Qt
from datebase import Product, ProductType, ProductOnWarehouse, Connect
from AddProduct import AddProductDialog
from styles import TABLE_WIDGET_STYLE, CARD_STYLE, ICON_BUTTON_STYLE
from sqlalchemy import func

class ProductCard(QFrame):
    def __init__(self, product, stock, parent_widget, session, parent=None):
        super().__init__(parent)
        self.product = product
        self.stock = stock
        self.parent_widget = parent_widget
        self.session = session
        self.setFrameShape(QFrame.Box)

        self.setup_ui()
        self.setStyleSheet(CARD_STYLE)
        self.setProperty("selected", False)
        self.mousePressEvent = self.toggle_selection

    def setup_ui(self):
        layout = QHBoxLayout()

        left_layout = QVBoxLayout()
        name = self.product.Наименование or "Не указано"
        type_name = self.product.тип.Наименование if self.product.тип else "Не указан"
        cost = self.product.Стоимость or "Не указана"

        left_layout.addWidget(QLabel(f"Наименование: {name}"))
        left_layout.addWidget(QLabel(f"Тип: {type_name}"))
        left_layout.addWidget(QLabel(f"Стоимость: {cost}"))
        left_layout.addWidget(QLabel(f"Количество: {self.stock}"))

        layout.addLayout(left_layout)
        self.setLayout(layout)

    def toggle_selection(self, event):
        selected = self.property("selected")
        self.setProperty("selected", not selected)
        self.setStyleSheet(CARD_STYLE)
        self.parent_widget.update_selection(self)

    def mouseDoubleClickEvent(self, event):
        self.setProperty("selected", True)
        self.setStyleSheet(CARD_STYLE)
        self.parent_widget.update_selection(self)
        self.parent_widget.edit_product()

class ProductWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.session = Connect.create_connection()
        self.selected_card = None
        self.setup_ui()

    def setup_ui(self):
        self.layout = QVBoxLayout(self)
        self.btnLayout = QHBoxLayout()
        self.filterLayout = QHBoxLayout()

        self.addBtn = QPushButton()
        self.addBtn.setIcon(QIcon("images/plus.svg"))
        self.addBtn.setStyleSheet(ICON_BUTTON_STYLE)
        self.addBtn.setFixedSize(40, 40)
        self.addBtn.clicked.connect(self.add_product)

        self.deleteBtn = QPushButton()
        self.deleteBtn.setIcon(QIcon("images/trash.svg"))
        self.deleteBtn.setStyleSheet(ICON_BUTTON_STYLE)
        self.deleteBtn.setFixedSize(40, 40)
        self.deleteBtn.clicked.connect(self.delete_product)

        self.searchLabel = QLabel("Поиск:")
        self.searchEdit = QLineEdit()
        self.searchEdit.textChanged.connect(self.search_products)

        self.typeLabel = QLabel("Тип продукции:")
        self.typeCombo = QComboBox()
        self.load_product_types()
        self.typeCombo.currentIndexChanged.connect(self.filter_by_type)

        self.btnLayout.addWidget(self.addBtn)
        self.btnLayout.addWidget(self.deleteBtn)
        self.btnLayout.addStretch()

        self.filterLayout.addWidget(self.searchLabel)
        self.filterLayout.addWidget(self.searchEdit)
        self.filterLayout.addWidget(self.typeLabel)
        self.filterLayout.addWidget(self.typeCombo)

        self.layout.addLayout(self.btnLayout)
        self.layout.addLayout(self.filterLayout)

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

    def load_product_types(self):
        self.typeCombo.clear()
        self.typeCombo.addItem("Все типы", None)
        types = self.session.query(ProductType).all()
        for type_ in types:
            self.typeCombo.addItem(type_.Наименование, type_.id)

    def load_cards(self, search_query=None, type_id=None):
        
        for i in reversed(range(self.cards_layout.count())):
            widget = self.cards_layout.itemAt(i).widget()
            if widget:
                widget.deleteLater()
        self.selected_card = None

        query = self.session.query(Product)

        if search_query:
            query = query.filter(
                (Product.Наименование.ilike(f"%{search_query}%")) |
                (Product.Описание.ilike(f"%{search_query}%"))
            )

        if type_id:
            query = query.filter(Product.id_тип == type_id)

        products = query.all()

        stock_query = (
            self.session.query(ProductOnWarehouse.id_продукции, func.sum(ProductOnWarehouse.Количество).label("total_stock"))
            .group_by(ProductOnWarehouse.id_продукции)
            .all()
        )
        stock_dict = {item.id_продукции: item.total_stock for item in stock_query}

        for product in products:
            total_stock = stock_dict.get(product.id, 0)
            card = ProductCard(product, total_stock, self, self.session)
            self.cards_layout.addWidget(card)

    def update_selection(self, card):
        if self.selected_card and self.selected_card != card:
            self.selected_card.setProperty("selected", False)
            self.selected_card.setStyleSheet(CARD_STYLE)
        self.selected_card = card if card.property("selected") else None

    def search_products(self):
        search_query = self.searchEdit.text().strip()
        type_id = self.typeCombo.currentData()
        self.load_cards(search_query if search_query else None, type_id)

    def filter_by_type(self):
        search_query = self.searchEdit.text().strip()
        type_id = self.typeCombo.currentData()
        self.load_cards(search_query if search_query else None, type_id)

    def add_product(self):
        dialog = AddProductDialog(self.session, self)
        if dialog.exec() == QDialog.Accepted:
            self.load_cards(search_query=self.searchEdit.text().strip(), type_id=self.typeCombo.currentData())

    def edit_product(self):
        if not self.selected_card:
            QMessageBox.warning(self, "Предупреждение", "Выберите продукт для редактирования")
            return
        product = self.selected_card.product
        dialog = AddProductDialog(self.session, self, product)
        if dialog.exec() == QDialog.Accepted:
            self.load_cards(search_query=self.searchEdit.text().strip(), type_id=self.typeCombo.currentData())

    def delete_product(self):
        if not self.selected_card:
            QMessageBox.warning(self, "Предупреждение", "Выберите продукт для удаления")
            return
        product = self.selected_card.product
        reply = QMessageBox.question(self, "Подтверждение", "Вы уверены, что хотите удалить этот продукт?",
                                    QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.session.delete(product)
            self.session.commit()
            self.load_cards(search_query=self.searchEdit.text().strip(), type_id=self.typeCombo.currentData())
            QMessageBox.information(self, "Успех", "Продукт успешно удалён!")