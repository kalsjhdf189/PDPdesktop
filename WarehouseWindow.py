
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QHBoxLayout, QDialog, QFormLayout, QTextEdit,
    QComboBox, QLineEdit, QMessageBox, QSizePolicy, QScrollArea, QFrame, QLabel
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon
from datebase import Warehouse, WarehouseType, LegalAddress, Connect, ProductOnWarehouse
from ProductOnWarehouseWindow import ProductOnWarehouseWidget
from styles import TABLE_WIDGET_STYLE, DIALOG_STYLE, ICON_BUTTON_STYLE, CARD_STYLE
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.units import cm

def get_main_window(widget):
    """Ищет MainWindow среди родителей виджета."""
    parent = widget
    while parent is not None:
        if parent.__class__.__name__ == "MainWindow":
            return parent
        parent = parent.parent()
    return None

class AddWarehouseDialog(QDialog):
    def __init__(self, session, parent=None, warehouse=None):
        super().__init__(parent)
        self.session = session
        self.warehouse = warehouse
        self.setWindowTitle("Редактировать склад" if warehouse else "Добавить склад")
        self.setStyleSheet(CARD_STYLE)
        self.setup_ui()

    def setup_ui(self):
        layout = QFormLayout(self)

        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("Введите название склада")
        if self.warehouse:
            self.name_edit.setText(self.warehouse.Название or "")
        layout.addRow("Название:", self.name_edit)

        self.type_combo = QComboBox()
        types = self.session.query(WarehouseType).all()
        for type_ in types:
            self.type_combo.addItem(type_.Наименование, type_.id)
        if self.warehouse and self.warehouse.id_тип:
            for index in range(self.type_combo.count()):
                if self.type_combo.itemData(index) == self.warehouse.id_тип:
                    self.type_combo.setCurrentIndex(index)
                    break
        layout.addRow("Тип склада:", self.type_combo)

        self.description_edit = QTextEdit()
        self.description_edit.setPlaceholderText("Введите описание (необязательно)")
        if self.warehouse:
            self.description_edit.setText(self.warehouse.Описание or "")
        layout.addRow("Описание:", self.description_edit)

        self.address_combo = QComboBox()
        addresses = self.session.query(LegalAddress).all()
        for address in addresses:
            address_str = f"{address.Индекс}, {address.Регион}, {address.Город}, {address.Улица}, {address.Дом}"
            self.address_combo.addItem(address_str, address.id)
        if self.warehouse and self.warehouse.id_юр_адрес:
            for index in range(self.address_combo.count()):
                if self.address_combo.itemData(index) == self.warehouse.id_юр_адрес:
                    self.address_combo.setCurrentIndex(index)
                    break
        layout.addRow("Адрес:", self.address_combo)

        self.save_btn = QPushButton("Сохранить")
        self.save_btn.clicked.connect(self.save_warehouse)
        layout.addWidget(self.save_btn)

        self.setStyleSheet(DIALOG_STYLE)

    def save_warehouse(self):
        name = self.name_edit.text().strip()
        if not name:
            QMessageBox.warning(self, "Ошибка", "Название склада не может быть пустым")
            return

        if self.warehouse:
            
            self.warehouse.Название = name
            self.warehouse.id_тип = self.type_combo.currentData()
            self.warehouse.Описание = self.description_edit.text().strip() or None
            self.warehouse.id_юр_адрес = self.address_combo.currentData()
        else:
            
            new_warehouse = Warehouse(
                Название=name,
                id_тип=self.type_combo.currentData(),
                Описание=self.description_edit.text().strip() or None,
                id_юр_адрес=self.address_combo.currentData()
            )
            self.session.add(new_warehouse)
        
        self.session.commit()
        QMessageBox.information(self, "Успех", "Склад успешно сохранён!")
        self.accept()

class SelectWarehouseDialog(QDialog):
    def __init__(self, session, parent=None):
        super().__init__(parent)
        self.session = session
        self.setWindowTitle("Выбор склада для отчёта")
        self.setup_ui()

    def setup_ui(self):
        layout = QFormLayout(self)

        self.warehouse_combo = QComboBox()
        self.warehouse_combo.addItem("Все склады", None)  
        warehouses = self.session.query(Warehouse).all()
        for warehouse in warehouses:
            self.warehouse_combo.addItem(warehouse.Название, warehouse.id)
        layout.addRow("Склад:", self.warehouse_combo)

        btn_layout = QHBoxLayout()
        self.ok_btn = QPushButton("ОК")
        self.ok_btn.clicked.connect(self.accept)
        self.cancel_btn = QPushButton("Отмена")
        self.cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(self.ok_btn)
        btn_layout.addWidget(self.cancel_btn)
        layout.addRow(btn_layout)

        self.setStyleSheet(DIALOG_STYLE)

    def get_selected_warehouse_id(self):
        return self.warehouse_combo.currentData()

class WarehouseCard(QFrame):
    def __init__(self, warehouse, parent_widget, session, parent=None):
        super().__init__(parent)
        self.warehouse = warehouse
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
        name = self.warehouse.Название or "Не указан"
        type_name = self.warehouse.тип.Наименование if self.warehouse.тип else "Не указан"
        address = self.warehouse.юридический_адрес
        address_str = (f"{address.Индекс}, {address.Регион}, {address.Город}, {address.Улица}, {address.Дом}"
                       if address else "Не указан")

        left_layout.addWidget(QLabel(f"Название: {name}"))
        left_layout.addWidget(QLabel(f"Тип: {type_name}"))
        left_layout.addWidget(QLabel(f"Адрес: {address_str}"))

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
        self.parent_widget.edit_warehouse()

class WarehouseWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.session = Connect.create_connection()
        self.selected_card = None
        self.setup_ui()

    def setup_ui(self):
        self.layout = QVBoxLayout(self)
        self.btn_layout = QHBoxLayout()

        self.add_btn = QPushButton()
        self.add_btn.setIcon(QIcon("images/plus.svg"))
        self.add_btn.setStyleSheet(ICON_BUTTON_STYLE)
        self.add_btn.setFixedSize(40, 40)
        self.add_btn.clicked.connect(self.add_warehouse)

        self.delete_btn = QPushButton()
        self.delete_btn.setIcon(QIcon("images/trash.svg"))
        self.delete_btn.setStyleSheet(ICON_BUTTON_STYLE)
        self.delete_btn.setFixedSize(40, 40)
        self.delete_btn.clicked.connect(self.delete_warehouse)

        self.report_btn = QPushButton()
        self.report_btn.setIcon(QIcon("images/report.svg"))
        self.report_btn.setStyleSheet(ICON_BUTTON_STYLE)
        self.report_btn.setFixedSize(40, 40)
        self.report_btn.clicked.connect(self.generate_stock_report)

        self.movements_btn = QPushButton("Перемещения")
        self.movements_btn.setStyleSheet(TABLE_WIDGET_STYLE)
        self.movements_btn.clicked.connect(self.show_movements)

        self.invoices_btn = QPushButton("Поступления")
        self.invoices_btn.setStyleSheet(TABLE_WIDGET_STYLE)
        self.invoices_btn.clicked.connect(self.show_invoices)

        self.product_stock_btn = QPushButton("Продукция на складе")
        self.product_stock_btn.setStyleSheet(TABLE_WIDGET_STYLE)
        self.product_stock_btn.clicked.connect(self.show_product_stock)

        self.btn_layout.addWidget(self.add_btn)
        self.btn_layout.addWidget(self.delete_btn)
        self.btn_layout.addWidget(self.report_btn)
        self.btn_layout.addWidget(self.movements_btn)
        self.btn_layout.addWidget(self.invoices_btn)
        self.btn_layout.addWidget(self.product_stock_btn)
        self.btn_layout.addStretch()

        self.layout.addLayout(self.btn_layout)

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
        self.selected_card = None

        
        warehouses = self.session.query(Warehouse).all()

        if not warehouses:
            self.cards_layout.addWidget(QLabel("Нет складов"))
        else:
            for warehouse in warehouses:
                card = WarehouseCard(warehouse, self, self.session)
                self.cards_layout.addWidget(card)

    def update_selection(self, card):
        if self.selected_card and self.selected_card != card:
            self.selected_card.setProperty("selected", False)
            self.setStyleSheet(CARD_STYLE)
        self.selected_card = card if card.property("selected") else None

    def add_warehouse(self):
        dialog = AddWarehouseDialog(self.session, self)
        if dialog.exec() == QDialog.Accepted:
            self.load_cards()

    def edit_warehouse(self):
        if not self.selected_card:
            QMessageBox.warning(self, "Предупреждение", "Выберите склад для редактирования")
            return
        warehouse = self.selected_card.warehouse
        dialog = AddWarehouseDialog(self.session, self, warehouse)
        if dialog.exec() == QDialog.Accepted:
            self.load_cards()

    def delete_warehouse(self):
        if not self.selected_card:
            QMessageBox.warning(self, "Предупреждение", "Выберите склад для удаления")
            return
        warehouse = self.selected_card.warehouse
        reply = QMessageBox.question(self, "Подтверждение", "Вы уверены, что хотите удалить этот склад?",
                                    QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            try:
                self.session.delete(warehouse)
                self.session.commit()
                self.load_cards()
                QMessageBox.information(self, "Успех", "Склад успешно удалён!")
            except Exception as e:
                self.session.rollback()
                QMessageBox.critical(self, "Ошибка", f"Не удалось удалить склад: {str(e)}")

    def generate_stock_report(self):
        
        dialog = SelectWarehouseDialog(self.session, self)
        if dialog.exec() != QDialog.Accepted:
            return  

        selected_warehouse_id = dialog.get_selected_warehouse_id()

        
        pdfmetrics.registerFont(TTFont('SegoeUIRegular', 'C:/Windows/Fonts/SegoeUI.ttf'))

        
        if selected_warehouse_id is None:
            warehouses = self.session.query(Warehouse).all()
        else:
            warehouses = [self.session.query(Warehouse).filter_by(id=selected_warehouse_id).first()]
            if not warehouses[0]:
                QMessageBox.warning(self, "Предупреждение", "Выбранный склад не найден!")
                return

        elements = []

        
        styles = getSampleStyleSheet()
        title_style = styles['Heading2']
        title_style.fontName = 'SegoeUIRegular'
        title_style.fontSize = 14
        title_style.leading = 16
        title_style.alignment = 1  

        
        has_data = False
        for warehouse in warehouses:
            products = self.session.query(ProductOnWarehouse).filter_by(id_склада=warehouse.id).all()
            if products:
                has_data = True
                break

        if not has_data:
            QMessageBox.warning(self, "Предупреждение", "На выбранном складе(ах) нет продукции для отчёта!")
            return

        for warehouse in warehouses:
            products = self.session.query(ProductOnWarehouse).filter_by(id_склада=warehouse.id).all()
            if not products:
                continue

            warehouse_name = warehouse.Название if warehouse and warehouse.Название else "Не указан"
            elements.append(Paragraph(f"Склад: {warehouse_name}", title_style))
            elements.append(Spacer(1, 0.2 * cm))

            data = [["Продукция", "Количество"]]
            for product_stock in products:
                product_name = product_stock.продукция.Наименование if product_stock.продукция else "Не указан"
                quantity = product_stock.Количество if product_stock.Количество is not None else "Не указано"
                data.append([product_name, str(quantity)])

            table = Table(data, colWidths=[10 * cm, 4 * cm])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, -1), 'SegoeUIRegular'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('FONTSIZE', (0, 1), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('BOX', (0, 0), (-1, -1), 1, colors.black),
                ('LEFTPADDING', (0, 0), (-1, -1), 6),
                ('RIGHTPADDING', (0, 0), (-1, -1), 6),
                ('TOPPADDING', (0, 0), (-1, -1), 6),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ]))
            elements.append(table)
            elements.append(Spacer(1, 0.5 * cm))

        pdf_file = "stock_report.pdf"
        doc = SimpleDocTemplate(pdf_file, pagesize=A4)
        doc.build(elements)
        QMessageBox.information(self, "Успех", f"Отчёт успешно сохранён как {pdf_file}!")

    def show_movements(self):
        main_window = get_main_window(self)
        if main_window is None:
            QMessageBox.critical(self, "Ошибка", "Не удалось найти главное окно приложения")
            return
        main_window.from_warehouse = True
        main_window.toggle_movement_table()

    def show_invoices(self):
        main_window = get_main_window(self)
        if main_window is None:
            QMessageBox.critical(self, "Ошибка", "Не удалось найти главное окно приложения")
            return
        main_window.from_warehouse = True
        main_window.toggle_invoice_table()

    def show_product_stock(self):
        main_window = get_main_window(self)
        if main_window is None:
            QMessageBox.critical(self, "Ошибка", "Не удалось найти главное окно приложения")
            return
        main_window.from_warehouse = True
        main_window.toggle_product_stock_table()