from PySide6.QtWidgets import (
    QWidget, QTableWidget, QVBoxLayout, QTableWidgetItem, QPushButton, QHBoxLayout, 
    QDialog, QFormLayout, QComboBox, QLineEdit, QDateTimeEdit, QMessageBox, QSizePolicy, 
    QHeaderView, QLabel, QScrollArea, QFrame, QTextEdit, QFileDialog
)
from PySide6.QtCore import Qt, QDateTime
from PySide6.QtGui import QIcon
from datebase import ProductOnWarehouse, OrderProduct, Product, Order, Employee, Partner, Delivery, Payment, Delivery_method, Connect, LegalAddress, OrderAttachment
from styles import TABLE_WIDGET_STYLE, DIALOG_STYLE, ICON_BUTTON_STYLE, CARD_STYLE
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from datetime import datetime
import os

class OrderProductsDialog(QDialog):
    def __init__(self, session, order, parent=None):
        super().__init__(parent)
        self.session = session
        self.order = order
        self.attached_file_path = None
        self.setWindowTitle(f"Продукция заказа #{order.id}")
        self.setGeometry(100,100,400,200)
        self.setup_ui()
        self.load_attachment()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        info_label = QLabel(f"ID заказа: {self.order.id}\nДата создания: {self.order.Дата_создания}")
        layout.addWidget(info_label)

        content_layout = QHBoxLayout()

        self.table = QTableWidget()
        self.table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        content_layout.addWidget(self.table)

        self.attach_file_btn = QPushButton("Прикрепить файл")
        self.attach_file_btn.clicked.connect(self.attach_file)
        content_layout.addWidget(self.attach_file_btn)

        layout.addLayout(content_layout)

        btn_layout = QHBoxLayout()
        self.add_btn = QPushButton("Добавить продукцию")
        self.add_btn.setEnabled(False)
        self.add_btn.setStyleSheet("background-color: gray; color: white;")
        self.add_btn.clicked.connect(self.add_order_product)
        self.closeASIS = QPushButton("Закрыть")
        self.closeASIS.clicked.connect(self.reject)
        btn_layout.addWidget(self.add_btn)
        btn_layout.addWidget(self.closeASIS)
        layout.addLayout(btn_layout)

        self.load_table_data()
        self.setStyleSheet(DIALOG_STYLE)

    def load_attachment(self):
        attachment = self.session.query(OrderAttachment).filter(OrderAttachment.order_id == self.order.id).first()
        if attachment:
            self.attached_file_path = attachment.file_path
            file_name = os.path.basename(self.attached_file_path)
            self.attach_file_btn.setText(file_name)
            self.add_btn.setEnabled(True)
            self.add_btn.setStyleSheet("")
        else:
            self.attached_file_path = None
            self.attach_file_btn.setText("Прикрепить файл")
            self.add_btn.setEnabled(False)
            self.add_btn.setStyleSheet("background-color: gray; color: white;")

    def attach_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Выберите файл", "", "Все файлы (*);;Текстовые файлы (*.txt);;PDF файлы (*.pdf)"
        )
        if file_path:
            self.attached_file_path = file_path
            file_name = os.path.basename(file_path)
            self.attach_file_btn.setText(file_name)
            self.add_btn.setEnabled(True)
            self.add_btn.setStyleSheet("")
            attachment = self.session.query(OrderAttachment).filter(OrderAttachment.order_id == self.order.id).first()
            if attachment:
                attachment.file_path = file_path
            else:
                new_attachment = OrderAttachment(order_id=self.order.id, file_path=file_path)
                self.session.add(new_attachment)
            self.session.commit()
            QMessageBox.information(self, "Успех", f"Файл прикреплен: {file_name}")
        elif not self.attached_file_path:
            self.attached_file_path = None
            self.attach_file_btn.setText("Прикрепить файл")
            self.add_btn.setEnabled(False)
            self.add_btn.setStyleSheet("background-color: gray; color: white;")
            QMessageBox.warning(self, "Предупреждение", "Файл не был выбран.")
            
    def load_table_data(self):
        order_products = self.session.query(OrderProduct).filter(OrderProduct.id_заказа == self.order.id).all()
        columns = ["Наименование", "Количество", "Стоимость"]
        self.table.setColumnCount(len(columns))
        self.table.setHorizontalHeaderLabels(columns)
        self.table.setRowCount(len(order_products))

        for row, order_product in enumerate(order_products):
            product = self.session.query(Product).filter(Product.id == order_product.id_продукции).first()
            self.table.setItem(row, 0, QTableWidgetItem(product.Наименование if product else "Не указан"))
            self.table.setItem(row, 1, QTableWidgetItem(str(order_product.Количество)))
            self.table.setItem(row, 2, QTableWidgetItem(str(order_product.Стоимость or "0.0")))

    def add_order_product(self):
        if not self.attached_file_path:
            QMessageBox.warning(self, "Ошибка", "Необходимо прикрепить файл перед добавлением продукции!")
            return
        dialog = AddOrderProductDialog(self.session, self.order, self)
        if dialog.exec() == QDialog.Accepted:
            self.load_table_data()

class PaymentDialog(QDialog):
    def __init__(self, session, order, parent=None):
        super().__init__(parent)
        self.session = session
        self.order = order
        self.setWindowTitle(f"Оплата заказа #{order.id}")
        self.setGeometry(100, 100, 300, 200)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        payment = self.session.query(Payment).filter(Payment.id == self.order.id_оплата).first()
        
        if payment:
            info_label = QLabel(
                f"ID оплаты: {payment.id}\n"
                f"Дата оплаты: {payment.Дата_оплаты or 'Не указана'}\n"
                f"Статус: {payment.Статус or 'Не указан'}\n"
                f"Сумма: {payment.Сумма or '0.0'}"
            )
        else:
            info_label = QLabel("Оплата не найдена")
        
        layout.addWidget(info_label)
        
        close_btn = QPushButton("Закрыть")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)
        
        self.setStyleSheet(DIALOG_STYLE)

class DeliveryDialog(QDialog):
    def __init__(self, session, order, parent=None):
        super().__init__(parent)
        self.session = session
        self.order = order
        self.setWindowTitle(f"Доставка заказа #{order.id}")
        self.setGeometry(100, 100, 400, 250)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        delivery = self.session.query(Delivery).filter(Delivery.id == self.order.id_доставка).first()
        
        if delivery:
            method = delivery.способ_доставки.Наименование if delivery.способ_доставки else "Не указан"
            address = delivery.юридический_адрес
            address_str = (
                f"{address.Индекс}, {address.Регион}, {address.Город}, "
                f"ул. {address.Улица}, д. {address.Дом}" if address else "Не указан"
            )
            info_label = QLabel(
                f"ID доставки: {delivery.id}\n"
                f"Способ доставки: {method}\n"
                f"Адрес доставки: {address_str}\n"
                f"Статус: {delivery.Статус or 'Не указан'}\n"
                f"Стоимость: {delivery.Стоимость or '0.0'}"
            )
        else:
            info_label = QLabel("Доставка не найдена")
        
        layout.addWidget(info_label)
        
        close_btn = QPushButton("Закрыть")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)
        
        self.setStyleSheet(DIALOG_STYLE)

class AddOrderProductDialog(QDialog):
    def __init__(self, session, order, parent=None):
        super().__init__(parent)
        self.session = session
        self.order = order
        self.setWindowTitle("Добавить продукцию к заказу")
        self.setup_ui()

    def setup_ui(self):
        layout = QFormLayout(self)
        self.product_combo = QComboBox()
        products = self.session.query(Product).all()
        for product in products:
            self.product_combo.addItem(product.Наименование, product.id)
        self.product_combo.setStyleSheet(TABLE_WIDGET_STYLE)
        layout.addRow("Продукция:", self.product_combo)

        self.quantity_edit = QLineEdit()
        self.quantity_edit.setPlaceholderText("Введите количество")
        layout.addRow("Количество:", self.quantity_edit)

        self.cost_edit = QLineEdit()
        self.cost_edit.setPlaceholderText("Стоимость рассчитывается автоматически")
        self.cost_edit.setReadOnly(True)
        layout.addRow("Стоимость:", self.cost_edit)

        self.product_combo.currentIndexChanged.connect(self.update_cost)
        self.quantity_edit.textChanged.connect(self.update_cost)

        self.save_btn = QPushButton("Сохранить")
        self.save_btn.clicked.connect(self.save_order_product)
        layout.addWidget(self.save_btn)

        self.setStyleSheet(DIALOG_STYLE)
        self.update_cost()

    def update_cost(self):
        try:
            product_id = self.product_combo.currentData()
            quantity = int(self.quantity_edit.text()) if self.quantity_edit.text().strip() else 0
            if quantity <= 0:
                self.cost_edit.setText("0.0")
                return

            product = self.session.query(Product).filter(Product.id == product_id).first()
            price = product.Стоимость if product and product.Стоимость is not None else 0.0
            cost = price * quantity
            self.cost_edit.setText(f"{cost:.2f}")
        except ValueError:
            self.cost_edit.setText("0.0")

    def save_order_product(self):
        product_id = self.product_combo.currentData()
        try:
            quantity = int(self.quantity_edit.text())
            if quantity <= 0:
                raise ValueError("Количество должно быть положительным")
        except ValueError as e:
            QMessageBox.warning(self, "Ошибка", f"Некорректные данные: {str(e)}")
            return

        product = self.session.query(Product).filter(Product.id == product_id).first()
        price = product.Стоимость if product and product.Стоимость is not None else 0.0
        cost = price * quantity

        existing_product = self.session.query(OrderProduct).filter(
            OrderProduct.id_заказа == self.order.id,
            OrderProduct.id_продукции == product_id
        ).first()

        if existing_product:
            existing_product.Количество += quantity
            existing_product.Стоимость = price * existing_product.Количество
        else:
            new_order_product = OrderProduct(
                id_заказа=self.order.id,
                id_продукции=product_id,
                Количество=quantity,
                Стоимость=cost
            )
            self.session.add(new_order_product)

        payment = self.session.query(Payment).filter(Payment.id == self.order.id_оплата).first()
        if payment:
            order_products = self.session.query(OrderProduct).filter(OrderProduct.id_заказа == self.order.id).all()
            total_amount = sum(op.Стоимость or 0.0 for op in order_products)
            payment.Сумма = total_amount
        else:
            new_payment = Payment(
                Дата_оплаты=QDateTime.currentDateTime().toPython(),
                Статус="Ожидает",
                Сумма=cost
            )
            self.session.add(new_payment)
            self.session.flush()
            self.order.id_оплата = new_payment.id

        self.session.commit()
        QMessageBox.information(self, "Успех", "Продукция добавлена к заказу!")
        self.accept()

class AddOrderDialog(QDialog):
    def __init__(self, session, parent=None, order=None):
        super().__init__(parent)
        self.session = session
        self.order = order
        self.setWindowTitle("Редактировать заказ" if order else "Добавить заказ")
        self.setup_ui()

    def setup_ui(self):
        layout = QFormLayout(self)
        self.employee_combo = QComboBox()
        employees = self.session.query(Employee).all()
        for emp in employees:
            self.employee_combo.addItem(f"{emp.Фамилия} {emp.Имя[0]}. {emp.Отчество[0]}.", emp.id)
        self.employee_combo.setStyleSheet(TABLE_WIDGET_STYLE)
        if self.order:
            self.employee_combo.setCurrentIndex(self.employee_combo.findData(self.order.id_сотрудник))
        layout.addRow("Сотрудник:", self.employee_combo)

        self.partner_combo = QComboBox()
        partners = self.session.query(Partner).all()
        for partner in partners:
            self.partner_combo.addItem(partner.Наименование, partner.id)
        self.partner_combo.setStyleSheet(TABLE_WIDGET_STYLE)
        if self.order:
            self.partner_combo.setCurrentIndex(self.partner_combo.findData(self.order.id_партнер))
        layout.addRow("Клиент:", self.partner_combo)

        self.datetime_edit = QDateTimeEdit()
        self.datetime_edit.setCalendarPopup(True)
        self.datetime_edit.setDisplayFormat("yyyy-MM-dd HH:mm:ss")
        if self.order and self.order.Дата_создания:
            try:
                order_datetime = self.order.Дата_создания
                if isinstance(order_datetime, datetime):
                    self.datetime_edit.setDateTime(QDateTime(order_datetime))
                else:
                    order_datetime = datetime.strptime(str(order_datetime), "%Y-%m-%d %H:%M:%S")
                    self.datetime_edit.setDateTime(QDateTime(order_datetime))
            except (ValueError):
                self.datetime_edit.setDateTime(QDateTime.currentDateTime())
        else:
            self.datetime_edit.setDateTime(QDateTime.currentDateTime())
        layout.addRow("Дата и время создания:", self.datetime_edit)

        self.status_combo = QComboBox()
        self.status_combo.addItems(["В обработке", "Принят", "Согласован", "В пути", "Завершён", "Отменён"])
        self.status_combo.setStyleSheet(TABLE_WIDGET_STYLE)
        if self.order:
            self.status_combo.setCurrentText(self.order.Статус)
        layout.addRow("Статус:", self.status_combo)

        self.delivery_combo = QComboBox()
        delivery_methods = self.session.query(Delivery).all()
        for delivery in delivery_methods:
            method_name = delivery.способ_доставки.Наименование if delivery.способ_доставки else "Не указан"
            self.delivery_combo.addItem(f"Доставка #{delivery.id} ({method_name})", delivery.id)
        self.delivery_combo.setStyleSheet(TABLE_WIDGET_STYLE)
        if self.order:
            self.delivery_combo.setCurrentIndex(self.delivery_combo.findData(self.order.id_доставка))
        layout.addRow("Доставка:", self.delivery_combo)

        self.payment_combo = QComboBox()
        payments = self.session.query(Payment).all()
        for payment in payments:
            self.payment_combo.addItem(f"Оплата #{payment.id} ({payment.Сумма})", payment.id)
        self.payment_combo.setStyleSheet(TABLE_WIDGET_STYLE)
        if self.order:
            self.payment_combo.setCurrentIndex(self.payment_combo.findData(self.order.id_оплата))
        layout.addRow("Оплата:", self.payment_combo)

        self.comment_edit = QTextEdit(self.order.Комментарий or "" if self.order else "")
        self.comment_edit.setPlaceholderText("Введите комментарий")
        layout.addRow("Комментарий:", self.comment_edit)

        if self.order:
            self.view_products_btn = QPushButton("Просмотреть продукцию")
            self.view_products_btn.clicked.connect(self.view_order_products)
            layout.addWidget(self.view_products_btn)

            self.view_payment_btn = QPushButton("Просмотреть оплату")
            self.view_payment_btn.clicked.connect(self.view_payment)
            layout.addWidget(self.view_payment_btn)

            self.view_delivery_btn = QPushButton("Просмотреть доставку")
            self.view_delivery_btn.clicked.connect(self.view_delivery)
            layout.addWidget(self.view_delivery_btn)

            self.report_btn = QPushButton("Сформировать отчёт")
            self.report_btn.clicked.connect(self.generate_order_report)
            layout.addWidget(self.report_btn)

        self.save_btn = QPushButton("Сохранить")
        self.save_btn.clicked.connect(self.save_order)
        layout.addWidget(self.save_btn)

        self.setStyleSheet(DIALOG_STYLE)

    def view_order_products(self):
        dialog = OrderProductsDialog(self.session, self.order, self)
        dialog.exec()

    def view_payment(self):
        dialog = PaymentDialog(self.session, self.order, self)
        dialog.exec()

    def view_delivery(self):
        dialog = DeliveryDialog(self.session, self.order, self)
        dialog.exec()

    def generate_order_report(self):
        pdfmetrics.registerFont(TTFont('SegoeUI', 'C:/Windows/Fonts/SegoeUI.ttf'))
        order = self.order
        if not order:
            QMessageBox.warning(self, "Ошибка", "Заказ не найден!")
            return

        order_products = self.session.query(OrderProduct).filter(OrderProduct.id_заказа == order.id).all()
        if not order_products:
            QMessageBox.warning(self, "Предупреждение", "В заказе нет продукции для отчёта!")
            return

        pdf_file = f"order_report_{order.id}.pdf"
        doc = SimpleDocTemplate(pdf_file, pagesize=A4)
        elements = []
        styles = getSampleStyleSheet()
        style = styles['Normal']
        style.fontName = 'SegoeUI'
        style.fontSize = 14

        elements.append(Paragraph(f"Заказ #{order.id}", style))
        elements.append(Spacer(1, 12))
        elements.append(Paragraph(f"Клиент: {order.партнер.Наименование}", style))
        elements.append(Spacer(1, 12))
        elements.append(Paragraph(f"Дата создания: {order.Дата_создания}", style))
        elements.append(Spacer(1, 12))
        elements.append(Paragraph("<br/><br/>", style))

        data = [["Продукция", "Количество", "Стоимость"]]
        for op in order_products:
            product = self.session.query(Product).filter(Product.id == op.id_продукции).first()
            product_name = product.Наименование if product else "Не указан"
            data.append([product_name, op.Количество, op.Стоимость or "0.0"])

        table = Table(data)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, -1), 'SegoeUI'),
            ('FONTSIZE', (0, 0), (-1, 0), 14),
            ('FONTSIZE', (0, 1), (-1, -1), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ]))

        elements.append(table)
        doc.build(elements)
        QMessageBox.information(self, "Успех", f"Отчет по заказу #{order.id} успешно сохранён как {pdf_file}!")

    def save_order(self):
        new_status = self.status_combo.currentText()
        old_status = self.order.Статус if self.order else None

        if self.order:
            self.order.id_сотрудник = self.employee_combo.currentData()
            self.order.id_партнер = self.partner_combo.currentData()
            self.order.Дата_создания = self.datetime_edit.dateTime().toPython()
            self.order.Статус = new_status
            self.order.id_доставка = self.delivery_combo.currentData()
            self.order.id_оплата = self.payment_combo.currentData()
            self.order.Комментарий = self.comment_edit.toPlainText().strip() or None
        else:
            new_order = Order(
                id_сотрудник=self.employee_combo.currentData(),
                id_партнер=self.partner_combo.currentData(),
                Дата_создания=self.datetime_edit.dateTime().toPython(),
                Статус=new_status,
                id_доставка=self.delivery_combo.currentData(),
                id_оплата=self.payment_combo.currentData(),
                Комментарий=self.comment_edit.toPlainText().strip() or None
            )
            self.session.add(new_order)

        order_id = self.order.id if self.order else None
        if not order_id:
            self.session.flush()
            order_id = new_order.id

        payment = self.session.query(Payment).filter(Payment.id == self.payment_combo.currentData()).first()
        if payment:
            order_products = self.session.query(OrderProduct).filter(OrderProduct.id_заказа == order_id).all()
            total_amount = sum(op.Стоимость or 0.0 for op in order_products)
            payment.Сумма = total_amount
        else:
            new_payment = Payment(
                Дата_оплаты=QDateTime.currentDateTime().toPython(),
                Статус="Ожидает",
                Сумма=0.0
            )
            self.session.add(new_payment)
            self.session.flush()
            if self.order:
                self.order.id_оплата = new_payment.id
            else:
                new_order.id_оплата = new_payment.id

        if new_status == "Согласован" and old_status != "Согласован":
            order_products = self.session.query(OrderProduct).filter(OrderProduct.id_заказа == order_id).all()
            for order_product in order_products:
                product_id = order_product.id_продукции
                quantity = order_product.Количество
                stock = self.session.query(ProductOnWarehouse).filter(
                    ProductOnWarehouse.id_продукции == product_id
                ).first()

                if stock:
                    if stock.Количество >= quantity:
                        stock.Количество -= quantity
                        if stock.Количество == 0:
                            self.session.delete(stock)
                    else:
                        QMessageBox.warning(self, "Ошибка", f"Недостаточно продукции {product_id} на складе!")
                        self.session.rollback()
                        return
                else:
                    QMessageBox.warning(self, "Ошибка", f"Продукция {product_id} не найдена на складе!")
                    self.session.rollback()
                    return

        self.session.commit()
        self.accept()

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
        partner_name = self.order.партнер.Наименование if self.order.партнер else "Не указан"
        payment = self.session.query(Payment).filter(Payment.id == self.order.id_оплата).first()
        total_amount = payment.Сумма if payment else "0.0"
        left_layout.addWidget(QLabel(f"Клиент: {partner_name}"))
        left_layout.addWidget(QLabel(f"Дата создания: {self.order.Дата_создания}"))
        left_layout.addWidget(QLabel(f"Общая сумма: {total_amount}"))

        right_layout = QVBoxLayout()
        self.status_label = QLabel(self.order.Статус or "Не указан")
        self.status_label.setFixedWidth(100)
        self.status_label.setAlignment(Qt.AlignCenter)
        if self.order.Статус in ["Согласован", "Принят", "В обработке", "В пути"]:
            self.status_label.setStyleSheet("background-color: #E5C46A; color: black; font-weight: bold; padding: 5px; border-radius: 5px;")
        elif self.order.Статус == "Отменён":
            self.status_label.setStyleSheet("background-color: #C42222; color: white; font-weight: bold; padding: 5px; border-radius: 5px;")
        elif self.order.Статус == "Завершён":
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
        self.parent_widget.edit_order()

class OrderWidget(QWidget):
    def __init__(self, parent=None, calendarPopup=True):
        super().__init__(parent)
        self.session = Connect.create_connection()
        self.selected_card = None
        self.setup_ui()

    def setup_ui(self):
        self.layout = QVBoxLayout(self)
        self.btnLayout = QHBoxLayout()

        self.date_filter_layout = QHBoxLayout()
        self.from_date = QDateTimeEdit()
        self.from_date.setCalendarPopup(True)
        self.from_date.setDisplayFormat("yyyy-MM-dd HH:mm:ss")
        self.from_date.setDateTime(QDateTime(2000, 1, 1, 0, 0, 0))
        self.from_date.dateTimeChanged.connect(self.load_cards)

        self.to_date = QDateTimeEdit()
        self.to_date.setCalendarPopup(True)
        self.to_date.setDisplayFormat("yyyy-MM-dd HH:mm:ss")
        self.to_date.setDateTime(QDateTime(2000, 1, 1, 0, 0, 0))
        self.to_date.dateTimeChanged.connect(self.load_cards)
        
        self.partner_combo = QComboBox()
        self.partner_combo.addItem("Все клиенты", 0)
        partners = self.session.query(Partner).all()
        for partner in partners:
            self.partner_combo.addItem(partner.Наименование, partner.id)
        self.partner_combo.setStyleSheet(TABLE_WIDGET_STYLE)
        self.partner_combo.currentIndexChanged.connect(self.load_cards)
        
        self.reset_btn = QPushButton("Сбросить")
        self.reset_btn.setStyleSheet(TABLE_WIDGET_STYLE)
        self.reset_btn.clicked.connect(self.reset_filters)
        
        self.date_filter_layout.addWidget(QLabel("От:"))
        self.date_filter_layout.addWidget(self.from_date)
        self.date_filter_layout.addWidget(QLabel("До:"))
        self.date_filter_layout.addWidget(self.to_date)
        self.date_filter_layout.addWidget(QLabel("Клиент:"))
        self.date_filter_layout.addWidget(self.partner_combo)
        self.date_filter_layout.addWidget(self.reset_btn)
        self.date_filter_layout.addStretch()

        self.addBtn = QPushButton()
        self.addBtn.setIcon(QIcon("images/plus.svg"))
        self.addBtn.setStyleSheet(ICON_BUTTON_STYLE)
        self.addBtn.setFixedSize(40, 40)
        self.addBtn.clicked.connect(self.add_order)
        
        self.deleteBtn = QPushButton()
        self.deleteBtn.setIcon(QIcon("images/trash.svg"))
        self.deleteBtn.setStyleSheet(ICON_BUTTON_STYLE)
        self.deleteBtn.setFixedSize(40, 40)
        self.deleteBtn.clicked.connect(self.delete_order)
        
        self.report_btn = QPushButton()
        self.report_btn.setIcon(QIcon("images/report.svg"))
        self.report_btn.setStyleSheet(ICON_BUTTON_STYLE)
        self.report_btn.clicked.connect(self.generate_orders_report)

        self.btnLayout.addWidget(self.addBtn)
        self.btnLayout.addWidget(self.deleteBtn)
        self.btnLayout.addWidget(self.report_btn)
        self.btnLayout.addStretch()

        self.layout.addLayout(self.date_filter_layout)
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

    def reset_filters(self):
        """Сбрасывает все фильтры и загружает все заказы."""
        self.from_date.setDateTime(QDateTime(2000, 1, 1, 0, 0, 0))
        self.from_date.setStyleSheet(TABLE_WIDGET_STYLE)
        self.to_date.setDateTime(QDateTime(2000, 1, 1, 0, 0, 0))
        self.from_date.setStyleSheet(TABLE_WIDGET_STYLE)
        self.partner_combo.setCurrentIndex(0)
        self.load_cards()

    def load_cards(self):
        for i in reversed(range(self.cards_layout.count())):
            widget = self.cards_layout.itemAt(i).widget()
            if widget is not None:
                widget.deleteLater()
        self.selected_card = None

        from_date = self.from_date.dateTime().toPython()
        to_date = self.to_date.dateTime().toPython()
        partner_id = self.partner_combo.currentData()
        placeholder_date = datetime(2000, 1, 1, 0, 0, 0)

        query = self.session.query(Order)
        if from_date != placeholder_date or to_date != placeholder_date:
            query = query.filter(
                Order.Дата_создания >= from_date,
                Order.Дата_создания <= to_date
            )
        if partner_id != 0:
            query = query.filter(Order.id_партнер == partner_id)
        
        orders = query.all()

        for order in orders:
            card = OrderCard(order, self, self.session)
            self.cards_layout.addWidget(card)

    def update_selection(self, card):
        if self.selected_card and self.selected_card != card:
            self.selected_card.setProperty("selected", False)
            self.selected_card.setStyleSheet(CARD_STYLE)
        self.selected_card = card if card.property("selected") else None

    def add_order(self):
        dialog = AddOrderDialog(self.session, self)
        if dialog.exec() == QDialog.Accepted:
            self.load_cards()
            QMessageBox.information(self, "Успех", "Заказ успешно добавлен!")

    def edit_order(self):
        if not self.selected_card:
            QMessageBox.warning(self, "Предупреждение", "Выберите заказ для редактирования")
            return
        order = self.selected_card.order
        dialog = AddOrderDialog(self.session, self, order)
        if dialog.exec() == QDialog.Accepted:
            self.load_cards()
            QMessageBox.information(self, "Успех", "Заказ успешно отредактирован!")

    def delete_order(self):
        if not self.selected_card:
            QMessageBox.warning(self, "Предупреждение", "Выберите заказ для удаления")
            return
        order = self.selected_card.order
        reply = QMessageBox.question(self, "Подтверждение", "Вы уверены, что хотите удалить этот заказ?",
                                    QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.deleteBtn.setEnabled(False)
            self.session.delete(order)
            self.session.commit()
            self.load_cards()
            self.deleteBtn.setEnabled(True)
            QMessageBox.information(self, "Успех", "Заказ успешно удалён!")

    def generate_orders_report(self):
        pdfmetrics.registerFont(TTFont('SegoeUI', 'C:/Windows/Fonts/SegoeUI.ttf'))
        from_date = self.from_date.dateTime().toPython()
        to_date = self.to_date.dateTime().toPython()
        partner_id = self.partner_combo.currentData()
        placeholder_date = datetime(2000, 1, 1, 0, 0, 0)

        query = self.session.query(Order)
        if from_date != placeholder_date or to_date != placeholder_date:
            query = query.filter(
                Order.Дата_создания >= from_date,
                Order.Дата_создания <= to_date
            )
        if partner_id != 0:
            query = query.filter(Order.id_партнер == partner_id)
        
        orders = query.all()
        if not orders:
            QMessageBox.warning(self, "Предупреждение", "Нет заказов для формирования отчёта!")
            return

        pdf_file = f"orders_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        doc = SimpleDocTemplate(pdf_file, pagesize=A4)
        elements = []
        styles = getSampleStyleSheet()
        style = styles['Normal']
        style.fontName = 'SegoeUI'
        style.fontSize = 14

        elements.append(Paragraph("Отчёт по заказам", style))
        elements.append(Spacer(1, 12))

        if from_date != placeholder_date or to_date != placeholder_date:
            elements.append(Paragraph(f"Период: {from_date} - {to_date}", style))
            elements.append(Spacer(1, 12))
        if partner_id != 0:
            partner = self.session.query(Partner).filter(Partner.id == partner_id).first()
            partner_name = partner.Наименование if partner else "Не указан"
            elements.append(Paragraph(f"Клиент: {partner_name}", style))
            elements.append(Spacer(1, 12))
        elements.append(Paragraph("<br/><br/>", style))

        data = [["ID заказа", "Клиент", "Дата создания", "Общая сумма", "Статус"]]
        for order in orders:
            partner_name = order.партнер.Наименование if order.партнер else "Не указан"
            payment = self.session.query(Payment).filter(Payment.id == order.id_оплата).first()
            total_amount = payment.Сумма if payment else "0.0"
            data.append([str(order.id), partner_name, str(order.Дата_создания), str(total_amount), order.Статус or "Не указан"])

        table = Table(data)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, -1), 'SegoeUI'),
            ('FONTSIZE', (0, 0), (-1, 0), 14),
            ('FONTSIZE', (0, 1), (-1, -1), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ]))

        elements.append(table)
        doc.build(elements)
        QMessageBox.information(self, "Успех", f"Отчёт по заказам успешно сохранён как {pdf_file}!")