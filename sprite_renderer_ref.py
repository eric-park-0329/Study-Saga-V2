from PIL import Image
from pathlib import Path

ASSET_DIR = Path(__file__).resolve().parent / "assets"
ORDER = ["bottom","shoes","top","hair","accessory"]

class SpriteRendererRef:
    def __init__(self, scale=6):
        self.gender="male"
        self.layers = {k: None for k in ORDER}
        self.scale = scale
    def set_gender(self, g): self.gender = "female" if g=="female" else "male"
    def set_layer(self, slot, item): self.layers[slot]=item
    def _open(self, name): return Image.open(ASSET_DIR/name).convert("RGBA")
    def render(self):
        base = self._open("base_female.png" if self.gender=="female" else "base_male.png").copy()
        canvas = Image.new("RGBA", base.size, (0,0,0,0))
        canvas.alpha_composite(base)
        for s in ORDER:
            fn = self.layers.get(s)
            if fn:
                try: canvas.alpha_composite(self._open(fn))
                except FileNotFoundError: pass
        w,h = canvas.size
        return canvas.resize((w*self.scale, h*self.scale), Image.NEAREST)
