"""Generate the 1200x630 social preview card.

Run once when the brand changes; the PNG is committed. Pillow is a build-time
tool only and is deliberately not in requirements.txt.

    python tools/make_og_image.py
"""
from PIL import Image, ImageDraw, ImageFont

W, H = 1200, 630
BRAND = (124, 58, 237)
INDIGO = (79, 70, 229)
DEEP = (25, 19, 59)
MID = (39, 32, 91)


def font(name, size):
    for candidate in (name, "segoeuib.ttf", "arialbd.ttf"):
        try:
            return ImageFont.truetype(f"C:/Windows/Fonts/{candidate}", size)
        except OSError:
            continue
    return ImageFont.load_default()


def main():
    image = Image.new("RGB", (W, H), DEEP)
    draw = ImageDraw.Draw(image)

    # Diagonal base gradient, deep indigo into violet.
    for y in range(H):
        t = y / H
        draw.line(
            [(0, y), (W, y)],
            fill=(
                int(DEEP[0] + (MID[0] - DEEP[0]) * t),
                int(DEEP[1] + (MID[1] - DEEP[1]) * t),
                int(DEEP[2] + (MID[2] - DEEP[2]) * t),
            ),
        )

    # Two soft brand glows, matching the hero.
    glow = Image.new("RGB", (W, H), (0, 0, 0))
    gdraw = ImageDraw.Draw(glow)
    gdraw.ellipse([-160, -220, 560, 420], fill=BRAND)
    gdraw.ellipse([760, 300, 1420, 900], fill=INDIGO)
    from PIL import ImageChops, ImageFilter
    glow = glow.filter(ImageFilter.GaussianBlur(170))
    # Screen the glow on so it adds light instead of averaging the base away.
    image = ImageChops.screen(image, ImageChops.multiply(glow, Image.new("RGB", (W, H), (108, 108, 108))))
    draw = ImageDraw.Draw(image)

    # Faint grid, the same motif as the hero panel.
    for x in range(0, W, 58):
        draw.line([(x, 0), (x, H)], fill=(255, 255, 255), width=1)
    for y in range(0, H, 58):
        draw.line([(0, y), (W, y)], fill=(255, 255, 255), width=1)
    grid = Image.blend(image, Image.new("RGB", (W, H), DEEP), 0.96)
    image = Image.blend(image, grid, 0.75)
    draw = ImageDraw.Draw(image)

    draw.text((84, 92), "MENTICS", font=font("seguibl.ttf", 76), fill=(255, 255, 255))
    draw.text((86, 196), "Stop guessing.", font=font("segoeuib.ttf", 82), fill=(255, 255, 255))
    draw.text((86, 288), "Start achieving.", font=font("segoeuib.ttf", 82), fill=(198, 186, 255))

    body = font("seguisb.ttf", 33)
    draw.text((88, 416),
              "A personalized SAT, ACT, and college plan built from your",
              font=body, fill=(206, 202, 236))
    draw.text((88, 460),
              "real scores \u2014 one focused step at a time.",
              font=body, fill=(206, 202, 236))

    draw.line([(88, 540), (240, 540)], fill=BRAND, width=6)
    draw.text((88, 560), "mentics.vercel.app", font=font("seguisb.ttf", 27), fill=(160, 152, 205))

    image.save("static/og-cover.png", "PNG", optimize=True)
    print(f"wrote static/og-cover.png ({W}x{H})")


if __name__ == "__main__":
    main()
