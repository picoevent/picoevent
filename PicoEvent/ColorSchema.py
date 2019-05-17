# I think there can be something cool to come from this eventually, I'm bad at picking colors


class ColorSchema:
    def __init__(self):
        self._color_table = []

    def _get_color_for_index(self, index):
        if index < len(self._color_table):
            return self._color_table[index]
        else:
            corrected_index = index % len(self._color_table)
            return self._color_table[corrected_index]

    def hex_code(self, index: int) -> str:
        return self._get_color_for_index(index)

    def rgb(self, index: int) -> tuple:
        rgb = self._get_color_for_index(index)
        red = int(rgb[0:2], 16)
        green = int(rgb[2:4], 16)
        blue = int(rgb[4:6], 16)
        return red, green, blue


class DefaultColorSchema(ColorSchema):
    def __init__(self):
        super().__init__()
        colors = ["233142",
                  "facf5a",
                  "ff5959"
                  "4f9da6",
                  "022c43",
                  "ffd700",
                  "115173",
                  "053f5e",
                  "3a9679",
                  "fabc60",
                  "11144c",
                  "085f63",
                  "49beb7",
                  "facf5a",
                  "ff5959"]
        self._color_table.extend(colors)
