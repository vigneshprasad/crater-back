import base64
import tempfile

from PIL import Image


def get_temporary_image(temp_file):
    size = (200, 200)
    color = (255, 0, 0, 0)
    image = Image.new("RGBA", size, color)
    image = image.convert("RGB")
    image.save(temp_file, 'jpeg')
    return temp_file


def get_test_image():
    temp_file = tempfile.NamedTemporaryFile()
    return get_temporary_image(temp_file)


def get_test_base64_image():
    temp_file = tempfile.NamedTemporaryFile()
    test_image = get_temporary_image(temp_file)
    with open(test_image.name, "rb") as image_file:
        encoded_string = base64.b64encode(image_file.read())
    return f'data:image/png;base64,{encoded_string.decode("utf-8")}'
