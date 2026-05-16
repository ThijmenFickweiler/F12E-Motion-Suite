import sys
import json
import time

from PyQt6.QtWidgets import (
    QApplication, QWidget, QLabel, QMainWindow, QTabWidget,
    QTextEdit, QDockWidget, QListWidget, QTreeWidget,
    QTreeWidgetItem, QMessageBox, QDialog, QHBoxLayout
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QGuiApplication, QPixmap, QAction
from collections import defaultdict


supported_products = []
preformed_ide_tree = []
selected_drive_pn = ""


class startup_splash_screen(QWidget):
    def center(self):
        screen = QGuiApplication.primaryScreen().geometry()
        self.move(
            (screen.width() - self.width()) // 2,
            (screen.height() - self.height()) // 2
        )

    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.setFixedSize(600, 350)

        self.splash_screen_background = QLabel(self)
        self.splash_screen_background.setPixmap(QPixmap("splash_screen_background.png"))
        self.splash_screen_background.setScaledContents(True)
        self.splash_screen_background.resize(self.size())
        self.splash_screen_background.lower()

        self.bottom_left_label = QLabel("Preparing experience", self)
        self.bottom_left_label.move(10, self.height() - 30)

        self.center()

class select_drive_dialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Select Drive")
        self.setFixedSize(500, 600)

        layout = QHBoxLayout(self)

        self.tree = QTreeWidget()
        self.tree.setHeaderLabel("Supported Products")
        self.tree.itemDoubleClicked.connect(self.select_clicked_product)

        groups = defaultdict(list)

        for product in supported_products:
            groups[product["product_line"]].append(product["product_name"])

        for product_line, products in groups.items():
            line_item = QTreeWidgetItem([product_line])
            self.tree.addTopLevelItem(line_item)

            for product_name in products:
                line_item.addChild(QTreeWidgetItem([product_name]))

            line_item.setExpanded(True)

        layout.addWidget(self.tree)

    def select_clicked_product(self, item, column):
        global selected_drive_pn
        selected_drive_pn = item.text(0)

        names = [p["product_name"] for p in supported_products]

        if selected_drive_pn not in names:
            QMessageBox.critical(self, "Error", "Invalid product selected")
            return

        self.accept()

class main_window(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("F12E Motion Suite")
        self.resize(1200, 800)

        menu_bar = self.menuBar()
        file_menu = menu_bar.addMenu("File")

        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self.close)

        file_menu.addAction(exit_action)

        self.tabs = QTabWidget()
        self.tabs.addTab(QTextEdit("Tab1"), "Tab1")
        self.tabs.addTab(QTextEdit("Tab2"), "Tab2")
        self.setCentralWidget(self.tabs)

        self.left_tree = QTreeWidget()
        self.left_tree.setHeaderLabel("No Drive Connected")

        left_dock = QDockWidget("Project Tree", self)
        left_dock.setWidget(self.left_tree)
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, left_dock)

        right_dock = QDockWidget("Properties", self)
        right_dock.setWidget(QTextEdit("Property inspector"))
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, right_dock)

        bottom_dock = QDockWidget("Compile", self)
        bottom_dock.setWidget(QTextEdit(">>> terminal output..."))
        self.addDockWidget(Qt.DockWidgetArea.BottomDockWidgetArea, bottom_dock)

        self.setDockNestingEnabled(True)

    def open_drive(self):
        self.left_tree.clear()

        enabled = set()

        with open("application_definitions.json", "r") as f:
            data = json.load(f)
            enabled = set(
                data["supported_products"][selected_drive_pn]["enabled_features"]
            )

        for header, children in preformed_ide_tree:
            parent = QTreeWidgetItem([header])
            self.left_tree.addTopLevelItem(parent)

            for child in children:
                if child in enabled:
                    parent.addChild(QTreeWidgetItem([child]))

            self.left_tree.setHeaderLabel(selected_drive_pn)

def load_supported_products():
    global supported_products, preformed_ide_tree

    with open("application_definitions.json", "r") as f:
        data = json.load(f)

    for name, info in data["supported_products"].items():
        supported_products.append({
            "product_name": name,
            "product_line": info["product_line"]
        })

    preformed_ide_tree = list(data["ide_tree"].items())

def load_ide_tree():
    with open("application_definitions.json", "r") as f:
        data = json.load(f)

    return list(data["ide_tree"].items())

def start_communication():
    return True

def load_ui():
    return True

def run_step(splash, text, func):
    splash.bottom_left_label.setText(text)
    splash.bottom_left_label.adjustSize()
    QApplication.processEvents()

    result = func()
    time.sleep(0.25)
    return result

app = QApplication(sys.argv)

splash = startup_splash_screen()
splash.show()
QApplication.processEvents()

try:
    run_step(splash, "Loading Supported Products...", load_supported_products)
    run_step(splash, "Loading IDE Tree...", load_ide_tree)
    run_step(splash, "Starting communication...", start_communication)
    run_step(splash, "Loading UI...", load_ui)

except FileNotFoundError:
    QMessageBox.critical(None, "Error 1001", "Application Definitions not found")
    sys.exit(1)

except json.JSONDecodeError:
    QMessageBox.critical(None, "Error 1002", "Invalid JSON")
    sys.exit(1)

splash.close()

window = main_window()

dialog = select_drive_dialog()

if dialog.exec() == QDialog.DialogCode.Accepted:
    window.show()
    window.open_drive()

sys.exit(app.exec())