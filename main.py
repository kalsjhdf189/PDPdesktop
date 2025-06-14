import sys
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QPushButton, QVBoxLayout, QHBoxLayout, QWidget, QSizePolicy, QHeaderView, QLabel, QMessageBox
)
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtCore import Qt, QTimer
from ProductWindow import ProductWidget
from MovementWindow import MovementWidget
from IncomingInvoiceWindow import IncomingInvoiceWidget
from OrderWindow import OrderWidget
from WarehouseWindow import WarehouseWidget
from ProductOnWarehouseWindow import ProductOnWarehouseWidget
from MainScreenWindow import MainScreenWidget
from PartnerWindow import PartnerWidget
from datebase import Order, Connect
from styles import MAIN_WINDOW_STYLE, SIDEBAR_BUTTON_STYLE, SIDEBAR_BUTTON_ACTIVE_STYLE, ICON_BUTTON_STYLE

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Bentonit")
        self.setWindowIcon(QIcon('images/ico.ico'))
        self.setGeometry(200, 200, 900, 600)
        self.product_widget = None
        self.movement_widget = None
        self.invoice_widget = None
        self.order_widget = None
        self.warehouse_widget = None
        self.product_stock_widget = None
        self.main_screen_widget = None
        self.partner_widget = None
        self.from_warehouse = False  
        self.session = Connect.create_connection()
        self.last_order_id = self.get_last_order_id()  
        self.setup_ui()
        self.setup_order_check_timer()

    def setup_ui(self):
        self.main_widget = QWidget()
        self.main_layout = QHBoxLayout(self.main_widget)  

        self.sidebar_widget = QWidget()
        self.sidebar_widget.setFixedWidth(200)
        self.sidebar_layout = QVBoxLayout(self.sidebar_widget)
        self.sidebar_layout.setSpacing(10)
        self.sidebar_layout.setContentsMargins(10, 10, 10, 10)

        self.logo_label = QLabel()
        self.logo_label.setPixmap(QPixmap("images/logo.png").scaled(180, 60, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        self.logo_label.setAlignment(Qt.AlignCenter)
        self.sidebar_layout.addWidget(self.logo_label)

        self.show_products_btn = QPushButton("Продукция")
        self.show_products_btn.setStyleSheet(SIDEBAR_BUTTON_STYLE)
        self.show_products_btn.clicked.connect(self.toggle_product_table)

        self.show_orders_btn = QPushButton("Заказы")
        self.show_orders_btn.setStyleSheet(SIDEBAR_BUTTON_STYLE)
        self.show_orders_btn.clicked.connect(self.toggle_order_table)

        self.show_warehouses_btn = QPushButton("Склады")
        self.show_warehouses_btn.setStyleSheet(SIDEBAR_BUTTON_STYLE)
        self.show_warehouses_btn.clicked.connect(self.toggle_warehouse_table)

        self.show_partners_btn = QPushButton("Клиенты")
        self.show_partners_btn.setStyleSheet(SIDEBAR_BUTTON_STYLE)
        self.show_partners_btn.clicked.connect(self.toggle_partner_table)

        self.sidebar_layout.addWidget(self.show_products_btn)
        self.sidebar_layout.addWidget(self.show_orders_btn)
        self.sidebar_layout.addWidget(self.show_warehouses_btn)
        self.sidebar_layout.addWidget(self.show_partners_btn)
        self.sidebar_layout.addStretch()

        self.content_container = QWidget()
        self.content_layout = QVBoxLayout(self.content_container)

        self.header_layout = QHBoxLayout()
        
        self.back_to_warehouse_btn = QPushButton()
        self.back_to_warehouse_btn.setIcon(QIcon("images/backward.svg"))
        self.back_to_warehouse_btn.setStyleSheet(ICON_BUTTON_STYLE)
        self.back_to_warehouse_btn.setFixedSize(40, 40)
        self.back_to_warehouse_btn.clicked.connect(self.return_to_warehouses)
        self.back_to_warehouse_btn.setVisible(False)  
        self.header_layout.addWidget(self.back_to_warehouse_btn)
        
        self.close_btn = QPushButton()
        self.close_btn.setIcon(QIcon("images/back.svg"))
        self.close_btn.setStyleSheet(ICON_BUTTON_STYLE)
        self.close_btn.setFixedSize(40, 40)
        self.close_btn.clicked.connect(self.close_current_widget)
        self.close_btn.setVisible(False)  
        self.header_layout.addStretch()
        self.header_layout.addWidget(self.close_btn)

        self.content_area = QWidget()
        self.content_area_layout = QVBoxLayout(self.content_area)

        self.content_layout.addLayout(self.header_layout)
        self.content_layout.addWidget(self.content_area)

        self.main_layout.addWidget(self.sidebar_widget)
        self.main_layout.addWidget(self.content_container)

        self.setCentralWidget(self.main_widget)
        self.setStyleSheet(MAIN_WINDOW_STYLE)

        self.show_main_screen()

    def setup_order_check_timer(self):
        self.order_check_timer = QTimer(self)
        self.order_check_timer.timeout.connect(self.check_new_orders)
        self.order_check_timer.start(10000)  

    def get_last_order_id(self):
        last_order = self.session.query(Order).order_by(Order.id.desc()).first()
        return last_order.id if last_order else 0

    def check_new_orders(self):
        new_orders = self.session.query(Order).filter(Order.id > self.last_order_id).all()
        if new_orders:
            self.last_order_id = max(order.id for order in new_orders)  
            QMessageBox.information(
                self,
                "Новый заказ",
                f"Поступило {len(new_orders)} новых заказов!"
            )
            if self.main_screen_widget is not None:
                self.main_screen_widget.load_cards()

    def show_main_screen(self):
        if self.main_screen_widget is None:
            self.clear_content_area()
            self.main_screen_widget = MainScreenWidget(self)
            self.content_area_layout.addWidget(self.main_screen_widget)
            self.reset_other_buttons("main")
            self.close_btn.setVisible(False)  
            self.back_to_warehouse_btn.setVisible(False)  

    def toggle_product_table(self):
        if self.product_widget is None:
            self.clear_content_area()
            self.product_widget = ProductWidget(self)
            self.content_area_layout.addWidget(self.product_widget)
            self.show_products_btn.setStyleSheet(SIDEBAR_BUTTON_ACTIVE_STYLE)
            self.reset_other_buttons("product")
            self.close_btn.setVisible(True)  
            self.from_warehouse = False
            self.back_to_warehouse_btn.setVisible(False)  

    def toggle_invoice_table(self):
        if self.invoice_widget is None:
            self.clear_content_area()
            self.invoice_widget = IncomingInvoiceWidget(self)
            self.content_area_layout.addWidget(self.invoice_widget)
            self.reset_other_buttons("invoice")
            self.close_btn.setVisible(True)  
            self.back_to_warehouse_btn.setVisible(self.from_warehouse)
        else:
            self.clear_content_area()
            self.show_main_screen()

    def toggle_order_table(self):
        if self.order_widget is None:
            self.clear_content_area()
            self.order_widget = OrderWidget(self)
            self.content_area_layout.addWidget(self.order_widget)
            self.show_orders_btn.setStyleSheet(SIDEBAR_BUTTON_ACTIVE_STYLE)
            self.reset_other_buttons("order")
            self.close_btn.setVisible(True)  
            self.from_warehouse = False
            self.back_to_warehouse_btn.setVisible(False)  

    def toggle_warehouse_table(self):
        if self.warehouse_widget is None:
            self.clear_content_area()
            self.warehouse_widget = WarehouseWidget(self)
            self.content_area_layout.addWidget(self.warehouse_widget)
            self.show_warehouses_btn.setStyleSheet(SIDEBAR_BUTTON_ACTIVE_STYLE)
            self.reset_other_buttons("warehouse")
            self.close_btn.setVisible(True)  
            self.from_warehouse = False
            self.back_to_warehouse_btn.setVisible(False)  

    def toggle_movement_table(self):
        if self.movement_widget is None:
            self.clear_content_area()
            self.movement_widget = MovementWidget(self)
            self.content_area_layout.addWidget(self.movement_widget)
            self.reset_other_buttons("movement")
            self.close_btn.setVisible(True)  
            self.back_to_warehouse_btn.setVisible(self.from_warehouse)
        else:
            self.clear_content_area()
            self.show_main_screen()

    def toggle_product_stock_table(self):
        if self.product_stock_widget is None:
            self.clear_content_area()
            self.product_stock_widget = ProductOnWarehouseWidget(self)
            self.content_area_layout.addWidget(self.product_stock_widget)
            self.reset_other_buttons("product_stock")
            self.close_btn.setVisible(True)  
            self.back_to_warehouse_btn.setVisible(self.from_warehouse)
        else:
            self.clear_content_area()
            self.show_main_screen()

    def toggle_partner_table(self):
        if self.partner_widget is None:
            self.clear_content_area()
            self.partner_widget = PartnerWidget(self)
            self.content_area_layout.addWidget(self.partner_widget)
            self.show_partners_btn.setStyleSheet(SIDEBAR_BUTTON_ACTIVE_STYLE)
            self.reset_other_buttons("partner")
            self.close_btn.setVisible(True)  
            self.from_warehouse = False
            self.back_to_warehouse_btn.setVisible(False)  

    def clear_content_area(self):
        if self.product_widget is not None:
            self.content_area_layout.removeWidget(self.product_widget)
            self.product_widget.deleteLater()
            self.product_widget = None
            self.show_products_btn.setStyleSheet(SIDEBAR_BUTTON_STYLE)
        if self.movement_widget is not None:
            self.content_area_layout.removeWidget(self.movement_widget)
            self.movement_widget.deleteLater()
            self.movement_widget = None
        if self.invoice_widget is not None:
            self.content_area_layout.removeWidget(self.invoice_widget)
            self.invoice_widget.deleteLater()
            self.invoice_widget = None
        if self.order_widget is not None:
            self.content_area_layout.removeWidget(self.order_widget)
            self.order_widget.deleteLater()
            self.order_widget = None
            self.show_orders_btn.setStyleSheet(SIDEBAR_BUTTON_STYLE)
        if self.warehouse_widget is not None:
            self.content_area_layout.removeWidget(self.warehouse_widget)
            self.warehouse_widget.deleteLater()
            self.warehouse_widget = None
            self.show_warehouses_btn.setStyleSheet(SIDEBAR_BUTTON_STYLE)
        if self.product_stock_widget is not None:
            self.content_area_layout.removeWidget(self.product_stock_widget)
            self.product_stock_widget.deleteLater()
            self.product_stock_widget = None
        if self.main_screen_widget is not None:
            self.content_area_layout.removeWidget(self.main_screen_widget)
            self.main_screen_widget.deleteLater()
            self.main_screen_widget = None
        if self.partner_widget is not None:
            self.content_area_layout.removeWidget(self.partner_widget)
            self.partner_widget.deleteLater()
            self.partner_widget = None
            self.show_partners_btn.setStyleSheet(SIDEBAR_BUTTON_STYLE)
        self.back_to_warehouse_btn.setVisible(False)  

    def reset_other_buttons(self, active_section):
        if active_section != "product":
            self.show_products_btn.setStyleSheet(SIDEBAR_BUTTON_STYLE)
        if active_section != "order":
            self.show_orders_btn.setStyleSheet(SIDEBAR_BUTTON_STYLE)
        if active_section != "warehouse":
            self.show_warehouses_btn.setStyleSheet(SIDEBAR_BUTTON_STYLE)
        if active_section != "partner":
            self.show_partners_btn.setStyleSheet(SIDEBAR_BUTTON_STYLE)

    def close_current_widget(self):
        self.clear_content_area()
        self.show_main_screen()  
        self.close_btn.setVisible(False)
        self.back_to_warehouse_btn.setVisible(False)

    def return_to_warehouses(self):
        if self.from_warehouse:
            self.clear_content_area()
            self.warehouse_widget = WarehouseWidget(self)
            self.content_area_layout.addWidget(self.warehouse_widget)
            self.show_warehouses_btn.setStyleSheet(SIDEBAR_BUTTON_ACTIVE_STYLE)
            self.reset_other_buttons("warehouse")
            self.close_btn.setVisible(True)
            self.back_to_warehouse_btn.setVisible(False)
            self.from_warehouse = False