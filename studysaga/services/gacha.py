import random

class GachaMachine:
  COSTS = {'bronze':10, 'silver':30, 'gold':60}
  def __init__(self, db):
    self.db = db

  def roll(self, tier):
    cost = self.COSTS.get(tier, 10)
    if not self.db.spend_crystals(cost):
      return False, None
    pool = self.db.pool_by_tier(tier)
    item = random.choice(pool) if pool else None
    if not item:
      return False, None
    got = self.db.add_item_id(item['id'])
    return True, got
