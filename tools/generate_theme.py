#!/usr/bin/env python3
"""Rebuild the original Clean Blue UI assets with python3-cairo (not needed to install)."""
import math
from pathlib import Path
import cairo

ROOT = Path(__file__).resolve().parents[1]
THEME = ROOT / "themes/clean-blue"


def rounded(ctx, x, y, w, h, radius):
    ctx.new_sub_path()
    for cx, cy, angle in [(x+w-radius, y+radius, -90),
                          (x+w-radius, y+h-radius, 0),
                          (x+radius, y+h-radius, 90),
                          (x+radius, y+radius, 180)]:
        ctx.arc(cx, cy, radius, math.radians(angle), math.radians(angle+90))
    ctx.close_path()


def main():
    THEME.mkdir(parents=True, exist_ok=True)
    surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, 64, 64)
    ctx = cairo.Context(surface)
    for spread, alpha in [(3, .018), (2, .03), (1, .05)]:
        rounded(ctx, 4-spread, 5-spread, 56+2*spread, 55+2*spread, 9+spread)
        ctx.set_source_rgba(.1, .18, .30, alpha)
        ctx.fill()
    rounded(ctx, 4.5, 3.5, 55, 55, 8)
    ctx.set_source_rgb(1, 1, 1)
    ctx.fill_preserve()
    ctx.set_source_rgb(.84, .88, .93)
    ctx.set_line_width(1)
    ctx.stroke()
    surface.write_to_png(str(THEME / "panel.png"))
    surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, 32, 32)
    ctx = cairo.Context(surface)
    rounded(ctx, 0, 0, 32, 32, 5)
    ctx.set_source_rgb(.13, .46, .94)
    ctx.fill()
    surface.write_to_png(str(THEME / "highlight.png"))
    for name in ["prev", "next", "arrow", "radio"]:
        surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, 16, 16)
        ctx = cairo.Context(surface)
        ctx.set_source_rgb(.42, .49, .59)
        ctx.set_line_width(1.5)
        ctx.set_line_cap(cairo.LINE_CAP_ROUND)
        ctx.set_line_join(cairo.LINE_JOIN_ROUND)
        if name == "radio":
            ctx.set_source_rgb(.13, .46, .94)
            ctx.arc(8, 8, 3, 0, 2*math.pi)
            ctx.fill()
        else:
            points = [(10, 4), (6, 8), (10, 12)] if name == "prev" else [(6, 4), (10, 8), (6, 12)]
            ctx.move_to(*points[0])
            for point in points[1:]:
                ctx.line_to(*point)
            ctx.stroke()
        surface.write_to_png(str(THEME / (name + ".png")))


if __name__ == "__main__":
    main()
