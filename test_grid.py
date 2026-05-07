from PIL import Image, ImageDraw

def draw_analysis_grid(img: Image.Image) -> Image.Image:
    grid_img = img.copy()
    draw = ImageDraw.Draw(grid_img, "RGBA")
    w, h = img.size
    
    cols = 10
    rows = 10
    line_color = (0, 212, 255, 120)  # Cyan
    text_color = (255, 255, 255, 255)
    text_bg = (0, 0, 0, 200)
    
    for i in range(1, cols):
        x = int(w * (i / cols))
        draw.line([(x, 0), (x, h)], fill=line_color, width=2)
        label = str(int((i / cols) * 1000))
        draw.rectangle([x-12, 0, x+12, 12], fill=text_bg)
        draw.text((x-10, 0), label, fill=text_color)
        draw.rectangle([x-12, h-12, x+12, h], fill=text_bg)
        draw.text((x-10, h-12), label, fill=text_color)
        
    for i in range(1, rows):
        y = int(h * (i / rows))
        draw.line([(0, y), (w, y)], fill=line_color, width=2)
        label = str(int((i / rows) * 1000))
        draw.rectangle([0, y-6, 24, y+6], fill=text_bg)
        draw.text((2, y-6), label, fill=text_color)
        draw.rectangle([w-24, y-6, w, y+6], fill=text_bg)
        draw.text((w-22, y-6), label, fill=text_color)

    # Add center crosshairs for every cell
    for i in range(cols):
        for j in range(rows):
            cx = int(w * ((i + 0.5) / cols))
            cy = int(h * ((j + 0.5) / rows))
            draw.line([(cx-2, cy), (cx+2, cy)], fill=line_color, width=1)
            draw.line([(cx, cy-2), (cx, cy+2)], fill=line_color, width=1)

    return grid_img

# Create dummy image
img = Image.new('RGB', (800, 600), color = (73, 109, 137))
out = draw_analysis_grid(img)
out.save('test_grid.png')
