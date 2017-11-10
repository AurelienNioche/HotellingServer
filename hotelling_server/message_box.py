from PyQt5.QtWidgets import QMessageBox


class MessageBox:

    def show_question(self, msg, question="", yes="Yes", no="No", focus="No"):
        """question with customs buttons"""

        msg_box = QMessageBox(self)
        msg_box.setText(msg)
        msg_box.setInformativeText(question)
        msg_box.setIcon(QMessageBox.Question)
        no_button = msg_box.addButton(no, QMessageBox.ActionRole)
        yes_button = msg_box.addButton(yes, QMessageBox.ActionRole)
        msg_box.setDefaultButton((yes_button, no_button)[focus == no])

        msg_box.exec_()

        return msg_box.clickedButton() == yes_button

    def show_warning(self, msg):

        button_reply = QMessageBox().warning(
            self, "", msg,
            QMessageBox.Ok
        )

        return button_reply == QMessageBox.Yes

    def show_critical_and_retry(self, msg):

        button_reply = QMessageBox().critical(
            self, "", msg,  # Parent, title, message
            QMessageBox.Close | QMessageBox.Retry,  # Buttons
            QMessageBox.Retry  # Default button
        )

        return button_reply == QMessageBox.Retry

    def show_critical_and_ok(self, msg):

        button_reply = QMessageBox().critical(
            self, "", msg,  # Parent, title, message
            QMessageBox.Close | QMessageBox.Ok,  # Buttons
            QMessageBox.Ok  # Default button
        )

        return button_reply == QMessageBox.Ok

    def show_critical(self, msg):

        QMessageBox().critical(
            self, "", msg,  # Parent, title, message
            QMessageBox.Close
        )

    def show_info(self, msg):

        QMessageBox().information(
            self, "", msg,
            QMessageBox.Ok
        )
