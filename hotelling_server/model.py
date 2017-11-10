import sys

from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QIcon

from . import interface, controller


class Model:

    """Model class.
    Create the elements of the model, orchestrate their interactions.
    """

    def __init__(self):

        self.git_branch = "php_server"

        self.app = QApplication(sys.argv)
        self.app.setWindowIcon(QIcon("img/icon.icns"))
        self.ui = interface.UI(model=self)
        self.controller = controller.Controller(model=self)

    def run(self):

        try:

            self.controller.start()
            self.ui.setup()
            self.ui.show()
            sys.exit(self.app.exec_())

        except Exception as e:
            self.ui.fatal_error(error_message=str(e))
