from PyQt5.QtWidgets import QMenuBar, QMenu, QAction

from utils.utils import Logger


class MenuBar(QMenuBar, Logger):

    name = "MenuBar"

    def __init__(self, parent):

        super().__init__(parent=parent)
        
        self.edit_menu = self.addMenu("Edit")
        self.action_menu = self.addMenu("Actions")
    
        self.show_config_files = QAction("Edit config files", self)
        self.erase_sql_tables = QAction("Erase sql tables", self)
        self.messenger = QAction("Chat with strangers", self)
        self.missing_players = QAction("Set missing players", self)

        self.setup_edit()
        self.setup_action()

        self.show()

    def setup_edit(self):

        self.show_config_files.triggered.connect(self.parent().show_menubar_frame_config_files) 
        self.edit_menu.addAction(self.show_config_files)

    def setup_action(self):
        
        # Erase sql tables
        self.erase_sql_tables.triggered.connect(self.parent().show_menubar_frame_erase_sql_tables) 
        self.action_menu.addAction(self.erase_sql_tables)

        # Messenger
        self.messenger.triggered.connect(self.parent().show_menubar_frame_messenger)
        self.action_menu.addAction(self.messenger)

        # Missing Players
        self.missing_players.triggered.connect(self.parent().show_menubar_frame_missing_players)
        self.action_menu.addAction(self.missing_players)

