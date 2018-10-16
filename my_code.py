from PIL import Image, ImageDraw
from random import choice

import os
import sys
import logging
import argparse
from datetime import datetime

EMPTY_PICTURE_NAME = "space"
SHAPE_FILENAME = "shape.jpg"
IMAGE_FILENAME = "image.jpg"
FOLDERS = ["NoisyImg", "UnnoisyImg", "DetectedImg", "DetectedNoisyImg", "LatticeImg", "UnlaticeImg", "DetectedLaticeImg"]

WHITE_COLOR = 255
LATICE_COLOR = 155#200
BLACK_COLOR = 0

P = [0.1, 0.2, 0.3, 0.4]

logging.basicConfig()
logger = logging.getLogger('RecognitionApp')
logger.setLevel(logging.INFO)

class Images:
    def __init__(self, pictures_number):
        self._images = list()
        self._name = "Test!.jpg"
        self._pictures_number = pictures_number

    def _copy_img(self, images, lattice=False):
        if not lattice:
            self._images = list()
            if type(images) is list:
                for image in images:
                    self._images.append(image.copy())
            else:
                for p in P:
                    self._images.append(images.copy())
        else:
            self._images.append(images.copy())

    def get_images(self):
        return self._images

    def save_images(self, path):
        for image in (self._images):
            index = self._images.index(image)
            im_path = os.path.join(path, self._name.replace('!', str(P[index])))
            image.save(im_path)

    def close_images(self):
        for image in self._images:
            image.close()

class InputImages(Images):
    def __init__(self, path, pictures_number):
        super().__init__(pictures_number)
        self._shapes = list()
        self._symbol_path = path
        self._image = None

    def __normalize_image(self, image):
        if image.width != image.height:
            logger.error("{} Images are incorrect in folder {}".format(datetime.now(), self._symbol_path))
            sys.exit(-1)
        normalize_image = Image.new('L', image.size)
        bb_box = (0, 0, image.width, image.height)
        normalize_image.paste(image, bb_box)
        return normalize_image

    def __set_images(self):
        if not os.path.exists(self._symbol_path):
            logger.error("{} Path {} is not exist".format(datetime.now(), self._symbol_path))
            sys.exit(-1)
        files = list(files for root, dirs, files in os.walk(self._symbol_path)).pop()
        if files is list():
            logger.error("{} Folder {} is empty".format(datetime.now(), self._symbol_path))
            sys.exit(-1)
        for file in list(os.path.join(self._symbol_path, file) for file in files):
            logger.info("{} File {} is processing".format(datetime.now(), file))
            im = self.__normalize_image(Image.open(file))
            self._images.append(im)
            if EMPTY_PICTURE_NAME in file:
                continue
            self._shapes.append(im)
        logger.info("{} Characters reading is complete".format(datetime.now()))

    def __generate_image(self):
        self.__set_images()

        im_size = self._images[0].height
        out_im_size = im_size * self._pictures_number
        self._image = Image.new('L', (out_im_size, out_im_size))

        im_range = range(0, self._pictures_number)
        for horizontal_number in im_range:
            for vertical_number in im_range:
                bb_box = (horizontal_number * im_size,
                          vertical_number * im_size,
                          (horizontal_number + 1) * im_size,
                          (vertical_number + 1) * im_size)
                self._image.paste(choice(self._images), bb_box)
        logger.info("{} Image has generated".format(datetime.now()))

    def get_generated_image(self):
        self.__generate_image()
        return self._image

    def get_shape(self, path):
        shape = choice(self._shapes)
        shape_path = os.path.join(path, SHAPE_FILENAME)
        shape.save(shape_path)
        return shape

    def close_images(self, shape):
        for image in self._images:
            if image != shape:
                image.close()
        logger.info("{} Images with symbols has closed".format(datetime.now()))

    def save_and_close_generated_image(self, path):
        save_path = os.path.join(path, IMAGE_FILENAME)
        self._image.save(save_path)
        self._image.close()
        logger.info("{} Image have closed".format(datetime.now()))

class NoisyImages(Images):
    def __init__(self, picture_number):
        super().__init__(picture_number)

    def __get_pixels_dict(self, im_size, pixels):
        pixels_size = range(0, im_size)
        pixels_dict = {'w': list(), 'b': list()}
        board = round(WHITE_COLOR/2)
        for x in pixels_size:
            for y in pixels_size:
                pixels_dict['w'].append((x, y)) if pixels[x, y] < board else pixels_dict['b'].append((x, y))
        return pixels_dict

    def corrupt_images(self, image):
        self._copy_img(image)
        self._name = "Noisy!.jpg"
        for image in self._images:
            logger.info("{} Image {} is started to corrupt". format(datetime.now(), self._images.index(image)))
            pixels = image.load()
            im_size = image.width
            pixels_dict = self.__get_pixels_dict(im_size, pixels)

            for color in pixels_dict:
                index = self._images.index(image)
                number = round(P[index] * len(pixels_dict[color]))
                color_pixels = pixels_dict[color]
                for i in range(0, number):
                    x, y = choice(color_pixels)
                    pixels[x, y] = WHITE_COLOR - pixels[x, y]
                    color_pixels.remove((x, y))
            logger.info("{} Image {} is complite to corrupt".format(datetime.now(), self._images.index(image)))

class UnnoisyImages(Images):
    def __init__(self, picture_number):
        super().__init__(picture_number)

    def __median_filter(self, im_size, pixels):
        board = (WHITE_COLOR + BLACK_COLOR) / 2
        size_range = range(1, im_size - 1)
        for x in size_range:
            for y in size_range:
                median = 0
                for i in range(x-1, x+2):
                    for j in range(y-1, y+2):
                        median += pixels[i, j]
                median /= 9
                pixels[x, y] = BLACK_COLOR if median < board else WHITE_COLOR

    def unnoise_images(self, images):
        super()._copy_img(images)
        self._name = "UnnoisyImg!.jpg"
        for image in self._images:
            logger.info("{} Image {} is started to unnoise".format(datetime.now(), self._images.index(image)))
            self.__median_filter(image.width, image.load())
            logger.info("{} Image {} is complite to unnoise".format(datetime.now(), self._images.index(image)))

class LaticeImages(Images):
    def __init__(self, image, step, width, pictures_number=0):
        super().__init__(pictures_number)
        self._copy_img(image, True)
        self._name = "LatticeImg.jpg"
        self._step = step
        self._width = width

    def __generate_lattice(self):
        step_lattice = 0
        width_lattice = 0
        lattice_range = list()
        pixels_range = range(0, self._images[0].width)
        for item in pixels_range:
            step_lattice = step_lattice + 1 if (step_lattice < self._step and width_lattice == 0) else 0
            width_lattice = width_lattice + 1 if (width_lattice < self._width and step_lattice == 0) else 0
            if width_lattice != 0:
                lattice_range.append(item)
        return lattice_range

    def create_lattice(self):
        logger.info("{} Lattice generation (width = {}, step = {})is started".format(datetime.now(),
                                                                                     self._width,
                                                                                     self._step))
        pixels = self._images[0].load()
        pixels_range = range(0, self._images[0].width)
        lattice_range = self.__generate_lattice()
        for x in lattice_range:
            for y in pixels_range:
                pixels[x, y] = LATICE_COLOR
        for y in lattice_range:
            for x in pixels_range:
                pixels[x, y] = LATICE_COLOR
        logger.info("{} Lattice generation is started".format(datetime.now()))


class RemoveLaticeImages(Images):
    def __init__(self, image, picture_number):
        super().__init__(picture_number)
        self._copy_img(image, True)
        self._name = "RemoveLaticeImg.jpg"
        self._width = 0
        self._step = 0
        self._letice_range = None

    def __find_lattice(self):
        pixels = self._images[0].load()
        white_pixels = 0
        black_pixels = 0
        for item in range(0, self._images[0].height):
            if pixels[0, item] == WHITE_COLOR and black_pixels != 0:
                self._width = black_pixels
                self._step = white_pixels
                return
            if pixels[0, item] == WHITE_COLOR:
                white_pixels += 1
            else:
                black_pixels += 1

    def __generate_lattice(self):
        self.__find_lattice()
        step_lattice = 0
        width_lattice = 0
        lattice_range = list()
        pixels_range = range(0, self._images[0].width)
        for item in pixels_range:
            step_lattice = step_lattice + 1 if (step_lattice < self._step and width_lattice == 0) else 0
            width_lattice = width_lattice + 1 if (width_lattice < self._width and step_lattice == 0) else 0
            if width_lattice != 0:
                lattice_range.append(item)
        self._letice_range = lattice_range

    def __clear_image(self):
        pixels = self._images[0].load()
        pixels_range = range(0, self._images[0].width)
        for x in self._letice_range:
            for y in pixels_range:
                pixels[x, y] = BLACK_COLOR
        for y in self._letice_range:
            for x in pixels_range:
                pixels[x, y] = BLACK_COLOR

    def remove_lattice(self):
        logger.info("{} Lattice removing (width = {}, step = {})is started".format(datetime.now(),
                                                                                     self._width,
                                                                                     self._step))
        self.__generate_lattice()
        self.__clear_image()
        logger.info("{} Lattice generation is started".format(datetime.now()))

    # def coefficient(self, shape):
    #     shape_pixels = shape.load()
    #     size_range = range(0, shape.width)
    #     black_corrupted_pixels = 0
    #     black_pixels = 0
    #     repeat_pixels = 0
    #     for x in size_range:
    #         for y in size_range:
    #             if shape_pixels[x, y] == BLACK_COLOR:
    #                 black_pixels += 1
    #                 if x in self._letice_range or y in self._letice_range:
    #                     black_corrupted_pixels += 1
    #                     if x in self._letice_range and y in self._letice_range:
    #                         repeat_pixels += 1
    #     black_corrupted_pixels -= repeat_pixels / 2
    #     return black_corrupted_pixels / black_pixels


        #
        # part_im_size = int(self._images[0].width / self._pictures_number)
        # width, step = self.__find_lattice()
        # straight_count = width + step
        # count = round(part_im_size / straight_count, 0)
        # square_lattice = width * part_im_size * count * 2 - width**2 * count**2
        # return square_lattice / part_im_size**2

class Detection(Images):
    def __init__(self, picture_number):
        super().__init__(picture_number)

    def __process_shapes(self, shape, image_part):
        image_part_pixels = image_part.load()
        shape_pixels = shape.load()
        size_range = range(0, image_part.width)
        black_pixels_count = 0
        black_shape_pixels = 0
        for x in size_range:
            for y in size_range:
                if shape_pixels[x, y] == BLACK_COLOR:
                    black_shape_pixels += 1
                    if image_part_pixels[x, y] == BLACK_COLOR:
                        black_pixels_count += 1
        k = black_pixels_count / black_shape_pixels
        return k

    def __find_shapes(self, images, shape, coeficient=None):
        picture_range = range(0, self._pictures_number)
        im_size = int(self._images[0].width / self._pictures_number)
        for image in images:
            logger.info("{} Image {} is started detection".format(datetime.now(), images.index(image)))
            index = images.index(image)
            p = 1 - P[index] if coeficient is None else 1 - coeficient
            for horizontal in picture_range:
                for vertical in picture_range:
                    top = horizontal * im_size
                    bottom = top + im_size
                    left = vertical * im_size
                    right = left + im_size
                    bounding_box = (left, top, right, bottom)
                    image_part = image.crop(bounding_box)
                    k = self.__process_shapes(shape, image_part)
                    if k >= p:
                        im = self._images[index]
                        ImageDraw.ImageDraw(im).rectangle(bounding_box, fill=None, outline=0)
            logger.info("{} Image {} is complite detection".format(datetime.now(), images.index(image)))


    def process_unnoisy_images(self, unnoized_images, corrupted_images, shape, coeficient=None):
        self._copy_img(corrupted_images)
        self._name = "DetectedImg!.jpg"
        logger.info("{} Unnoisy images is started detection".format(datetime.now()))
        self.__find_shapes(unnoized_images, shape)
        if coeficient is None:
            self.__find_shapes(unnoized_images, shape)
        else:
            self.__find_shapes(unnoized_images, shape, coeficient)
        logger.info("{} Unnoisy images is complited detection".format(datetime.now()))

    def process_noisy_images(self, corrupted_images, shape):
        self._copy_img(corrupted_images)
        self._name = "DetectedNoisyImg!.jpg"
        logger.info("{} Noisy images is started detection".format(datetime.now()))
        self.__find_shapes(self._images, shape)
        logger.info("{} Noisy images is complited detection".format(datetime.now()))

class Execution():
    def __init__(self):
        pass

    def __create_parser(self):
        parser = argparse.ArgumentParser()
        parser.add_argument('-p', '--path', type=str, help='Path to folder with images')
        parser.add_argument('-n', '--number', type=int, help='Number pictures in picture')
        parser.add_argument('-w', '--width', type=int, help="Width lattice")
        parser.add_argument('-s', '--step', type=int, help="Step lattice")
        return parser.parse_args()

    def __mkdir(self, path):
        dirs = dict()
        save_path = os.path.abspath(os.path.join(path, '..'))
        for folder in FOLDERS:
            folder_path = os.path.join(save_path, folder)
            if os.path.exists(folder_path):
                import shutil
                shutil.rmtree(folder_path)
            os.mkdir(folder_path)
            dirs.update({folder: folder_path})
        return dirs

    def main(self):
        arg_parser = self.__create_parser()
        dirs_img = self.__mkdir(arg_parser.path)
        input_images = InputImages(arg_parser.path, arg_parser.number)
        image = input_images.get_generated_image()

        noisy_images = NoisyImages(arg_parser.number)
        noisy_images.corrupt_images(image)

        unnoisy_images = UnnoisyImages(arg_parser.number)
        unnoisy_images.unnoise_images(noisy_images.get_images())

        shape = input_images.get_shape(os.path.join(arg_parser.path, '..'))

        detection = Detection(arg_parser.number)

        detection.process_unnoisy_images(unnoisy_images.get_images(), noisy_images.get_images(), shape)
        detection.save_images(dirs_img['DetectedImg'])
        detection.close_images()

        detection.process_noisy_images(noisy_images.get_images(), shape)
        detection.save_images(dirs_img['DetectedNoisyImg'])
        detection.close_images()

        lattice_image = LaticeImages(image, arg_parser.step, arg_parser.width)
        lattice_image.create_lattice()

        lattice_image.save_images(dirs_img['LatticeImg'])

        unlatice_image = RemoveLaticeImages(lattice_image.get_images()[0], arg_parser.number)
        unlatice_image.remove_lattice()

        detection_lattice = Detection(arg_parser.number)

        detection_lattice.process_unnoisy_images(unlatice_image.get_images(), lattice_image.get_images(), shape, 0)
        detection_lattice.save_images(dirs_img['DetectedLaticeImg'])
        detection_lattice.close_images()

        lattice_image.save_images(dirs_img['LatticeImg'])
        lattice_image.close_images()

        unlatice_image.save_images(dirs_img['UnlaticeImg'])
        unlatice_image.close_images()

        input_images.close_images(shape)
        input_images.save_and_close_generated_image(os.path.join(arg_parser.path, '..'))

        noisy_images.save_images(dirs_img['NoisyImg'])
        noisy_images.close_images()

        unnoisy_images.save_images(dirs_img['UnnoisyImg'])
        unnoisy_images.close_images()

if __name__ == "__main__":
    execution = Execution()
    execution.main()