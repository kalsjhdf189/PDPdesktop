from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QHBoxLayout, QDialog, QFormLayout, QComboBox, QMessageBox, 
    QSizePolicy, QLineEdit, QDateTimeEdit, QScrollArea, QFrame, QLabel
)
from PySide6.QtCore import QDateTime, Qt
from PySide6.QtGui import QIcon
from datebase import Employee, Product, ProductMovement, ProductOnWarehouse, Warehouse, Connect
from styles import TABLE_WIDGET_STYLE, DIALOG_STYLE, ICON_BUTTON_STYLE, CARD_STYLE
from sqlalchemy import and_

class EditMovementDialog(QDialog):
    def __init__(self, session, movement, parent=None):
        super().__init__(parent)
        self.session = session
        self.movement = movement
        self.setWindowTitle("Редактировать перемещение")
        self.setStyleSheet(CARD_STYLE)
        self.setup_ui()

    def setup_ui(self):
        layout = QFormLayout(self)

        self.status_combo = QComboBox()
        self.status_combo.addItems(["В пути", "Доставлен", "Отменён"])
        self.status_combo.setCurrentText(self.movement.Статус or "В пути")
        layout.addRow("Статус:", self.status_combo)

        self.save_btn = QPushButton("Сохранить")
        self.save_btn.clicked.connect(self.save_changes)
        layout.addWidget(self.save_btn)

        self.setStyleSheet(DIALOG_STYLE)

    def save_changes(self):
        new_status = self.status_combo.currentText()
        old_status = self.movement.Статус

        if new_status != old_status:
            self.movement.Статус = new_status
            if new_status == "Доставлено" and old_status != "Доставлено":
                product_id = self.movement.id_продукции
                to_warehouse_id = self.movement.id_склад_куда
                quantity = self.movement.Количество

                to_stock = self.session.query(ProductOnWarehouse).filter(
                    and_(
                        ProductOnWarehouse.id_продукции == product_id,
                        ProductOnWarehouse.id_склада == to_warehouse_id
                    )
                ).first()
                if to_stock:
                    to_stock.Количество += quantity
                else:
                    new_stock = ProductOnWarehouse(
                        id_продукции=product_id,
                        id_склада=to_warehouse_id,
                        Количество=quantity
                    )
                    self.session.add(new_stock)

            self.session.commit()
            QMessageBox.information(self, "Успех", "Статус перемещения успешно обновлён!")
        else:
            QMessageBox.information(self, "Информация", "Статус не изменился.")
        self.accept()

class AddMovementDialog(QDialog):
    def __init__(self, session, parent=None):
        super().__init__(parent)
        self.session = session
        self.setWindowTitle("Добавить перемещение")
        self.setStyleSheet(CARD_STYLE)
        self.setup_ui()

    def setup_ui(self):
        layout = QFormLayout(self)

        self.product_combo = QComboBox()
        products = self.session.query(Product).all()
        for product in products:
            self.product_combo.addItem(product.Наименование, product.id)
        layout.addRow("Продукция:", self.product_combo)

        self.from_warehouse_combo = QComboBox()
        warehouses = self.session.query(Warehouse).all()
        for warehouse in warehouses:
            self.from_warehouse_combo.addItem(warehouse.Название, warehouse.id)
        layout.addRow("Склад откуда:", self.from_warehouse_combo)

        self.to_warehouse_combo = QComboBox()
        for warehouse in warehouses:
            self.to_warehouse_combo.addItem(warehouse.Название, warehouse.id)
        layout.addRow("Склад куда:", self.to_warehouse_combo)

        self.quantity_edit = QLineEdit()
        self.quantity_edit.setPlaceholderText("Введите количество")
        layout.addRow("Количество:", self.quantity_edit)

        self.date_edit = QDateTimeEdit()
        self.date_edit.setDateTime(QDateTime.currentDateTime())
        self.date_edit.setDisplayFormat("yyyy-MM-dd HH:mm:ss")
        layout.addRow("Дата перемещения:", self.date_edit)

        self.status_combo = QComboBox()
        self.status_combo.addItems(["В пути", "Доставлен", "Отменён"])
        layout.addRow("Статус:", self.status_combo)

        self.employee_combo = QComboBox()
        employees = self.session.query(Employee).all()
        for emp in employees:
            self.employee_combo.addItem(f"{emp.Фамилия} {emp.Имя[0]}. {emp.Отчество[0]}.", emp.id)
        layout.addRow("Сотрудник:", self.employee_combo)

        self.save_btn = QPushButton("Сохранить")
        self.save_btn.clicked.connect(self.save_movement)
        layout.addWidget(self.save_btn)

        self.setStyleSheet(DIALOG_STYLE)

    def save_movement(self):
        product_id = self.product_combo.currentData()
        from_warehouse_id = self.from_warehouse_combo.currentData()
        to_warehouse_id = self.to_warehouse_combo.currentData()

        if from_warehouse_id == to_warehouse_id:
            QMessageBox.warning(self, "Ошибка", "Склад 'откуда' и склад 'куда' не могут быть одинаковыми!")
            return

        try:
            quantity = int(self.quantity_edit.text())
            if quantity <= 0:
                raise ValueError("Количество должно быть положительным")
        except ValueError as e:
            QMessageBox.warning(self, "Ошибка", f"Некорректное количество: {str(e)}")
            return

        stock = self.session.query(ProductOnWarehouse).filter(
            ProductOnWarehouse.id_продукции == product_id,
            ProductOnWarehouse.id_склада == from_warehouse_id
        ).first()

        if not stock or stock.Количество < quantity:
            QMessageBox.warning(self, "Ошибка", "Недостаточно продукции на складе 'откуда'!")
            return

        new_movement = ProductMovement(
            id_продукции=product_id,
            id_склад_откуда=from_warehouse_id,
            id_склад_куда=to_warehouse_id,
            Количество=quantity,
            Дата_перемещения=self.date_edit.dateTime().toPython(),
            Статус=self.status_combo.currentText(),
            id_сотрудник=self.employee_combo.currentData()
        )
        self.session.add(new_movement)

        stock.Количество -= quantity
        if stock.Количество == 0:
            self.session.delete(stock)

        if self.status_combo.currentText() == "Доставлено":
            to_stock = self.session.query(ProductOnWarehouse).filter(
                ProductOnWarehouse.id_продукции == product_id,
                ProductOnWarehouse.id_склада == to_warehouse_id
            ).first()
            if to_stock:
                to_stock.Количество += quantity
            else:
                new_stock = ProductOnWarehouse(
                    id_продукции=product_id,
                    id_склада=to_warehouse_id,
                    Количество=quantity
                )
                self.session.add(new_stock)

        self.session.commit()
        QMessageBox.information(self, "Успех", "Перемещение успешно добавлено!")
        self.accept()

class MovementCard(QFrame):
    def __init__(self, movement, parent_widget, session, parent=None):
        super().__init__(parent)
        self.movement = movement
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
        product_name = self.movement.продукция.Наименование if self.movement.продукция else "Не указан"
        from_warehouse = self.movement.склад_откуда.Название if self.movement.склад_откуда else "Не указан"
        to_warehouse = self.movement.склад_куда.Название if self.movement.склад_куда else "Не указан"
        employee_name = (f"{self.movement.сотрудник.Фамилия} {self.movement.сотрудник.Имя[0]}. {self.movement.сотрудник.Отчество[0]}."
                        if self.movement.сотрудник else "Не указан")
        left_layout.addWidget(QLabel(f"Продукция: {product_name}"))
        left_layout.addWidget(QLabel(f"Откуда: {from_warehouse} -> Куда: {to_warehouse}"))
        left_layout.addWidget(QLabel(f"Количество: {self.movement.Количество}"))
        left_layout.addWidget(QLabel(f"Дата: {self.movement.Дата_перемещения}"))
        left_layout.addWidget(QLabel(f"Сотрудник: {employee_name}"))

        right_layout = QVBoxLayout()
        self.status_label = QLabel(self.movement.Статус or "Не указан")
        self.status_label.setFixedWidth(100)
        self.status_label.setAlignment(Qt.AlignCenter)
        if self.movement.Статус == "В пути":
            self.status_label.setStyleSheet("background-color: #E5C46A; color: black; font-weight: bold; padding: 5px; border-radius: 5px;")
        elif self.movement.Статус == "Отменён":
            self.status_label.setStyleSheet("background-color: #C42222; color: white; font-weight: bold; padding: 5px; border-radius: 5px;")
        elif self.movement.Статус == "Доставлен":
            self.status_label.setStyleSheet("background-color: #5ABD5D; color: black; font-weight: bold; padding: 5px; border-radius: 5px;")
        else:
            self.status_label.setStyleSheet("background-color: #CCCCCC; color: black; font-weight: bold; padding: 5px; border-radius: 5px;")
        right_layout.addWidget(self.status_label)

        layout.addLayout(left_layout)
        layout.addLayout(right_layout)
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
        self.parent_widget.edit_movement()

class MovementWidget(QWidget):
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
        self.add_btn.clicked.connect(self.add_movement)
        self.btn_layout.addWidget(self.add_btn)
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

        movements = self.session.query(ProductMovement).all()

        for movement in movements:
            card = MovementCard(movement, self, self.session)
            self.cards_layout.addWidget(card)

    def update_selection(self, card):
        if self.selected_card and self.selected_card != card:
            self.selected_card.setProperty("selected", False)
            self.selected_card.setStyleSheet(CARD_STYLE)
        self.selected_card = card if card.property("selected") else None

    def add_movement(self):
        dialog = AddMovementDialog(self.session, self)
        if dialog.exec() == QDialog.Accepted:
            self.load_cards()

    def edit_movement(self):
        if not self.selected_card:
            QMessageBox.warning(self, "Предупреждение", "Выберите перемещение для редактирования")
            return
        movement = self.selected_card.movement
        dialog = EditMovementDialog(self.session, movement, self)
        if dialog.exec() == QDialog.Accepted:
            self.load_cards()