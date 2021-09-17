from PIL import Image


def preprocess(image: Image) -> Image:
    return crop(image, x=7874, y=644, width=224, height=224)


def brand(image: Image, *, brand: Image) -> Image:
    return __apply_brand(
        crop(image, x=7036, y=162, width=1920, height=1080),
        brand=brand)


def crop(image: Image, *, x: int, y: int, width: int, height: int) -> Image:
    return image.crop((x, y, x + width, y + height))


def __apply_brand(image: Image, *, brand: Image) -> Image:
    branded = image.copy()
    branded.paste(brand, (0, 0), brand)
    return branded
