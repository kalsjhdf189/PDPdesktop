# IncomingInvoiceWindow.py
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QHBoxLayout, QDialog, QFormLayout, 
    QComboBox, QLineEdit, QDateTimeEdit, QMessageBox, QSizePolicy, QScrollArea, QFrame, QLabel
)
from PySide6.QtCore import QDateTime, Qt
from PySide6.QtGui import QIcon
from datebase import Product, IncomingInvoice, ProductOnWarehouse, Warehouse, Connect
from styles import TABLE_WIDGET_STYLE, DIALOG_STYLE, ICON_BUTTON_STYLE, CARD_STYLE
from sqlalchemy import and_

class AddIncomingInvoiceDialog(QDialog):
    def __init__(self, session, parent=None):
        super().__init__(parent)
        self.session = session
        self.setWindowTitle("Добавить поступление товара")
        self.setup_ui()

    def setup_ui(self):
        layout = QFormLayout(self)

        self.product_combo = QComboBox()
        products = self.session.query(Product).all()
        for product in products:
            self.product_combo.addItem(product.Наименование, product.id)
        layout.addRow("Продукция:", self.product_combo)

        self.warehouse_combo = QComboBox()
        warehouses = self.session.query(Warehouse).all()
        for warehouse in warehouses:
            self.warehouse_combo.addItem(warehouse.Название, warehouse.id)
        layout.addRow("Склад:", self.warehouse_combo)

        self.date_edit = QDateTimeEdit()
        self.date_edit.setDateTime(QDateTime.currentDateTime())
        self.date_edit.setDisplayFormat("yyyy-MM-dd HH:mm:ss")
        layout.addRow("Дата поступления:", self.date_edit)

        self.quantity_edit = QLineEdit()
        self.quantity_edit.setPlaceholderText("Введите количество")
        layout.addRow("Количество товара:", self.quantity_edit)

        self.save_btn = QPushButton("Сохранить")
        self.save_btn.clicked.connect(self.save_invoice)
        layout.addWidget(self.save_btn)

        self.setStyleSheet(DIALOG_STYLE)

    def save_invoice(self):
        product_id = self.product_combo.currentData()
        warehouse_id = self.warehouse_combo.currentData()
        date = self.date_edit.dateTime().toPython()
        try:
            quantity = int(self.quantity_edit.text())
            if quantity <= 0:
                raise ValueError("Количество должно быть положительным")
        except ValueError as e:
            QMessageBox.warning(self, "Ошибка", f"Некорректное количество: {str(e)}")
            return

        new_invoice = IncomingInvoice(
            id_продукция=product_id,
            id_склад=warehouse_id,
            Дата_поступления=date,
            Кол_во_товара=quantity
        )
        self.session.add(new_invoice)

        stock = self.session.query(ProductOnWarehouse).filter(
            and_(
                ProductOnWarehouse.id_продукции == product_id,
                ProductOnWarehouse.id_склада == warehouse_id
            )
        ).first()

        if stock:
            stock.Количество += quantity
        else:
            new_stock = ProductOnWarehouse(
                id_продукции=product_id,
                id_склада=warehouse_id,
                Количество=quantity
            )
            self.session.add(new_stock)

        self.session.commit()
        QMessageBox.information(self, "Успех", "Поступление успешно добавлено!")
        self.accept()

class IncomingInvoiceCard(QFrame):
    def __init__(self, invoice, session):
        super().__init__()
        self.setFrameShape(QFrame.Box)
        self.setLineWidth(1)
        self.setStyleSheet(CARD_STYLE)

        self.invoice = invoice
        self.session = session

        # Основной горизонтальный layout карточки
        layout = QHBoxLayout()

        # Левая часть: основная информация о поступлении
        left_layout = QVBoxLayout()
        product_name = invoice.продукция.Наименование if invoice.продукция else "Не указан"
        warehouse_name = invoice.склад.Название if invoice.склад else "Не указан"
        left_layout.addWidget(QLabel(f"ID: {invoice.id}"))
        left_layout.addWidget(QLabel(f"Продукция: {product_name}"))
        left_layout.addWidget(QLabel(f"Склад: {warehouse_name}"))
        left_layout.addWidget(QLabel(f"Количество: {invoice.Кол_во_товара}"))
        left_layout.addWidget(QLabel(f"Дата: {invoice.Дата_поступления}"))

        # Добавляем информацию в карточку
        layout.addLayout(left_layout)
        self.setLayout(layout)

class IncomingInvoiceWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.session = Connect.create_connection()
        self.setup_ui()

    def setup_ui(self):
        self.layout = QVBoxLayout(self)
        self.btn_layout = QHBoxLayout()

        self.add_btn = QPushButton()
        self.add_btn.setIcon(QIcon("images/plus.svg"))
        self.add_btn.setStyleSheet(ICON_BUTTON_STYLE)
        self.add_btn.setFixedSize(40, 40)
        self.add_btn.clicked.connect(self.add_invoice)
        self.btn_layout.addWidget(self.add_btn)  # Кнопка добавления слева
        self.btn_layout.addStretch()

        self.layout.addLayout(self.btn_layout)

        # Создаем область прокрутки для карточек
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
        # Очищаем текущие карточки
        for i in reversed(range(self.cards_layout.count())):
            widget = self.cards_layout.itemAt(i).widget()
            if widget is not None:
                widget.deleteLater()

        invoices = self.session.query(IncomingInvoice).all()

        for invoice in invoices:
            card = IncomingInvoiceCard(invoice, self.session)
            self.cards_layout.addWidget(card)

    def add_invoice(self):
        dialog = AddIncomingInvoiceDialog(self.session, self)
        if dialog.exec() == QDialog.Accepted:
            self.load_cards()
            QMessageBox.information(self, "Успех", "Поступление успешно добавлено!")