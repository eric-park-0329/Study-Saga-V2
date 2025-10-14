
from sprite_renderer_ref import SpriteRendererRef

variants = [
    ("female", {"hair_color":"#C04B2B","skin_color":"#F2D3B7","shirt_color":"#2E7D32","pants_color":"#5C7A3F","shoes_color":"#3E2B1A","belt_color":"#A1742C","has_glasses":True}),
    ("female", {"hair_color":"#3C2B7A","skin_color":"#F2D3B7","shirt_color":"#4B7BD8","pants_color":"#5C7A9F","shoes_color":"#2B2B3C"}),
    ("male",   {"hair_color":"#5C3A1A","skin_color":"#E3BFA3","shirt_color":"#2F6DB5","pants_color":"#637A3A","shoes_color":"#3E2B1A","has_mustache":True}),
    ("male",   {"hair_color":"#1E1E1E","skin_color":"#E3BFA3","shirt_color":"#9CA3AF","pants_color":"#7B8794","shoes_color":"#434C5E"}),
]

for i,(sex, ap) in enumerate(variants, start=1):
    r = SpriteRendererRef(sex=sex)
    img = r.render(ap)
    img.save(f"sample_{i}_{sex}.png")
print("Wrote sample sprites.")
