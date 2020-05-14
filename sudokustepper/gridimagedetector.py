# -*- coding: utf-8 -*-

import cv2
import numpy as np
from sudokustepper.grid import Grid
import pytesseract

USE_CAMERA: bool = False
IMG_PATH = "../ocr_test_images/2.jpg"
TESSERACT_CONFIG = r"--oem 1 --psm 10 -l eng outputbase digits"


def downsample_square(img, new_dimension: int):
    h = img.shape[0]
    w = img.shape[1]

    x = 0
    y = 0
    new_width = w
    new_height = h
    if w < h:
        # Image is portrait - crop evenly from top/bottom
        y = (h - w) // 2
        new_height = w
    elif w > h:
        # Image is landscape - crop evenly from left/right
        x = (w - h) // 2
        new_width = h

    cropped = img[y:y + new_height, x:x + new_width]
    resized = cv2.resize(cropped, (new_dimension, new_dimension))

    return resized


def threshold(img):
    # Smoothing
    smoothed = cv2.GaussianBlur(img, (3, 3), 0)
    # Adaptive threshold
    thresh = cv2.adaptiveThreshold(smoothed, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 5, 6)
    # Invert to white-on-black
    thresh_inv = cv2.bitwise_not(thresh)

    return thresh_inv


def find_crop_grid(img, crop_dimension: int):
    # Dilate slightly to enhance the edges
    kernel = np.ones((3, 3), dtype=np.uint8)
    dilated = cv2.dilate(img, kernel, iterations=1)

    contours, hierarchy = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if len(contours) == 0:
        return None

    contours = sorted(contours, key=cv2.contourArea, reverse=True)
    # TODO: filter through contours to find the squarest one
    largest_contour = contours[0]

    # Mask out anything outside the grid (in case minAreaRect is not very accurate)
    mask = np.zeros(img.shape, img.dtype)
    mask = cv2.drawContours(mask, [largest_contour], 0, 255, cv2.FILLED)
    masked = cv2.copyTo(img, mask)

    # Find the approximate polygon to match the contour
    epsilon = 10
    poly = cv2.approxPolyDP(largest_contour, epsilon, True)
    if len(poly) != 4:
        return None

    # TODO check if any of the points are duplicated

    # Sort the points - split by y-value, then sort each group by x-value
    sorted_by_y = sorted(poly, key=lambda p: p[0][1])
    top_points = sorted_by_y[:2]
    bottom_points = sorted_by_y[2:]
    top_points.sort(key=lambda p: p[0][0])
    bottom_points.sort(key=lambda p: p[0][0])

    top_left = top_points[0]
    top_right = top_points[1]
    bottom_left = bottom_points[0]
    bottom_right = bottom_points[1]

    # Allow for a slight "bulge" in the sides of the corrected image, caused by non-flat paper
    # This allows attempts to preserve the outermost border for the benefit of the cell finder
    warp_border = 5
    max_dim = crop_dimension - warp_border - 1

    # Arrange the points in clockwise order, starting closest to the origin (top-left)
    src_points = np.array([top_left, top_right, bottom_right, bottom_left], dtype=np.float32)
    dst_points = np.array([
        [warp_border, warp_border],
        [max_dim, warp_border],
        [max_dim, max_dim],
        [warp_border, max_dim]
    ], dtype=np.float32)

    mat = cv2.getPerspectiveTransform(src_points, dst_points)
    corrected = cv2.warpPerspective(
        masked,
        mat,
        (crop_dimension, crop_dimension),
        flags=cv2.INTER_LINEAR,
        borderMode=cv2.BORDER_CONSTANT,
        borderValue=0
    )

    return corrected


def split_grid_cells(img):
    # Dilate slightly to enhance the edges
    kernel = np.ones((3, 3), dtype=np.uint8)
    dilated = cv2.dilate(img, kernel, iterations=1)

    contours, hierarchy = cv2.findContours(dilated, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

    rects = []
    for contour in contours:
        rect = cv2.boundingRect(contour)
        x, y, w, h = rect

        # Each rect should be (roughly) square.
        aspect_epsilon = 0.3
        aspect = w / h
        if abs(1 - aspect) > aspect_epsilon:    # note: 1 denotes a square aspect
            continue

        # Each rect should have a pixel area of roughly (image_area / 81)
        # TODO maybe we can shift these epsilon values until len(rects) becomes 81
        area_epsilon = 1000
        expected_area = img.size // 81  # number of pixels
        rect_area = w * h
        if abs(expected_area - rect_area) > area_epsilon:
            continue

        # Shrink the rect ever so slightly, to remove any border
        shrink_border = 5
        x = x + shrink_border
        y = y + shrink_border
        w = w - shrink_border * 2
        h = h - shrink_border * 2

        # img = cv2.rectangle(img, (x, y), (x + w, y + h), 180, 2)
        rects.append((x, y, w, h))

    # We expect to see 81 grid cells
    if len(rects) != 81:
        return None

    # Sort the rects by y-position
    rects.sort(key=lambda r: r[1])
    # Sort each sub-group of 9 by x-position
    for i in range(0, len(rects), 9):
        rects[i:i + 9] = sorted(rects[i:i + 9], key=lambda r: r[0])

    # Finally, split the grid image up into 81 individual rectangles
    cell_imgs = []
    for rect in rects:
        x, y, w, h = rect
        cell_imgs.append(img[y:y + h, x:x + w])

    return cell_imgs


def parse_single_cell(img):
    img = cv2.resize(img, (20, 20), cv2.INTER_CUBIC)
    img = 255 - img

    ret = pytesseract.image_to_string(img, config=TESSERACT_CONFIG)
    if ret is None or not ret.isdigit():
        return "0"

    return ret


def main():
    capture = None
    if USE_CAMERA:
        capture = cv2.VideoCapture(0)

    finish = False
    while not finish:
        if USE_CAMERA:
            _, frame = capture.read()
        else:
            frame = cv2.imread(IMG_PATH)

        if frame is None:
            print("Could not load image file")
            return

        frame = downsample_square(frame, 512)

        # Start processing the image
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        thresh = threshold(gray)

        grid_img = find_crop_grid(thresh, 333)
        if grid_img is None:
            continue

        cell_imgs = split_grid_cells(grid_img)
        if cell_imgs is None:
            continue

        print("Found grid. Performing OCR...")

        grid_str = []
        for cell in cell_imgs:
            c = parse_single_cell(cell)
            grid_str.append(c)

        assert len(grid_str) == 81

        grid_str = "".join(grid_str)
        print(grid_str)

        g = Grid(grid_str)
        print(g)
        print("Grid is VALID" if g.valid else "Grid is INVALID")

        if USE_CAMERA:
            if cv2.waitKey(1) & 0xFF == ord('q'):
                finish = True
        else:
            finish = True

    if USE_CAMERA:
        capture.release()

    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
