"""Performs optical scan of a ballot."""

import numpy as np
import argparse
import cv2
import os
import re

BALLOT_WIDTH = 34
BALLOT_HEIGHT = 41
map_timing_marks = np.zeros([BALLOT_WIDTH, BALLOT_HEIGHT], dtype = object)
row_to_slope = np.zeros([BALLOT_HEIGHT], dtype = object)
COLUMN_TO_SLOPE = 0

###############################################################################
# REQUIRES: The section (either, "row", "left", or "right"), all the shapes
#           found on the image (contours), and the name of the ballot (img).
# MODIFIES: Nothing.
# EFFECTS:  Returns a list of the shapes in the specified section.
def get_list_of_section_shapes(section, contours, img):
    # grab shapes just in section ---------------------------------------------
    shapes_in_section = []

    for shape in contours:
        approx = cv2.approxPolyDP(shape,0.01*cv2.arcLength(shape,True),True)

        # only look for shapes bigger than 150 pixel area
        if cv2.contourArea(shape) > 150:
            out_of_range = False

            for vertex in shape:
                # check does not sink below certain y range
                if section == "row":
                    y_coord = vertex[0][1]

                    if (y_coord > 80):
                        out_of_range = True
                # check does not pass certain x range
                elif section == "left":
                    x_coord = vertex[0][0]

                    if (x_coord > 50):
                        out_of_range = True
                # check does not pass certain x range
                elif section == "right":
                    ballot_width = img.shape[1]
                    x_coord = vertex[0][0]

                    if (x_coord < ballot_width - 50):
                        out_of_range = True
                # check within range
                elif section == "bottom":
                    x_coord = vertex[0][0]
                    y_coord = vertex[0][1]

                    if (y_coord < 1530):
                        out_of_range = True
                    if (x_coord < 400 or x_coord > 800):
                        out_of_range = True

            # grab shapes that are in the section
            if not out_of_range:
                # draw different sections in different colors
                if section == "row":
                    cv2.drawContours(img,[shape],0,(0,0,255),-1) # red
                elif section == "left":
                    cv2.drawContours(img,[shape],0,(255,255,0),-1) # aqua
                elif section == "right":
                    cv2.drawContours(img,[shape],0,(0,255,255),-1) # yellow
                elif section == "bottom":
                    cv2.drawContours(img,[shape],0,(0,255,0),-1) # green

                # append to list of shapes
                shapes_in_section.append(shape)

    if (section == "row" and len(shapes_in_section) != 34):
        print("--------------------------------------------------------------")
        print("ERROR: Invalid ballot. Top row of timing marks is not 34.")
        print("--------------------------------------------------------------")
        exit(1)
    elif (section == "left" and len(shapes_in_section) != 41):
        print("--------------------------------------------------------------")
        print("ERROR: Invalid ballot. Left column of timing marks is not 41.")
        print("--------------------------------------------------------------")
        exit(1)
    elif (section == "bottom" and len(shapes_in_section) != 1):
        print("--------------------------------------------------------------")
        print("ERROR: Invalid ballot. Bottom row of timing marks is not 1.")
        print("--------------------------------------------------------------")
        exit(1)

    return shapes_in_section

###############################################################################
# REQUIRES: The section (either, "row", "left", or "right") and a list of the
#           shapes in the specified section.
# MODIFIES: The numpy 2D array map_timing_marks.
# EFFECTS:  Given the list of shapes from the specified section, finds the
#           center of mass in (x, y) pixels, and adds the center of mass to the
#           numpy 2D array map_timing_marks.
def populate_section(section, shapes_in_section):
    # populate map_timing_marks top row with center of masses -----------------
    center_of_masses_in_section = []

    for shape in shapes_in_section:
        # define average variables
        x_sum = 0
        y_sum = 0
        total_vertices = 0

        # sum x coordinates, y coordinates, and total vertices in each shape
        for vertex in shape:
            x_sum += vertex[0][0]
            y_sum += vertex[0][1]
            total_vertices += 1

        # calculate the center of mass (x, y) for each shape
        average_x = int(x_sum / total_vertices)
        average_y = int(y_sum / total_vertices)
        center_of_mass = (average_x, average_y)

        # add to list (will sort later)
        center_of_masses_in_section.append(center_of_mass)

    # sort center_of_masses_in_top_row by x value
    if section == "row":
        center_of_masses_in_section.sort()
    elif section == "left":
        center_of_masses_in_section.sort(key = lambda x: x[1])
    elif section == "right":
        center_of_masses_in_section.sort(key = lambda x: x[1])

    # add center of masses to the top row of map_timing_marks
    for i, x in enumerate(center_of_masses_in_section):
        global COLUMN_TO_SLOPE
        if section == "row":
            map_timing_marks[i][0] = x
        elif section == "left":
            map_timing_marks[0][i] = x
        elif section == "right":
            map_timing_marks[BALLOT_WIDTH - 1][i] = x
        elif section == "bottom":
            # coordinates of the bottom tick
            coord_bottom = x

            # coordinates of the top tick
            coord_top = map_timing_marks[17][0]

            # get slope
            if coord_top[0] == coord_bottom[0]:
                COLUMN_TO_SLOPE = 0
            else:
                slope = (coord_top[1] - coord_bottom[1]) / (coord_top[0] - coord_bottom[0])

                # add to data structure
                COLUMN_TO_SLOPE = slope

###############################################################################
# REQUIRES:
# MODIFIES: The numpy 2D array map_timing_marks.
def calculate_list_of_slopes():
    for i in range(BALLOT_HEIGHT):

        # if slope is valid
        if map_timing_marks[BALLOT_WIDTH - 1][i] != 0:
            # grab coordinates
            coord_left = map_timing_marks[0][i]
            coord_right = map_timing_marks[BALLOT_WIDTH - 1][i]

            # get slope
            slope = (coord_left[1] - coord_right[1]) / (coord_left[0] - coord_right[0])

            # add to data structure
            row_to_slope[i] = slope

###############################################################################
# REQUIRES:
# MODIFIES: Nothing.
# EFFECTS:  Returns a list of the shapes in the specified section.
def get_bubble(x_coord_bubble, y_coord_bubble, contours, img):
    for shape in contours:
        approx = cv2.approxPolyDP(shape,0.01*cv2.arcLength(shape,True),True)
        strikes = 0
        num_vertices = 0

        if cv2.contourArea(shape) > 200 and cv2.contourArea(shape) < 600:
            out_of_range = False

            for vertex in shape:
                num_vertices += 1

                # check within range
                x_coord = vertex[0][0]
                y_coord = vertex[0][1]

                if (abs(y_coord_bubble - y_coord) > 30):
                    out_of_range = True
                elif y_coord < 700:
                    out_of_range = True
                    break
                elif x_coord < 50 or x_coord > 1100:
                    out_of_range = True
                elif abs(x_coord_bubble - x_coord) > 80:
                    out_of_range = True

            # only allow small percent of strikes
            if strikes / num_vertices > 0.9:
                out_of_range = True

            # grab shapes that are in the section
            if not out_of_range:
                # draw different sections in different colors
                cv2.drawContours(img,[shape],0,(3,186,252),-1) # orange

                return True

    return False

###############################################################################
# REQUIRES:
# MODIFIES:
def grab_casted_vote(timing_mark_coordinates, output_file, contours, img):
    ofile = open(timing_mark_coordinates, "r")

    first_bubble = False
    second_bubble = False

    # loop through coordinates in timing mark file
    for i, line in enumerate(ofile):
        # grab timing mark coordinates from file
        coordinate = line.rstrip()  # strip new line
        coordinate = coordinate.strip("(")  # remove parenthesis
        coordinate = coordinate.strip(")")  # remove parenthesis
        coordinate = re.split(',', coordinate)  # split by comma
        x_coord = int(coordinate[0].strip())  # remove whitespace
        y_coord = int(coordinate[1].strip())  # remove whitespace

        # find pixel coordinates
        top_coord = map_timing_marks[x_coord][0]
        left_coord = map_timing_marks[0][y_coord]
        x_calibration = 0
        
        if COLUMN_TO_SLOPE == 0:
            x_calibration = 0
        else:
            x_calibration = (y_coord / BALLOT_HEIGHT) * (1600 / COLUMN_TO_SLOPE)
        y_calibration = x_coord * row_to_slope[y_coord]

        x_coord_bubble = top_coord[0] + x_calibration
        y_coord_bubble = left_coord[1] + y_calibration

        # debug comments
        # print("------------------------------------------------------------")
        # print("timing mark coordinates:", line, end='')
        # print("pixel coordinates: (" + str(x_coord_bubble) + ", " + str(y_coord_bubble) + ")")
        # print("x-slope:", row_to_slope[y_coord])
        # print("y-slope:", COLUMN_TO_SLOPE)


        # with coordinates, check if bubble filled in
        bubble = get_bubble(x_coord_bubble, y_coord_bubble, contours, img)
        # print("bubble:", bubble)
        # print("------------------------------------------------------------")

        # save bubble
        if (i + 1) % 2 != 0:  # odd
            first_bubble = bubble
        else:  # even
            second_bubble = bubble

            answer = check_bubbles(first_bubble, second_bubble)

            # append to output file
            ofile = open(output_file, "a+")  # append, create if does not exist
            ofile.write(answer + "\n")
            ofile.close()

###############################################################################
def check_bubbles(first_bubble, second_bubble):
    if first_bubble and not second_bubble:
        return "Yes"
    elif second_bubble and not first_bubble:
        return "No"
    elif not first_bubble and not second_bubble:
        return "Neither"
    else:
        return "Both"

###############################################################################
def main(args):
    assert os.path.isfile(args.input_file), "Input file does not exist"
    assert os.path.isfile(args.timing_mark_coordinates), "Timing mark file does not exist"
    # assert not os.path.isfile(args.output_file), "Output file already exists"

    # img = cv2.imread('shapes.png')
    # img = cv2.imread('shapes.jpg')
    img = cv2.imread(args.input_file)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    ret,thresh = cv2.threshold(gray,150,255,1)
    contours,h = cv2.findContours(thresh,1,2)

    # populate map_timing_marks ...............................................

    # populate the top row of map_timing_marks -> (0, 0) to (34, 0)
    shapes_top = get_list_of_section_shapes("row", contours, img)
    populate_section("row", shapes_top)

    # populate the left column of map_timing_marks -> (0, 0) to (0, 41)
    shapes_left = get_list_of_section_shapes("left", contours, img)
    populate_section("left", shapes_left)

    # populate the right column of map_timing_marks -> (34, 0) to (34, 41)
    shapes_right = get_list_of_section_shapes("right", contours, img)
    populate_section("right", shapes_right)

    # calculate list of slopes ................................................

    # get left to right tilt
    calculate_list_of_slopes()

    # get top to bottom tilt
    shapes_bottom = get_list_of_section_shapes("bottom", contours, img)
    populate_section("bottom", shapes_bottom)

    # check where vote was cast ...............................................

    # reset output file
    file = open(args.output_file, "w+")
    file.close()

    grab_casted_vote(args.timing_mark_coordinates, args.output_file, contours, img)

    # show ballot timing marks ................................................
    cv2.imshow('img',img)
    cv2.waitKey(0)
    cv2.destroyAllWindows()

###############################################################################
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Scanner parser")
    parser.add_argument('input_file', type=str, help="File to scan")
    parser.add_argument('timing_mark_coordinates', type=str, help="Timing mark coordinates")
    parser.add_argument('output_file', type=str, help="File to output results")
    main(parser.parse_args())
