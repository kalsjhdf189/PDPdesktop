# MainScreenWindow.py
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QScrollArea, QFrame, QLabel, QMessageBox, QHBoxLayout
)
from PySide6.QtCore import Qt
from datebase import Order, Connect, Employee
from styles import TABLE_WIDGET_STYLE, CARD_STYLE
from sqlalchemy.orm import Session

class OrderCard(QFrame):
    def __init__(self, order, parent_widget, session, parent=None):
        super().__init__(parent)
        self.order = order
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

        order_id = str(self.order.id) if self.order.id else "Не указан"
        creation_date = self.order.Дата_создания.strftime("%Y-%m-%d %H:%M:%S") if self.order.Дата_создания else "Не указана"
        partner_name = self.order.партнер.Наименование if self.order.партнер else "Не указан"

        left_layout.addWidget(QLabel(f"Заказ №: {order_id}"))
        left_layout.addWidget(QLabel(f"Дата создания: {creation_date}"))
        left_layout.addWidget(QLabel(f"Партнёр: {partner_name}"))

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
        reply = QMessageBox.question(
            self, "Подтверждение", "Принять данный заказ?",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            try:
                self.order.id_сотрудник = 1  # Placeholder: Замените на реальный ID сотрудника
                self.order.Статус = "Принят"
                self.session.commit()
                self.parent_widget.load_cards()
                QMessageBox.information(self, "Успех", "Заказ успешно принят!")
            except Exception as e:
                self.session.rollback()
                QMessageBox.critical(self, "Ошибка", f"Не удалось принять заказ: {str(e)}")

class MainScreenWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.session = Connect.create_connection()
        self.selected_card = None
        self.setup_ui()

    def setup_ui(self):
        self.layout = QVBoxLayout(self)

        # Заголовок
        self.title_label = QLabel("Ожидающие принятия заказы")
        self.title_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        self.layout.addWidget(self.title_label)

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
        self.selected_card = None

        # Загружаем заказы, где сотрудник не указан и статус не "Отменён"
        orders = self.session.query(Order).filter(
            Order.id_сотрудник == None,
            Order.Статус != "Отменён"
        ).all()

        if not orders:
            self.cards_layout.addWidget(QLabel("Нет заказов, ожидающих принятия"))
        else:
            for order in orders:
                card = OrderCard(order, self, self.session)
                self.cards_layout.addWidget(card)

    def update_selection(self, card):
        if self.selected_card and self.selected_card != card:
            self.selected_card.setProperty("selected", False)
            self.selected_card.setStyleSheet(CARD_STYLE)
        self.selected_card = card if card.property("selected") else None