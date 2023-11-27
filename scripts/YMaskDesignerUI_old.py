import numpy as np
import sys

from matplotlib.path import Path
import matplotlib.pyplot as plt

from PyQt5 import QtCore, QtGui, QtWidgets


class MainWindow(QtWidgets.QMainWindow):
    """
    A class for the main window of the Mask Designer Application.

    Variables:
        image: The image to be labelled. (QPixmap)
        imageLabel: The label for the image. (QLabel)
        loaded_image: Whether or not an image has been loaded. (bool)
        started_labelling: Whether or not labelling has started. (bool)
        labelled_points: The points that have been labelled. (list)
        instructionsLabel: The label for the instructions. (QLabel)
        getBackgroundImageButton: The button to get the background image. (QPushButton)
        numYArenas: Edit Text for the number of Y-Arenas in the image. (QLineEdit)
        choiceBoundaryDistance: Edit Text for the distance between the choice boundary and the Y-Arena centre. (QLineEdit)
        startButton: The button to start labelling. (QPushButton)

    Methods:
        get_image: Get the image from the user and display it.
        start_labelling: Start labelling the Y-Arenas in the image.
        eventFilter: Mouse Click Event filter for the image label.
        get_pointer_position: Get the position of the mouse pointer in the image.
        draw_and_update_points: Draw the labelled points and update the image.
        create_mask_from_polygon: Create a mask from any polygon path.
        create_mask_from_keypoints: Create a mask from the keypoints for a single Y-Arena.
        create_mask_from_points: Create a mask from all the labelled points.
        plot_mask: Plot the mask.
        save_mask: Save the mask.
        show_tips: Show the tips for labelling.
    """

    def __init__(self, image_file=None, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)

        # set up the main layout
        layout = QtWidgets.QGridLayout()

        self.image_file = image_file

        # Add button to get background image
        self.getBackgroundImageButton = QtWidgets.QPushButton("Get Background Image")
        layout.addWidget(self.getBackgroundImageButton, 0, 0)
        self.getBackgroundImageButton.clicked.connect(self.get_image)

        # Add edit box for getting the number of Y-Arenas in the image
        layout.addWidget(QtWidgets.QLabel("Number of Y-Arenas"), 0, 1)
        self.numYArenas = QtWidgets.QLineEdit("16")
        self.numYArenas.setValidator(QtGui.QIntValidator(1, 100))
        layout.addWidget(self.numYArenas, 0, 2)

        # Add edit box for getting the choice boundary distance
        layout.addWidget(QtWidgets.QLabel("Choice Boundary Distance"), 0, 3)
        self.choiceBoundaryDistance = QtWidgets.QLineEdit("0.8")
        self.choiceBoundaryDistance.setValidator(QtGui.QDoubleValidator(0.0, 1.0, 1))
        layout.addWidget(self.choiceBoundaryDistance, 0, 4)

        # Add a labelling start button
        self.startButton = QtWidgets.QPushButton("Start Labelling")
        self.startButton.clicked.connect(self.start_labelling)
        layout.addWidget(self.startButton, 0, 5)

        # Add label for the background image
        self.imageLabel = QtWidgets.QLabel()
        layout.addWidget(self.imageLabel, 1, 0, 1, 6)
        self.imageLabel.setScaledContents(True)

        # Install event filter to catch mouse clicks
        self.imageLabel.installEventFilter(self)

        # Initialise the status variables
        self.loaded_image = False
        self.started_labelling = False
        self.labelled_points = []

        # Add a label for the instructions
        self.instructionsLabel = QtWidgets.QLabel('Load an image and click "Start Labelling" to begin labelling.')
        layout.addWidget(self.instructionsLabel, 2, 0, 1, 4)

        # Add a button to show the tutorial for labelling
        self.showTutorialButton = QtWidgets.QPushButton("Show Tutorial")
        self.showTutorialButton.clicked.connect(self.show_tutorial)
        layout.addWidget(self.showTutorialButton, 2, 4, 1, 2)

        # Create the main widget
        w = QtWidgets.QWidget()
        w.setLayout(layout)

        # Set the central widget
        self.setCentralWidget(w)

        # Set the window title
        self.setWindowTitle("Y-Arena Mask Designer")
        self.show()

    def get_image(self):
        """
        Get the image from the user.
        """
        # if an image file has been specified as an argument, ask the user if they want to use that image
        if self.image_file is not None:
            reply = QtWidgets.QMessageBox.question(
                self,
                "Use Image File",
                "Do you want to use the existing image file?",
                QtWidgets.QMessageBox.Yes,
                QtWidgets.QMessageBox.No,
            )
            if reply == QtWidgets.QMessageBox.No:
                self.image_file = QtWidgets.QFileDialog.getOpenFileName(self, "Open Background PNG File", ".", "*.png")
            else:
                self.image_file = [self.image_file]
        else:
            self.image_file = QtWidgets.QFileDialog.getOpenFileName(self, "Open Background PNG File", ".", "*.png")

        if self.image_file:
            self.image = QtGui.QPixmap(self.image_file[0])
            self.imageLabel.setPixmap(self.image)
            self.imageLabel.resize(self.image.size())
            self.imageLabel.show()
            self.loaded_image = True
        else:
            # give the user an error message
            self.instructionsLabel.setText('Please load an image and click "Start Labelling" to begin labelling.')
            self.loaded_image = False

    def start_labelling(self):
        """
        Start labelling the Y-Arenas.
        """
        if self.loaded_image:
            self.instructionsLabel.setText(
                "Right Click to add next Y-Arena keypoint and Left Click to remove the last one. (Click on Show Tutorial button for Keypoint identity)"
            )

            # disable all buttons and text boxes
            self.getBackgroundImageButton.setEnabled(False)
            self.numYArenas.setEnabled(False)
            self.startButton.setEnabled(False)
            self.choiceBoundaryDistance.setEnabled(False)
            self.started_labelling = True
        else:
            self.instructionsLabel.setText('First load an image and then click "Start Labelling" to begin labelling.')

    def get_pointer_position(self, event):
        """
        Get pixel coordinates of the mouse pointer.

        Variables:
            event: The mouse event. (QMouseEvent)
        """
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

    def draw_and_update_points(self):
        """
        Draw the points on the image and update the image label.
        """
        # redraw the image
        self.image = QtGui.QPixmap(self.image_file[0])
        self.imageLabel.setPixmap(self.image)
        self.imageLabel.resize(self.image.size())
        self.imageLabel.show()

        # draw the points on the image
        painter = QtGui.QPainter(self.image)
        painter.setPen(QtGui.QPen(QtCore.Qt.red, 2))
        for point in self.labelled_points:
            painter.drawEllipse(point[0], point[1], 2, 2)
        painter.end()

        # update the label
        self.imageLabel.setPixmap(self.image)
        self.imageLabel.resize(self.image.size())
        self.imageLabel.show()

    def eventFilter(self, source, event):
        """
        Event filter for the image label.

        Variables:
            source: The source of the event. (QObject)
            event: The event. (QEvent)
        """

        # check if the object is the image label with a pixmap and if the event is a left mouse click and if the labelling has started
        if (
            source == self.imageLabel
            and source.pixmap()
            and not source.pixmap().isNull()
            and event.type() == QtCore.QEvent.MouseButtonPress
            and event.button() == QtCore.Qt.LeftButton
            and self.started_labelling
        ):

            # get the position of the click
            x, y = self.get_pointer_position(event)
            self.labelled_points.append((x, y))

            if len(self.labelled_points) == int(self.numYArenas.text()) * 6:
                self.instructionsLabel.setText("Click anywhere on the image to finish labelling.")

            if len(self.labelled_points) == int(self.numYArenas.text()) * 6 + 1:
                self.instructionsLabel.setText("Processing and Saving...")
                # remove the last point
                self.labelled_points.pop()
                # start the processing
                self.create_mask_from_points()
                self.plot_masks_and_verify()
                if self.mask_correct:
                    self.save_mask()
                self.instructionsLabel.setText("Done!")
                self.started_labelling = False
                self.getBackgroundImageButton.setEnabled(True)
                self.numYArenas.setEnabled(True)
                self.startButton.setEnabled(True)
                self.choiceBoundaryDistance.setEnabled(True)
                self.labelled_points = []
                self.draw_and_update_points()

            # draw the points on the image
            self.draw_and_update_points()

        # check if the object is the image label with a pixmap and if the event is a right mouse click and if the labelling has started
        elif (
            source == self.imageLabel
            and source.pixmap()
            and not source.pixmap().isNull()
            and event.type() == QtCore.QEvent.MouseButtonPress
            and event.button() == QtCore.Qt.RightButton
            and self.started_labelling
        ):

            # remove the last point
            if len(self.labelled_points) >= 1:
                self.labelled_points.pop()

            # draw the points on the image
            self.draw_and_update_points()

        return super(MainWindow, self).eventFilter(source, event)

    def create_mask_from_polygon(self, polygon):
        """
        Create a mask from a polygon using numpy and matplotlib.

        Variables:
            polygon: The polygon to create the mask from. (list)
        """
        # get the size of the image
        width = self.image.width()
        height = self.image.height()

        # create a black meshgrid
        x, y = np.meshgrid(np.arange(width), np.arange(height))

        # flatten the meshgrid
        x = x.flatten()
        y = y.flatten()

        # get all the points in the grid
        points = np.vstack((x, y)).T

        # create path from the polygon
        path = Path(polygon)

        # create a mask from the path
        grid = path.contains_points(points)
        grid = grid.reshape((height, width))

        return grid

    def create_mask_from_keypoints(self, keypoints):
        """
        Create mask from the keypoints of each Y-Arena.

        Variables:
            keypoints: The keypoints of each Y-Arena. (list)
        """
        # convert the keypoints to a array
        keypoints = np.array(keypoints)

        # find the arena center
        arena_center = np.mean(keypoints[:3], axis=0)

        # find the arena arm widths
        arm1_width = np.linalg.norm(keypoints[2] - keypoints[0])
        arm2_width = np.linalg.norm(keypoints[0] - keypoints[1])
        arm3_width = np.linalg.norm(keypoints[1] - keypoints[2])

        # find the arena arm angles
        arm1_slope = np.arctan2(keypoints[2][1] - keypoints[0][1], keypoints[2][0] - keypoints[0][0])
        arm2_slope = np.arctan2(keypoints[0][1] - keypoints[1][1], keypoints[0][0] - keypoints[1][0])
        arm3_slope = np.arctan2(keypoints[1][1] - keypoints[2][1], keypoints[1][0] - keypoints[2][0])

        # find the positions of the arena arms
        arm1_end_1 = keypoints[3] - np.array([arm1_width / 2 * np.cos(arm1_slope), arm1_width / 2 * np.sin(arm1_slope)])
        arm1_end_2 = keypoints[3] + np.array([arm1_width / 2 * np.cos(arm1_slope), arm1_width / 2 * np.sin(arm1_slope)])
        arm2_end_1 = keypoints[4] - np.array([arm2_width / 2 * np.cos(arm2_slope), arm2_width / 2 * np.sin(arm2_slope)])
        arm2_end_2 = keypoints[4] + np.array([arm2_width / 2 * np.cos(arm2_slope), arm2_width / 2 * np.sin(arm2_slope)])
        arm3_end_1 = keypoints[5] - np.array([arm3_width / 2 * np.cos(arm3_slope), arm3_width / 2 * np.sin(arm3_slope)])
        arm3_end_2 = keypoints[5] + np.array([arm3_width / 2 * np.cos(arm3_slope), arm3_width / 2 * np.sin(arm3_slope)])

        # find the edges of the reward zones
        reward_distance = float(self.choiceBoundaryDistance.text())
        arm1_reward_edge_1 = (1 - reward_distance) * keypoints[2] + reward_distance * arm1_end_2
        arm1_reward_edge_2 = (1 - reward_distance) * keypoints[0] + reward_distance * arm1_end_1
        arm2_reward_edge_1 = (1 - reward_distance) * keypoints[0] + reward_distance * arm2_end_2
        arm2_reward_edge_2 = (1 - reward_distance) * keypoints[1] + reward_distance * arm2_end_1
        arm3_reward_edge_1 = (1 - reward_distance) * keypoints[1] + reward_distance * arm3_end_2
        arm3_reward_edge_2 = (1 - reward_distance) * keypoints[2] + reward_distance * arm3_end_1

        # define the boundaries of the arms of the arena
        arm1_points = np.array([keypoints[2], arena_center, keypoints[0], arm1_end_1, arm1_end_2])
        arm2_points = np.array([keypoints[0], arena_center, keypoints[1], arm2_end_1, arm2_end_2])
        arm3_points = np.array([keypoints[1], arena_center, keypoints[2], arm3_end_1, arm3_end_2])

        # define the boundaries of the reward zones of the arena
        arm1_reward_points = np.array([arm1_reward_edge_1, arm1_reward_edge_2, arm1_end_1, arm1_end_2])
        arm2_reward_points = np.array([arm2_reward_edge_1, arm2_reward_edge_2, arm2_end_1, arm2_end_2])
        arm3_reward_points = np.array([arm3_reward_edge_1, arm3_reward_edge_2, arm3_end_1, arm3_end_2])

        # create the masks for the arms of the arena
        arm_polygons = [arm1_points, arm2_points, arm3_points]
        arm_reward_polygons = [arm1_reward_points, arm2_reward_points, arm3_reward_points]
        arm_masks = [self.create_mask_from_polygon(poly) for poly in arm_polygons]
        arm_reward_masks = [self.create_mask_from_polygon(poly) for poly in arm_reward_polygons]
        return arm_masks, arm_reward_masks

    def create_mask_from_points(self):
        """
        Create a mask from the points.
        """
        self.arm_masks = []
        self.arm_reward_masks = []
        for i in range(len(self.labelled_points) // 6):
            # get the points of the Y-Arena and create the mask
            arm, reward = self.create_mask_from_keypoints(self.labelled_points[i * 6 : (i + 1) * 6])
            self.arm_masks += arm
            self.arm_reward_masks += reward

    def plot_masks_and_verify(self):
        """
        Plot the masks.
        """
        image = np.zeros_like(self.arm_masks[0])
        for i in range(1, len(self.arm_masks) + 1):
            image = image + (2 * i) * self.arm_masks[i - 1]
            image = image + (2 * i + 1) * self.arm_reward_masks[i - 1]
        # scale the image between 0 and 255
        image = (image - np.min(image)) / (np.max(image) - np.min(image)) * 255
        image = image.astype(np.uint8)

        # plot the image
        plt.imshow(image, cmap="gray")
        plt.show()

        # send an dialog to ask if the mask is correct
        reply = QtWidgets.QMessageBox.question(
            self,
            "Verify Mask",
            "Is the mask correct?",
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
            QtWidgets.QMessageBox.No,
        )
        if reply == QtWidgets.QMessageBox.Yes:
            self.mask_correct = True
        else:
            self.mask_correct = False

        self.combined_mask = np.int32(np.sum(self.arm_masks, axis=0) > 0)

    def save_mask(self):
        """
        Save the mask.
        """
        # Create dialog to save the mask
        file_name, _ = QtWidgets.QFileDialog.getSaveFileName(self, "Save Masks", ".", "*.npz")
        if file_name:
            # save the mask as a numpy array
            np.savez_compressed(
                file_name,
                arm_masks=self.arm_masks,
                arm_reward_masks=self.arm_reward_masks,
                arm_keypoints=np.array(self.labelled_points).reshape(-1, 6, 2),
                combined_mask=self.combined_mask,
                allow_pickle=True,
            )
        else:
            # show error message
            QtWidgets.QMessageBox.warning(self, "Error", "Please select a file to save the mask.")
            self.save_mask()

    def show_tutorial(self):
        """
        Show the tutorial in a new dialog.
        """
        # create a new dialog
        dialog = QtWidgets.QDialog()
        dialog.setWindowTitle("Tutorial")

        # draw image from file called marker_tutorial.png
        tutorial_image = QtGui.QPixmap("sixteeny/gui/resources/marker_tutorial.png")
        image_label = QtWidgets.QLabel()
        image_label.setPixmap(tutorial_image)
        image_label.setAlignment(QtCore.Qt.AlignCenter)

        # add the image to the dialog
        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(image_label)
        dialog.setLayout(layout)

        # show the dialog
        dialog.show()
        dialog.exec_()
        pass


if __name__ == "__main__":
    app = QtWidgets.QApplication([])
    if len(sys.argv) > 1:
        window = MainWindow(sys.argv[1])
    else:
        window = MainWindow()
    window.show()
    app.exec_()