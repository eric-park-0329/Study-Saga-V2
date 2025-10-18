from dataclasses import dataclass

@dataclass
class Theme:
    name: str
    bg: tuple
    card: tuple
    text: tuple
    accent: tuple
    accent_text: tuple
    muted: tuple
    gold: tuple
    silver: tuple
    bronze: tuple

LIGHT = Theme(
    name="light",
    bg=(0.96, 0.97, 1, 1),
    card=(1, 1, 1, 1),
    text=(0, 0, 0, 1),
    accent=(0.2, 0.4, 0.9, 1),
    accent_text=(1, 1, 1, 1),
    muted=(0, 0, 0, 0.65),
    gold=(1.0, 0.88, 0.35, 1),
    silver=(0.82, 0.86, 0.95, 1),
    bronze=(0.90, 0.70, 0.45, 1),
)

DARK = Theme(
    name="dark",
    bg=(0.07, 0.08, 0.10, 1),
    card=(0.12, 0.13, 0.16, 1),
    text=(1, 1, 1, 1),
    accent=(0.35, 0.65, 1.0, 1),
    accent_text=(0, 0, 0, 1),
    muted=(1, 1, 1, 0.7),
    gold=(1.0, 0.9, 0.4, 1),
    silver=(0.75, 0.8, 0.9, 1),
    bronze=(0.85, 0.6, 0.4, 1),
)
