from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QTableWidget, QTableWidgetItem, \
    QHeaderView, QVBoxLayout, QAbstractItemView, QWidget


class TableLayout(QWidget):

    name = "TableLayout"

    def __init__(self, parent, role, labels):
        
        super().__init__()

        self.setParent(parent)
        self.role = role
        self.columns = labels

        self.table = QTableWidget()

        self.layout = QVBoxLayout()
        self.layout.addWidget(self.table)

        self.setLayout(self.layout)

    def prepare(self, rows):
        
        columns = self.columns["fancy_labels"]

        # empty tables
        self.table.clear()

        # set non editable and disable selection
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setSelectionMode(QAbstractItemView.NoSelection)
        self.table.setFocusPolicy(Qt.NoFocus)

        # set height and width
        self.table.setColumnCount(len(columns))
        self.table.setRowCount(len(rows))

        # fit the widget
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.verticalHeader().setSectionResizeMode(QHeaderView.Stretch)

        # set column names (parameters to print)
        for i, param in enumerate(columns):
            self.table.setHorizontalHeaderItem(i, QTableWidgetItem(param))

        # set rows names (server ids, then game ids)
        for i, ids in enumerate(rows):
            self.table.setVerticalHeaderItem(
                    i, QTableWidgetItem("Server id: {} | Game id: {}".format(*ids))
            )

    def update(self, rows, parameters):

        # set rows names (server ids, then game ids)
        for i, ids in enumerate(rows):
            self.table.setVerticalHeaderItem(
                    i, QTableWidgetItem("Server id: {} | Game id: {}".format(*ids))
            )

        self.fill_table(rows, parameters)

    def fill_table(self, rows, parameters):

        # for each game_id
        for x, (name, game_id) in enumerate(rows):

            # for each label
            for y, label in enumerate(self.columns["labels"]):

                data = parameters["current_state"][label]
                cond = game_id in parameters["{}s_id".format(self.role)].keys()

                if cond:
                    role_id = parameters["{}s_id".format(self.role)][game_id]

                    # if data is available
                    if len(data) > int(role_id):
                        string = str(data[role_id])
                        self.table.setItem(x, y, QTableWidgetItem(string))
