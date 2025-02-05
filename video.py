from PySide6.QtWidgets import QApplication, QMainWindow, QWidget, QSlider, QStackedWidget, QLabel, QVBoxLayout, QStatusBar, QToolBar, QTableView
from PySide6.QtGui import QAction, QKeySequence
from PySide6.QtCore import QTimer, QObject, QEvent, Qt, QAbstractTableModel
from PySide6.QtMultimedia import QMediaPlayer
from PySide6.QtMultimediaWidgets import QVideoWidget
from pyvidplayer2 import VideoPySide

from modules import DictModel

import time
import yaml
import os
import typing
import logging

configFile = "config.yaml"
configTemplate = """
# Default formatted config
#
# Names will show up in a dropdown for the action menu to label timestamps followed by a key shortcut for it
labels:
  Name:
    Display_Name: Name
    Shortcut: Ctrl+1
  Other_name:
    Display_Name: Other_Name
    Shortcut: Ctrl+2
  Other_name_again:
    Display_Name: Other_name_again
    Shortcut: Ctrl+3
"""

if(not os.path.exists(configFile)):
    with open(configFile, "w") as file:
        print("Missing config file, creating...")
        yaml.dump(yaml.safe_load(configTemplate), file, indent=2)
    exit()

class TimestampModel(QAbstractTableModel):
    def __init__(self):
        super().__init__()
        self.timestamps = {}
    
    def data(self, index, role):
        if(role == Qt.DisplayRole):
            return list(self.timestamps.items())[index.row()][index.column()]

    def headerData(self, section: int, orientation: Qt.Orientation, role = Qt.DisplayRole):
        if(role == Qt.DisplayRole and orientation == Qt.Horizontal):
            if(section == 0):
                return "Timestamp"
            elif(section == 1):
                return "Action"
            else:
                return None

    def rowCount(self, index):
        length = len(list(self.timestamps.keys()))
        return length
    
    def columnCount(self, index):
        try:
            length = len(list(self.timestamps.items())[0])
        except IndexError:
            length = 2
        return length

class TimestampWindow(QWidget):
    def __init__(self, model: TimestampModel):
        super().__init__()
        self._layout = QVBoxLayout()
        self.table = QTableView()
        self.model = model
        self.table.setModel(self.model)
        self._layout.addWidget(self.table)
        self.setLayout(self._layout)

        self.setWindowTitle("Timestamp viewer")

class VideoWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.videoFile = "test.mp4"
        self.video = VideoPySide(self.videoFile)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update)
        self.timer.start(int(1/self.video.frame_rate))

        self.timerWidget = QStatusBar()
        #self.mainLayout = QVBoxLayout()
        #self.timerWidget = QLabel()
        #self.timerWidget.setStyleSheet("font-size: 24px")

        #self.mainLayout.addWidget(self.timerWidget)
        #self.setLayout(self.mainLayout)
        #self.timerWidget.setAlignment(Qt.AlignLeft|Qt.AlignBottom)
    
    def paintEvent(self, _):
        if(self.video.active):
            self.video.draw(self, (0, 0))
        else:
            self.video = VideoPySide(self.videoFile)
            self.video.mute()
            return
        #self.timerWidget.setText(time.strftime("%H:%M:%S", time.gmtime(self.video.get_pos())))
        self.timerWidget.showMessage(self.timestamp)
    
    @property
    def timestamp(self):
        return time.strftime("%H:%M:%S", time.gmtime(self.video.get_pos()))

class Window(QMainWindow):
    def __init__(self):
        super().__init__()

        self.timestamps = dict()

        with open(configFile, "r") as file:
            self.config: dict = yaml.safe_load(file)
        
        self.timestamps = dict()

        self.setWindowTitle(f"Logiwise Observation Tool")

        #self.mainLayout = QVBoxLayout()

        self.videoWidget = VideoWidget()
        self.setFixedSize(self.videoWidget.video.current_size[0], self.videoWidget.video.current_size[1])

        self.stackWidget = QStackedWidget(self)
        self.stackWidget.addWidget(self.videoWidget)
        self.setCentralWidget(self.stackWidget)
        self.setStatusBar(self.videoWidget.timerWidget)

        menu = self.menuBar()
        labelAddMenu = menu.addMenu("&Add")
        labelViewMenu = menu.addMenu("&View")
        labelExportMenu = menu.addMenu("&Export")

        viewTimestamps = QAction("All timestamps", self)
        viewTimestamps.setStatusTip("Shows all timestamps with corresponding labels")
        viewTimestamps.triggered.connect(self.onViewTimestampsClick)
        labelViewMenu.addAction(viewTimestamps)

        exportTimestamps = QAction("Export timestamps", self)
        exportTimestamps.setStatusTip("Shows all timestamps with corresponding labels")
        exportTimestamps.triggered.connect(self.onViewTimestampsClick)
        labelExportMenu.addAction(exportTimestamps)

        # Lambda in a loop doesn't work greatly but I still need to pass values so I know what button got triggered
        # So a new function it is!
        labels: dict = self.config["labels"]
        for label, values in labels.items():
            actionButton = self.createLabelButton(label, values)
            labelAddMenu.addAction(actionButton)
            actionButton = self.createLabelTimestampButton(label, values)
            labelViewMenu.addAction(actionButton)
            actionButton = self.createLabelExportButton(label, values)
            labelExportMenu.addAction(actionButton)

        # Initializing these so we have a table to update whenever

        self.timestampTable = TimestampModel()
        self.timestampWindow = TimestampWindow(self.timestampTable)

        #toolbar = QToolBar("Toolbar")
        #self.addToolBar(toolbar)

        #button_action = QAction("Add label", self)
        #button_action.setStatusTip("Add label of an action at current timestamp")
        #button_action.triggered.connect(self.onAddLabelClick)
        #toolbar.addAction(button_action)
    
    def createLabelButton(self, label: str, values: dict()):
        actionButton = QAction(f"{values['Display_Name']} ({values['Shortcut']})", self)
        actionButton.setStatusTip("Add label at current timestamp")
        actionButton.triggered.connect(lambda: self.onAddLabelClick(label))
        actionButton.setShortcut(QKeySequence(f"{values['Shortcut']}"))
        return actionButton
    
    def createLabelTimestampButton(self, label: str, values: dict()):
        actionButton = QAction(f"Timestamps of {values['Display_Name']}", self)
        actionButton.setStatusTip("Show timestamps for this label")
        actionButton.triggered.connect(lambda: self.onViewLabelTimestampClick(label))
        return actionButton
    
    def createLabelExportButton(self, label: str, values: dict()):
        actionButton = QAction(f"Export timestamps of {values['Display_Name']}", self)
        actionButton.setStatusTip("Export timestamps for this label")
        actionButton.triggered.connect(lambda: self.onExportLabelClick(label))
        return actionButton

    def onAddLabelClick(self, label: str):
        print(f"Label {label} triggered at time {self.videoWidget.timestamp}")
        self.timestamps[self.videoWidget.timestamp] = label

        # Force an update of the table by invalidating the display, this is bad but Pyside forced my hand
        self.timestampTable.beginResetModel()
        self.timestampTable.timestamps = self.timestamps
        self.timestampTable.endResetModel()
    
    def onViewTimestampsClick(self, _):
        print("Timestamp viewer for all labels clicked")
        if(len(self.timestamps.keys()) == 0):
            return
        self.timestampWindow.show()

    def onViewLabelTimestampClick(self, label: str):
        print(f"Timestamp for label {label} viewer clicked")
    
    def onExportLabelClick(self, label: str):
        print(f"Export for label {label} triggered")

    def closeEvent(self, event):
        # Properly close the video object
        self.videoWidget.video.close()
        self.timestampWindow.destroy()
    
    def keyPressEvent(self, event):
        # Prevent keys being registered multiple times
        if(event.isAutoRepeat()):
            return
        
        video = self.videoWidget.video
        if(event.key() == Qt.Key_Escape):
            self.close()
            print("Closing program")
        elif(event.key() == Qt.Key_Space):
            video.toggle_pause()
        elif(event.key() == Qt.Key_Left):
            video.seek(-5)
        elif(event.key() == Qt.Key_Right):
            video.seek(5)
        else:
            print(event.key())

app = QApplication([])
win = Window()
win.show()
app.exec()