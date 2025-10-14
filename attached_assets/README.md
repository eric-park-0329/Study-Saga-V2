
# Pixel Character Renderer (Female/Male bases only)

This renders player sprites **using ONLY the two provided base images** (`assets/base_female.png`, `assets/base_male.png`).  
It recolors hair/skin/shirt/pants/shoes while preserving the original shading and adds optional glasses/mustache overlays.

## Files
- `assets/base_female.png`, `assets/base_male.png`
- `sprite_renderer_ref.py` — renderer (masking + shade-preserving recolor)
- `color_utils.py` — color helpers
- `db.py` — compact DB (adds gender, glasses, mustache) + `build_appearance()`
- `demo_generate.py` — generates sample_*.png
- `demo_from_db.py` — renders `player_preview.png` from DB

## Usage
```bash
python demo_generate.py
python demo_from_db.py
```

## Appearance dictionary
```python
ap = {
  "sex": "female",               # "male" or "female" (choose base)
  "skin_color": "#F2D3B7",
  "hair_color": "#C04B2B",
  "shirt_color": "#3A7BD5",
  "pants_color": "#5C7A3F",
  "shoes_color": "#3E2B1A",
  "belt_color": "#A1742C",       # optional
  "has_glasses": True,
  "glasses_color": "#000000",
  "has_mustache": False,
  "facial_hair_color": "#2C1B18"
}
```
