
import bcrypt
from PySide6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QPushButton, QHBoxLayout, QComboBox, QLabel, QLineEdit, QMessageBox, QFormLayout
from PySide6.QtGui import QIcon
from datebase import Employee, Connect
from styles import LOGIN_WINDOW_STYLE

class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        self.setWindowTitle("Авторизация")
        self.setWindowIcon(QIcon('ico.ico'))
        self.resize(300, 150)
        self.session = Connect.create_connection()
        self.setup_ui()

    def setup_ui(self):
        self.layout = QVBoxLayout()

        self.userComboBox = QComboBox()
        self.load_user_logins()

        self.passLineEdit = QLineEdit()
        self.passLineEdit.setEchoMode(QLineEdit.Password)

        self.buttonUserLayout = QHBoxLayout()
        btn1 = QPushButton("Войти")
        btn1.clicked.connect(self.on_login_click)
        btn2 = QPushButton("Выход")
        btn2.clicked.connect(self.close)
        
        self.buttonUserLayout.addWidget(btn1)
        self.buttonUserLayout.addWidget(btn2)
        
        self.formLayout = QFormLayout()
        self.formLayout.addRow("Имя пользователя:", self.userComboBox)
        self.formLayout.addRow("Пароль:", self.passLineEdit)

        self.layout.addLayout(self.formLayout)
        self.layout.addLayout(self.buttonUserLayout)
        self.layout.addStretch()

        widget = QWidget()
        widget.setLayout(self.layout)
        self.setCentralWidget(widget)
        
        self.setStyleSheet(LOGIN_WINDOW_STYLE)

    def load_user_logins(self):
        users = self.session.query(Employee).all()
        logins = [user.Логин for user in users]
        self.userComboBox.addItems(logins)

    def on_login_click(self):
        Логин = self.userComboBox.currentText()
        password = self.passLineEdit.text()
        
        user = self.session.query(Employee).filter_by(Логин=Логин).first()
                       
        if user and bcrypt.checkpw(password.encode('utf-8'), user.Пароль.encode('utf-8')):
            QMessageBox.information(self, "Успех", f"Добро пожаловать, {user.Фамилия}!")
            self.open_main_window()
        else:
            QMessageBox.warning(self, "Ошибка", "Неверный логин или пароль!")
            
    def open_main_window(self):
        from main import MainWindow as MainAppWindow  
        self.main_window = MainAppWindow()
        self.main_window.show()
        self.close()