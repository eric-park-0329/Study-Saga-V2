
from db import DB
from sprite_renderer_ref import SpriteRendererRef

db = DB("app.db")
ap = db.build_appearance()
r = SpriteRendererRef(sex=ap.get("sex","male"))
img = r.render(ap)
img.save("player_preview.png")
print("Wrote player_preview.png")
