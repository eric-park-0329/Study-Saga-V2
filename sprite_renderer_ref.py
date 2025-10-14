from PIL import Image
from pathlib import Path
from typing import Optional

APP_DIR = Path(__file__).resolve().parent
ASSET_DIR = APP_DIR / "assets"

LAYER_ORDER = ["bottom","shoes","top","hair","accessory"]

class SpriteRendererRef:
    def __init__(self, pixel_scale: int = 4):
        self.pixel_scale = pixel_scale
        self.base_gender = "male"
        self.layers = {k: None for k in LAYER_ORDER}

    def set_gender(self, gender: str):
        if gender not in ("male","female"):
            raise ValueError("gender must be 'male' or 'female'")
        self.base_gender = gender

    def set_layer(self, slot: str, filename: Optional[str]):
        if slot not in self.layers:
            raise ValueError(f"unknown slot '{slot}'")
        self.layers[slot] = filename

    def _open(self, name: str) -> Image.Image:
        p = ASSET_DIR / name
        if not p.exists():
            raise FileNotFoundError(f"asset not found: {p}")
        return Image.open(p).convert("RGBA")

    def render(self) -> Image.Image:
        base = self._open("base_male.png" if self.base_gender=="male" else "base_female.png").copy()
        canvas = Image.new("RGBA", base.size, (0,0,0,0))
        canvas.alpha_composite(base)
        for slot in LAYER_ORDER:
            fn = self.layers.get(slot)
            if not fn: continue
            try:
                canvas.alpha_composite(self._open(fn))
            except FileNotFoundError:
                pass
        w,h = canvas.size
        return canvas.resize((w*self.pixel_scale, h*self.pixel_scale), Image.NEAREST)
