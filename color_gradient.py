from PIL import Image, ImageDraw
import numpy

def hex_to_rgb(hex_color):
    hex_color = hex_color.lstrip("#")
    return numpy.array(list(int(hex_color[i:i + 2], 16) for i in (0, 2, 4)))

def show_hex_colors(color1, color2, N=300):
    img_width = 1000
    img_height = 100
    img = Image.new('RGB', (img_width, img_height), color='white')
    draw = ImageDraw.Draw(img)

    rect_width = img_width // N
    rect_height = img_height

    c1 = hex_to_rgb(color1)
    c2 = hex_to_rgb(color2)

    for i in range(N):
        rect_x1 = i * rect_width
        rect_y1 = 0
        rect_x2 = rect_x1 + rect_width
        rect_y2 = rect_height
        position = [rect_x1, rect_y1, rect_x2, rect_y2]

        alpha = i/(N-1)
        color = "#{:02x}{:02x}{:02x}".format(
                *list((c1 * (1 - alpha) + c2* alpha).astype("int"))
        )
        draw.rectangle(position, fill=color)

    img.show()

show_hex_colors("#0000ff", "#ff0000", N=200)

