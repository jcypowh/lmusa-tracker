def hex_to_rgb(hex_color):
    hex_color = (hex_color or "#4f46e5").lstrip("#")
    if len(hex_color) == 3:
        hex_color = "".join(c * 2 for c in hex_color)
    return tuple(int(hex_color[i:i + 2], 16) for i in (0, 2, 4))


def rgb_to_hex(rgb):
    return "#%02x%02x%02x" % rgb


def mix_with_white(hex_color, percent):
    t = max(0, min(100, percent or 0)) / 100
    r, g, b = hex_to_rgb(hex_color)
    mixed = tuple(round(255 + (c - 255) * t) for c in (r, g, b))
    return rgb_to_hex(mixed)


def readable_text_color(hex_color):
    r, g, b = hex_to_rgb(hex_color)
    luminance = 0.299 * r + 0.587 * g + 0.114 * b
    return "#161616" if luminance > 150 else "#ffffff"
