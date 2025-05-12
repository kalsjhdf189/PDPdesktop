# AddProduct.py
from PySide6.QtWidgets import QDialog, QFormLayout, QLineEdit, QPushButton, QComboBox, QMessageBox, QTextEdit
from datebase import Product, ProductType
from styles import DIALOG_STYLE

class AddProductDialog(QDialog):
    def __init__(self, session, parent=None, product=None):
        super().__init__(parent)
        self.session = session
        self.product = product
        self.setWindowTitle("Редактировать продукцию" if product else "Добавить продукцию")
        self.setup_ui()

    def setup_ui(self):
        layout = QFormLayout(self)

        self.type_combo = QComboBox()
        types = self.session.query(ProductType).all()
        for t in types:
            self.type_combo.addItem(t.Наименование, t.id)
        if self.product:
            self.type_combo.setCurrentIndex(self.type_combo.findData(self.product.id_тип))
        layout.addRow("Тип:", self.type_combo)

        self.name_edit = QLineEdit(self.product.Наименование if self.product else "")
        layout.addRow("Наименование:", self.name_edit)

        self.description_edit = QTextEdit(self.product.Описание if self.product else "")
        layout.addRow("Описание:", self.description_edit)

        self.cost_edit = QLineEdit(str(self.product.Стоимость) if self.product else "")
        layout.addRow("Стоимость:", self.cost_edit)

        self.weight_edit = QLineEdit(self.product.Вес if self.product else "")
        layout.addRow("Вес:", self.weight_edit)

        self.package_size_edit = QLineEdit(self.product.Размер_упаковки if self.product else "")
        layout.addRow("Размер упаковки:", self.package_size_edit)

        self.image_edit = QLineEdit(self.product.Изображение if self.product else "")
        layout.addRow("Изображение:", self.image_edit)

        self.save_btn = QPushButton("Сохранить")
        self.save_btn.clicked.connect(self.save_product)
        layout.addWidget(self.save_btn)

        self.setStyleSheet(DIALOG_STYLE)

    def save_product(self):
        try:
            name = self.name_edit.text().strip()
            if not name:
                raise ValueError("Наименование не может быть пустым")

            cost = float(self.cost_edit.text()) if self.cost_edit.text().strip() else None
            weight = self.weight_edit.text().strip() or None
            package_size = self.package_size_edit.text().strip() or None
            image = self.image_edit.text().strip() or None

            if self.product:
                self.product.id_тип = self.type_combo.currentData()
                self.product.Наименование = name
                self.product.Описание = self.description_edit.toPlainText().strip() or None
                self.product.Стоимость = cost
                self.product.Вес = weight
                self.product.Размер_упаковки = package_size
                self.product.Изображение = image
                self.session.commit()
                QMessageBox.information(self, "Успех", "Продукт успешно обновлён!")
            else:
                new_product = Product(
                    id_тип=self.type_combo.currentData(),
                    Наименование=name,
                    Описание=self.description_edit.toPlainText().strip() or None,
                    Стоимость=cost,
                    Вес=weight,
                    Размер_упаковки=package_size,
                    Изображение=image
                )
                self.session.add(new_product)
                self.session.commit()
                QMessageBox.information(self, "Успех", "Продукт успешно добавлен!")
            self.accept()
        except ValueError as e:
            QMessageBox.warning(self, "Ошибка", str(e))
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось сохранить продукт: {str(e)}")
            self.session.rollback()