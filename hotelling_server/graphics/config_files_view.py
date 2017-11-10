from PyQt5.QtWidgets import QWidget, QTabWidget, QFormLayout, QLabel, \
        QLineEdit, QVBoxLayout, QHBoxLayout, QPushButton, QCheckBox



from utils.utils import Logger


class ConfigFilesWindow(QWidget):

    name = "ConfigFilesWindow"

    def __init__(self, parent, param):
        
        super().__init__()
        
        self.parent = parent
        self.setWindowTitle("Edit config files")
        self.param = param

        self.save_button = QPushButton("Save changes for the current game")
        self.write_button = QPushButton("Writes changes to files")

        self.tab_values = dict()
        self.tabs = QTabWidget(self)

        self.setup()

    def setup(self):
    
        self.fill_layout()

        for key in self.param.keys():
            self.tab_values[key] = Tab(self.param[key], key)
            self.tabs.addTab(self.tab_values[key], key)

        self.save_button.clicked.connect(self.push_save_button)
        self.write_button.clicked.connect(self.push_write_button)

    def fill_layout(self):

        vertical_layout = QVBoxLayout()
        horizontal_layout = QHBoxLayout()
        
        vertical_layout.addWidget(self.tabs)

        # horizontal_layout.addWidget(self.apply_button)
        horizontal_layout.addWidget(self.save_button)
        horizontal_layout.addWidget(self.write_button)

        vertical_layout.addLayout(horizontal_layout)

        self.setLayout(vertical_layout)

    def push_save_button(self):
        
        for key in self.param.keys():
            self.parent.save_parameters(key, self.tab_values[key].get_values())

        self.parent.show_warning(
        "For the moment, parameters are not loaded in interface when modifying them from here.")
        
        self.hide()

    def push_write_button(self):
        
        for key in self.param.keys():
            self.parent.write_parameters(key, self.tab_values[key].get_values())

        self.hide()


class Tab(QWidget):

    def __init__(self, param, name):

        super().__init__()
        
        self.name = name
        self.data = param
        self.widgets = dict()
        self.setup()

    def setup(self):
        self.fill_layout()

    def fill_layout(self):

        form_layout = QFormLayout()

        for key, value in self.data.items():

            if type(value) == bool:
                self.widgets[key] = QCheckBox()
                self.widgets[key].setChecked(value)

            else:
                self.widgets[key] = QLineEdit(str(value))

            form_layout.addRow(QLabel(key), self.widgets[key])

        self.setLayout(form_layout)

    def get_values(self):

        return {k: self.get_value(v) for k, v in self.widgets.items()}
    
    @staticmethod
    def get_value(widget):

        if type(widget) == QLineEdit:

            if widget.text().isdigit():
                return int(widget.text()) 

            elif "," in widget.text():
                return eval(widget.text())
            
            else:
                return widget.text()

        else:

            return widget.isChecked()










