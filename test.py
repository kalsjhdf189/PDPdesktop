import pytest
from unittest.mock import patch, MagicMock
from datebase import Product, ProductOnWarehouse, ProductMovement, Warehouse, Employee, Position, Passport, BankDetails, LegalAddress
from MovementWindow import AddMovementDialog  

def test_add_product_arrival(db_session):
    """Тест-кейс №6: Создание поступления продукции."""
    
    legal_address = LegalAddress(Индекс=123456, Регион="Москва", Город="Москва", Улица="Ленина", Дом=10)
    warehouse = Warehouse(id=1, Название="Склад 1", id_юр_адрес=legal_address.id, id_тип=1)
    product = Product(id=1, Наименование="Товар А", id_тип=1)
    passport = Passport(Серия=1234, Номер=567890, Кем_выдан="ОВД", Дата_выдачи="2020-01-01")
    bank_details = BankDetails(
        Название_организации="ООО Тест", Название_банка="Сбербанк", ИНН=1234567890,
        БИК=123456789, Корреспондентский_счет="30101810400000000225"
    )
    position = Position(Наименование="Менеджер")
    employee = Employee(
        Фамилия="Иванов", Имя="Иван", Отчество="Иванович", Дата_рождения="1980-01-01",
        id_паспорт=passport.id, id_банк_реквизиты=bank_details.id, id_должность=position.id,
        Логин="ivanov", Пароль="pass123"
    )
    product_on_warehouse = ProductOnWarehouse(id_склада=warehouse.id, id_продукции=product.id, Количество=100)
    db_session.add_all([legal_address, warehouse, product, passport, bank_details, position, employee, product_on_warehouse])
    db_session.commit()

    
    dialog = AddMovementDialog(db_session)
    dialog.product_combo.currentData = MagicMock(return_value=1)
    dialog.from_warehouse_combo.currentData = MagicMock(return_value=None)
    dialog.to_warehouse_combo.currentData = MagicMock(return_value=1)
    dialog.quantity_edit.text = MagicMock(return_value='400')
    dialog.date_edit.dateTime = MagicMock(return_value='2025-01-11 11:01:01')
    dialog.status_combo.currentText = MagicMock(return_value='Доставлено')
    dialog.employee_combo.currentData = MagicMock(return_value=employee.id)

    
    with patch('PySide6.QtWidgets.QMessageBox.information') as mock_msg:
        dialog.save_movement()

    
    updated_stock = db_session.query(ProductOnWarehouse).filter_by(id_склада=1, id_продукции=1).first()
    assert updated_stock.Количество == 500
    movement = db_session.query(ProductMovement).filter_by(id_продукции=1, id_склад_куда=1).first()
    assert movement is not None
    assert movement.Количество == 400
    assert movement.Статус == 'Доставлено'
    mock_msg.assert_called_with(dialog, 'Успех', 'Перемещение успешно добавлено!')

def test_movement_same_warehouse(db_session):
    """Тест-кейс №7: Перемещение с одинаковыми складами."""
    
    legal_address = LegalAddress(Индекс=123456, Регион="Москва", Город="Москва", Улица="Ленина", Дом=10)
    warehouse = Warehouse(id=1, Название="Склад 1", id_юр_адрес=legal_address.id, id_тип=1)
    product = Product(id=1, Наименование="Товар А", id_тип=1)
    passport = Passport(Серия=1234, Номер=567890, Кем_выдан="ОВД", Дата_выдачи="2020-01-01")
    bank_details = BankDetails(
        Название_организации="ООО Тест", Название_банка="Сбербанк", ИНН=1234567890,
        БИК=123456789, Корреспондентский_счет="30101810400000000225"
    )
    position = Position(Наименование="Менеджер")
    employee = Employee(
        Фамилия="Иванов", Имя="Иван", Отчество="Иванович", Дата_рождения="1980-01-01",
        id_паспорт=passport.id, id_банк_реквизиты=bank_details.id, id_должность=position.id,
        Логин="ivanov", Пароль="pass123"
    )
    product_on_warehouse = ProductOnWarehouse(id_склада=warehouse.id, id_продукции=product.id, Количество=100)
    db_session.add_all([legal_address, warehouse, product, passport, bank_details, position, employee, product_on_warehouse])
    db_session.commit()

    
    dialog = AddMovementDialog(db_session)
    dialog.product_combo.currentData = MagicMock(return_value=1)
    dialog.from_warehouse_combo.currentData = MagicMock(return_value=1)
    dialog.to_warehouse_combo.currentData = MagicMock(return_value=1)
    dialog.quantity_edit.text = MagicMock(return_value='22')
    dialog.date_edit.dateTime = MagicMock(return_value='2025-05-14 11:00:00')
    dialog.status_combo.currentText = MagicMock(return_value='В пути')
    dialog.employee_combo.currentData = MagicMock(return_value=employee.id)

    
    with patch('PySide6.QtWidgets.QMessageBox.warning') as mock_msg:
        dialog.save_movement()

    
    mock_msg.assert_called_with(dialog, 'Ошибка', 'Склад "откуда" и склад "куда" не могут быть одинаковыми!')
    assert db_session.query(ProductMovement).count() == 0
    stock = db_session.query(ProductOnWarehouse).filter_by(id_склада=1, id_продукции=1).first()
    assert stock.Количество == 100

def test_movement_large_quantity(db_session):
    """Тест-кейс №8: Перемещение большого количества продукции."""
    
    legal_address = LegalAddress(Индекс=123456, Регион="Москва", Город="Москва", Улица="Ленина", Дом=10)
    warehouse1 = Warehouse(id=1, Название="Склад 1", id_юр_адрес=legal_address.id, id_тип=1)
    warehouse2 = Warehouse(id=2, Название="Склад 2", id_юр_адрес=legal_address.id, id_тип=1)
    product = Product(id=1, Наименование="Товар А", id_тип=1)
    passport = Passport(Серия=1234, Номер=567890, Кем_выдан="ОВД", Дата_выдачи="2020-01-01")
    bank_details = BankDetails(
        Название_организации="ООО Тест", Название_банка="Сбербанк", ИНН=1234567890,
        БИК=123456789, Корреспондентский_счет="30101810400000000225"
    )
    position = Position(Наименование="Менеджер")
    employee = Employee(
        Фамилия="Иванов", Имя="Иван", Отчество="Иванович", Дата_рождения="1980-01-01",
        id_паспорт=passport.id, id_банк_реквизиты=bank_details.id, id_должность=position.id,
        Логин="ivanov", Пароль="pass123"
    )
    product_on_warehouse = ProductOnWarehouse(id_склада=warehouse1.id, id_продукции=product.id, Количество=100)
    db_session.add_all([legal_address, warehouse1, warehouse2, product, passport, bank_details, position, employee, product_on_warehouse])
    db_session.commit()

    
    dialog = AddMovementDialog(db_session)
    dialog.product_combo.currentData = MagicMock(return_value=1)
    dialog.from_warehouse_combo.currentData = MagicMock(return_value=1)
    dialog.to_warehouse_combo.currentData = MagicMock(return_value=2)
    dialog.quantity_edit.text = MagicMock(return_value='999999999999999999')
    dialog.date_edit.dateTime = MagicMock(return_value='2025-05-14 11:00:00')
    dialog.status_combo.currentText = MagicMock(return_value='В пути')
    dialog.employee_combo.currentData = MagicMock(return_value=employee.id)

    
    with patch('PySide6.QtWidgets.QMessageBox.warning') as mock_msg:
        dialog.save_movement()

    
    mock_msg.assert_called_with(dialog, 'Ошибка', 'Недостаточно продукции на складе "откуда"!')
    assert db_session.query(ProductMovement).count() == 0
    stock = db_session.query(ProductOnWarehouse).filter_by(id_склада=1, id_продукции=1).first()
    assert stock.Количество == 100