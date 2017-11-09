import sys
from PyQt5 import QtCore, QtWidgets

from utils.utils import Logger


class Conversations:

    """
    Conversation manager which is not a qt object.
    """

    def __init__(self, parent):

        self.dic = {}

        self.selected = None
        self.parent = parent

    def create_new_conversation(self, user_name):

        self.dic[user_name] = Conversation(user_name)

    def change_selected(self, user_name):

        self.selected = user_name

    def new_message_from_admin(self, message):

        if self.selected is not None and message:

            self.add_content(user_name=self.selected, emitter="Admin", content=message)

    def new_message_from_user(self, user_name, message):

        self.add_content(user_name, user_name, message)

    def get_current_content(self):

        return self.dic[self.selected].content

    def add_content(self, user_name, emitter, content):

        self.dic[user_name].add_content("[{}] {}\n".format(emitter, content))


class Conversation:

    """
    A conversation is just a string with a name, isn't it ?
    Not a qt object.
    """

    def __init__(self, user_name):

        super().__init__()

        self.user_name = user_name
        self.content = ""

    def add_content(self, new_content):

        self.content += new_content


class LeftPanel(QtWidgets.QWidget):

    """
    The left panel of the app that contains:
    - a menu with the different conversations opened.
    - a button for opening a new message.
    """

    def __init__(self, parent, conversation_picker):
        # noinspection PyArgumentList
        QtWidgets.QWidget.__init__(self, parent=parent)

        self.conversation_picker = conversation_picker

        layout = QtWidgets.QVBoxLayout(self)

        button_new_conversation = QtWidgets.QPushButton("New")
        # noinspection PyUnresolvedReferences
        button_new_conversation.clicked.connect(self.click_new_conversation)

        # noinspection PyArgumentList
        layout.addWidget(self.conversation_picker)
        # noinspection PyArgumentList
        layout.addWidget(button_new_conversation)

    def click_new_conversation(self):

        # noinspection PyArgumentList
        user_name, ok = QtWidgets.QInputDialog().getText(self, 'New conversation', 'To:')

        if ok:

            self.parent().change_selected_conversation(user_name)
            return True

        else:
            return False


class RightPanel(QtWidgets.QWidget):

    """
    The right panel that contains:
     - the content of the current opened conversation and
     - the place where the admin writes.
    """

    def __init__(self, parent, message_writer, conversation_display):
        # noinspection PyArgumentList
        QtWidgets.QWidget.__init__(self, parent=parent)

        layout = QtWidgets.QVBoxLayout()

        self.conversation_display_support = \
            ConversationDisplaySupport(parent=parent, conversation_display=conversation_display)
        self.message_writer_support = \
            MessageWriterSupport(parent=parent, message_writer=message_writer)

        # noinspection PyArgumentList
        layout.addWidget(self.conversation_display_support)
        # noinspection PyArgumentList
        layout.addWidget(self.message_writer_support)

        self.setLayout(layout)


class MessageWriter(QtWidgets.QPlainTextEdit):

    """
    The widget where the admin enters the text he wants to send.
    """

    def __init__(self, interface):

        super().__init__()
        self.interface = interface

    def keyPressEvent(self, event):

        if event.key() == QtCore.Qt.Key_Return:
            self.send()
        else:
            super().keyPressEvent(event)

    def send(self):

        self.interface.new_message_from_admin(self.toPlainText())
        self.setPlainText("")


class MessageWriterSupport(QtWidgets.QWidget):

    """
    This widget contains the 'message writer' (the widget where the admin enters the text he wants to send).
    """

    def __init__(self, parent, message_writer):

        # noinspection PyArgumentList
        QtWidgets.QWidget.__init__(self, parent=parent)

        self.message_writer = message_writer

        layout = QtWidgets.QHBoxLayout(self)

        button_send = QtWidgets.QPushButton("Send")
        # noinspection PyUnresolvedReferences
        button_send.clicked.connect(self.message_writer.send)
        button_send.setSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)

        # noinspection PyArgumentList
        layout.addWidget(self.message_writer)
        # noinspection PyArgumentList
        layout.addWidget(button_send)


class ConversationDisplaySupport(QtWidgets.QWidget):

    """
    This widget contains the  'conversation display'.
    """

    def __init__(self, parent, conversation_display):

        # noinspection PyArgumentList
        QtWidgets.QWidget.__init__(self, parent=parent)

        layout = QtWidgets.QHBoxLayout(self)
        # noinspection PyArgumentList
        layout.addWidget(conversation_display)


class Entry(QtWidgets.QLabel):

    """
    Each instance of this class is a part of the 'conversation picker'.
    """

    def __init__(self, user_name, interface):

        super().__init__()

        self.user_name = user_name
        self.interface = interface

        self.setText(user_name)
        self.setContentsMargins(10, 0, 10, 0)

        self.pending_messages = 0

        self.setAutoFillBackground(True)

    def select(self):

        # When user select this entry, proceed to this...

        self.pending_messages = 0
        self.setText(self.user_name)

        self.change_background_color("blue")

    def deselect(self):

        # When user selects an another entry, proceed to this...

        self.change_background_color("transparent")

    def mousePressEvent(self, event):

        self.interface.change_selected_conversation(self.user_name)

    def new_pending_message(self):

        self.pending_messages += 1
        self.setText("{} <b>[{}]</b>".format(self.user_name, self.pending_messages))

    def change_background_color(self, color):

        colors = {
            "gray": QtCore.Qt.lightGray, "transparent": QtCore.Qt.transparent,
            "blue": "#5294E2"}

        self.setStyleSheet("background-color: {};".format(colors[color]))

        # if not hex color
        # p = self.palette()
        # p.setColor(self.backgroundRole(), colors[color])
        # self.setPalette(p)


class ConversationPicker(QtWidgets.QTableWidget):

    """
    Contained in the left bar. Used for storing links for all the open discussions.
    User click on entries to 'pick' one.
    """

    def __init__(self, interface):

        super().__init__(0, 1)

        self.interface = interface

        # Hide the headers
        self.verticalHeader().hide()
        self.horizontalHeader().hide()

        # Expand first column
        self.horizontalHeader().setStretchLastSection(True)

        # To avoid perturbing selection of entries, disable focus
        self.setFocusPolicy(QtCore.Qt.NoFocus)

        # Container for entries
        self.entries = {}

    def create_new_entry(self, user_name, select=False):

        # Create a new entry in the menu...
        self.entries[user_name] = Entry(user_name, self.interface)

        self.insertRow(0)
        self.setCellWidget(0, 0, self.entries[user_name])

        if select:
            self.entries[user_name].setFocus()

    def new_pending_message(self, user_name):

        # Will have as a consequence to add a number next to the name...
        self.entries[user_name].new_pending_message()

    def pick(self, user_name):

        for key in self.entries:
            self.entries[key].deselect()

        self.entries[user_name].select()


class ConversationDisplay(QtWidgets.QPlainTextEdit):

    """
    Contained in the right bar.
    It is the widget used for displaying the content of a conversation.
    """

    def __init__(self):

        super().__init__()

        self.setReadOnly(True)

    def display(self, text):

        self.setPlainText(text)
        self.verticalScrollBar().setValue(self.verticalScrollBar().maximum())


class MessengerFrame(QtWidgets.QWidget, Logger):

    """
    Main frame of the messenger.
    """

    name = "MessengerFrame"

    def __init__(self, parent):

        # noinspection PyArgumentList
        super().__init__()

        self.parent = parent
        self.setWindowTitle("Messenger")

        layout = QtWidgets.QHBoxLayout(self)

        self.conversation_display = ConversationDisplay()
        self.conversations = Conversations(parent=self)

        self.conversation_picker = ConversationPicker(interface=self)
        self.message_writer = MessageWriter(interface=self)

        self.left_panel = \
            LeftPanel(parent=self, conversation_picker=self.conversation_picker)
        self.right_panel = \
            RightPanel(parent=self, message_writer=self.message_writer, conversation_display=self.conversation_display)

        layout.addWidget(self.left_panel, alignment=QtCore.Qt.AlignHCenter)
        # noinspection PyArgumentList
        layout.addWidget(self.right_panel)

    def change_selected_conversation(self, user_name):

        self.log("Change selected_conversation (selected is '{}').".format(user_name))

        # Because SQL is case insensitive
        user_name = user_name.lower().capitalize()

        if user_name not in self.conversations.dic.keys():

            self.conversations.create_new_conversation(user_name)
            self.conversation_picker.create_new_entry(user_name, select=True)

        self.conversations.change_selected(user_name)
        content = self.conversations.get_current_content()

        self.conversation_display.display(content)
        self.conversation_picker.pick(user_name)

    def new_message_from_admin(self, message):

        if message:

            self.log("I will send message '{}'.".format(message))

            if self.conversations.selected is None:
                if not self.left_panel.click_new_conversation():
                    self.log("Sending of the message cancelled.")
                    return

            self.conversations.new_message_from_admin(message)
            self.conversation_display.display(self.conversations.get_current_content())
            self.parent.send_message_to_user(self.conversations.selected, message)

    def new_message_from_user(self, user_name, message):

        # Because SQL is case insensitive
        user_name = user_name.lower().capitalize()

        new_user = user_name not in self.conversations.dic.keys()

        if new_user:
            self.conversations.create_new_conversation(user_name)
            self.conversation_picker.create_new_entry(user_name, select=self.conversations.selected is None)

        self.conversations.new_message_from_user(user_name, message)

        if self.conversations.selected is None:
            self.conversations.selected = user_name

        if self.conversations.selected == user_name:
            self.conversation_display.display(self.conversations.get_current_content())
            self.conversation_picker.pick(user_name)

        else:
            self.conversation_picker.new_pending_message(user_name)


if __name__ == '__main__':

    app = QtWidgets.QApplication(sys.argv)
    window = MessengerFrame()
    window.resize(1000, 500)
    window.show()
    sys.exit(app.exec_())
