import numpy as np
import cv2

BALLOT_WIDTH = 34
BALLOT_HEIGHT = 41
map_timing_marks = np.zeros([BALLOT_WIDTH, BALLOT_HEIGHT], dtype = object)
row_to_slope = np.zeros([BALLOT_HEIGHT], dtype = object)

###############################################################################
def PolyArea(x,y):
    return 0.5*np.abs(np.dot(x,np.roll(y,1))-np.dot(y,np.roll(x,1)))

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

            # grab shapes that are in the section
            if not out_of_range:
                # draw different sections in different colors
                if section == "row":
                    cv2.drawContours(img,[shape],0,(0,0,255),-1) # red
                elif section == "left":
                    cv2.drawContours(img,[shape],0,(255,255,0),-1) # aqua
                elif section == "right":
                    cv2.drawContours(img,[shape],0,(0,255,255),-1) # yellow

                # append to list of shapes
                shapes_in_section.append(shape)

    if (section == "row" and len(shapes_in_section) != 34) or \
       (section == "left" and len(shapes_in_section) != 41):
        print("--------------------------------------------------------------")
        print("ERROR: Invalid ballot. Top row of timing marks is not 34.")
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
        if section == "row":
            map_timing_marks[i][0] = x
        elif section == "left":
            map_timing_marks[0][i] = x
        elif section == "right":
            map_timing_marks[BALLOT_WIDTH - 1][i] = x


###############################################################################
# REQUIRES: The section (either, "row", "left", or "right") and a list of the
#           shapes in the specified section.
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
def main():
    # img = cv2.imread('shapes.png')
    # img = cv2.imread('shapes.jpg')
    img = cv2.imread('000002.jpg')
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
    calculate_list_of_slopes()

    # populate map_timing_marks for where bubbles are .........................

    ###########################################################################
    ###########################################################################
    ###########################################################################
    # below is testing junk

    # for cnt in contours:
        # approx = cv2.approxPolyDP(cnt,0.01*cv2.arcLength(cnt,True),True)

        # if len(approx) == 4:
        #     print ("\n\napprox len: ", len(approx))
        #     print ("approx    : ", approx)
        #     print("approx shape:", approx.shape)
        #     a = np.reshape(approx, (2, approx.shape[0]))
        #     print(a)
        #     print("area: ", PolyArea(a[0], a[1]))

            # print ("square")
            # cv2.drawContours(img,[cnt],0,(0,0,255),-1) # red
        # print("contour area:", cv2.contourArea(cnt))
        # print("sides:", len(approx))

        # if cv2.contourArea(cnt) > 150:
        #     x_coord = cnt[0][0][0]
        #     y_coord = cnt[0][0][1]

        #     # only draw a shape if it is at the top of the ballot
        #     if (y_coord < 80):
        #         cv2.drawContours(img,[cnt],0,(0,0,255),-1) # red

        # if cv2.contourArea(cnt) > 150:
        #     if len(approx) == 5:
        #         print ("pentagon")
        #         cv2.drawContours(img,[cnt],0,255,-1) # blue
        #     elif len(approx) == 2:
        #         cv2.drawContours(img,[cnt],0,(255,0,255),-1) # dark pink
        #     elif len(approx) == 3:
        #         print ("triangle")
        #         cv2.drawContours(img,[cnt],0,(0,255,0),-1) # green
        #     elif len(approx) == 4:
        #         print ("square")
        #         cv2.drawContours(img,[cnt],0,(0,0,255),-1) # red
        #     elif len(approx) == 6:
        #         cv2.drawContours(img,[cnt],0,(102,0,102),-1) # purple
        #     elif len(approx) == 7:
        #         cv2.drawContours(img,[cnt],0,(120,120,120),-1)
        #     elif len(approx) == 8:
        #         cv2.drawContours(img,[cnt],0,(160,160,160),-1)
        #     elif len(approx) == 9:
        #         print ("half-circle")
        #         cv2.drawContours(img,[cnt],0,(255,255,0),-1) # aqua
        #     elif len(approx) > 15:
        #         print ("circle")
        #         cv2.drawContours(img,[cnt],0,(0,255,255),-1) # yellow
        #     else:
        #         print ("other shape")
        #         cv2.drawContours(img,[cnt],0,(203,192,255),-1) # pink

    cv2.imshow('img',img)
    cv2.waitKey(0)
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
