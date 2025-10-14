
from PIL import Image
import colorsys

def hex_to_rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i+2], 16) for i in (0,2,4))

def lum(rgb):
    r,g,b = [c/255.0 for c in rgb]
    return 0.2126*r + 0.7152*g + 0.0722*b

def set_luma(rgb, target_l):
    r,g,b = [c/255.0 for c in rgb[:3]]
    h,l,s = colorsys.rgb_to_hls(r,g,b)
    nr,ng,nb = colorsys.hls_to_rgb(h, max(0.0, min(1.0, target_l)), s)
    return (int(nr*255), int(ng*255), int(nb*255), 255)

def recolor_preserve_shade(img, mask, base_mean_rgb, target_rgb):
    if img.mode != "RGBA": img = img.convert("RGBA")
    w, h = img.size
    p = img.load()
    m = mask.load()
    L0 = max(1e-4, lum(base_mean_rgb))
    Lt = lum(target_rgb)
    out = Image.new("RGBA", (w,h), (0,0,0,0))
    q = out.load()
    for y in range(h):
        for x in range(w):
            if m[x,y] > 0:
                px = p[x,y]
                # shade factor vs mean of this region
                Lp = lum(px[:3])
                factor = Lp / L0
                newL = max(0.0, min(1.0, factor * Lt))
                # reuse target hue/sat, set luminance
                r,g,b,a = set_luma(target_rgb+(255,), newL)
                q[x,y] = (r,g,b, px[3])
    img = img.copy()
    img.alpha_composite(out)
    return img
