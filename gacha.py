import random
from typing import Tuple, Optional
import db as DB

COSTS = {'bronze':10, 'silver':30, 'gold':60}
WEIGHTS = {'bronze':[0.85,0.13,0.02], 'silver':[0.70,0.25,0.05], 'gold':[0.55,0.35,0.10]}
PITY_RARE={'bronze':10, 'silver':7, 'gold':5}
PITY_EPIC={'bronze':30, 'silver':20, 'gold':10}

def roll(user_id: int, tier: str) -> Tuple[bool, Optional[dict], str, dict]:
    cost=COSTS.get(tier,10)
    if not DB.spend_crystals(user_id, cost):
        return False, None, "Not enough crystals.", {}
    pool=DB.pool_by_tier(tier)
    if not pool: return False, None, "No items in pool.", {}

    pr,pe = DB.get_pity(user_id, tier)
    force_rare = pr+1>=PITY_RARE.get(tier,10)
    force_epic = pe+1>=PITY_EPIC.get(tier,30)

    weights=WEIGHTS.get(tier,[0.8,0.18,0.02])
    groups={1:[i for i in pool if i['rarity']==1],
            2:[i for i in pool if i['rarity']==2],
            3:[i for i in pool if i['rarity']>=3]}

    if force_epic and groups[3]:
        grp=3
    elif force_rare and (groups[2] or groups[3]):
        grp=2 if groups[2] else 3
    else:
        grp = random.choices([1,2,3], weights=weights, k=1)[0]
        if not groups.get(grp):
            grp = 1 if groups[1] else (2 if groups[2] else 3)

    item = random.choice(groups.get(grp, pool))
    DB.add_item_to_inventory(user_id, item['id'])
    DB.update_pity(user_id, tier, item['rarity'])
    if item['rarity']>=3: DB.grant_achievement(user_id, "RARE_FIND")

    pity = {"rare":PITY_RARE.get(tier,10), "rare_stacks": pr+1 if item['rarity']<2 else 0,
            "epic":PITY_EPIC.get(tier,30), "epic_stacks": pe+1 if item['rarity']<3 else 0}
    return True, item, "Success", pity
