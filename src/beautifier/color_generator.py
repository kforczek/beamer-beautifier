import random


class RGBRandomizer:
    """Represents a randomizer for RGB colors."""
    def __init__(self, rmin = 0, rmax = 255,
                        gmin = 0, gmax = 255,
                        bmin = 0, bmax = 255):
        self.red = random.randint(rmin, rmax)
        self.green = random.randint(gmin, gmax)
        self.blue = random.randint(bmin, bmax)


class RandomColor:
    """Represents a random RGB color definition."""
    def __init__(self, randomizer=RGBRandomizer()):
        self._red = randomizer.red
        self._green = randomizer.green
        self._blue = randomizer.blue

    def as_tuple(self):
        """
        :return: Tuple (r, g, b) representing the color.
        """
        return self._red, self._green, self._blue

    def latex_definition(self, col_name) -> str:
        """
        :return: LaTeX statement defining the color.
        """
        return f"\\definecolor{{{col_name}}}{{RGB}}{{{self._red},{self._green},{self._blue}}}"

    def is_dark(self) -> bool:
        return self._red + self._green + self._blue < 3*128

    def similar_color(self, change: int):
        """
        :return: A similar color with its RGB values randomized in the range [current+change, current]
        if change is less than 0 or in the range [current, current+change] if the change is more than 0.
        """
        if change < 0:
            r_low = max(0, self._red + change)
            g_low = max(0, self._green + change)
            b_low = max(0, self._blue + change)
            r_high = self._red
            g_high = self._green
            b_high = self._blue
        else:
            r_low = self._red
            g_low = self._green
            b_low = self._blue
            r_high = min(255, self._red + change)
            g_high = min(255, self._green + change)
            b_high = min(255, self._blue + change)

        return RandomColor(RGBRandomizer(r_low, r_high, g_low, g_high, b_low, b_high))


def palette_color_defs(color1, name1, color2, name2, color3, name3, color4, name4) -> str:
    defs = ""
    for pal_name, col, col_name in (('primary', color1, name1), ('secondary', color2, name2), ('tertiary', color3, name3), ('quaternary', color4, name4)):
        defs += f"\\setbeamercolor{{palette {pal_name}}}{{bg={col_name}, fg={'white' if col.is_dark() else 'black'}}}\n"
    return defs[:-1]


def get_random_color_set() -> str:
    color1 = RandomColor(RGBRandomizer(50, 200, 50, 200, 50, 200))
    color2 = color1.similar_color(20)
    color3 = color2.similar_color(30)
    color4 = color3.similar_color(20)

    palette_defs = palette_color_defs(color1, "RandomColor1", color2, "RandomColor2", color3, "RandomColor3", color4, "RandomColor4")
    structure_def = "\\setbeamercolor{structure}{fg=RandomColor1}"

    return f"""
{color1.latex_definition("RandomColor1")}
{color2.latex_definition("RandomColor2")}
{color3.latex_definition("RandomColor3")}
{color4.latex_definition("RandomColor4")}
{palette_defs}
{structure_def}
    """
