from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFrame, QLabel, QPushButton, QScrollArea,
    QDialog, QFormLayout, QComboBox, QLineEdit, QTextEdit, QMessageBox
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QIcon
import requests
from datebase import Partner, PartnerType, ScopeApplication, LegalAddress, Connect
from styles import TABLE_WIDGET_STYLE, CARD_STYLE, DIALOG_STYLE, ICON_BUTTON_STYLE

DADATA_API_KEY = "045de845fe99870f9368b07ff0592323d0cd1edb"
DADATA_API_URL = "https://suggestions.dadata.ru/suggestions/api/4_1/rs/suggest/address"

class PartnerCard(QFrame):
    def __init__(self, partner, parent_widget, session, parent=None):
        super().__init__(parent)
        self.partner = partner
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

        partner_name = self.partner.Наименование or "Не указан"
        scope_application = self.partner.сфера_применения.Наименование if self.partner.сфера_применения else "Не указан"
        email = self.partner.email or "Не указан"

        left_layout.addWidget(QLabel(f"Наименование: {partner_name}"))
        left_layout.addWidget(QLabel(f"Сфера применения: {scope_application}"))
        left_layout.addWidget(QLabel(f"Email: {email}"))

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
        self.parent_widget.edit_partner()

class AddPartnerDialog(QDialog):
    def __init__(self, session, parent=None, partner=None):
        super().__init__(parent)
        self.session = session
        self.partner = partner
        self.setWindowTitle("Редактировать клиента" if partner else "Добавить клиента")
        self.address_data = {}  
        self.setup_ui()

    def setup_ui(self):
        layout = QFormLayout(self)

        self.name_edit = QLineEdit(self.partner.Наименование or "" if self.partner else "")
        self.name_edit.setPlaceholderText("Введите наименование")
        layout.addRow("Наименование:", self.name_edit)

        self.inn_edit = QLineEdit(self.partner.ИНН or "" if self.partner else "")
        self.inn_edit.setPlaceholderText("Введите ИНН")
        layout.addRow("ИНН:", self.inn_edit)

        self.director_edit = QLineEdit(self.partner.ФИО_директора or "" if self.partner else "")
        self.director_edit.setPlaceholderText("Введите ФИО директора")
        layout.addRow("ФИО директора:", self.director_edit)

        self.type_combo = QComboBox()
        partner_types = self.session.query(PartnerType).all()
        for p_type in partner_types:
            self.type_combo.addItem(p_type.Наименование, p_type.id)
        if self.partner:
            self.type_combo.setCurrentIndex(self.type_combo.findData(self.partner.id_тип_партнера))
        layout.addRow("Тип клиента:", self.type_combo)

        self.scope_combo = QComboBox()
        scope_applications = self.session.query(ScopeApplication).all()
        for scope in scope_applications:
            self.scope_combo.addItem(scope.Наименование, scope.id)
        if self.partner:
            self.scope_combo.setCurrentIndex(self.scope_combo.findData(self.partner.id_сфера_применения))
        layout.addRow("Сфера применения:", self.scope_combo)

        self.phone_edit = QLineEdit(self.partner.Телефон or "" if self.partner else "")
        self.phone_edit.setPlaceholderText("Введите телефон")
        layout.addRow("Телефон:", self.phone_edit)

        self.email_edit = QLineEdit(self.partner.email or "" if self.partner else "")
        self.email_edit.setPlaceholderText("Введите email")
        layout.addRow("Email:", self.email_edit)

        self.sales_points_edit = QTextEdit(self.partner.Места_продаж or "" if self.partner else "")
        self.sales_points_edit.setPlaceholderText("Введите места продаж")
        layout.addRow("Места продаж:", self.sales_points_edit)

        self.address_edit = QLineEdit()
        if self.partner and self.partner.юридический_адрес:
            address = self.partner.юридический_адрес
            self.address_edit.setText(
                f"{address.Индекс}, {address.Регион}, {address.Город}, ул. {address.Улица}, д. {address.Дом}"
            )
        self.address_edit.setPlaceholderText("Введите адрес")
        self.address_edit.textChanged.connect(self.on_address_changed)
        layout.addRow("Адрес:", self.address_edit)

        self.address_suggestions = QComboBox()
        self.address_suggestions.setVisible(False)  
        self.address_suggestions.currentIndexChanged.connect(self.on_suggestion_selected)
        layout.addRow("", self.address_suggestions)

        self.index_edit = QLineEdit()
        self.index_edit.setVisible(False)
        self.region_edit = QLineEdit()
        self.region_edit.setVisible(False)
        self.city_edit = QLineEdit()
        self.city_edit.setVisible(False)
        self.street_edit = QLineEdit()
        self.street_edit.setVisible(False)
        self.house_edit = QLineEdit()
        self.house_edit.setVisible(False)

        self.save_btn = QPushButton("Сохранить")
        self.save_btn.clicked.connect(self.save_partner)
        layout.addWidget(self.save_btn)

        self.setStyleSheet(DIALOG_STYLE)

        self.address_timer = QTimer(self)
        self.address_timer.setSingleShot(True)
        self.address_timer.timeout.connect(self.fetch_address_suggestions)

    def on_address_changed(self, text):
        if text.strip():
            self.address_timer.start(500)  
        else:
            self.address_suggestions.clear()
            self.address_suggestions.setVisible(False)

    def fetch_address_suggestions(self):
        query = self.address_edit.text().strip()
        if not query:
            return

        headers = {
            "Authorization": f"Token {DADATA_API_KEY}",
            "Content-Type": "application/json"
        }
        data = {"query": query, "count": 5}

        try:
            response = requests.post(DADATA_API_URL, json=data, headers=headers, timeout=5)
            response.raise_for_status()
            suggestions = response.json().get("suggestions", [])

            self.address_suggestions.clear()
            self.address_suggestions.addItem("Выберите адрес")
            for suggestion in suggestions:
                self.address_suggestions.addItem(suggestion["value"], suggestion["data"])
            self.address_suggestions.setVisible(True if suggestions else False)

        except requests.RequestException as e:
            QMessageBox.warning(self, "Ошибка", f"Не удалось получить подсказки адреса: {str(e)}")
            self.address_suggestions.setVisible(False)

    def on_suggestion_selected(self, index):
        if index <= 0:  
            return

        suggestion_data = self.address_suggestions.itemData(index)
        if suggestion_data:
            self.address_data = suggestion_data
            self.address_edit.setText(self.address_suggestions.currentText())
            self.address_suggestions.setVisible(False)

            self.index_edit.setText(suggestion_data.get("postal_code", ""))
            self.region_edit.setText(suggestion_data.get("region_with_type", ""))
            self.city_edit.setText(suggestion_data.get("city_with_type", "") or suggestion_data.get("settlement_with_type", ""))
            self.street_edit.setText(suggestion_data.get("street_with_type", ""))
            self.house_edit.setText(suggestion_data.get("house", ""))

    def save_partner(self):
        try:
            name = self.name_edit.text().strip()
            if not name:
                raise ValueError("Наименование обязательно для заполнения")
            inn = self.inn_edit.text().strip() or None
            director = self.director_edit.text().strip() or None
            type_id = self.type_combo.currentData()
            scope_id = self.scope_combo.currentData()
            phone = self.phone_edit.text().strip() or None
            email = self.email_edit.text().strip() or None
            sales_points = self.sales_points_edit.toPlainText().strip() or None

            if not self.address_data:
                raise ValueError("Выберите адрес из подсказок")

            index = self.index_edit.text().strip()
            region = self.region_edit.text().strip()
            city = self.city_edit.text().strip()
            street = self.street_edit.text().strip()
            house = self.house_edit.text().strip()

            if not all([index, region, city, street, house]):
                raise ValueError("Все поля адреса обязательны для заполнения")
            index = int(index)
            house = int(house)

        except ValueError as e:
            QMessageBox.warning(self, "Ошибка", f"Некорректные данные: {str(e)}")
            return

        try:
            if self.partner:
                self.partner.Наименование = name
                self.partner.ИНН = inn
                self.partner.ФИО_директора = director
                self.partner.id_тип_партнера = type_id
                self.partner.id_сфера_применения = scope_id
                self.partner.Телефон = phone
                self.partner.email = email
                self.partner.Места_продаж = sales_points

                if self.partner.юридический_адрес:
                    self.partner.юридический_адрес.Индекс = index
                    self.partner.юридический_адрес.Регион = region
                    self.partner.юридический_адрес.Город = city
                    self.partner.юридический_адрес.Улица = street
                    self.partner.юридический_адрес.Дом = house
                else:
                    legal_address = LegalAddress(
                        Индекс=index,
                        Регион=region,
                        Город=city,
                        Улица=street,
                        Дом=house
                    )
                    self.session.add(legal_address)
                    self.session.flush()
                    self.partner.id_юр_адрес = legal_address.id
            else:
                legal_address = LegalAddress(
                    Индекс=index,
                    Регион=region,
                    Город=city,
                    Улица=street,
                    Дом=house
                )
                self.session.add(legal_address)
                self.session.flush()

                new_partner = Partner(
                    id_юр_адрес=legal_address.id,
                    Наименование=name,
                    ИНН=inn,
                    ФИО_директора=director,
                    id_тип_партнера=type_id,
                    id_сфера_применения=scope_id,
                    Телефон=phone,
                    email=email,
                    Места_продаж=sales_points,
                )
                self.session.add(new_partner)

            self.session.commit()
            self.accept()
        except Exception as e:
            self.session.rollback()
            QMessageBox.critical(self, "Ошибка", f"Не удалось сохранить клиента: {str(e)}")

class PartnerWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.session = Connect.create_connection()
        self.selected_card = None
        self.setup_ui()

    def setup_ui(self):
        self.layout = QVBoxLayout(self)
        self.btnLayout = QHBoxLayout()

        self.addBtn = QPushButton()
        self.addBtn.setIcon(QIcon("images/plus.svg"))
        self.addBtn.setStyleSheet(ICON_BUTTON_STYLE)
        self.addBtn.setFixedSize(40, 40)
        self.addBtn.clicked.connect(self.add_partner)

        self.deleteBtn = QPushButton()
        self.deleteBtn.setIcon(QIcon("images/trash.svg"))
        self.deleteBtn.setStyleSheet(ICON_BUTTON_STYLE)
        self.deleteBtn.setFixedSize(40, 40)
        self.deleteBtn.clicked.connect(self.delete_partner)

        self.btnLayout.addWidget(self.addBtn)
        self.btnLayout.addWidget(self.deleteBtn)
        self.btnLayout.addStretch()

        self.layout.addLayout(self.btnLayout)

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

        partners = self.session.query(Partner).all()

        if not partners:
            self.cards_layout.addWidget(QLabel("Нет клиентов"))
        else:
            for partner in partners:
                card = PartnerCard(partner, self, self.session)
                self.cards_layout.addWidget(card)

    def update_selection(self, card):
        if self.selected_card and self.selected_card != card:
            self.selected_card.setProperty("selected", False)
            self.selected_card.setStyleSheet(CARD_STYLE)
        self.selected_card = card if card.property("selected") else None

    def add_partner(self):
        dialog = AddPartnerDialog(self.session, self)
        if dialog.exec() == QDialog.Accepted:
            self.load_cards()
            QMessageBox.information(self, "Успех", "Клиент успешно добавлен!")

    def edit_partner(self):
        if not self.selected_card:
            QMessageBox.warning(self, "Предупреждение", "Выберите клиента для редактирования")
            return
        partner = self.selected_card.partner
        dialog = AddPartnerDialog(self.session, self, partner)
        if dialog.exec() == QDialog.Accepted:
            self.load_cards()
            QMessageBox.information(self, "Успех", "Клиент успешно отредактирован!")

    def delete_partner(self):
        if not self.selected_card:
            QMessageBox.warning(self, "Предупреждение", "Выберите клиента для удаления")
            return
        partner = self.selected_card.partner
        reply = QMessageBox.question(
            self, "Подтверждение", "Вы уверены, что хотите удалить этого клиента?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            try:
                self.session.delete(partner)
                self.session.commit()
                self.load_cards()
                QMessageBox.information(self, "Успех", "Клиент успешно удалён!")
            except Exception as e:
                self.session.rollback()
                QMessageBox.critical(self, "Ошибка", f"Не удалось удалить клиента: {str(e)}")