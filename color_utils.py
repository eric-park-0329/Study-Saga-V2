from PIL import Image
from typing import Tuple, List

PALETTE_20: List[str] = [
    "#ff0000","#ff7f00","#ffbf00","#ffff00","#bfff00",
    "#7fff00","#00ff00","#00ff7f","#00ffbf","#00ffff",
    "#00bfff","#007fff","#0000ff","#7f00ff","#bf00ff",
    "#ff00ff","#ff007f","#ff00bf","#964B00","#ffffff"
]

def hex_to_rgb(h: str) -> Tuple[int,int,int]:
    h = h.strip().lstrip("#")
    if len(h) == 3:
        h = "".join([c*2 for c in h])
    r = int(h[0:2], 16); g = int(h[2:4], 16); b = int(h[4:6], 16)
    return r,g,b

def recolor_preserve_shade(img: Image.Image, hex_color: str) -> Image.Image:
    if not hex_color:
        return Image.new("RGBA", img.size, (0,0,0,0))
    r,g,b = hex_to_rgb(hex_color)
    src = img.convert("RGBA")
    out = Image.new("RGBA", src.size)
    src_px = src.load(); out_px = out.load()
    for y in range(src.height):
        for x in range(src.width):
            pr,pg,pb,pa = src_px[x,y]
            if pa == 0:
                out_px[x,y] = (0,0,0,0); continue
            lum = max(pr,pg,pb)/255.0
            nr = int(r*lum); ng = int(g*lum); nb = int(b*lum)
            out_px[x,y] = (nr,ng,nb,pa)
    return out
