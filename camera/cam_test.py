#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import time
import cv2
import numpy as np
import click
import click_log
import logging
from imutils.video import VideoStream

logging.basicConfig(format='%(asctime)s %(message)s')

def nothing(x):
    pass


@click.command()
@click.option('--video', required=True, help='Video stream number', default=0, type=int)
@click_log.simple_verbosity_option(default='INFO')
def run(video):
    logging.info("Process started")

    vs = VideoStream(src=video).start()

    cv2.namedWindow("Trackbars")

    minHSV = np.array([165, 132, 98])
    maxHSV = np.array([195, 255,  255])

    cv2.createTrackbar("minH", "Trackbars", 0, 255, nothing)
    cv2.createTrackbar("minS", "Trackbars", 0, 255, nothing)
    cv2.createTrackbar("minV", "Trackbars", 0, 255, nothing)

    cv2.setTrackbarPos("minH", "Trackbars", minHSV[0])
    cv2.setTrackbarPos("minS", "Trackbars", minHSV[1])
    cv2.setTrackbarPos("minV", "Trackbars", minHSV[2])

    cv2.createTrackbar("maxH", "Trackbars", 0, 255, nothing)
    cv2.setTrackbarPos("maxH", "Trackbars", maxHSV[0])


    time.sleep(2.0)

    logging.info('Loop start')

    counter = 0

    while True:

        logging.info("Frame read")
        time.sleep(0.05)
        image = vs.read()

        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

        minH = cv2.getTrackbarPos("minH", "Trackbars")
        minS = cv2.getTrackbarPos("minS", "Trackbars")
        minV = cv2.getTrackbarPos("minV", "Trackbars")

        maxH = cv2.getTrackbarPos("maxH", "Trackbars")

        lowerLimit = np.uint8([minH, minS, minV])

        upperLimit = np.uint8([maxH, 255,  255])

        mask = cv2.inRange(hsv, lowerLimit, upperLimit)

        result = cv2.bitwise_and(image	, image	, mask=mask)

        cv2.imshow("frame", image)
        cv2.imshow("mask", mask)
        cv2.imshow("result", result)

        key = cv2.waitKey(1)

        if key == 27:
            break

    vs.stop()

    cv2.destroyAllWindows()


def main():
    run()
    # try:
    #     run()
    # except KeyboardInterrupt:
    #     pass
    # except Exception as e:
    #     logging.error(e)
    #     sys.exit(1)


if __name__ == '__main__':
    main()


