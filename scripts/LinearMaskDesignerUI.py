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
        self.arenasTextBox.setText("1")
        self.arenasTextBox.setValidator(QtGui.QIntValidator(1, 100))
        self.arenasTextBox.setAlignment(QtCore.Qt.AlignRight)

        self.widthLabel = QtWidgets.QLabel("Width of Arena:")
        self.widthTextBox = QtWidgets.QLineEdit()
        self.widthTextBox.setText("5")
        self.widthTextBox.setValidator(QtGui.QIntValidator(1,1000))
        self.widthTextBox.setAlignment(QtCore.Qt.AlignRight)

        topLayout.addWidget(self.arenasLabel, 1, 0)
        topLayout.addWidget(self.arenasTextBox, 1, 1)
        topLayout.addWidget(self.widthLabel, 1, 2)
        topLayout.addWidget(self.widthTextBox, 1, 3)

        # third row
        self.poisLabel = QtWidgets.QLabel("Number of POIs:")
        self.poisTextBox = QtWidgets.QLineEdit()
        self.poisTextBox.setText("0")
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
        self.imageLabel.setScaledContents(True)

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
        # convert to int
        x = int(x)
        y = int(y)
        return x, y
    
    # a function to draw the points on the image based on where the user clicks
    def draw_points(self, event):
        # redraw the image
        self.image = QtGui.QPixmap(self.backgroundTextBox.text())
        self.imageLabel.setPixmap(self.image)
        self.imageLabel.resize(self.image.size())
        self.imageLabel.show()

        # draw the labelled endpoints in red
        dot_size = int(0.01 * self.image.width())
        painter = QtGui.QPainter(self.image)

        painter.setPen(QtGui.QPen(QtCore.Qt.red, dot_size))
        for arena in self.labelled_endpoints:
            for endpoint in arena:
                painter.drawEllipse(endpoint[0], endpoint[1], dot_size, dot_size)

        # draw the arena numbers
        painter.setPen(QtGui.QPen(QtCore.Qt.red, 1))
        for i, arena in enumerate(self.labelled_endpoints):
            for j, endpoint in enumerate(arena):
                painter.drawText(endpoint[0]+dot_size, endpoint[1]-dot_size, f"{i+1}.{j+1}")

        # if there are two endpoints, join them with a line
        painter.setPen(QtGui.QPen(QtCore.Qt.red, dot_size//2))
        for arena in self.labelled_endpoints:
            if len(arena)==2:
                painter.drawLine(arena[0][0], arena[0][1], arena[1][0], arena[1][1])

        
        # draw the labelled pois in blue
        painter.setPen(QtGui.QPen(QtCore.Qt.blue, dot_size//2))
        for arena in self.labelled_pois:
            for poi in arena:
                painter.drawEllipse(poi[0], poi[1], dot_size//2, dot_size//2)

        # draw the poi numbers
        painter.setPen(QtGui.QPen(QtCore.Qt.blue, 1))
        for i, arena in enumerate(self.labelled_pois):
            for j, poi in enumerate(arena):
                painter.drawText(poi[0]+dot_size//2, poi[1]-dot_size//2, f"{i+1}.{j+1}")
        
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
                if len(self.labelled_endpoints)==0 or len(self.labelled_endpoints[-1])==2:
                    # add the first endpoint
                    self.labelled_endpoints.append([(x,y)])
                    self.draw_points(event)

                    # set the instructions
                    self.instructionsTextBox.setText("Click on the image to label the second endpoint of the arena. Right click to undo.")
                else:
                    # add the second endpoint
                    self.labelled_endpoints[-1].append((x,y))
                    self.draw_points(event)

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
            print("POI" if self.currently_labeling_poi else "Endpoint")

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
                    self.labelled_pois[-1].pop()
                    self.draw_points(event)
                    # set the instructions
                    self.instructionsTextBox.setText("Click on the image to label the next POI of the arena. Right click to undo.")
            else:
                if len(self.labelled_endpoints)==0 or len(self.labelled_endpoints[-1])==2:
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
                # get the endpoints
                x1, y1 = arena[0]
                x2, y2 = arena[1]
                # define the 4 corners of the rectangle using the width//2 perpendicular to the line joining the endpoints
                # get the slope of the line joining the endpoints
                slope = (y2-y1)/(x2-x1)
                # get the angle of the line joining the endpoints
                angle = np.arctan(slope)
                # get the perpendicular angle
                perp_angle = angle + np.pi/2
                # get the x and y offsets
                x_offset = self.arena_width//2 * np.cos(perp_angle)
                y_offset = self.arena_width//2 * np.sin(perp_angle)
                # get the 4 corners
                c1 = (int(x1+x_offset), int(y1+y_offset))
                c2 = (int(x1-x_offset), int(y1-y_offset))
                c3 = (int(x2-x_offset), int(y2-y_offset))
                c4 = (int(x2+x_offset), int(y2+y_offset))
                # create a path
                path = Path([c1, c2, c3, c4])
                # fill the path
                x, y = np.mgrid[:height, :width]
                points = np.transpose((x.ravel(), y.ravel()))
                grid = path.contains_points(points)
                grid = grid.reshape(x.shape)
                # add the grid to the masks
                masks[f"arena_{len(masks)+1}"] = grid
                # add the grid to the merged mask (red channel)
                merged[:,:,0] += grid.astype(np.uint8)*255

            # make the merged mask image
            merged = Image.fromarray(merged.transpose(1,0,2)) 
            # open the background image
            background = Image.open(self.backgroundTextBox.text())
            # overlay the merged mask on the background image
            merged.putalpha(128)
            background.paste(merged, (0,0), merged)

            # save the image as a temporary file
            background.save("temp.png")

            # show the merged mask to the user using the image label
            self.image = QtGui.QPixmap("temp.png")
            self.imageLabel.setPixmap(self.image)
            self.imageLabel.resize(self.image.size())
            self.imageLabel.show()

            # delete the temporary file
            os.remove("temp.png")

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

        # save the masks as a json file
        masks = {k: v.tolist() for k, v in masks.items()}
        with open(os.path.dirname(self.backgroundTextBox.text()) + "/masks.json", "w") as f:
            json.dump(masks, f)

        # design a linear transformation function that maps each rectangle to a standard square
        transforms = {}
        for arena in self.labelled_endpoints:
                # get the endpoints
                x1, y1 = arena[0]
                x2, y2 = arena[1]
                # define the 4 corners of the rectangle using the width//2 perpendicular to the line joining the endpoints
                # get the slope of the line joining the endpoints
                slope = (y2-y1)/(x2-x1)
                # get the angle of the line joining the endpoints
                angle = np.arctan(slope)
                # get the perpendicular angle
                perp_angle = angle + np.pi/2
                # get the x and y offsets
                x_offset = self.arena_width//2 * np.cos(perp_angle)
                y_offset = self.arena_width//2 * np.sin(perp_angle)
                # get the 4 corners
                c1 = (x1+x_offset, y1+y_offset)
                c2 = (x1-x_offset, y1-y_offset)
                c3 = (x2-x_offset, y2-y_offset)
                c4 = (x2+x_offset, y2+y_offset)
                # define the transformation function
                def transform(point):
                    # get the x and y coordinates
                    x, y = point
                    # transform to bring the first endpoint to (0,0)
                    x, y = x-x1, y-y1
                    # get length of the line joining the endpoints
                    length = np.sqrt((x2-x1)**2 + (y2-y1)**2)
                    # scale to bring the second endpoint to a radius of 1
                    x, y = x/length, y/length
                    # rotate by -angle to bring the second endpoint to (1,0)
                    x, y = x*np.cos(-angle) - y*np.sin(-angle), x*np.sin(-angle) + y*np.cos(-angle)
                    # # scale to bring the width to 1
                    x, y = x, y*length/self.arena_width
                    # return the transformed coordinates
                    return x, y
                
                # plot the two endpoints and the transformed corners
                for i,c in enumerate([arena[0],arena[1],c1, c2, c3, c4]):
                    plt.scatter(*transform(c), c=plt.cm.viridis(i/6), label=f"Point {i+1}")
                plt.gca().set_aspect('equal', adjustable='box')
                plt.legend()
                plt.show()

                # save the transformation function
                transforms[f"arena_{len(transforms)+1}"] = transform

                

        # make a poi dictionary
        pois = {}
        for i, arena in enumerate(self.labelled_pois):
            pois[f"arena_{i+1}_original"] = np.array(arena).tolist()
            pois[f"arena_{i+1}_transformed"] = [list(transforms[f"arena_{i+1}"](poi)) for poi in arena]
        
        # DEBUG: PLot the transformed pois
        for i, arena in enumerate(self.labelled_pois):
            for j,poi in enumerate(pois["arena_1_transformed"]):
                plt.scatter(poi[0], poi[1], c=plt.cm.viridis(j/len(pois[f"arena_{i+1}_transformed"])), label=f"POI {j+1}")
        plt.legend()
        plt.show()

        # save the pois as a json file
        with open(os.path.dirname(self.backgroundTextBox.text()) + "/pois.json", "w") as f:
            json.dump(pois, f)


        # set the instructions
        self.instructionsTextBox.setText("Click on Start Labeling to start again.")
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




        






        





