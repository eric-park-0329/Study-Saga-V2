
from PIL import Image, ImageDraw, ImageStat, ImageFilter
import os
from color_utils import hex_to_rgb, recolor_preserve_shade

ASSETS_DIR = os.path.join(os.path.dirname(__file__), "assets")

SEED_BOXES = {
    "female": {
        "hair":  (90, 95, 150, 140),
        "skin":  (165,120, 190,150),
        "shirt": (160,190, 220,230),
        "pants": (165,260, 220,315),
        "shoes": (125,355, 215,390),
        "belt":  (180,240, 215,260)
    },
    "male": {
        "hair":  (90, 105, 150, 150),
        "skin":  (165,130, 190,160),
        "shirt": (160,195, 220,235),
        "pants": (165,265, 220,320),
        "shoes": (125,360, 215,395),
        "belt":  (180,242, 215,262)
    }
}

def crop_mean(img, box):
    region = img.crop(box).convert("RGBA")
    stat = ImageStat.Stat(region)
    r,g,b,a = [int(v) for v in stat.mean]
    return (r,g,b,255)

def make_mask_by_similarity(base, mean_rgb, tol=52):
    if base.mode != "RGBA": base = base.convert("RGBA")
    w,h = base.size
    p = base.load()
    mask = Image.new("L", (w,h), 0)
    q = mask.load()
    mr,mg,mb = mean_rgb[:3]
    for y in range(h):
        for x in range(w):
            r,g,b,a = p[x,y]
            if a < 16: continue
            dist = ((r-mr)**2 + (g-mg)**2 + (b-mb)**2) ** 0.5
            if dist < tol:
                q[x,y] = 255
    mask = mask.filter(ImageFilter.BLUR)
    mask = mask.point(lambda v: 255 if v>100 else 0)
    return mask

class SpriteRendererRef:
    def __init__(self, sex="female", scale=1, bg=None):
        self.sex = sex
        self.scale = scale
        self.bg = bg
        fn = "base_female.png" if sex=="female" else "base_male.png"
        base = Image.open(os.path.join(ASSETS_DIR, fn)).convert("RGBA")
        if scale != 1:
            base = base.resize((base.width*scale, base.height*scale), Image.NEAREST)
        self.base = base
        self._masks = None
        self._means = None

    def _ensure_masks(self):
        if self._masks is not None: return
        boxes = SEED_BOXES[self.sex]
        means = {k: crop_mean(self.base, box) for k,box in boxes.items()}
        masks = {k: make_mask_by_similarity(self.base, means[k], tol=52 if k!="skin" else 40) for k in boxes.keys()}
        self._means, self._masks = means, masks

    def render(self, ap:dict):
        self._ensure_masks()
        img = self.base.copy()

        def apply(part, hex_color):
            nonlocal img
            if hex_color:
                img = recolor_preserve_shade(img, self._masks[part], self._means[part][:3], hex_to_rgb(hex_color))

        apply("hair",  ap.get("hair_color"))
        apply("skin",  ap.get("skin_color"))
        apply("shirt", ap.get("shirt_color"))
        apply("pants", ap.get("pants_color"))
        apply("shoes", ap.get("shoes_color"))
        if ap.get("belt_color"):
            apply("belt", ap.get("belt_color"))

        if self.bg:
            canvas = Image.new("RGBA", img.size, self.bg)
            canvas.alpha_composite(img)
            img = canvas

        img = self._acc(img, ap)
        return img

    def _acc(self, img, ap):
        has_glasses = ap.get("has_glasses", False)
        has_mustache = ap.get("has_mustache", False)
        if not (has_glasses or has_mustache):
            return img

        w,h = img.size
        draw = ImageDraw.Draw(img)
        skin_mask = self._masks["skin"]
        bbox = skin_mask.getbbox() or (0,0,w,h)
        x0,y0,x1,y1 = bbox
        # assume head is top-left area of skin bbox
        head = (x0, y0, int(x0+(x1-x0)*0.65), int(y0+(y1-y0)*0.55))

        if has_glasses:
            c = hex_to_rgb(ap.get("glasses_color", "#000000"))
            gx0, gy0, gx1, gy1 = head
            ey = int(gy0 + (gy1-gy0)*0.45)
            gH = max(2, (gy1-gy0)//10)
            gW = max(6, (gx1-gx0)//4)
            draw.rectangle((gx0+6, ey, gx0+6+gW, ey+gH), outline=c, width=1)
            rx = gx0+6+gW+6
            draw.rectangle((rx, ey, rx+gW, ey+gH), outline=c, width=1)
            draw.line((gx0+6+gW, ey+gH//2, rx, ey+gH//2), fill=c, width=1)

        if has_mustache:
            c = hex_to_rgb(ap.get("facial_hair_color", "#2C1B18"))
            mx0,my0,mx1,my1 = head
            my = int(my0 + (my1-my0)*0.62)
            mw = max(18, (mx1-mx0)//2)
            mh = max(2, (my1-my0)//18)
            cx = mx0 + (mx1-mx0)//2
            draw.rectangle((cx-mw//2, my, cx+mw//2, my+mh), fill=c)
        return img
