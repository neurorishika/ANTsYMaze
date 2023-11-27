# a GUI for designing masks for the Linear Choice Assay

import numpy as np
import sys
import os
from PIL import Image
import json


from matplotlib.path import Path
import matplotlib.pyplot as plt

from PyQt5 import QtCore, QtGui, QtWidgets

class MainWindow(QtWidgets.QMainWindow):

    ## MAIN WINDOW DESIGN

    # At the Top: 
    # 1. An option to load a new background image (Label + Text Box + Browse Button) (Row 1)
    # 2. Number of Arenas per Image (Label + Positive Integer Text Box with a default value of 24) (Row 2)
    # 3. Width of the Arena (Label + Positive Integer Text Box with a default value of 100) (Row 2)
    # 4. Number of POIs per Arena (Label + Positive Integer Text Box with a default value of 0) (Row 3)
    # 5. Start Labeling Button (Row 4)

    # In the Middle:
    # 1. A canvas for the background image (Row 1)

    # At the Bottom:
    # 1. Instructions Text Box (Row 1)
    # 2. Show Example Button (Row 1)


    def __init__(self, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)

        # set up the main layout
        layout = QtWidgets.QVBoxLayout()

        # set up the top layout
        topLayout = QtWidgets.QGridLayout()
        topLayout.setSpacing(10)

        # first row
        self.backgroundLabel = QtWidgets.QLabel("Background Image:")
        self.backgroundTextBox = QtWidgets.QLineEdit()
        self.backgroundBrowseButton = QtWidgets.QPushButton("Browse")
        self.backgroundBrowseButton.clicked.connect(self.browseBackgroundImage)
        topLayout.addWidget(self.backgroundLabel, 0, 0)
        topLayout.addWidget(self.backgroundTextBox, 0, 1, 1, 2)
        topLayout.addWidget(self.backgroundBrowseButton, 0, 3)

        # second row
        self.arenasLabel = QtWidgets.QLabel("Number of Arenas:")
        self.arenasTextBox = QtWidgets.QLineEdit()
        self.arenasTextBox.setText("8")
        self.arenasTextBox.setValidator(QtGui.QIntValidator(1, 100))
        self.arenasTextBox.setAlignment(QtCore.Qt.AlignRight)

        self.widthLabel = QtWidgets.QLabel("Width of Arena:")
        self.widthTextBox = QtWidgets.QLineEdit()
        self.widthTextBox.setText("100")
        self.widthTextBox.setValidator(QtGui.QIntValidator(1,1000))
        self.widthTextBox.setAlignment(QtCore.Qt.AlignRight)

        topLayout.addWidget(self.arenasLabel, 1, 0)
        topLayout.addWidget(self.arenasTextBox, 1, 1)
        topLayout.addWidget(self.widthLabel, 1, 2)
        topLayout.addWidget(self.widthTextBox, 1, 3)

        # third row
        self.poisLabel = QtWidgets.QLabel("Number of POIs:")
        self.poisTextBox = QtWidgets.QLineEdit()
        self.poisTextBox.setText("3")
        self.poisTextBox.setValidator(QtGui.QIntValidator(0, 10))
        self.poisTextBox.setAlignment(QtCore.Qt.AlignRight)

        topLayout.addWidget(self.poisLabel, 2, 0, 1, 2)
        topLayout.addWidget(self.poisTextBox, 2, 2, 1, 2)

        # fourth row
        self.startLabelingButton = QtWidgets.QPushButton("Start Labeling")
        self.startLabelingButton.clicked.connect(self.startLabeling)
        # disable the button until an image is loaded
        self.startLabelingButton.setEnabled(False)

        topLayout.addWidget(self.startLabelingButton, 3, 0, 1, 4)

        # add the top layout to the main layout
        layout.addLayout(topLayout)

        # set up the middle layout with an Image Label
        middleLayout = QtWidgets.QHBoxLayout()
        self.imageLabel = QtWidgets.QLabel()
        # make the image label scalable
        self.imageLabel.setScaledContents(True)
        self.imageLabel.setSizePolicy(QtWidgets.QSizePolicy.Ignored, QtWidgets.QSizePolicy.Ignored)
        # set the image label to accept mouse clicks
        self.imageLabel.setMouseTracking(True)
        # change the cursor to a crosshair
        self.imageLabel.setCursor(QtCore.Qt.CrossCursor)

        # add event listener for mouse clicks
        self.imageLabel.installEventFilter(self)

        # initialize status variables
        self.loaded_image = False
        self.currently_labeling = False
        self.currently_labeling_poi = False

        # add the image label to the middle layout
        middleLayout.addWidget(self.imageLabel)

        # add the middle layout to the main layout
        layout.addLayout(middleLayout)

        # set up the bottom layout 
        bottomLayout = QtWidgets.QHBoxLayout()

        # first row (single line)
        self.instructionsTextBox = QtWidgets.QTextEdit()
        self.instructionsTextBox.setMaximumHeight(50)
        self.instructionsTextBox.setReadOnly(True)
        
        # set default instructions
        self.instructionsTextBox.setText("Load a background image and click Start Labeling to begin.")

        self.showExampleButton = QtWidgets.QPushButton("Show Example")
        self.showExampleButton.clicked.connect(self.showExample)

        bottomLayout.addWidget(self.instructionsTextBox)
        bottomLayout.addWidget(self.showExampleButton)

        # add the bottom layout to the main layout
        layout.addLayout(bottomLayout)

        # set the main layout
        widget = QtWidgets.QWidget()
        widget.setLayout(layout)

        self.setCentralWidget(widget)

        # set the window title
        self.setWindowTitle("ANTsYMaze Linear Mask Designer")
        # set the window size
        self.resize(800, 600)
        self.show()

    ## LOAD BACKGROUND IMAGE
    def browseBackgroundImage(self):
        # open a file dialog to select the background image
        filename = QtWidgets.QFileDialog.getOpenFileName(self, "Open File", "", "Image Files (*.png *.jpg *.jpeg *.bmp)")
        if filename[0] != "":
            # set the background image
            self.backgroundTextBox.setText(filename[0])
            self.image = QtGui.QPixmap(filename[0])
            self.imageLabel.setPixmap(self.image)
            self.imageLabel.resize(self.image.width(), self.image.height())
            self.imageLabel.show()
            self.loaded_image = True
            
            # set the instructions
            self.instructionsTextBox.setText("Check options and click Start Labeling to begin.")
            # enable the start labeling button
            self.startLabelingButton.setEnabled(True)
        else:
            # alert the user that no image was selected
            msg = QtWidgets.QMessageBox()
            msg.setIcon(QtWidgets.QMessageBox.Critical)
            msg.setText("No image selected!")
            msg.setWindowTitle("Error")
            msg.exec_()
            self.loaded_image = False
            self.instructionsTextBox.setText("Make sure to select a background image and click Start Labeling to begin.")

    ## START LABELING
    def startLabeling(self):
        # check if the image is loaded
        assert self.loaded_image
        # disable all the options
        self.backgroundTextBox.setEnabled(False)
        self.backgroundBrowseButton.setEnabled(False)
        self.arenasTextBox.setEnabled(False)
        self.widthTextBox.setEnabled(False)
        self.poisTextBox.setEnabled(False)
        # rename the start labeling button to restart labeling
        self.startLabelingButton.setText("Restart Labeling")
        # set the instructions
        self.instructionsTextBox.setText("Click on the image to start labelling the first endpoint of the first arena.")
        # set the status variables
        self.currently_labeling = True
        self.currently_labeling_poi = False
        self.n_arenas = int(self.arenasTextBox.text())
        self.n_pois = int(self.poisTextBox.text())
        self.arena_width = int(self.widthTextBox.text())
        self.labelled_endpoints = []
        self.labelled_pois = []
        # draw the points
        self.draw_points(None)

    ## SHOW EXAMPLE
    def showExample(self):
        pass

    ## EVENTS

    # a function to get the position of a mouse click wrt the image
    def get_pointer_position(self, event):
        # get the position of the click
        x = event.x()
        y = event.y()
        # get the size of the image
        width = self.image.width()
        height = self.image.height()
        # get the size of the label
        label_width = self.imageLabel.width()
        label_height = self.imageLabel.height()
        # get the size of the pixmap
        pixmap_width = self.imageLabel.pixmap().width()
        pixmap_height = self.imageLabel.pixmap().height()
        # convert the click position to the position of the pixmap
        x = x * pixmap_width / label_width
        y = y * pixmap_height / label_height
        # convert the pixmap position to the position of the image
        x = x * width / pixmap_width
        y = y * height / pixmap_height
        return x, y
    
    # a function to draw the points on the image based on where the user clicks
    def draw_points(self, event):
        # redraw the image
        self.image = QtGui.QPixmap(self.backgroundTextBox.text())
        self.imageLabel.setPixmap(self.image)
        self.imageLabel.resize(self.image.size())
        self.imageLabel.show()
        # draw the labelled endpoints in red
        dot_size = int(0.005
                        * self.image.width())
        painter = QtGui.QPainter(self.image)

        painter.setPen(QtGui.QPen(QtCore.Qt.red, dot_size))
        for arena in self.labelled_endpoints:
            for endpoint in arena:
                # painter.drawEllipse(endpoint[0], endpoint[1], dot_size, dot_size)
                painter.drawEllipse(int(np.round(endpoint[0])), int(np.round(endpoint[1])), dot_size, dot_size)

        # draw the arena numbers
        painter.setPen(QtGui.QPen(QtCore.Qt.red, 1))
        for i, arena in enumerate(self.labelled_endpoints):
            for j, endpoint in enumerate(arena):
                # painter.drawText(endpoint[0]+dot_size, endpoint[1]-dot_size, f"{i+1}.{j+1}")
                painter.drawText(int(np.round(endpoint[0]))+dot_size, int(np.round(endpoint[1]))-dot_size, f"{i+1}.{j+1}")

        # if there are three endpoints, get the centroid, join each endpoint to the centroid and draw the line
        for arena in self.labelled_endpoints:
            if len(arena)==3:
                # get the centroid
                centroid = np.mean(arena, axis=0)
                # draw the centroid point
                painter.setPen(QtGui.QPen(QtCore.Qt.red, dot_size))
                painter.drawEllipse(int(np.round(centroid[0])), int(np.round(centroid[1])), dot_size, dot_size)
                # connect each endpoint to the centroid
                painter.setPen(QtGui.QPen(QtCore.Qt.red, dot_size//2))
                for endpoint in arena:
                    painter.drawLine(int(np.round(endpoint[0])), int(np.round(endpoint[1])), int(np.round(centroid[0])), int(np.round(centroid[1])))
        
        # draw the labelled pois in blue
        painter.setPen(QtGui.QPen(QtCore.Qt.blue, dot_size//2))
        for arena in self.labelled_pois:
            for poi in arena:
                # painter.drawEllipse(poi[0], poi[1], dot_size//2, dot_size//2)
                painter.drawEllipse(int(np.round(poi[0])), int(np.round(poi[1])), dot_size//2, dot_size//2)

        # draw the poi numbers
        painter.setPen(QtGui.QPen(QtCore.Qt.blue, 1))
        for i, arena in enumerate(self.labelled_pois):
            for j, poi in enumerate(arena):
                # painter.drawText(poi[0]+dot_size//2, poi[1]-dot_size//2, f"{i+1}.{j+1}")
                painter.drawText(int(np.round(poi[0]))+dot_size//2, int(np.round(poi[1]))-dot_size//2, f"{i+1}.{j+1}")
        
        painter.end()

        # update the image
        self.imageLabel.setPixmap(self.image)
        self.imageLabel.resize(self.image.size())
        self.imageLabel.show()

    # the event filter for the image label to handle left and right clicks
    def eventFilter(self, source, event):
        # check if the object is the image label with a pixmap and if the event is a left mouse click and if the labelling has started
        if (
            source == self.imageLabel
            and self.imageLabel.pixmap()
            and event.type() == QtCore.QEvent.MouseButtonPress
            and event.button() == QtCore.Qt.LeftButton
            and self.currently_labeling
        ):
            # get the x and y coordinates of the click
            x, y = self.get_pointer_position(event)

            # handle poi vs endpoint
            # CASE 1: POI LABELLING
            if self.currently_labeling_poi:
                if len(self.labelled_pois)==0 or len(self.labelled_pois[-1])==self.n_pois:
                    # add the poi
                    self.labelled_pois.append([(x,y)])
                    self.draw_points(event)
                    if self.n_pois == 1:
                        # ask the user if are sure to move on to the next arena
                        msg = QtWidgets.QMessageBox()
                        msg.setIcon(QtWidgets.QMessageBox.Question)
                        msg.setText(f"Arena {len(self.labelled_pois)} POI has been labelled. Do you want to move on to the next step?")
                        msg.setWindowTitle("Confirm")
                        msg.setStandardButtons(QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
                        retval = msg.exec_()
                        if retval == QtWidgets.QMessageBox.No:
                            # remove the poi
                            self.labelled_pois.pop()
                            self.draw_points(event)
                            # set the instructions
                            self.instructionsTextBox.setText("Click on the image to label the next POI of the arena. Right click to undo.")
                        else:
                            # check if there are any arenas left to label
                            if len(self.labelled_endpoints) < self.n_arenas:
                                # set the instructions
                                self.instructionsTextBox.setText("Click on the image to start labelling the first endpoint of the next arena.")
                                # set the status variables
                                self.currently_labeling_poi = False
                            else:
                                # set the instructions
                                self.instructionsTextBox.setText("All arenas have been labelled.")
                                # set the status variables
                                self.currently_labeling = False
                                self.currently_labeling_poi = False
                                # generate the masks
                                self.generate_masks()
                    else:
                        # set the instructions
                        self.instructionsTextBox.setText("Click on the image to label the next POI of the arena. Right click to undo.")
                else:
                    # add the other pois
                    self.labelled_pois[-1].append((x,y))
                    self.draw_points(event)

                    # see if there are any pois left to label
                    if len(self.labelled_pois[-1])==self.n_pois:
                        # ask the user if are sure to move on to the next arena
                        msg = QtWidgets.QMessageBox()
                        msg.setIcon(QtWidgets.QMessageBox.Question)
                        msg.setText(f"Arena {len(self.labelled_pois)} POIs have been labelled. Do you want to move on to the next step?")
                        msg.setWindowTitle("Confirm")
                        msg.setStandardButtons(QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
                        msg.setDefaultButton(QtWidgets.QMessageBox.Yes)
                        retval = msg.exec_()
                        if retval == QtWidgets.QMessageBox.No:
                            # remove the poi
                            self.labelled_pois[-1].pop()
                            self.draw_points(event)
                            # set the instructions
                            self.instructionsTextBox.setText("Click on the image to label the next POI of the arena. Right click to undo.")
                        else:
                            # check if there are any arenas left to label
                            if len(self.labelled_endpoints) < self.n_arenas:
                                # set the instructions
                                self.instructionsTextBox.setText("Click on the image to start labelling the first endpoint of the next arena.")
                                # set the status variables
                                self.currently_labeling_poi = False
                            else:
                                # set the instructions
                                self.instructionsTextBox.setText("All arenas have been labelled.")
                                # set the status variables
                                self.currently_labeling = False
                                self.currently_labeling_poi = False
                                # generate the masks
                                self.generate_masks()
                    else:
                        # set the instructions
                        self.instructionsTextBox.setText("Click on the image to label the next POI of the arena. Right click to undo.")
            # CASE 2: ENDPOINT LABELLING
            else:
                if len(self.labelled_endpoints)==0 or len(self.labelled_endpoints[-1])==3:
                    # add the first endpoint
                    self.labelled_endpoints.append([(x,y)])
                    self.draw_points(event)

                    # set the instructions
                    self.instructionsTextBox.setText("Click on the image to label the second endpoint of the arena. Right click to undo.")
                else:
                    # add the next endpoint
                    self.labelled_endpoints[-1].append((x,y))
                    self.draw_points(event)

                    # check if there are any endpoints left to label
                    if len(self.labelled_endpoints[-1])==3:
                        # ask the user if are sure to move on to the next arena
                        msg = QtWidgets.QMessageBox()
                        msg.setIcon(QtWidgets.QMessageBox.Question)
                        msg.setText(f"Arena {len(self.labelled_endpoints)} has been labelled. Do you want to move on to the next step?")
                        msg.setWindowTitle("Confirm")
                        msg.setStandardButtons(QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
                        msg.setDefaultButton(QtWidgets.QMessageBox.Yes)
                        retval = msg.exec_()

                        if retval == QtWidgets.QMessageBox.No:
                            # remove the second endpoint
                            self.labelled_endpoints[-1].pop()
                            self.draw_points(event)
                            # set the instructions
                            self.instructionsTextBox.setText("Click on the image to label the second endpoint of the arena. Right click to undo.")
                        else:
                            # check if there are any poi to label
                            if self.n_pois > 0:
                                # set the instructions
                                self.instructionsTextBox.setText("Click on the image to label the first POI of the arena.")
                                # set the status variables
                                self.currently_labeling_poi = True
                            else:
                                # check if there are any arenas left to label
                                if len(self.labelled_endpoints) < self.n_arenas:
                                    # set the instructions
                                    self.instructionsTextBox.setText("Click on the image to start labelling the first endpoint of the next arena.")
                                else:
                                    # set the instructions
                                    self.instructionsTextBox.setText("All arenas have been labelled.")
                                    # set the status variables
                                    self.currently_labeling = False
                                    self.currently_labeling_poi = False
                                    # generate the masks
                                    self.generate_masks()

        # check if the object is the image label with a pixmap and if the event is a right mouse click and if the labelling has started
        if (
            source == self.imageLabel
            and self.imageLabel.pixmap()
            and event.type() == QtCore.QEvent.MouseButtonPress
            and event.button() == QtCore.Qt.RightButton
            and self.currently_labeling
        ):

            # handle poi vs endpoint
            # CASE 1: POI LABELLING
            if self.currently_labeling_poi:
                if len(self.labelled_pois)==0 or len(self.labelled_pois[-1])==self.n_pois:
                    # Tell the user that there are no pois to undo
                    msg = QtWidgets.QMessageBox()
                    msg.setIcon(QtWidgets.QMessageBox.Warning)
                    msg.setText("No more POIs to undo!")
                    msg.setWindowTitle("Warning")
                    msg.exec_()

                    # set the instructions
                    self.instructionsTextBox.setText("Click on the image to label the next POI of the arena.")
                else:
                    # remove the last poi
                    # check if there are any pois left to remove
                    if len(self.labelled_pois[-1])>0:
                        self.labelled_pois[-1].pop()
                    else:
                        # warn the user that there are no pois to remove
                        msg = QtWidgets.QMessageBox()
                        msg.setIcon(QtWidgets.QMessageBox.Warning)
                        msg.setText("No more POIs to undo!")
                        msg.setWindowTitle("Warning")
                        msg.exec_()

                    self.draw_points(event)
                    # set the instructions
                    self.instructionsTextBox.setText("Click on the image to label the next POI of the arena. Right click to undo.")
            else:
                if len(self.labelled_endpoints)==0 or len(self.labelled_endpoints[-1])==3:
                    # Tell the user that there are no endpoints to undo
                    msg = QtWidgets.QMessageBox()
                    msg.setIcon(QtWidgets.QMessageBox.Warning)
                    msg.setText("No more endpoints to undo!")
                    msg.setWindowTitle("Warning")
                    msg.exec_()

                    # set the instructions
                    self.instructionsTextBox.setText("Click on the image to start labelling the first endpoint of the arena.")
                else:
                    # remove the first endpoint
                    self.labelled_endpoints.pop()
                    self.draw_points(event)
                    
                    # set the instructions
                    self.instructionsTextBox.setText("Click on the image to label the first endpoint of the arena. Right click to undo.")

        return super(MainWindow, self).eventFilter(source, event)
    
    # a function to generate the masks
    def generate_masks(self):

        while True:

            # get the size of the image
            width = self.image.width()
            height = self.image.height()

            # create an empty dictionary of masks
            masks = {}
            merged = np.zeros((height, width, 4), dtype=np.uint8) # 4 channels: RGBA
            

            # draw a rectangle for each arena from the endpoints
            for arena in self.labelled_endpoints:
                # # get the endpoints
                # x1, y1 = arena[0]
                # x2, y2 = arena[1]
                # x3, y3 = arena[2]
                # get the centroid
                centroid = np.mean(arena, axis=0)
                # define the 4 corners of the rectangle using the width//2 perpendicular to the line joining ech endpoint to the centroid
                arena_arm_masks = []
                # loop through the endpoints
                for endpoint in arena:
                    # get the angle of the line joining the endpoint and the centroid
                    angle = np.arctan2(centroid[1]-endpoint[1], centroid[0]-endpoint[0])
                    # get the perpendicular angle
                    perp_angle = angle + np.pi/2
                    # get the x and y offsets
                    x_offset = self.arena_width//2 * np.cos(perp_angle)
                    y_offset = self.arena_width//2 * np.sin(perp_angle)
                    # get the corners of the pentagon (rectangl + centroid)
                    c1 = (int(endpoint[0]+x_offset), int(endpoint[1]+y_offset))
                    c2 = (int(endpoint[0]-x_offset), int(endpoint[1]-y_offset))
                    c3 = (int(centroid[0]-x_offset), int(centroid[1]-y_offset))
                    # centroid is the 4th corner
                    c4 = (int(centroid[0]), int(centroid[1]))
                    # the fifth corner is the last corner of the rectangle
                    c5 = (int(centroid[0]+x_offset), int(centroid[1]+y_offset))
                    # create a path
                    path = Path([c1, c2, c3, c4, c5])
                    # fill the path
                    x, y = np.mgrid[:width, :height]
                    points = np.transpose((x.ravel(), y.ravel()))
                    grid = path.contains_points(points)
                    grid = grid.reshape(x.shape)
                    # add the grid to the masks
                    arena_arm_masks.append(grid.astype(np.uint8).T*255)
                # merge all the arena arm masks into one mask
                arena_mask = np.zeros((height, width), dtype=np.uint8)
                for arm_mask in arena_arm_masks:
                    # add only where there is no overlap
                    arena_mask += arm_mask * (arena_mask==0)
                # add the arena mask to the masks
                masks[f"arena_{len(masks)+1}"] = arena_mask
                # add the arena mask to the merged mask (red channel)
                merged[:,:,0] += arena_mask

            # make the merged mask image
            merged_image = Image.fromarray(merged) 
            # save the merged mask image in the output folder
            merged_image.save(os.path.dirname(self.backgroundTextBox.text()) + "/{}_merged_mask.png".format(os.path.basename(self.backgroundTextBox.text()).split(".")[0]))
            # open the background image
            background = Image.open(self.backgroundTextBox.text())
            # overlay the merged mask on the background image
            merged_image.putalpha(128)
            background.paste(merged_image, (0,0), merged_image)

            # save the overlayed image in the output folder
            background.save(os.path.dirname(self.backgroundTextBox.text()) + "/{}_overlay.png".format(os.path.basename(self.backgroundTextBox.text()).split(".")[0]))

            # show the merged mask to the user using the image label
            self.image = QtGui.QPixmap(os.path.dirname(self.backgroundTextBox.text()) + "/{}_overlay.png".format(os.path.basename(self.backgroundTextBox.text()).split(".")[0]))
            self.imageLabel.setPixmap(self.image)
            self.imageLabel.resize(self.image.size())
            self.imageLabel.show()

            # alert the user that the masks have been generated
            msg = QtWidgets.QMessageBox()
            msg.setIcon(QtWidgets.QMessageBox.Information)
            msg.setText("Masks have been generated! Move the window to see the masks.")
            msg.setWindowTitle("Success")
            msg.exec_()


            # ask the user if they are happy with the width
            msg = QtWidgets.QMessageBox()
            msg.setIcon(QtWidgets.QMessageBox.Question)
            msg.setText("Are you happy with the width of the arenas?")
            msg.setWindowTitle("Confirm")
            msg.setStandardButtons(QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
            msg.setDefaultButton(QtWidgets.QMessageBox.Yes)
            retval = msg.exec_()

            if retval == QtWidgets.QMessageBox.Yes:
                break
            else:
                # ask the user to enter the width again
                while True:
                    width, okPressed = QtWidgets.QInputDialog.getInt(self, "Get Width","Width of the arena:", self.arena_width, 1, 1000, 1)
                    if okPressed:
                        self.arena_width = width
                        break
                    else:
                        continue
        
        # loop through pois and check if they are inside the arenas
        if self.n_pois > 0:
            self.instructionsTextBox.setText("Checking if the POIs are inside the arenas...")
            for i, arena in enumerate(self.labelled_endpoints):
                # create all the paths for the arena
                paths = []
                centroid = np.mean(arena, axis=0)
                # loop through the endpoints
                for endpoint in arena:
                    # get the angle of the line joining the endpoint and the centroid
                    angle = np.arctan2(centroid[1]-endpoint[1], centroid[0]-endpoint[0])
                    # get the perpendicular angle
                    perp_angle = angle + np.pi/2
                    # get the x and y offsets
                    x_offset = self.arena_width//2 * np.cos(perp_angle)
                    y_offset = self.arena_width//2 * np.sin(perp_angle)
                    # get the corners of the pentagon (rectangl + centroid)
                    c1 = (int(endpoint[0]+x_offset), int(endpoint[1]+y_offset))
                    c2 = (int(endpoint[0]-x_offset), int(endpoint[1]-y_offset))
                    c3 = (int(centroid[0]-x_offset), int(centroid[1]-y_offset))
                    # centroid is the 4th corner
                    c4 = (int(centroid[0]), int(centroid[1]))
                    # the fifth corner is the last corner of the rectangle
                    c5 = (int(centroid[0]+x_offset), int(centroid[1]+y_offset))
                    # create a path
                    path = Path([c1, c2, c3, c4, c5])
                    paths.append(path)

                # loop through the pois
                to_pop = []
                if len(self.labelled_pois[i])>0:
                    for j, poi in enumerate(self.labelled_pois[i]):
                        # check if the poi is inside the arena
                        if np.any([path.contains_point(poi) for path in paths]):
                            # keep the poi
                            pass
                        else:
                            print(f"POI {j+1} of arena {i+1} is outside the arena. Removing it...")
                            # remove the poi
                            to_pop.append(j)
                # remove the pois
                if len(to_pop)>0:
                    for j in to_pop[::-1]:
                        self.labelled_pois[i].pop(j)

        # save the masks as a json file
        self.instructionsTextBox.setText("Saving the masks...")
        masks = {k: v.tolist() for k, v in masks.items()}
        with open(os.path.dirname(self.backgroundTextBox.text()) + "/{}_masks.json".format(os.path.basename(self.backgroundTextBox.text()).split(".")[0]), "w") as f:
            json.dump(masks, f)

        # save the endpoints as a json file
        self.instructionsTextBox.setText("Saving the endpoints...")
        endpoints = {}
        endpoints["width"] = self.arena_width
        for i, arena in enumerate(self.labelled_endpoints):
            endpoints[f"arena_{i+1}_original"] = [list(endpoint) for endpoint in arena]
        with open(os.path.dirname(self.backgroundTextBox.text()) + "/{}_endpoints.json".format(os.path.basename(self.backgroundTextBox.text()).split(".")[0]), "w") as f:
            json.dump(endpoints, f)

        # make a poi dictionary
        self.instructionsTextBox.setText("Saving the POIs...")
        pois = {}
        for i, arena in enumerate(self.labelled_pois):
            pois[f"arena_{i+1}_original"] = np.array(arena).tolist()

        # save the pois as a json file
        with open(os.path.dirname(self.backgroundTextBox.text()) + "/{}_pois.json".format(os.path.basename(self.backgroundTextBox.text()).split(".")[0]), "w") as f:
            json.dump(pois, f)


        # set the instructions
        self.instructionsTextBox.setText("Completed. Click on Start Labeling to start again.")
        # set the status variables
        self.currently_labeling = False
        self.currently_labeling_poi = False
        self.labelled_endpoints = []
        self.labelled_pois = []
        # enable all the options
        self.backgroundTextBox.setEnabled(True)
        self.backgroundBrowseButton.setEnabled(True)
        self.arenasTextBox.setEnabled(True)
        self.widthTextBox.setEnabled(True)
        self.poisTextBox.setEnabled(True)
        # rename the start labeling button to restart labeling
        self.startLabelingButton.setText("Start Labeling")


# run the GUI
def main():
    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow()
    app.exec_()

if __name__ == "__main__":
    main()




        






        





