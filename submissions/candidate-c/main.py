"""Behavior clone of a public elite action calendar."""
import base64
import json
import zlib
from collections import Counter
from pathlib import Path
from typing import Any
MODEL_PAYLOAD: str | None = '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'
MOVE_ACTIONS = {'NORTH', 'SOUTH', 'EAST', 'WEST'}
FIRST_YIELD_DAY = {'WHEAT': 2, 'CARROT': 2, 'TOMATO': 8, 'STRAWBERRY': 10, 'MELON': 10}
ANIMAL_STRUCTURES = {'GOOSE': 'COOP', 'COW': 'PASTURE', 'SHEEP': 'PASTURE'}
PASS = ['PASS']

def _load_actions() -> tuple[dict[str, Any], ...]:
    payload = MODEL_PAYLOAD
    if payload is None:
        model = json.loads(MODEL_PATH.read_text(encoding='utf-8'))
        payload = str(model['actions_zlib_b64'])
    compressed = base64.b64decode(payload)
    actions = json.loads(zlib.decompress(compressed).decode('utf-8'))
    if len(actions) != 720:
        raise ValueError('Distilled calendar must contain 720 records')
    return tuple(actions)
CALENDAR_ACTIONS = _load_actions()

def _tile_at(farm: dict[str, Any], position: tuple[int, int]) -> Any:
    x, y = position
    return farm['tiles'][y][x]

def _shed_adjacent(position: tuple[int, int], board_size: int) -> bool:
    half = board_size // 2
    return position in {(half - 1, half - 1), (half, half - 1), (half - 1, half), (half, half)}

def _inventory(private: dict[str, Any], worker: int) -> dict[str, Any]:
    inventories = private.get('inventories', [])
    if worker < len(inventories) and isinstance(inventories[worker], dict):
        return inventories[worker]
    return {}

def _valid_action(observation: dict[str, Any], worker: int, position: tuple[int, int], action: list[Any]) -> bool:
    if not action:
        return False
    operation = str(action[0])
    player = int(observation['player'])
    farm = observation['farms'][player]
    private = observation['private']
    tile = _tile_at(farm, position)
    inventory = _inventory(private, worker)
    board_size = len(farm['tiles'])
    if operation == 'PASS':
        return True
    if operation in MOVE_ACTIONS:
        x, y = position
        return {'NORTH': y > 0, 'SOUTH': y + 1 < board_size, 'WEST': x > 0, 'EAST': x + 1 < board_size}[operation]
    if operation == 'PLANT':
        return len(action) >= 2 and tile is None and (int(private.get('seeds', {}).get(str(action[1]), 0)) > 0)
    if operation == 'WATER':
        return isinstance(tile, dict) and tile.get('kind') == 'PLANT' and (not tile.get('watered_today', False))
    if operation == 'HARVEST':
        if not isinstance(tile, dict) or int(tile.get('yield_units', 0)) <= 0:
            return False
        if tile.get('kind') != 'PLANT':
            return bool(tile.get('animal'))
        crop = str(tile.get('crop'))
        age = int(observation.get('day', 0)) - int(tile.get('planted_day', 0))
        return age >= FIRST_YIELD_DAY[crop]
    if operation == 'FERTILIZE':
        return isinstance(tile, dict) and tile.get('kind') == 'PLANT' and (int(inventory.get('FERTILIZER', 0)) > 0)
    if operation == 'DIG':
        return tile is not None and (not (isinstance(tile, dict) and tile.get('animal')))
    if operation in {'BUILD_COOP', 'BUILD_PASTURE'}:
        return tile is None
    if operation == 'FEED':
        return isinstance(tile, dict) and tile.get('animal') and (not tile.get('fed_today', False)) and (int(inventory.get('WHEAT', 0)) > 0)
    if operation == 'CARE':
        return isinstance(tile, dict) and tile.get('animal') and (not tile.get('cared_today', False))
    if operation == 'COLLECT_FERTILIZER':
        return isinstance(tile, dict) and tile.get('animal') and bool(tile.get('fertilizer_available', False))
    if operation == 'PICKUP':
        return len(action) >= 2 and _shed_adjacent(position, board_size) and (int(private.get('shed', {}).get(str(action[1]), 0)) > 0)
    if operation == 'DROP':
        return _shed_adjacent(position, board_size) and any((int(quantity) > 0 for quantity in inventory.values()))
    if operation == 'PLACE' and len(action) >= 2:
        item = str(action[1])
        if int(inventory.get(item, 0)) <= 0:
            return False
        if item in ANIMAL_STRUCTURES:
            return isinstance(tile, dict) and tile.get('kind') == ANIMAL_STRUCTURES[item] and (not tile.get('animal'))
        return _shed_adjacent(position, board_size)
    return False

def _local_repair(observation: dict[str, Any], worker: int, position: tuple[int, int]) -> list[Any]:
    player = int(observation['player'])
    farm = observation['farms'][player]
    private = observation['private']
    tile = _tile_at(farm, position)
    inventory = _inventory(private, worker)
    board_size = len(farm['tiles'])
    if isinstance(tile, dict) and int(tile.get('yield_units', 0)) > 0:
        action = ['HARVEST']
        if _valid_action(observation, worker, position, action):
            return action
    if isinstance(tile, dict) and tile.get('animal'):
        if not tile.get('fed_today', False) and int(inventory.get('WHEAT', 0)) > 0:
            return ['FEED']
        if tile.get('fed_today', False) and (not tile.get('cared_today', False)):
            return ['CARE']
        if tile.get('fertilizer_available', False):
            return ['COLLECT_FERTILIZER']
    if isinstance(tile, dict) and tile.get('kind') == 'PLANT' and (not tile.get('watered_today', False)) and (int(tile.get('consecutive_unwatered', 0)) >= 1):
        return ['WATER']
    if _shed_adjacent(position, board_size) and any((int(quantity) > 0 for quantity in inventory.values())):
        return ['DROP']
    return PASS

def _sanitize_units(observation: dict[str, Any], planned: dict[str, Any]) -> tuple[list[Any], list[list[Any]]]:
    player = int(observation['player'])
    farm = observation['farms'][player]
    positions = [tuple(farm['farmer']), *(tuple(position) for position in farm.get('hands', []))]
    planned_actions = [planned.get('farmer', PASS)]
    planned_actions.extend(planned.get('hands', []))
    sanitized = []
    for worker, position in enumerate(positions):
        action = planned_actions[worker] if worker < len(planned_actions) and isinstance(planned_actions[worker], list) else PASS
        sanitized.append(list(action) if _valid_action(observation, worker, position, action) else _local_repair(observation, worker, position))
    available_seeds = Counter(observation['private'].get('seeds', {}))
    for crop in tuple(available_seeds):
        planters = [worker for worker, action in enumerate(sanitized) if action[:2] == ['PLANT', crop]]
        for worker in planters[available_seeds[crop]:]:
            sanitized[worker] = PASS
    return (sanitized[0], sanitized[1:])

def calendar_decide(observation: dict[str, Any]) -> dict[str, Any]:
    next_record = int(observation.get('step', 0)) + 1
    if next_record >= len(CALENDAR_ACTIONS):
        return {'farmer': PASS, 'hands': [], 'market': []}
    planned = CALENDAR_ACTIONS[next_record]
    return {'farmer': list(planned.get('farmer', PASS)), 'hands': [list(action) for action in planned.get('hands', [])], 'market': [list(order) for order in planned.get('market', [])]}
'Deterministic shortest-path primitives for the obstacle-free farm grid.'
from collections.abc import Iterable
Position = tuple[int, int]
Action = list[str]

def distance(origin: Position, target: Position) -> int:
    """Return the exact shortest path length on the farm grid."""
    return abs(origin[0] - target[0]) + abs(origin[1] - target[1])

def step_toward(origin: Position, target: Position, action_at_target: Action) -> Action:
    """Take one deterministic shortest-path step or act at the target."""
    if origin == target:
        return action_at_target
    if target[0] < origin[0]:
        return ['WEST']
    if target[0] > origin[0]:
        return ['EAST']
    if target[1] < origin[1]:
        return ['NORTH']
    return ['SOUTH']

def nearest_position(origin: Position, targets: Iterable[Position]) -> Position:
    """Return the nearest target with stable row-major tie-breaking."""
    return min(targets, key=lambda target: (distance(origin, target), target[1], target[0]))

def pair_route_cost(positions: tuple[Position, Position], target: Position) -> tuple[int, int]:
    """Rank a paired route by completion time, then total travel."""
    distances = tuple((distance(position, target) for position in positions))
    return (max(distances), sum(distances))
'Public observation features and inference for learned macro policies.'
from collections import Counter
from math import sqrt
from typing import Any
ARM_COMPACT = 0
ARM_EXPANDED = 1
ARM_COMPACT_CROP = 2
ARM_EXPANDED_CROP = 3
MACRO_ARMS = (ARM_COMPACT, ARM_EXPANDED, ARM_COMPACT_CROP, ARM_EXPANDED_CROP)
FEATURE_NAMES = ('player', 'own_money_k', 'opponent_money_k', 'money_lead_k', 'opponent_hands', 'opponent_land', 'opponent_wheat', 'opponent_nonwheat', 'opponent_cows', 'opponent_sheep', 'opponent_geese', 'opponent_structures', 'opponent_weeds', 'price_wheat', 'price_strawberry', 'price_melon', 'price_milk', 'price_wool', 'price_fertilizer', 'shops_wheat', 'shops_strawberry', 'shops_milk', 'shops_wool')
WHEAT_SHOPS = {'BAKERY', 'BRUNCH_SPOT', 'FARMERS_MARKET', 'ICE_CREAM_SHOP', 'PIZZA_SHOP'}
STRAWBERRY_SHOPS = {'BRUNCH_SPOT', 'FARMERS_MARKET', 'ICE_CREAM_SHOP', 'SMOOTHIE_SHOP'}
MILK_SHOPS = {'ICE_CREAM_SHOP', 'PIZZA_SHOP', 'SMOOTHIE_SHOP'}

def _public_counts(farm: dict[str, Any]) -> dict[str, Counter[str]]:
    counts = {'crops': Counter(), 'animals': Counter(), 'structures': Counter(), 'terrain': Counter()}
    for row in farm.get('tiles', []):
        for tile in row:
            if not isinstance(tile, dict):
                continue
            if tile.get('kind') == 'PLANT':
                counts['crops'][str(tile.get('crop', 'UNKNOWN'))] += 1
            if tile.get('animal'):
                counts['animals'][str(tile['animal'])] += 1
            if tile.get('kind') in {'COOP', 'PASTURE'}:
                counts['structures'][str(tile['kind'])] += 1
            if tile.get('kind') == 'WEED':
                counts['terrain']['WEED'] += 1
    return counts

def extract_macro_features(observation: dict[str, Any]) -> dict[str, float]:
    """Extract only state that is public to both players."""
    player = int(observation['player'])
    farms = observation['farms']
    own = farms[player]
    opponent = farms[1 - player]
    counts = _public_counts(opponent)
    crops = counts['crops']
    animals = counts['animals']
    prices = observation.get('market', {}).get('prices', {})
    shops = Counter(observation.get('town', {}).get('unlocked_shops', []))
    own_money = float(own.get('money', 0))
    opponent_money = float(opponent.get('money', 0))
    features = {'player': float(player), 'own_money_k': own_money / 1000.0, 'opponent_money_k': opponent_money / 1000.0, 'money_lead_k': (own_money - opponent_money) / 1000.0, 'opponent_hands': float(len(opponent.get('hands', []))), 'opponent_land': float(len(opponent.get('unlocked_quadrants', []))), 'opponent_wheat': float(crops['WHEAT']), 'opponent_nonwheat': float(sum(crops.values()) - crops['WHEAT']), 'opponent_cows': float(animals['COW']), 'opponent_sheep': float(animals['SHEEP']), 'opponent_geese': float(animals['GOOSE']), 'opponent_structures': float(sum(counts['structures'].values())), 'opponent_weeds': float(counts['terrain']['WEED']), 'price_wheat': float(prices.get('WHEAT', 0)) / 25.0, 'price_strawberry': float(prices.get('STRAWBERRY', 0)) / 120.0, 'price_melon': float(prices.get('MELON', 0)) / 250.0, 'price_milk': float(prices.get('MILK', 0)) / 160.0, 'price_wool': float(prices.get('WOOL', 0)) / 200.0, 'price_fertilizer': float(prices.get('FERTILIZER', 0)) / 100.0, 'shops_wheat': float(sum((shops[shop] for shop in WHEAT_SHOPS))), 'shops_strawberry': float(sum((shops[shop] for shop in STRAWBERRY_SHOPS))), 'shops_milk': float(sum((shops[shop] for shop in MILK_SHOPS))), 'shops_wool': float(shops['YARN_STORE'])}
    return {name: features[name] for name in FEATURE_NAMES}

def select_macro_arm(model: dict[str, Any], features: dict[str, float]) -> int:
    """Evaluate a learned macro policy."""
    if model.get('type') == 'knn':
        return _select_knn_arm(model, features)
    node = model
    while 'arm' not in node:
        feature = str(node['feature'])
        branch = 'left' if features[feature] <= float(node['threshold']) else 'right'
        node = node[branch]
    arm = int(node['arm'])
    if arm not in MACRO_ARMS:
        raise ValueError(f'Unknown macro arm: {arm}')
    return arm

def _select_knn_arm(model: dict[str, Any], features: dict[str, float]) -> int:
    names = [str(name) for name in model['features']]
    means = model['means']
    scales = model['scales']
    distances = []
    for example in model['examples']:
        squared = sum((((features[name] - float(example['features'][name])) / float(scales[name])) ** 2 for name in names))
        distances.append((sqrt(squared), example))
    neighbors = sorted(distances, key=lambda item: item[0])[:int(model['k'])]
    power = float(model.get('distance_power', 1.0))
    scores = {}
    for arm in MACRO_ARMS:
        weighted = 0.0
        weight_sum = 0.0
        for distance, example in neighbors:
            if str(arm) not in example['outcomes']:
                continue
            weight = 1.0 if power == 0 else 1.0 / (distance + 0.1) ** power
            weighted += weight * float(example['outcomes'][str(arm)]['utility'])
            weight_sum += weight
        if weight_sum > 0:
            scores[arm] = weighted / weight_sum
    if not scores:
        raise ValueError('KNN macro model has no compatible arm outcomes')
    return max(scores, key=lambda arm: (scores[arm], arm))
'Decision-time workload features for live macro selection.'
from typing import Any
PREMIUM_SERVICE_AGES = {'MELON': frozenset({6, 7, 8, 9, 10}), 'STRAWBERRY': frozenset({9, 11, 13, 15})}
LIVE_FEATURE_NAMES = FEATURE_NAMES + ('own_hands', 'own_land', 'own_wheat', 'own_nonwheat', 'own_strawberries', 'own_unwatered_crops', 'own_stressed_crops', 'own_harvestable_crop_units', 'own_animals', 'own_cows', 'own_sheep', 'own_geese', 'own_due_feed', 'own_due_care', 'own_collectable_animal_units', 'own_fertilizer_stock', 'own_service_tasks_per_worker', 'own_fertilizer_carriers', 'own_carried_fertilizer', 'own_due_melons', 'own_due_strawberries', 'own_unfertilized_due_melons', 'own_unfertilized_due_strawberries', 'own_unfertilized_due_premium', 'own_workers_on_due_melons', 'own_workers_on_due_strawberries', 'own_workers_on_due_premium', 'own_min_carrier_distance_to_due_melons', 'own_min_carrier_distance_to_due_strawberries', 'own_min_carrier_distance_to_due_premium', 'own_mean_worker_distance_to_due_premium', 'own_pending_feed', 'own_pending_care', 'own_pending_animal_harvests', 'own_pending_fertilizer_collection', 'own_pending_animal_service_per_worker')

def extract_live_macro_features(observation: dict[str, Any]) -> dict[str, float]:
    """Add own service burden to the public opponent and market context."""
    features = extract_macro_features(observation)
    player = int(observation['player'])
    farm = observation['farms'][player]
    private = observation.get('private', {})
    crops = []
    animals = []
    for row in farm.get('tiles', []):
        for tile in row:
            if not isinstance(tile, dict):
                continue
            if tile.get('kind') == 'PLANT':
                crops.append(tile)
            if tile.get('animal'):
                animals.append(tile)
    unwatered = sum((not tile.get('watered_today', False) for tile in crops))
    harvestable_crops = sum((int(tile.get('yield_units', 0)) for tile in crops))
    due_feed = sum((not tile.get('fed_today', False) and int(tile.get('consecutive_unfed', 0)) >= 1 for tile in animals))
    due_care = sum((tile.get('fed_today', False) and (not tile.get('cared_today', False)) for tile in animals))
    collectable_animals = sum((int(tile.get('yield_units', 0)) for tile in animals))
    service_tasks = unwatered + sum((int(tile.get('yield_units', 0)) > 0 for tile in crops)) + due_feed + due_care + sum((int(tile.get('yield_units', 0)) > 0 for tile in animals))
    workers = 1 + len(farm.get('hands', []))
    inventories = private.get('inventories', [])
    positions = [tuple(farm.get('farmer', (0, 0))), *(tuple(position) for position in farm.get('hands', []))]
    carried_fertilizer = [int(inventory.get('FERTILIZER', 0)) if isinstance(inventory, dict) else 0 for inventory in inventories[:len(positions)]]
    carriers = [worker for worker, quantity in enumerate(carried_fertilizer) if quantity > 0]
    day = int(observation.get('day', 0))
    due_by_crop: dict[str, list[tuple[int, int]]] = {'MELON': [], 'STRAWBERRY': []}
    unfertilized_by_crop = {'MELON': 0, 'STRAWBERRY': 0}
    for y, row in enumerate(farm.get('tiles', [])):
        for x, tile in enumerate(row):
            if not isinstance(tile, dict):
                continue
            crop = str(tile.get('crop', ''))
            if crop not in PREMIUM_SERVICE_AGES:
                continue
            age = day - int(tile.get('planted_day', day))
            if age not in PREMIUM_SERVICE_AGES[crop] or tile.get('watered_today', False):
                continue
            due_by_crop[crop].append((x, y))
            unfertilized_by_crop[crop] += int(tile.get('fertilized_until_day', -1)) < day
    due_premium = [target for crop in PREMIUM_SERVICE_AGES for target in due_by_crop[crop]]
    board_diameter = max(1, 2 * (len(farm.get('tiles', [])) - 1))
    no_target_distance = float(board_diameter + 1)
    carrier_distances = [distance(positions[worker], target) for worker in carriers for target in due_premium]
    minimum_carrier_distance_by_crop = {crop: float(min((distance(positions[worker], target) for worker in carriers for target in targets), default=no_target_distance)) for crop, targets in due_by_crop.items()}
    worker_target_distances = [min((distance(position, target) for position in positions)) for target in due_premium] if positions else []
    pending_feed = sum((not tile.get('fed_today', False) for tile in animals))
    pending_care = sum((not tile.get('cared_today', False) for tile in animals))
    pending_animal_harvests = sum((int(tile.get('yield_units', 0)) > 0 for tile in animals))
    pending_fertilizer_collection = sum((tile.get('fertilizer_available', False) for tile in animals))
    pending_animal_service = pending_feed + pending_care + pending_animal_harvests + pending_fertilizer_collection
    fertilizer_stock = int(private.get('shed', {}).get('FERTILIZER', 0)) + sum((int(inventory.get('FERTILIZER', 0)) for inventory in inventories if isinstance(inventory, dict)))
    own_features = {'own_hands': float(len(farm.get('hands', []))), 'own_land': float(len(farm.get('unlocked_quadrants', []))), 'own_wheat': float(sum((tile.get('crop') == 'WHEAT' for tile in crops))), 'own_nonwheat': float(sum((tile.get('crop') != 'WHEAT' for tile in crops))), 'own_strawberries': float(sum((tile.get('crop') == 'STRAWBERRY' for tile in crops))), 'own_unwatered_crops': float(unwatered), 'own_stressed_crops': float(sum((int(tile.get('consecutive_unwatered', 0)) > 0 for tile in crops))), 'own_harvestable_crop_units': float(harvestable_crops), 'own_animals': float(len(animals)), 'own_cows': float(sum((tile.get('animal') == 'COW' for tile in animals))), 'own_sheep': float(sum((tile.get('animal') == 'SHEEP' for tile in animals))), 'own_geese': float(sum((tile.get('animal') == 'GOOSE' for tile in animals))), 'own_due_feed': float(due_feed), 'own_due_care': float(due_care), 'own_collectable_animal_units': float(collectable_animals), 'own_fertilizer_stock': float(fertilizer_stock), 'own_service_tasks_per_worker': service_tasks / workers, 'own_fertilizer_carriers': float(len(carriers)), 'own_carried_fertilizer': float(sum(carried_fertilizer)), 'own_due_melons': float(len(due_by_crop['MELON'])), 'own_due_strawberries': float(len(due_by_crop['STRAWBERRY'])), 'own_unfertilized_due_melons': float(unfertilized_by_crop['MELON']), 'own_unfertilized_due_strawberries': float(unfertilized_by_crop['STRAWBERRY']), 'own_unfertilized_due_premium': float(sum(unfertilized_by_crop.values())), 'own_workers_on_due_melons': float(sum((position in due_by_crop['MELON'] for position in positions))), 'own_workers_on_due_strawberries': float(sum((position in due_by_crop['STRAWBERRY'] for position in positions))), 'own_workers_on_due_premium': float(sum((position in due_premium for position in positions))), 'own_min_carrier_distance_to_due_melons': minimum_carrier_distance_by_crop['MELON'], 'own_min_carrier_distance_to_due_strawberries': minimum_carrier_distance_by_crop['STRAWBERRY'], 'own_min_carrier_distance_to_due_premium': float(min(carrier_distances, default=no_target_distance)), 'own_mean_worker_distance_to_due_premium': sum(worker_target_distances) / len(worker_target_distances) if worker_target_distances else no_target_distance, 'own_pending_feed': float(pending_feed), 'own_pending_care': float(pending_care), 'own_pending_animal_harvests': float(pending_animal_harvests), 'own_pending_fertilizer_collection': float(pending_fertilizer_collection), 'own_pending_animal_service_per_worker': pending_animal_service / workers}
    combined = features | own_features
    return {name: combined[name] for name in LIVE_FEATURE_NAMES}
'Typed macro decisions for a residual Kaggriculture policy.'
from dataclasses import dataclass
from enum import IntEnum

class LaborDecision(IntEnum):
    KEEP = 0
    REDUCE_ONE = 1
    ADD_ONE = 2

class LandDecision(IntEnum):
    KEEP = 0
    BUY_NEXT = 1

class CropDecision(IntEnum):
    KEEP = 0
    DEMAND_BEST = 1
    WHEAT = 2
    STRAWBERRY = 3
    MELON = 4

class ServiceDecision(IntEnum):
    KEEP = 0
    SPARSE = 1
    FULL = 2
    ABANDON_LOW_VALUE = 3

class MarketDecision(IntEnum):
    KEEP = 0
    PRESERVE_CASH = 1
    PACE_SALES = 2
    LIQUIDATE = 3

class RecoveryDecision(IntEnum):
    KEEP = 0
    REPAIR_STATE_DRIFT = 1
ACTION_HEAD_SIZES = (len(LaborDecision), len(LandDecision), len(CropDecision), len(ServiceDecision), len(MarketDecision), len(RecoveryDecision))

@dataclass(frozen=True)
class ResidualAction:
    """One factored correction to the trusted calendar policy."""
    labor: LaborDecision = LaborDecision.KEEP
    land: LandDecision = LandDecision.KEEP
    crop: CropDecision = CropDecision.KEEP
    service: ServiceDecision = ServiceDecision.KEEP
    market: MarketDecision = MarketDecision.KEEP
    recovery: RecoveryDecision = RecoveryDecision.KEEP

    @property
    def is_keep_calendar(self) -> bool:
        return self == KEEP_CALENDAR

    def head_indices(self) -> tuple[int, ...]:
        """Return one categorical index for each policy head."""
        return tuple((int(value) for value in (self.labor, self.land, self.crop, self.service, self.market, self.recovery)))
KEEP_CALENDAR = ResidualAction()
'Stable state-vector contract for learned residual policies.'
from dataclasses import dataclass
from math import isfinite
from typing import Any
CLOCK_FEATURE_NAMES = ('day_fraction', 'hour_fraction', 'episode_fraction')
BASELINE_FEATURE_NAMES = ('baseline_hands', 'baseline_moves', 'baseline_plants', 'baseline_waters', 'baseline_harvests', 'baseline_animal_services', 'baseline_passes', 'baseline_market_orders', 'baseline_hires', 'baseline_land_orders', 'baseline_seed_units', 'baseline_animal_units', 'baseline_sell_units')
STATE_FEATURE_NAMES = (*CLOCK_FEATURE_NAMES, *LIVE_FEATURE_NAMES, *BASELINE_FEATURE_NAMES)
MOVE_ACTIONS = {'NORTH', 'SOUTH', 'EAST', 'WEST'}
ANIMAL_SERVICE_ACTIONS = {'FEED', 'CARE', 'COLLECT_FERTILIZER'}

@dataclass(frozen=True)
class EncodedState:
    """Named vector passed to a learned policy."""
    names: tuple[str, ...]
    values: tuple[float, ...]

    def __post_init__(self) -> None:
        if len(self.names) != len(self.values):
            raise ValueError('Feature names and values must have equal length')
        if not all((isfinite(value) for value in self.values)):
            raise ValueError('RL state contains a non-finite feature')

    def as_dict(self) -> dict[str, float]:
        return dict(zip(self.names, self.values, strict=True))

def _operation(action: Any) -> str:
    if not isinstance(action, list) or not action:
        return 'PASS'
    return str(action[0])

def _order_units(order: Any) -> int:
    if not isinstance(order, list):
        return 0
    if len(order) >= 3:
        return max(0, int(order[2]))
    return 1

def summarize_baseline_action(action: dict[str, Any]) -> dict[str, float]:
    """Describe what the trusted policy intends to do this transition."""
    farmer = action.get('farmer', ['PASS'])
    hands = action.get('hands', [])
    unit_operations = [_operation(farmer), *(_operation(hand_action) for hand_action in hands)]
    market = [order for order in action.get('market', []) if isinstance(order, list) and order]

    def market_units(operation: str) -> int:
        return sum((_order_units(order) for order in market if str(order[0]) == operation))
    return {'baseline_hands': float(len(hands)), 'baseline_moves': float(sum((operation in MOVE_ACTIONS for operation in unit_operations))), 'baseline_plants': float(unit_operations.count('PLANT')), 'baseline_waters': float(unit_operations.count('WATER')), 'baseline_harvests': float(unit_operations.count('HARVEST')), 'baseline_animal_services': float(sum((operation in ANIMAL_SERVICE_ACTIONS for operation in unit_operations))), 'baseline_passes': float(unit_operations.count('PASS')), 'baseline_market_orders': float(len(market)), 'baseline_hires': float(sum((str(order[0]) == 'HIRE' for order in market))), 'baseline_land_orders': float(sum((str(order[0]) == 'BUY_LAND' for order in market))), 'baseline_seed_units': float(market_units('BUY_SEED')), 'baseline_animal_units': float(market_units('BUY_ANIMAL')), 'baseline_sell_units': float(market_units('SELL'))}

def encode_state(observation: dict[str, Any], baseline_action: dict[str, Any]) -> EncodedState:
    """Encode legal observation data and the calendar's intended action."""
    day = int(observation.get('day', 0))
    hour = int(observation.get('hour', 0))
    step = int(observation.get('step', day * 24 + hour))
    values = {'day_fraction': min(max(day / 29.0, 0.0), 1.0), 'hour_fraction': min(max(hour / 23.0, 0.0), 1.0), 'episode_fraction': min(max(step / 718.0, 0.0), 1.0), **extract_live_macro_features(observation), **summarize_baseline_action(baseline_action)}
    return EncodedState(names=STATE_FEATURE_NAMES, values=tuple((float(values[name]) for name in STATE_FEATURE_NAMES)))
'Policy interface used by training and deployment adapters.'
from typing import Protocol

class ResidualPolicy(Protocol):

    def select_action(self, state: EncodedState) -> ResidualAction:
        """Choose a correction to the trusted calendar."""

class KeepCalendarPolicy:
    """Reference policy and mandatory training baseline."""

    def select_action(self, state: EncodedState) -> ResidualAction:
        del state
        return KEEP_CALENDAR
calendar = calendar_decide
'Fail-closed bridge from a residual policy to a Kaggle agent.'
from typing import Any, Callable, Protocol
AgentAction = dict[str, Any]
Baseline = Callable[[dict[str, Any]], AgentAction]

class UnsupportedResidualAction(RuntimeError):
    """Raised before an unimplemented learned action can reach Kaggle."""

class ResidualExecutor(Protocol):

    def apply(self, observation: dict[str, Any], baseline_action: AgentAction, residual_action: ResidualAction) -> AgentAction:
        """Safely translate one macro correction into primitive actions."""

def clone_action(action: AgentAction) -> AgentAction:
    return {'farmer': list(action.get('farmer', ['PASS'])), 'hands': [list(item) for item in action.get('hands', [])], 'market': [list(item) for item in action.get('market', [])]}

class KeepOnlyExecutor:
    """Phase-zero executor that permits no behavioral drift."""

    def apply(self, observation: dict[str, Any], baseline_action: AgentAction, residual_action: ResidualAction) -> AgentAction:
        del observation
        if not residual_action.is_keep_calendar:
            raise UnsupportedResidualAction(f'Residual execution is not implemented for {residual_action!r}')
        return clone_action(baseline_action)

def build_residual_agent(policy: ResidualPolicy, *, baseline: Baseline=calendar, executor: ResidualExecutor | None=None) -> Baseline:
    """Create a Kaggle callable while preserving deterministic safety."""
    selected_executor = executor or KeepOnlyExecutor()

    def agent(observation: dict[str, Any]) -> AgentAction:
        baseline_action = baseline(observation)
        state = encode_state(observation, baseline_action)
        residual_action = policy.select_action(state)
        return selected_executor.apply(observation, baseline_action, residual_action)
    return agent
'Candidate A: guarded calendar recovery and live terminal liquidation.'
import copy
from dataclasses import dataclass, field
from typing import Any
PASS = ['PASS']
MOVE_ACTIONS = {'NORTH', 'SOUTH', 'EAST', 'WEST'}
FINAL_EXECUTABLE_STEP = 718
TERMINAL_PLANNING_STEP = 700
TERMINAL_RETURN_STEP = 716
TERMINAL_SELL_STEP = 717
SHED_CAPACITY = 100
SELLABLE_PRODUCTS = ('MELON', 'MILK', 'WOOL', 'STRAWBERRY', 'TOMATO', 'CARROT', 'EGG', 'WHEAT', 'FERTILIZER')
ANIMAL_STRUCTURES = {'GOOSE': 'COOP', 'COW': 'PASTURE', 'SHEEP': 'PASTURE'}
RECOVERABLE_SETUP = {'PLANT', 'BUILD_COOP', 'BUILD_PASTURE'}
LOCKED_TILE_OPERATIONS = {'PLANT', 'WATER', 'HARVEST', 'FERTILIZE', 'DIG', 'BUILD_COOP', 'BUILD_PASTURE', 'FEED', 'CARE', 'COLLECT_FERTILIZER'}

@dataclass(frozen=True)
class PendingRepair:
    position: tuple[int, int]
    action: tuple[Any, ...]
    expires_step: int

@dataclass
class TerminalCommitment:
    target: tuple[int, int]
    shed: tuple[int, int]
    needs_water: bool
    phase: str = 'target'

@dataclass
class EpisodeRecovery:
    last_step: int = -1
    pending: dict[int, PendingRepair] = field(default_factory=dict)
    terminal: dict[int, TerminalCommitment] = field(default_factory=dict)

@dataclass(frozen=True)
class GuardEvent:
    guard_type: str
    worker: int
    step: int
    original_action: tuple[Any, ...]
    replacement_action: tuple[Any, ...]
    detail: str = ''

@dataclass
class CandidateATelemetry:
    """Structured residual counters for benchmark output only."""
    events: list[GuardEvent] = field(default_factory=list)
    prevented_invalid: int = 0
    recovered_units: int = 0
    sold_units: int = 0
    terminal_inventory_before: dict[str, int] = field(default_factory=dict)
    terminal_inventory_after: dict[str, int] = field(default_factory=dict)

    def record(self, *, guard_type: str, worker: int, step: int, original: list[Any], replacement: list[Any], detail: str='') -> None:
        if original == replacement:
            return
        self.events.append(GuardEvent(guard_type=guard_type, worker=worker, step=step, original_action=tuple(original), replacement_action=tuple(replacement), detail=detail))

    def summarize(self) -> dict[str, Any]:
        by_guard: dict[str, int] = {}
        for event in self.events:
            by_guard[event.guard_type] = by_guard.get(event.guard_type, 0) + 1
        return {'guard_firings': len(self.events), 'guard_types': by_guard, 'prevented_invalid': self.prevented_invalid, 'recovered_units': self.recovered_units, 'sold_units': self.sold_units, 'terminal_inventory_before': dict(self.terminal_inventory_before), 'terminal_inventory_after': dict(self.terminal_inventory_after), 'events': [{'guard_type': event.guard_type, 'worker': event.worker, 'step': event.step, 'original_action': list(event.original_action), 'replacement_action': list(event.replacement_action), 'detail': event.detail} for event in self.events]}

class CandidateAPolicy:
    """Enable only the deterministic Candidate A residual Options."""

    def __init__(self, *, enable_recovery: bool=True, enable_liquidation: bool=True, enable_terminal_commitments: bool=True) -> None:
        self._enable_recovery = enable_recovery
        self._enable_liquidation = enable_liquidation
        self._terminal_start = TERMINAL_PLANNING_STEP if enable_terminal_commitments else TERMINAL_RETURN_STEP

    def select_action(self, state: EncodedState) -> ResidualAction:
        features = state.as_dict()
        step = round(features['episode_fraction'] * FINAL_EXECUTABLE_STEP)
        market = MarketDecision.LIQUIDATE if self._enable_liquidation and step >= self._terminal_start else MarketDecision.KEEP
        return ResidualAction(market=market, recovery=RecoveryDecision.REPAIR_STATE_DRIFT if self._enable_recovery else RecoveryDecision.KEEP)

class CandidateAExecutor(ResidualExecutor):
    """Apply narrow recovery and liquidation without replacing strategy."""

    def __init__(self, baseline: Baseline, *, telemetry: CandidateATelemetry | None=None) -> None:
        self._baseline = baseline
        self._telemetry = telemetry
        self._episodes: dict[int, EpisodeRecovery] = {}

    def apply(self, observation: dict[str, Any], baseline_action: AgentAction, residual_action: ResidualAction) -> AgentAction:
        self._require_supported(residual_action)
        action = clone_action(baseline_action)
        player = int(observation['player'])
        step = int(observation.get('step', 0))
        episode = self._episode(player, step)
        if residual_action.recovery == RecoveryDecision.REPAIR_STATE_DRIFT:
            action = self._repair_units(observation, action, episode)
        if residual_action.market == MarketDecision.LIQUIDATE:
            action = self._terminal_units(observation, action, episode)
            if step >= TERMINAL_SELL_STEP:
                before = _shed_inventory(observation)
                market = self._terminal_market(observation, action)
                after = _projected_shed_after_market(before, market)
                if self._telemetry is not None:
                    self._telemetry.terminal_inventory_before = before
                    self._telemetry.terminal_inventory_after = after
                    self._telemetry.sold_units += sum((int(order[2]) for order in market if len(order) >= 3 and str(order[0]) == 'SELL'))
                action['market'] = market
        episode.last_step = step
        return action

    def _require_supported(self, action: ResidualAction) -> None:
        unsupported = action.labor != LaborDecision.KEEP or action.land != LandDecision.KEEP or action.crop != CropDecision.KEEP or (action.service != ServiceDecision.KEEP) or (action.market not in {MarketDecision.KEEP, MarketDecision.LIQUIDATE}) or (action.recovery not in {RecoveryDecision.KEEP, RecoveryDecision.REPAIR_STATE_DRIFT})
        if unsupported:
            raise UnsupportedResidualAction(f'Candidate A cannot execute {action!r}')

    def _episode(self, player: int, step: int) -> EpisodeRecovery:
        episode = self._episodes.setdefault(player, EpisodeRecovery())
        if step == 0 or step <= episode.last_step:
            episode = EpisodeRecovery()
            self._episodes[player] = episode
        return episode

    def _repair_units(self, observation: dict[str, Any], action: AgentAction, episode: EpisodeRecovery) -> AgentAction:
        player = int(observation['player'])
        step = int(observation.get('step', 0))
        farm = observation['farms'][player]
        positions = [tuple(farm['farmer']), *(tuple(position) for position in farm.get('hands', []))]
        baseline_planned = [action.get('farmer', PASS), *action.get('hands', [])]
        planned = [list(baseline_planned[worker]) if worker < len(baseline_planned) else list(PASS) for worker in range(len(positions))]
        for worker in range(len(positions), len(baseline_planned)):
            if self._telemetry is not None:
                stale = list(baseline_planned[worker])
                self._telemetry.record(guard_type='hand_align', worker=worker, step=step, original=stale, replacement=list(PASS), detail='dropped_stale_calendar_hand')
                self._telemetry.prevented_invalid += 1
        for worker, position in enumerate(positions):
            pending = episode.pending.get(worker)
            if pending is not None:
                replacement = self._continue_repair(observation, worker, position, pending)
                if replacement is not None:
                    original = list(planned[worker])
                    planned[worker] = replacement
                    if self._telemetry is not None:
                        self._telemetry.record(guard_type='pending_repair', worker=worker, step=step, original=original, replacement=replacement, detail='continue')
                    if replacement[0] == 'PLANT':
                        episode.pending[worker] = PendingRepair(position=position, action=('WATER',), expires_step=step + 1)
                    else:
                        episode.pending.pop(worker, None)
                    continue
                if self._telemetry is not None:
                    self._telemetry.record(guard_type='pending_repair', worker=worker, step=step, original=list(planned[worker]), replacement=list(planned[worker]), detail='cancelled')
                episode.pending.pop(worker, None)
            tile = _tile_at(farm, position)
            operation = str(planned[worker][0]) if planned[worker] else 'PASS'
            if operation in RECOVERABLE_SETUP and _is_weed(tile) and _repair_has_time(observation, operation) and self._repair_preserves_schedule(observation, worker, operation):
                original = list(planned[worker])
                episode.pending[worker] = PendingRepair(position=position, action=tuple(original), expires_step=step + (2 if operation == 'PLANT' else 1))
                planned[worker] = ['DIG']
                if self._telemetry is not None:
                    self._telemetry.record(guard_type='weed_dig', worker=worker, step=step, original=original, replacement=['DIG'])
                    self._telemetry.recovered_units += 1
            elif operation in LOCKED_TILE_OPERATIONS and _is_locked(tile):
                original = list(planned[worker])
                planned[worker] = list(PASS)
                if self._telemetry is not None:
                    self._telemetry.record(guard_type='locked_quadrant', worker=worker, step=step, original=original, replacement=list(PASS), detail='calendar_targeted_unpurchased_land')
                    self._telemetry.prevented_invalid += 1
            elif operation in LOCKED_TILE_OPERATIONS and operation != 'DIG' and _is_weed(tile):
                original = list(planned[worker])
                planned[worker] = ['DIG']
                if self._telemetry is not None:
                    self._telemetry.record(guard_type='weed_clear', worker=worker, step=step, original=original, replacement=['DIG'], detail='doomed_action_on_weed_cleared_in_place')
                    self._telemetry.prevented_invalid += 1
        return {'farmer': planned[0], 'hands': planned[1:], 'market': [list(order) for order in action.get('market', [])]}

    def _repair_preserves_schedule(self, observation: dict[str, Any], worker: int, operation: str) -> bool:
        next_action = self._future_action(observation, worker, 1)
        if operation == 'PLANT':
            return next_action == ['WATER'] and self._future_action(observation, worker, 2) == PASS
        return next_action == PASS

    def _future_action(self, observation: dict[str, Any], worker: int, offset: int) -> list[Any] | None:
        future = copy.deepcopy(observation)
        step = int(observation.get('step', 0)) + offset
        future['step'] = step
        future['day'] = step // 24
        future['hour'] = step % 24
        action = self._baseline(future)
        actions = [action.get('farmer', PASS), *action.get('hands', [])]
        if worker >= len(actions):
            return None
        worker_action = actions[worker]
        return list(worker_action) if isinstance(worker_action, list) else None

    def _continue_repair(self, observation: dict[str, Any], worker: int, position: tuple[int, int], pending: PendingRepair) -> list[Any] | None:
        step = int(observation.get('step', 0))
        if step > pending.expires_step or position != pending.position:
            return None
        player = int(observation['player'])
        farm = observation['farms'][player]
        private = observation['private']
        tile = _tile_at(farm, position)
        operation = str(pending.action[0])
        if operation == 'PLANT':
            crop = str(pending.action[1])
            if tile is None and int(private['seeds'].get(crop, 0)) > 0:
                return list(pending.action)
            return None
        if operation in {'BUILD_COOP', 'BUILD_PASTURE'}:
            return list(pending.action) if tile is None else None
        if operation == 'WATER':
            if isinstance(tile, dict) and tile.get('kind') == 'PLANT' and (not tile.get('watered_today', False)):
                return ['WATER']
        return None

    def _terminal_units(self, observation: dict[str, Any], action: AgentAction, episode: EpisodeRecovery) -> AgentAction:
        player = int(observation['player'])
        step = int(observation.get('step', 0))
        farm = observation['farms'][player]
        private = observation['private']
        positions = [tuple(farm['farmer']), *(tuple(position) for position in farm.get('hands', []))]
        planned = [action['farmer'], *action['hands']]
        shed_tiles = _shed_access_tiles(len(farm['tiles']))
        transitions = FINAL_EXECUTABLE_STEP - step + 1
        reserved = {commitment.target for commitment in episode.terminal.values()}
        for worker, position in enumerate(positions):
            commitment = episode.terminal.get(worker)
            if commitment is None and step < TERMINAL_RETURN_STEP:
                commitment = self._find_terminal_commitment(observation, worker, position, reserved)
                if commitment is not None:
                    episode.terminal[worker] = commitment
                    reserved.add(commitment.target)
                    if self._telemetry is not None:
                        self._telemetry.record(guard_type='terminal_commitment', worker=worker, step=step, original=list(planned[worker]), replacement=list(planned[worker]), detail='started')
            if commitment is None:
                continue
            original = list(planned[worker])
            replacement = self._follow_terminal_commitment(observation, worker, position, commitment)
            if replacement is None:
                if self._telemetry is not None:
                    self._telemetry.record(guard_type='terminal_commitment', worker=worker, step=step, original=original, replacement=original, detail='cancelled')
                episode.terminal.pop(worker, None)
                continue
            planned[worker] = replacement
            if self._telemetry is not None:
                self._telemetry.record(guard_type='terminal_commitment', worker=worker, step=step, original=original, replacement=replacement, detail=commitment.phase)
        if step < TERMINAL_RETURN_STEP:
            return {'farmer': planned[0], 'hands': planned[1:], 'market': action['market']}
        for worker, position in enumerate(positions):
            if worker in episode.terminal:
                continue
            inventory = _inventory(private, worker)
            if _sellable_units(inventory) > 0:
                original = list(planned[worker])
                if position in shed_tiles:
                    planned[worker] = ['DROP']
                    if self._telemetry is not None:
                        self._telemetry.record(guard_type='terminal_inventory_route', worker=worker, step=step, original=original, replacement=['DROP'])
                    continue
                target = nearest_position(position, shed_tiles)
                if distance(position, target) + 1 <= transitions:
                    replacement = step_toward(position, target, ['DROP'])
                    planned[worker] = replacement
                    if self._telemetry is not None:
                        self._telemetry.record(guard_type='terminal_inventory_route', worker=worker, step=step, original=original, replacement=replacement)
                    continue
            tile = _tile_at(farm, position)
            if _harvestable(tile):
                return_distance = min((distance(position, target) for target in shed_tiles))
                if return_distance + 2 <= transitions:
                    original = list(planned[worker])
                    planned[worker] = ['HARVEST']
                    if self._telemetry is not None:
                        self._telemetry.record(guard_type='terminal_inventory_route', worker=worker, step=step, original=original, replacement=['HARVEST'])
        return {'farmer': planned[0], 'hands': planned[1:], 'market': action['market']}

    def _find_terminal_commitment(self, observation: dict[str, Any], worker: int, position: tuple[int, int], reserved: set[tuple[int, int]]) -> TerminalCommitment | None:
        step = int(observation.get('step', 0))
        if step < TERMINAL_PLANNING_STEP:
            return None
        player = int(observation['player'])
        farm = observation['farms'][player]
        board_size = len(farm['tiles'])
        future_position = position
        trace: list[tuple[int, list[Any], tuple[int, int]]] = []
        harvest_step = None
        target = None
        for offset in range(FINAL_EXECUTABLE_STEP - step + 1):
            worker_action = self._future_action(observation, worker, offset)
            if not worker_action:
                return None
            operation = str(worker_action[0])
            trace.append((step + offset, worker_action, future_position))
            if operation == 'HARVEST':
                target = future_position
                harvest_step = step + offset
                break
            future_position = _moved(future_position, operation, board_size)
        if target is None or harvest_step is None or target in reserved:
            return None
        tile = _tile_at(farm, target)
        if not (isinstance(tile, dict) and tile.get('kind') == 'PLANT' and (int(tile.get('yield_units', 0)) > 0)):
            return None
        needs_water = False
        for _, worker_action, action_position in trace[:-1]:
            operation = str(worker_action[0])
            if operation in MOVE_ACTIONS or operation in {'PASS', 'DROP'}:
                continue
            if operation == 'WATER' and action_position == target:
                needs_water = not bool(tile.get('watered_today', False))
                continue
            return None
        shed_tiles = _shed_access_tiles(board_size)
        shed = nearest_position(target, shed_tiles)
        baseline_return = distance(target, shed) + 1
        if baseline_return <= FINAL_EXECUTABLE_STEP - harvest_step:
            return None
        required = distance(position, target) + int(needs_water) + 1 + distance(target, shed) + 1
        available = FINAL_EXECUTABLE_STEP - step + 1
        if required > available or required < available - 1:
            return None
        return TerminalCommitment(target=target, shed=shed, needs_water=needs_water)

    def _follow_terminal_commitment(self, observation: dict[str, Any], worker: int, position: tuple[int, int], commitment: TerminalCommitment) -> list[Any] | None:
        player = int(observation['player'])
        farm = observation['farms'][player]
        private = observation['private']
        if commitment.phase == 'target':
            if position != commitment.target:
                return step_toward(position, commitment.target, PASS)
            tile = _tile_at(farm, position)
            if commitment.needs_water:
                if not (isinstance(tile, dict) and tile.get('kind') == 'PLANT' and (not tile.get('watered_today', False))):
                    return None
                commitment.needs_water = False
                return ['WATER']
            if not _harvestable(tile):
                return None
            commitment.phase = 'shed'
            return ['HARVEST']
        inventory = _inventory(private, worker)
        if _sellable_units(inventory) <= 0:
            return None
        if position == commitment.shed:
            return ['DROP']
        return step_toward(position, commitment.shed, ['DROP'])

    def _terminal_market(self, observation: dict[str, Any], action: AgentAction) -> list[list[Any]]:
        projected = _projected_shed(observation, action)
        return [['SELL', product, int(projected.get(product, 0))] for product in SELLABLE_PRODUCTS if int(projected.get(product, 0)) > 0]

def _tile_at(farm: dict[str, Any], position: tuple[int, int]) -> Any:
    x, y = position
    return farm['tiles'][y][x]

def _is_weed(tile: Any) -> bool:
    return isinstance(tile, dict) and tile.get('kind') == 'WEED'

def _is_locked(tile: Any) -> bool:
    return tile == 'LOCKED'

def _repair_has_time(observation: dict[str, Any], operation: str) -> bool:
    day = int(observation.get('day', 0))
    hour = int(observation.get('hour', 0))
    if day >= 29:
        return False
    return hour <= (21 if operation == 'PLANT' else 22)

def _moved(position: tuple[int, int], operation: str, board_size: int) -> tuple[int, int]:
    offsets = {'NORTH': (0, -1), 'SOUTH': (0, 1), 'EAST': (1, 0), 'WEST': (-1, 0)}
    if operation not in offsets:
        return position
    dx, dy = offsets[operation]
    target = (position[0] + dx, position[1] + dy)
    if 0 <= target[0] < board_size and 0 <= target[1] < board_size:
        return target
    return position

def _inventory(private: dict[str, Any], worker: int) -> dict[str, Any]:
    inventories = private.get('inventories', [])
    if worker < len(inventories) and isinstance(inventories[worker], dict):
        return inventories[worker]
    return {}

def _shed_access_tiles(board_size: int) -> tuple[tuple[int, int], ...]:
    half = board_size // 2
    return ((half - 1, half - 1), (half, half - 1), (half - 1, half), (half, half))

def _sellable_units(inventory: dict[str, Any]) -> int:
    return sum((int(inventory.get(product, 0)) for product in SELLABLE_PRODUCTS))

def _harvestable(tile: Any) -> bool:
    return isinstance(tile, dict) and int(tile.get('yield_units', 0)) > 0

def _projected_shed(observation: dict[str, Any], action: AgentAction) -> dict[str, int]:
    player = int(observation['player'])
    farm = observation['farms'][player]
    private = observation['private']
    shed = {str(item): int(quantity) for item, quantity in private.get('shed', {}).items()}
    positions = [tuple(farm['farmer']), *(tuple(position) for position in farm.get('hands', []))]
    actions = [action['farmer'], *action['hands']]
    shed_tiles = set(_shed_access_tiles(len(farm['tiles'])))
    for worker, (position, worker_action) in enumerate(zip(positions, actions, strict=True)):
        if not worker_action:
            continue
        inventory = _inventory(private, worker)
        operation = str(worker_action[0])
        if operation == 'DROP' and position in shed_tiles:
            for item, quantity in inventory.items():
                room = max(0, SHED_CAPACITY - sum(shed.values()))
                deposited = min(max(0, int(quantity)), room)
                if deposited > 0:
                    shed[str(item)] = shed.get(str(item), 0) + deposited
            continue
        if operation != 'PLACE' or len(worker_action) < 2:
            continue
        item = str(worker_action[1])
        tile = _tile_at(farm, position)
        if item in ANIMAL_STRUCTURES and isinstance(tile, dict) and (tile.get('kind') == ANIMAL_STRUCTURES[item]) and (not tile.get('animal')):
            continue
        if position not in shed_tiles:
            continue
        requested = int(worker_action[2]) if len(worker_action) >= 3 else 1
        room = max(0, SHED_CAPACITY - sum(shed.values()))
        deposited = min(max(0, requested), int(inventory.get(item, 0)), room)
        if deposited > 0:
            shed[item] = shed.get(item, 0) + deposited
    return shed

def _shed_inventory(observation: dict[str, Any]) -> dict[str, int]:
    private = observation['private']
    return {str(item): int(quantity) for item, quantity in private.get('shed', {}).items() if int(quantity) > 0}

def _projected_shed_after_market(before: dict[str, int], market: list[list[Any]]) -> dict[str, int]:
    after = dict(before)
    for order in market:
        if len(order) < 3 or str(order[0]) != 'SELL':
            continue
        product = str(order[1])
        sold = int(order[2])
        if sold <= 0:
            continue
        remaining = max(0, after.get(product, 0) - sold)
        if remaining:
            after[product] = remaining
        else:
            after.pop(product, None)
    return after

def build_candidate_a_agent(*, baseline: Baseline, enable_recovery: bool=True, enable_liquidation: bool=True, enable_terminal_commitments: bool=True, telemetry: CandidateATelemetry | None=None) -> Baseline:
    executor = CandidateAExecutor(baseline, telemetry=telemetry)
    return build_residual_agent(CandidateAPolicy(enable_recovery=enable_recovery, enable_liquidation=enable_liquidation, enable_terminal_commitments=enable_terminal_commitments), baseline=baseline, executor=executor)
_DECIDE = build_candidate_a_agent(baseline=calendar)
'Candidate A: guarded recovery and liquidation over the elite calendar.'
from typing import Any

def decide(observation: dict[str, Any]) -> dict[str, Any]:
    return _DECIDE(observation)
candidate_a = decide
'Candidate B: sequential-affordability market residual over Candidate A.\n\nHypothesis: in a real batch of market orders for one turn, Candidate A\nsometimes places a SELL after a money- or shed-consuming order\n(BUY_PRODUCT/BUY_SEED/BUY_ANIMAL/HIRE/BUY_LAND) that it funds. Because the\n1.32.7 engine drains each order to completion before starting the next, a\nsell positioned after a purchase cannot fund it -- moving eligible sells\nearlier can only add cash/shed-room before later orders execute, never take\nany away, so it can only keep every previously-successful order successful\nand, sometimes, rescue one that used to fail.\n\nLive replay of Candidate A\'s real 33-episode captured record found this\npattern almost entirely in WHEAT/FERTILIZER sells trailing an unrelated\nspend (858 + 825 instances), not in premium sells (0 instances) -- so this\nmodule moves any SELL, not just the four premium products the original\ndesign brief singled out. That introduces a same-item overlap with\nBUY_PRODUCT (which only ever targets WHEAT/FERTILIZER) that the premium-only\nscope never had to consider: an exhaustive sweep over quantities and\ninventory levels found no case where every order\'s fulfilled quantity tied\nbut final money still differed -- the engine\'s "quote a buy at post-buy\ninventory" rule (built to make an unchanged-market buy/sell round-trip net\nzero) appears to make same-item reordering money-neutral whenever nothing\'s\nfulfillment changes, same as the cross-item case. That is an empirical\nfinding, not a proof, so `_is_strict_improvement` keeps a same-cost money\ncheck as a free safety net rather than assuming the invariant is airtight.\n\nThis module only ever moves a SELL, never changes what the baseline chose\nto buy -- but real replay still turned up a purchase type where *rescuing*\none is dangerous. Rescuing a HIRE is safe: Candidate A\'s own recovery\nalready re-aligns actions to the live hand count (extra/fewer hands is a\nknown, handled case). Rescuing a BUY_ANIMAL is not: the fixed calendar\nnever schedules care/feed for an animal it didn\'t plan for, and a rescued\nanimal can also fill the one pasture/coop slot the calendar\'s own later,\nalready-planned animal purchase needed. On real replay this cut both ways\nin one batch of games: a rescued HIRE gained +8578 on episode 103977950,\nwhile a rescued SHEEP purchase cost -37129 on episode 103937628 -- same\nmechanism, opposite outcome, because only one of the two purchase types has\na downstream consumer of the state it creates. So `_is_rescue_barrier`\nwalls off BUY_ANIMAL specifically: a sell may still jump HIRE/BUY_PRODUCT/\nBUY_SEED/BUY_LAND, but never crosses a BUY_ANIMAL order. BUY_SEED/BUY_LAND\nare structurally closer to BUY_PRODUCT (inert until something later\nchooses to use them, no ongoing care requirement, no capacity to block) but\nhave not been individually observed rescued in real replay either way.\n\nA prior implementation of this module (order-safe premium re-*sorting* via\npermutation search) was proven mathematically inert -- each product\'s price\ndepends only on that product\'s own running inventory, so permuting SELLs of\n*already-fixed* quantities can never change total revenue -- and was\nremoved after live replay confirmed zero of 264 eligible firings ever\nchanged anything.\n\nSecond residual, added after two live episodes (105061000, 105062726) showed\nthe same calendar turn (record 200: [BUY_PRODUCT WHEAT 16, BUY_LAND]) spend\nits way past the money a same-turn BUY_LAND needed, in both games, at both\nseats. The calendar only ever attempts BUY_LAND twice in the whole 720-step\nscript (records 122 and 200); when the second attempt is starved this way it\nis never retried, and every later scripted PLANT/WATER/HARVEST/BUILD_PASTURE\nthe calendar sends to that still-unowned quadrant reports the tile as the\nliteral string "LOCKED" and executes as a no-op for the rest of the episode\n(471 such no-ops observed in each replay). `_land_priority_ordering` moves a\nstarved BUY_LAND ahead of any HIRE/BUY_PRODUCT/BUY_SEED/BUY_ANIMAL that\nprecedes it in the same turn, but never crosses a SELL in either direction\n(a SELL only ever adds cash before land is evaluated, same reasoning as the\naffordability pass, so its position is left to that pass entirely) and never\nmoves anything if BUY_LAND was not itself starved.\n\nUnlike `_sequential_affordability_ordering`, this is not a strict-dominance\nrule: displacing a HIRE/BUY_PRODUCT/BUY_SEED/BUY_ANIMAL order can and usually\ndoes lower its fulfilled count, sometimes to zero. That is accepted on\npurpose -- an entire quadrant (LAND_PRICES[1] = 2000, ~500 remaining steps of\nextra planting/harvesting surface) is judged to dominate a partial WHEAT\nrestock or an extra hire on the turns actually observed -- rather than\nproven via the same fulfilled-count invariant the sell pass relies on. The\none thing it does inherit from that pass\'s hard-won lesson: it only ever\nreorders purchases against each other, never touches when a SELL reaches the\nshared market, so it cannot reproduce the live-opponent price-timing risk\nthat walled off BUY_ANIMAL rescues and burned the BUY_SEED live gate above.\nIt has been checked against both failing replays and the full offline test\nsuite; it has not yet been run through a fresh live-opponent paired gate the\nway the sell pass was, so treat it with the same "verify before fully\ntrusting at scale" posture that gate was built to enforce.\n\n**`_land_priority_ordering` is DISABLED by default** (opt in with\n`build_candidate_b_agent(enable_land_priority=True)`). The reason is risk,\nnot measured harm, and the distinction matters for anyone reading this later:\n\n- Instrumented measurement over 8 complete games (5752 decisions, 3408\n  non-empty market batches) found `_land_priority_ordering` changed the\n  order 3 times and `_sequential_affordability_ordering` changed it 8\n  times. The entire market layer alters roughly 1.4 decisions per game, so\n  neither rule can account for a large live rating gap in either direction.\n- The seeds 300-309 six-family gate scores 108-12 both with the rule\n  (section 8\'s original A+B gate) and without it (the later no-land run),\n  against the same 107-13 Candidate A control. That is a null result for\n  this rule, not evidence against it.\n\nSo it is switched off because it is the one residual in this module that was\nnever justified by the fulfilled-count invariant -- it deliberately sacrifices\nanother purchase -- and a rule that fires ~0.4 times per game with no measured\nbenefit is not worth an unproven tail risk. Do not describe turning it off as\n"fixing" a live regression: the measurements above cannot support that claim.\n'
import math
from typing import Any
MAX_MARKET_ORDERS = 10
TERMINAL_MARKET_STEP = 717
MARKET_I0 = 10000
PRICE_FLOOR = 1
HINGE_GAIN = 8.0
MARKET_PARAMS = {'WHEAT': (25, 400, 'sqrt', 0.8, 'log', 0.2), 'CARROT': (35, 450, 'hinge', 1.0, 'sqrt', 0.7), 'TOMATO': (60, 200, 'hinge', 0.4, 'sqrt', 0.6), 'STRAWBERRY': (120, 100, 'sqrt', 0.7, 'linear', 1.6), 'MELON': (250, 300, 'log', 0.2, 'sq', 3.6), 'EGG': (50, 332, 'hinge', 0.4, 'log', 0.2), 'MILK': (160, 122, 'sqrt', 0.6, 'linear', 1.6), 'WOOL': (200, 105, 'log', 0.2, 'sq', 3.2), 'FERTILIZER': (100, 200, 'linear', 0.4, 'linear', 0.4)}
SEED_COST = {'WHEAT': 10, 'CARROT': 20, 'TOMATO': 50, 'STRAWBERRY': 100, 'MELON': 80}
ANIMAL_COST = {'GOOSE': 300, 'COW': 400, 'SHEEP': 500}
LAND_PRICES = (1000, 2000, 4000)
FARM_HAND_COST_MULT = 1
SHED_CAPACITY = 100

def _shape(function: str, value: float, scale: int) -> float:
    value = max(0.0, value)
    if function == 'linear':
        return value
    if function == 'sq':
        return value * value
    if function == 'sqrt':
        return math.sqrt(value)
    if function == 'log':
        return math.log(1.0 + value)
    if function == 'hinge':
        if not scale or scale <= 0:
            return value
        unit = value / scale
        return unit + HINGE_GAIN * max(0.0, unit - 1.0) ** 2
    return value

def _market_price(product: str, inventory: int) -> int:
    base, scale, below_function, below_target, above_function, above_target = MARKET_PARAMS[product]
    if inventory < MARKET_I0:
        function = below_function
        target = below_target
        distance = MARKET_I0 - inventory
    else:
        function = above_function
        target = above_target
        distance = inventory - MARKET_I0
    amplitude = target * base / _shape(function, scale, scale)
    signed_change = (1 if inventory < MARKET_I0 else -1) * amplitude
    return max(PRICE_FLOOR, int(round(base + signed_change * _shape(function, distance, scale))))

def _fib(n: int) -> int:
    a, b = (1, 1)
    for _ in range(n):
        a, b = (b, a + b)
    return a

def _hire_cost(hires_already_today: int) -> int:
    return FARM_HAND_COST_MULT * _fib(hires_already_today)

def _next_land_cost(unlocked_quadrant_count: int) -> int | None:
    extra = unlocked_quadrant_count - 1
    if extra < 0 or extra >= len(LAND_PRICES):
        return None
    return LAND_PRICES[extra]

def _is_sell_order(order: list[Any]) -> bool:
    return len(order) >= 3 and str(order[0]) == 'SELL' and (int(order[2]) > 0)
_RESCUE_ELIGIBLE_OPS = {'HIRE', 'BUY_PRODUCT'}

def _is_rescue_barrier(order: list[Any]) -> bool:
    """True for a spend a sell must never be moved across.

    Only HIRE and BUY_PRODUCT are trusted rescue targets; everything else
    (BUY_ANIMAL, BUY_SEED, BUY_LAND) is walled off. Captured-replay testing
    (no live opponent, opponent actions fixed regardless of our timing)
    made BUY_ANIMAL look uniquely dangerous: rescuing a SHEEP purchase cost
    -37129 relative to Candidate A on episode 103937628, because the fixed
    calendar never schedules care for an animal it didn't plan for and the
    rescue can fill the pasture/coop slot its own later purchase needed.
    But a live paired-game gate against a mirror-match opponent (which
    *does* react to shared market state, unlike a replay) showed the same
    "sell wheat before buying seed/hire" calendar turn cost -15302 and
    flipped a win to a loss via a BUY_SEED rescue alone, with BUY_ANIMAL
    already walled off -- proving the risk isn't animal-specific. It's
    shared-market timing: reordering our own trades shifts the price the
    opponent's own concurrent trades land on, an effect the isolated
    single-player safety simulation in `_simulate_orders` cannot see by
    construction. HIRE (Candidate A's own recovery already re-aligns to the
    live hand count) and BUY_PRODUCT have only shown benefit so far, in
    both replay and live-opponent testing (episode 103977950: +8578 replay;
    seed 305 vs distilled-calendar: improved margin live) -- but that is
    two spend types' worth of evidence, not proof the risk can never touch
    them too. Widen this set only against new, separately-gated evidence.
    """
    return len(order) >= 1 and str(order[0]) not in _RESCUE_ELIGIBLE_OPS and (str(order[0]) != 'SELL')

def _has_reorder_opportunity(orders: list[list[Any]]) -> bool:
    """True if a sell sits after some other, non-barrier order."""
    seen_other = False
    for order in orders:
        if _is_rescue_barrier(order):
            seen_other = False
        elif _is_sell_order(order):
            if seen_other:
                return True
        else:
            seen_other = True
    return False

def _stable_partition_sells_first(tagged_orders: list[tuple[int, list[Any]]]) -> list[tuple[int, list[Any]]]:
    """Sells-first within each run, never crossing a rescue barrier."""
    result: list[tuple[int, list[Any]]] = []
    run: list[tuple[int, list[Any]]] = []
    for item in tagged_orders:
        if _is_rescue_barrier(item[1]):
            sells = [entry for entry in run if _is_sell_order(entry[1])]
            rest = [entry for entry in run if not _is_sell_order(entry[1])]
            result.extend(sells)
            result.extend(rest)
            result.append(item)
            run = []
        else:
            run.append(item)
    sells = [entry for entry in run if _is_sell_order(entry[1])]
    rest = [entry for entry in run if not _is_sell_order(entry[1])]
    result.extend(sells)
    result.extend(rest)
    return result

def _simulate_orders(*, money: float, shed: dict[str, int], market_inventory: dict[str, int], hires_today: int, unlocked_quadrant_count: int, tagged_orders: list[tuple[int, list[Any]]]) -> tuple[float, dict[int, int]]:
    """Replay one player's own order queue in isolation.

    Mirrors the 1.32.7 engine's per-order-then-per-unit commit loop for a
    single player's queue. Ignores simultaneous opponent trading on the same
    product at the same queue position -- an approximation already relied on
    elsewhere in this module for premium pricing -- but since both the
    baseline and candidate orderings are replayed under the identical
    approximation, the comparison between them stays valid.
    """
    shed = dict(shed)
    market_inventory = dict(market_inventory)
    fulfilled: dict[int, int] = {}
    for tag, order in tagged_orders:
        fulfilled[tag] = 0
        if not order:
            continue
        op = str(order[0])
        if op in ('SELL', 'BUY_PRODUCT', 'BUY_SEED', 'BUY_ANIMAL'):
            if len(order) < 3:
                continue
            item = str(order[1])
            try:
                requested = int(order[2])
            except (TypeError, ValueError):
                continue
            if requested <= 0:
                continue
            if op == 'SELL':
                if item not in market_inventory:
                    continue
                for _ in range(requested):
                    if shed.get(item, 0) <= 0:
                        break
                    price = _market_price(item, market_inventory[item])
                    shed[item] -= 1
                    money += price
                    if price > 1:
                        market_inventory[item] += 1
                    fulfilled[tag] += 1
            elif op == 'BUY_PRODUCT':
                if item not in ('WHEAT', 'FERTILIZER') or item not in market_inventory:
                    continue
                for _ in range(requested):
                    price = _market_price(item, market_inventory[item] - 1)
                    if money < price or sum(shed.values()) >= SHED_CAPACITY:
                        break
                    money -= price
                    shed[item] = shed.get(item, 0) + 1
                    market_inventory[item] -= 1
                    fulfilled[tag] += 1
            elif op == 'BUY_SEED':
                if item not in SEED_COST:
                    continue
                price = SEED_COST[item]
                for _ in range(requested):
                    if money < price:
                        break
                    money -= price
                    fulfilled[tag] += 1
            elif op == 'BUY_ANIMAL':
                if item not in ANIMAL_COST:
                    continue
                price = ANIMAL_COST[item]
                for _ in range(requested):
                    if money < price or sum(shed.values()) >= SHED_CAPACITY:
                        break
                    money -= price
                    shed[item] = shed.get(item, 0) + 1
                    fulfilled[tag] += 1
        elif op == 'HIRE':
            cost = _hire_cost(hires_today)
            if money >= cost:
                money -= cost
                hires_today += 1
                fulfilled[tag] = 1
        elif op == 'BUY_LAND':
            cost = _next_land_cost(unlocked_quadrant_count)
            if cost is not None and money >= cost:
                money -= cost
                unlocked_quadrant_count += 1
                fulfilled[tag] = 1
    return (money, fulfilled)

def _is_strict_improvement(baseline: tuple[float, dict[int, int]], candidate: tuple[float, dict[int, int]]) -> bool:
    """True if no order lost fulfillment, and something measurably improved.

    Never reject on final money alone: a rescued purchase spends money that
    a failed purchase would have left idle, so a rescued order's fulfilled
    count rising is itself the win, regardless of leftover cash. When every
    fulfilled count ties instead, fall back to requiring strictly more
    money -- not because a same-item sell/BUY_PRODUCT overlap is known to
    produce a money difference on a fulfilled tie (see module docstring: an
    exhaustive sweep found none), but because there is no proof it never
    can, and this check is free insurance if it ever does.
    """
    baseline_money, baseline_fulfilled = baseline
    candidate_money, candidate_fulfilled = candidate
    if any((candidate_fulfilled[tag] < count for tag, count in baseline_fulfilled.items())):
        return False
    if any((candidate_fulfilled[tag] > count for tag, count in baseline_fulfilled.items())):
        return True
    return candidate_money > baseline_money

def _sequential_affordability_ordering(observation: dict[str, Any], market_orders: list[list[Any]]) -> list[list[Any]]:
    """Move sells ahead of spends they could otherwise fund.

    Never invents, drops, or resizes an order -- only reorders the exact
    batch the baseline already chose -- and only takes effect when a local
    replay proves the reordered batch strictly dominates the baseline batch
    (never a smaller fulfilled quantity on any order, never less cash when
    every order's fulfilled quantity ties).
    """
    if int(observation.get('step', 0)) >= TERMINAL_MARKET_STEP:
        return market_orders
    if not market_orders or len(market_orders) > MAX_MARKET_ORDERS:
        return market_orders
    if not _has_reorder_opportunity(market_orders):
        return market_orders
    tagged = list(enumerate(market_orders))
    candidate_tagged = _stable_partition_sells_first(tagged)
    candidate_orders = [order for _, order in candidate_tagged]
    if candidate_orders == market_orders:
        return market_orders
    market = observation.get('market', {})
    market_inventory = {str(item): int(quantity) for item, quantity in market.get('inventory', {}).items()}
    if not market_inventory:
        return market_orders
    private = observation.get('private', {})
    shed = {str(item): int(quantity) for item, quantity in private.get('shed', {}).items()}
    player = int(observation.get('player', 0))
    farms = observation.get('farms')
    if not farms or player >= len(farms):
        return market_orders
    farm = farms[player]
    money = float(farm.get('money', 0))
    hires_today = int(farm.get('hires_today', 0))
    unlocked_quadrant_count = len(farm.get('unlocked_quadrants', []))
    baseline_outcome = _simulate_orders(money=money, shed=shed, market_inventory=market_inventory, hires_today=hires_today, unlocked_quadrant_count=unlocked_quadrant_count, tagged_orders=tagged)
    candidate_outcome = _simulate_orders(money=money, shed=shed, market_inventory=market_inventory, hires_today=hires_today, unlocked_quadrant_count=unlocked_quadrant_count, tagged_orders=candidate_tagged)
    if _is_strict_improvement(baseline_outcome, candidate_outcome):
        return candidate_orders
    return market_orders
_LAND_PRIORITY_DISPLACERS = {'BUY_PRODUCT', 'BUY_SEED', 'HIRE', 'BUY_ANIMAL'}

def _is_land_order(order: list[Any]) -> bool:
    return len(order) >= 1 and str(order[0]) == 'BUY_LAND'

def _land_first_ordering(tagged_orders: list[tuple[int, list[Any]]]) -> list[tuple[int, list[Any]]]:
    """Walk each BUY_LAND order back past adjacent non-SELL spends.

    Stops the moment it hits a SELL, another BUY_LAND, or the start of the
    batch -- so this never changes a SELL's position (that stays entirely
    the affordability pass's decision) and never reorders two BUY_LAND
    orders relative to each other.
    """
    result = list(tagged_orders)
    for index in range(len(result)):
        if not _is_land_order(result[index][1]):
            continue
        insert_at = index
        while insert_at > 0 and str(result[insert_at - 1][1][0]) in _LAND_PRIORITY_DISPLACERS:
            insert_at -= 1
        if insert_at != index:
            item = result.pop(index)
            result.insert(insert_at, item)
    return result

def _land_priority_ordering(observation: dict[str, Any], market_orders: list[list[Any]]) -> list[list[Any]]:
    """Rescue a BUY_LAND a preceding same-turn spend would otherwise starve.

    Only fires when reordering flips at least one BUY_LAND order from
    failing (fulfilled 0) to succeeding (fulfilled 1) in local simulation;
    see the module docstring for why this trades a purchase's fulfilled
    count away on purpose rather than requiring it never drop.
    """
    if int(observation.get('step', 0)) >= TERMINAL_MARKET_STEP:
        return market_orders
    if not market_orders or len(market_orders) > MAX_MARKET_ORDERS:
        return market_orders
    if not any((_is_land_order(order) for order in market_orders)):
        return market_orders
    tagged = list(enumerate(market_orders))
    candidate_tagged = _land_first_ordering(tagged)
    candidate_orders = [order for _, order in candidate_tagged]
    if candidate_orders == market_orders:
        return market_orders
    market = observation.get('market', {})
    market_inventory = {str(item): int(quantity) for item, quantity in market.get('inventory', {}).items()}
    if not market_inventory:
        return market_orders
    private = observation.get('private', {})
    shed = {str(item): int(quantity) for item, quantity in private.get('shed', {}).items()}
    player = int(observation.get('player', 0))
    farms = observation.get('farms')
    if not farms or player >= len(farms):
        return market_orders
    farm = farms[player]
    money = float(farm.get('money', 0))
    hires_today = int(farm.get('hires_today', 0))
    unlocked_quadrant_count = len(farm.get('unlocked_quadrants', []))
    baseline_outcome = _simulate_orders(money=money, shed=shed, market_inventory=market_inventory, hires_today=hires_today, unlocked_quadrant_count=unlocked_quadrant_count, tagged_orders=tagged)
    candidate_outcome = _simulate_orders(money=money, shed=shed, market_inventory=market_inventory, hires_today=hires_today, unlocked_quadrant_count=unlocked_quadrant_count, tagged_orders=candidate_tagged)
    land_tags = [tag for tag, order in tagged if _is_land_order(order)]
    baseline_fulfilled = baseline_outcome[1]
    candidate_fulfilled = candidate_outcome[1]
    rescued = any((baseline_fulfilled.get(tag, 0) == 0 and candidate_fulfilled.get(tag, 0) == 1 for tag in land_tags))
    return candidate_orders if rescued else market_orders

def build_candidate_b_agent(*, baseline: Baseline=candidate_a, enable_land_priority: bool=False) -> Baseline:
    """Create Candidate A plus the market-timing residuals."""

    def decide(observation: dict[str, Any]) -> AgentAction:
        action = clone_action(baseline(observation))
        market = _sequential_affordability_ordering(observation, action['market'])
        action['market'] = _land_priority_ordering(observation, market) if enable_land_priority else market
        return action
    return decide
'Behavior clone of an elite cow/sheep-pasture strategy ("fog flower").\n\nSource: episode 105144807, player 1 ("fog flower", public leaderboard\nscore 2882.6 at capture time), which beat "Giulio Ravasio" (leaderboard\nrank #2, 2965.4) 71471-69193. Unlike the two rejected clones in\n`experimental_distilled_pasture_agent.py` (sourced from this project\'s own\nmatch history, where opponents are matched near this project\'s own rating\nby Kaggle\'s ladder), this source was pulled directly from the leaderboard\nvia the Kaggle API and is a genuinely elite, top-tier result -- a much\nstronger candidate than anything sourced from this project\'s own games.\nSee rl/GOAL.md section 9c.\n\nSame method as `experimental_distilled_calendar_agent.py`: a fixed,\nopen-loop, per-step lookup into the exact recorded action sequence.\n'
import base64
import json
import zlib
from pathlib import Path
from typing import Any
MODEL_PAYLOAD: str | None = 'eNrtXdtuHFly/JWBnudBfeHNbxyp1xKWMxQoyo31gBgM4DUMGOuHsd8M/7tJUd1VXRWZEZHnFKk1/KQW+1LnfjIjIyN//e83//r7H3/76x9v/uGHX998uv78+c3Djz+8+bff/+Nf/vPpT0//+dvvf/z7X//r6//+58cfrC/8+uanL3/57dPd7fsv7+7fPL61/7C7fnqx2jzMfuyX27v7D/mvfd7d3Ix/5vLxA8/P+LzbvR+/czF75+fdze0vT49ef33rw8e73Rvr1dOPXf/y8efrr014d7t//GcN3vn8Ybf79PW9WRf3u8/3pz18HMOP7/785dPhJ7/+3uFjozEZ/3HyDTZIK60do0cND3juy7Qpo5c/ffl48/63x3Vw/+VpnNTpnzfp0831L/fDPE0aN3nMaSOff3XaMtiJx6e82xkjd5hdrQ/76/vd3Wx+Tx4ZTi/szrtrNKjNzQSz//wkMKM/wrkZd+L5Ve9G5uthtBkOwzua5eM8gA30InM+euqfno6fyYiBIV6mcbtrcN6AyRxmPx/Y6Xdfor3ZZE4G+PmTvRt1GBy8/mCbpuPZfXPM7l08r+Pz5fD26Hg5mexkYqUTZDRP8LzA04imTFsWw/kDf3n+0rZlSmOKvjL93KKjO3/Za3QPHzxZOF9HrWVoR2M3PCAd2fHflMd3G8/n9lU6++1vwXAOb9eHc/IT+YB1f9R4OBfqTPiKPWBuWMUOhuILaOtrN98ryILXTgTgGgUWI7yYtAPwcJGOnzFcrvhofX6f/DC6QFN7c/QAZAHPH3B7c7N7d//bn3Z39x9vPv7z3CDDnyA2GfpS4Sw9GlLxw4cl/fn2y3yqBoNh9BPEagAO9rffFiyZ4yeD1rc3bwstfjRO0jQOx8+o6bntpbd1rRlgw5KuuHXSI0Y38OiCar+M39/dfppeSsPW73COj0ek5/2w1L2DtuZ33Ny/t+FdyPT5/+Y2mkoL/ezkDHw6/RWUF5zQDlY7hYTPHiSTJ7fc0J1iIga6iTYHCsBVxI0fCFHY5iG0QdlPax4omobUlddbjaZi3r6S38wHHjp7BJGUvAtsB7gdyFc/nNoeyx+3WPphPuKk+dK4QDt5bFci2+vD9d0/KX1Agz5MJ5xYEz5Cw49bf2xzz0U/etSpGzHDIrQdTDDhlg2API7p5RSspGGigokPrrFtGEpEMO80NEibVV818HjHu9ZcMviXCaqvQW2T0BptOvGzpa2UG0TiwnspQ2vTjHaV7CofETOvGNVwky8xzdTy7Tr36nSMOfxy1ox+27PFENONDXig16092pWTW1B8jnML4g7BeFw9XhNd6ugUVE0VciUkPSBxsspSgYOYjnJhrWArPRhb8QqhSwXafMR0ajBkibE5b0Ovh0C4qsVQ28RHI3oq8TYCg23jGGxCIOIIEo9mOFt2hZGRDHK8dZDZFQIyZqAncAwmKFspEjY16378AfLqzGfx2Rx+cEDQ5ahO2dqsP8GIHE84a9Oe2pboWRdLFNuf03ceB/LuNgiCvTLkt6Q9mBig1R0NtxsMdNFHjifo8/3d9f6n3d3dX/Bj0SSNtrZhh5btethJ3yA1bn94fWmPIXzeYJp6YLPYclAtzHzgkbVVwcMM1BDZWiToXDGPoFk+W3F1MjXZP8PymlsB3cDF0V9DiMwgYRqW1QmNDFMv8iWkn4850JFYoX3nFhtAXc0P/Yf7TmuXrkFaTv7DzfOUP3OwF12MD7pCZ81gIsWrYa+nltfJxb55eD3g82yZCDOyP7et+CczhrUjAAbZF7NtITFQ7+LcKEtXUuOF0AcohWkzgW3Q54kl28t9SGV2+5vB2NwGN2k9aCiQB3vT6COUGUHOftQrHs0Rd+9g6Iz2U/4G6zhlUKo7mPiWaRxAPrvwQ4KVgF1Ml6VgRFJhvzSTBj4F2vgoyi8vNpjeNku5ShdUgWWQZyhifyNe0LtqP4UTo2GdoAODgPMznmcjkyWzfPX0mjTrFViT+Kkpi5lap/DQWbsGKLLK3eFYPKFlvjna4/qqrbuOsdZOFwDJaoELBlr/88+WvACnQ6OTLjfNN0KvYN5Q2iNt+6OEZPR85XPk+cF4wGxj0AKcUOE1wTEE4VPGuUiF76m23P729mktrt6qyUN4SBKWltC8kV82ak4tZYYczIe3Hy/t94q8xugZDJMjhji6YlHWS/y5ekYRa3pK+ENNg/1CSGi/PmRZUVmqZYDQzqO0o47wDZf3q80dQK2E2cpwPohb50CJs9zEYGmDHEbwJ8jNiOm5hcMsXbynvKBJmBmLjwTpkxmxa5EESoTHDIs6dEDQxhWSQjMhlvEjurI1uMeTZu4y3QALVF/XgVXoRxUycKQGYH8U8d+wayowAzsoSKhCNISYbeNi2LNGMA85UPcoFqyBGAZyC2LBDdCZ9jvipKKBhMs7Ea/IAKE6NjNLupY5eI5tcjgXrsTU9pg1KM5PQlhsmNjghF6remLHVkXzCIfbmnT9ErHUNSbexXoRiIJgQna0Dpt0mviGAsyI1NK9ACzELWOoSuE7HfI0oExaJjSyZPByuJKGt4dXSXyqY+xr9Lzgeho+O3rF3aTuWMmJ2Yst2fCrwd8VqMMA8rphB9wfTZ1YxvP2HJZKNDAcWEYJC7/Y3JFN69FHxGoG3jL3s7I0iJ68MOT4xtuKYDxdsrwIdYM0gZnBFXMWy9pk24vG4rowaPc7cTbCQanzV9lAqUTfVoKDnugz24X6SIqzRYYEYaGmDV/PpM4FG7ytBNc5wVNaFhB5Hh7DsiwicfOhK5kDleUILeNSZcMvRImN+zwdJ40N218SCnqXIxtw+Fts3L2UFiV6BfEm8/mGPn2DclGTc9sSkz4LYulbM5JU6R7rBAlkM+cxle0oRJGOF9zPH2/+/PjveejQMQ5qdBvMfp7ekcPi+/atWZ2DMM4hhmrnlrpV+4CpgBGLD0KMEKGTYGQxBLERWSswxDMpQHAYS0YzYNHEMvACFyN8Wrd2OQPrxKPmJqbej17KYk5qJoBLcL0CDJVTvqEVV2tZ1EF2XuKYpjh0+1KuOmEkcdF3cJda6nTyCU6rO+zLpLUGpOqdqkKhK085M5ADfafO33y/7uzosqlsparEQbs2xso9afvWFZ1JTIRXei6uV0pwoYtVT3eBMWjh4DGnH9q7JGZOojnMq5XVURJ2Bjyp1eBEtLHYKlpMnHInQ4x0QDtJK2YB7YQiG4u7BzusJkfvK84zu4eHwxhtxtXlkwQhBepIDtPQVJZapm5hRY1ka8hcmFU/OmYzlIL8rcwCmoMrJS8cNqeTnBshM35yLc1rmPvtq15B0zyPAL2bm1K9ajmIpiAK/KNmjfw6VG6wnHINQ/E04A9bSMnNlppO27C2hP7bXlbheDmZgNFWaGjOFUmxVzLM2pQxioyIWSLd5xjpmHBMKSiWCFEzLOLyWlgkDf7RprjCGB8hsWGfkXnh05ylS5ZFdKnBz+g2UsMZo+HSlzkJ5auhgInVya6RiIhZlidodd0JQduJ6OW5VSiMuWTWDhajYis9b1vzwFJgDGVaQKKW69wEWwflvgU7x1qhZqJmvpEyz5dvLZzxnijTVv1dMuO1raQv2AYeDyP7wifniYamI0joRci55iPLRqzeMsLmO3p+yFnGO18duZRSKaB0tDvAlc8T144uamG0g96cPbhSJGWAYhkqSIxa9IQlulYllQoYSEFfnudwGhLPAIdNQ8JGoW8LwS+bzAY+65OT4rxEqIxdmariczgvMWsrmKBm0dTAPqJxeIdpG91TJ5bLDDQogEWx3BjuRPz5XKtMEK41Y69IN5Y5x1zDoU3EV24xcz7gRwnpXxVTJgYU1wajhQIofPdcQf3AWJvOQ0hYO/lWtGG39KY4S7Jjxs8IqLW4E3KOzOnXgj/HkhJzb4bE3g4/vN6aVwuOXOD24k3Hu59D/RydFvu+WtuBGQxp8snPDSaUwsck/cwNcFbm9sa5q6PBUOX1NUT2RIByOrJ8GBpKl8PO487lleeFcy+J/ohmiD6pU9GGd7eg4AjdxLnSPc6LpUmPJMu9Pq2E06kIZYSIRaKm1H3uUhEeKuRlYXHJQWSS2r/yx+EVMTo1hm4gtRrCvsUJW7RjFv1dBRdQckmq2zMahHxFRuxS5zqcDG4hUYYQBblkBKyMQQDqyVhV8o4A6ofSjuQpiEYYhUmfXzEenKpyLyRAFWEsqAlwXVwoZcgsbJ0rA9CHNQRMxVjKcBMmXK1WZcXTq6VQPO5EqMBWT+HYTM2xiV5E41YCw11R4KIQIKb8ImO6l8aiTVynWNRwusGQqDVOUuyWEGhydhi8YDDvQ2yfM9QszS/iztDcExoHnH6XE76MEl8zU+lchJ8trkLYl1SlIUliDq3PhgC9XDYNRkKreylDuNtkKqyNLKxZRrGigldtcwEdN2WNKTKWdEsl0nptgRGh/ARLOVHEJTONlM6UOOjJKSchKXMMqQ8N1XJJaQ5ayA62BzGE9WS+5WYiz1CCbhzvQP79PhOSn6aeX0f0Qmgt8fZzjYivyFldJMFPpsO1ssQUFXyuhJxeQ3ht+uVFYWKCVKE+3OKFAqEsCbYp9sgoNwoxCp1/OqGqVP80F/1FvKO9Ugk2iqaqC4ZJ7CaVeIQFRW4zt9CMvrphY8ldxjf8dL4Ksr2kmjsbb4gOli6uWZpeqeaRCt1V0urc1VGkqF29NkVNFyY6swGcPMXMyXVdbQuBO5JmLqfClSkrPB1hl3FSytlsJJ1dMF0cM0edWlqMR837RSjF6CcsThyVuJjl1thSn6SODEtZczOTgm2B1uJ8366l7J0gub1unzhr00uQSAk1xXJafFmyORWIdmYCfQCZotOOhSbFKD/6G+PdWPgnarHE56Qo2sxPWHrNOl4My1R0lJLVGge8ByxXKU+pcUt17tWUQ3Rt9gaxSB6Esw5gcrusCWOWbc0Dvg14TnR6NdSa5QhtVIZDrehjj22OKcM8mPhEDMfdhYuIcBziahACCkaHG3ShnRUIw4yMliVejYiVQxvkbY6UiFEuroNaTvLFkGcucVz6M1aWygHDTqarDXwRMk+uvi//u0+uVJWIUq5wJjO4cz9cO36MerfQemAiXUmiSMfSLhi2ZiodBcWZNuYIjtcIVqzDdO9yCWYBc4nsmxm7bdorJLwUabzmgHFToMnSC8zjMhGVVRZqacwLx012AjJaWdZGsIMs1ARPUzRkOguqR6mMkItjVwTxgQJT5Sr3XQizzUOaNCjB0cGVIQMh3zTLeiho42JoHV5kxCvSvJOCyCgJ9DOVD7SA3ZETStHx0xez1/KcHdnxKqxWquldFlZCTkyPJZrHKoI7l0iKSsdsviyZMBi5YlFk+eUWKNP6wgy1NKdETJvKnWNsNAk2jkPmIMPcw8lnRzfBA9Cr+vhyiboW719EIo5ebKIV/N1F3KE7EACYWZrJmVKm21TqgADJVV7EhkYXEMIBy+swz4vlWFDNDGpbxulJbcgN9ncDkzoShJgO2mb2ARC7JV3e2LCO69ARhwVlTs9LLvWJHuY6wlGKdj7mCPDKkxbjkT+OnXzj5ljWlAlxHuMNkH8M8hdn5IdzMZxIisWetDCfp72x5tAn/A5VsCVvP+w6yM/GqwcfM6woDA4CwW6jBd8WZSYeIkxZI/qI+cJ2oU8DoY3UlHosX3eteqJCofjw3AnZhRpH7ctWqBOl54n5ZYmddZtXyZGISMF27aHrRdxH6B5b/nwClnbD75lvGXGqjOSSyiItx0LIzspQ1Z4rN5ENVkrtJG5+G7Enr4ojFEx2ENJCUwlLLuf6szieTKhzaRikmDBTiMmQ0gLwgcl0Rokfb1ETee8e2QdNEh5yb+zLoKfYhF85ebV6UDGcM5sSkeiPHT4sXM4JcLJmnsMqHQwDMSEpsrCnQOk2x7gDAco0SC/BRb4DBbHa0bnqzD3X1ewStA8iBESDkGYpGMS72fLbWOiVjTVYQSV4k0TrbDoU61r/101IxMl4SH2ExwbtFs9r5t3K84qC/Bdk5lN/lm8sLUVm+1Dy+/wdhtue22j14j4WyGPtFQyMvf/4jzydwce38uJxY1zT3SOyUatKgVQLFzDWTY4Z6EWTI9qFGrN23Mx8UxApg2A7L7AXxgN6sn74hghuWVecoo3REE2phOXp2hdNKgvhwsnHR8wr8lWI483OvMOLhwZXFm5ePX5Yz/S1HFhG5GGYUh4UaQNdyflVEZMMNvHJn2EN3C5CTyy0Qcqz80LNsq5Fih1FtrHOqZSv2nxHmoFUQkiGzafmmm7TfIulXjw0pfpYATweTaOnppYSKyoky/k2Vu4f+dXqxfq6+NOla/oGrnvOqbFhqRDEiRbIicTtZS/UKR8K2Mi0W8w/i5QGiIXtVKF+6yszwOx4K4iTF8GZXSi1FA2SipGUHkqz/7O4XwUws9IvqpRNjliRQVfgCl6ZihX5ohQ/tZ5Vaykq2Do5H2n86sSdMwVposIpuZvCE4lJ1p4oBNGoqObBh17ouIJHElPjsqSkFIFBjG0iQEt7Zl43Ij/MZ0R12MeX7ja2G7UkEulq31ZqbyNUqEhGy5HYsvS451YyZo+J1Mvwe+xaBHMQ+LkwaC6U+YtjE0ZkJK5AuxfPXrI95DxJti1a3OgQlDM2ACMYxcXUC8VJ8sqiNXycYXkex0+kxsm1OtPAppL+xVAkNbv15ICd1VdinFddJ0DO2SJgwLS9DXNgGEF5OqytmsYkpiUo3cQXHSq2nbLLdL9ZgutOZGTS4hLzRIUDGWVL6Sol84JFLBjjipfnTbMOTtMwVH2z3feFQ121JROhNY5r2Mf5cXVZmJmrnJR461AkXSZnCclwGGDw3NYcxieBYrqJKZRmtpawmAjuxRn2uUnoqPmuH1rVSXQLjl6PqrskVpeysTIL/qKRFS8OSbqWxGmpymwQ/Iv/Qx0fr9qvphyCQVQiZklipkRptQFhlWtOROdIMCmmviqFab5d3BXN7iBnaQ7RnHClJmunKLfqB1AB4Sq8ITc2VTaCCCwb11C4atORIkQGfAARnk+sit5Rf42Lbp0MXHRK8U1k6x+tS0Y7SfqkfrirMqQeBxuX3GqsZ4iJckKrSY/Ir5B9CgjG1DgEGvaguhUTbSgPKddIytL0Kg0WiBdw8aM5cNGGPuL2wG8/AXrOFXIP8XYifIXuzUlLXC4tPL9ZsntEyofVv539GQB/b00JJvqSBFWJMmOE971tzJVDVZyQ9hIWuHNirYuV7GGA0kAd5IMwfDYvlxTfTq7i8KurDSEZNBxS20mwkVAfJADtHXAJCvKcIE4cdYuoT1u7CK1+r8z7uG2GeJwwBwMW2EWepwzCswH/5Fw3p53nlDOgmSfD6VyQm4b96q5WCxMgjCVMFCp7S4EgqusIzemGyr9BOWdgG/dxLAJOlpQXSDBqonvoafKOoASqEosnjec+8w1Cr4i1kdd43jRD1OWDqKCiYXzKQyoz7gSFusmzuAyxRyWzU57p8FNANBBFcjKKg7O7MCvI8pGlcNL0OHvjRIEUbV6QZGy0fgnSQdI1SOJItul7icuy5ONs0zjBf7jOZJ4wpZnvGUGMHtiqUUYqW/SpAU6gHkLZt3BqfOFW2u9JoJMaoQaPu3487XdMkyPkyeILQxb0oaDQwVsB1zY6n2ReIPIZ5lCNWuWPbvZI2VsM6VB0xjrgmCEdyUpk1KK8HIddrYI7BlyNZu1b/5bflg1jgc0RLMOtckAjzDsv9WeUEomW4Vbbkghno4uxwZejHmMnDatXh9hECSsCWljZgT6FqEDtOu8PtBFlKyWzXQgR51hag0XBti2MV2QSXThWrMhUNwKBTIOAxePdsFm9J6FUQVmcgvWNVgVXs6u4l0D0qQS1WxrFz7cFc0ar9ZdYRFJx8yM+EhF91XgUjvw6vPTh1m0u2+QiCPW6tYI3WmfHJFJv7TYpWW9TlAqJoeWiQnpQwaG8xLnFVrgAUUNivFpN926hwIT7Bu+GIIDIsVmLqyshfSVpmWCV8/gHlizeWTrFidZxK7rrLSwMyQrAoxkCERaXrIPG6BpIcjQ32hrWkUVGSiXhlTSvnbhsZvekqtYMF7dZ7sBSi1AVAzuo7+GgSiSIuVNFxqQoo5ZjqlZhQaVXQGJ77kBFJ6Ben6MtBx6pIJH8dZp6nSvvj38o4GnWa6dnDEBHjorU1yzeno6Fw4iDuXyVo+uejpkFZCGGXGKwLtP1oMYBGhHIgeM1EmxK/98d0Y14BQlIJ8FwFNBZl4G4ubB8V8xNZgCKHSMuk1pjFeOahVA4o/wbOtH5hWHmXvJQUBzXQyatULyLXxLl3iiiJ1b5lTCkH7nyDrS4hEicQWF3JHQlymWFJ3uuHQUZJcmJfxPIsVRXIuveWot6seQtaD+5QORRl91Q90/i6fTgCBX9JH3taM/2wClJdFqD/DkXOEYfmMgvrxMWZfAen9iTi4KuKYG3gi5Zp0CDSZbDIaAwEVNhoRB8blcspS5KaJXzGZsU/bTIxBVOemijmsQbJjhLqHdMr7sOSnFCjKKiqkP0Omw1ILR5WH06ltK6M9j0mR546x5SCGc7NeFPkmJpNquLA5rSz6iqWWw5MbWs1tw/lSi6lwQ30hCxjXyTnUEENAmiBe2VCKlLJ7CwSVj1ZFFnVnNscpO7ecOojLeyO8YSDhUufpkLFwkNx4LmRwBtRlZzs4KD5Ljpb9ksxe8OfdP0y7ZiPT8HRUuxKhUROEjivW2kvK3sM5uJJedwWv4382al+k3QVzaqnzMAxGxvXplEMvE9laxSV9TUXVPtrEZio9qrWb/KcJq8BeKsvDxZJyl3kPv7nYCn2s7JbWlo1BMVMlfcWiTzmZvK44ZrRoWqDrzYJnNe5obpXkpnbVOVgR5uYOmL0AA9W5qwPbRVAqsXW9Z6IaYuBTUqyl5iwN0jhNUdaUtOkAkWXWpy3RAV1DPEtFPtFECbNFNdkGhCpFQMfNvy8bBuKm0yqRITDtlQ3USjKF6r8UlIibq/XdR69O04dFpghmJDwWmWs9Ei1k5nwiokxwT7CFjnKZedWqKn0tRHtgVilGEA5FyQISRZdboidRK40qAPkXWEOA6oE6xsKplXZDsUyHGc0YDazlJEwuq+YFpVXr84/FrVYNQnWZBQIQPGbLEKgxE0N38FwTAJsaUT839esi2VZ7OYbCRGU64G8JLabFNzhcvTUdEki8pWBkUYLS/nCLCLgyjguxlkhHeXp8JbEk7cQcpdlOZgSBb95FoEbHFF7jicrzIKSuu1EPeReSWEOiOSpMfWmUlk4/I6VU0QojIId6CeRFscgfWDSdgRovZ6rB56GKfl25/4b1VqvCNvJRwUApfLAyjlbIA2BrAhiywh36xgWseCsuEpyfeYGtdnOfki23L1YPrrJK8O21KkBEjkJaW76MSeqGgnNog3CLvRuPdrWkuX6LC80sYBz03Olon6fKT6OgzYvXpDJjUjDXFMYuETh1BpP0Q5unGB8pKp9Eyn9Yf7MOPCmFda/SHKGUeIBbIQO7LjmJJYI0+OVfLmKKJ6ulPeHJMdYtwdAmEczwTIF+pNmoPtyrE8ggahL8v8q28m6uWDS5uDoE6O6zExCPQd6Wxq5MjBKXHAPVy/2/iBRo4cycxFMyUDfDxP1eXDuYjelOW1iityfZvQJTHAptqflnSczoOr1TVtTEKF4RQivK91lyitxOJykvUt6i2qVaCYudLSg8JB57IOdHqgJqYmd0UvolmtacPanlJiqlVP850SgobVnCSUupj6Pj6lLN8ccJqipIToKgFGDfWNVD806VifzSTkfstceToSPYTySEiGMUzKgrGMNqAKSsobjHGbo5FFDgH0b8GOKm8fikzkBQSLCX/lwmydNg/tCqEL0gDH9IBcqGChGt/SSlJobrh/4uVRh6BdZDewK9ugAkp7BwdR8wHjfFoh7GALXQpbJE+txqgUYc2SaiF7qUxAezn3YDHxfSKGRGjlkGpulqCyNk+tG04ZFaYFulVhkCUtdkjBgfzCjFSsCG+UkHs4xVRSj8/vzhECoSaMQ1owQj1YDXGp9eUrkmA3jCzrluRsVsQoqsD5vDNv+cj1Simw1YEi5xserJT4RYh1Xbxa1YRzEQjjIJAjwEY1X3sBaC75DS1AFF/PE0GZdJVSgaFUWRyEzInyrlW9sNzaUOrV1jvK8pBR90NmDiHhuGUTuOa7CyV5brsxY2KHctCBvoS7Ic49pmZ8geJ1UlcF4oFXRlUCorKG3g6RpqlM/qXKW6wz/mJhI7h0yVFCykNAxzIoYpUBCi2TruWvt1BzekhlC1yfxFfWfAyZ4his/BgoDs7WkBjJwedSjZFDoPHSvtGDmpc5YiGWcWivI5IKLiBjBCen5VIVORJjZ+/6Vz0KY3lZvnrtVUeUgDrqrJyQK4kBQIlom7goZIFyitZXyDwlS+fYM316GuBftEcw4d+Ib9Fgsa9iV94o0i0k1172MidaSrk0i1mxAp4YMxEFL+eoqs93jajiMKaKoh7QLVlileV1yohCir6iGrQSZbtUqXdMYlEIspqTxeWb20qt5U1GeBXkPkLkTaT8N1TU6JOPaki+SQhdI21tk7DWzkMkb3XxfdHWIBMjQOSoikSQPdUDjBOZOahj4/APryYBA0RxzYUEtasyjniYAZ3IpPIquTf0AhQ1GZtcnBYd2l6BTeI6RftUW1TCCdylFKvTSzXbnmQKy05Q05SEYu1eJmbTToErHPkwNCoK+RO6p7hBnRNZXcR/R46NEmQ/XvePP3B3K1ea6rV5hPxPRLBCRgqlT9YVht1dUS73MJ6EvLfyIWDsE9UcZFsnTdaz3RTix7NEFIEjiHJy8EwsshuMTHlHzSlOryyjWmRvCOWyA3yUMowKpRvajCs00JVkTrADehVh4WV6WenVXNh0vAU88a+Bu9AUaXEIpenqoXJs++qm3svHuWdJJsWFlURGrbiRrqVP1Hkcuri9+ovbFsZfITLCy6ZPY7IbSejg8Nl++xneepR+mLMXG0RunX1bo5CxTZWNTd8qet2BrEVxKlBY82W01CRQ3KwksBHZZDm1RZFQWzzPMiwQR2lhQaWblAwrlDdtyarU9USpdg40190sxGbwjJqynojt7AZqNfNgo3MaQRK2CIt7fn1eFcG0pKxjmUkWuKO5Qnl26fKyaLqmIKX+sGokWeiz3tEN6mgS+BCLgErl6AVvSkBdWW2tCoOspVSowDxN0ny8pIa9uJ2TvjK43Ewi8ripwSfYonf2+rclfWV1msnXGKr71EaHVT1l8mtbcjtZXhX8g5NRZg57AV8g8g+yQLZiy+gEhhhjg1JqzoqsZyaxrAPsyeeSvH7gQFeJI3qgDAjuoiNpZKzvQ/jgSsyrK+pq0gPPzc1TagJWOFb83YWFVDhKLXCR2YHRwFbEEkNpbQz5g4Qf0BLpMGBnrgrL8iNNqQMxCzWp5RPLbQplAboXDG2ui0mybeyaJeg874WjZYU7e9bwnFzIq7OXrDlAi6SyEp7niYk2+/CFnvumaj6GfmMH4hc8JiPSGvQ1d1rpTrHA5CJ1PHMbS9RRcJvaodqgyT0HOQ2Z6shi9QSP7UgbRNygJllvzDzcZqU26pwNSu9H28HLiNkmHsxGdKrRHmEmQmB/c4jUtCKmBv3W3jdOkUEaBj+uW6c4uZT+WdtQ4gmVa64k8GBbevKwsOYbX1LTUi7MsmANWva99jh1WlSjv1buWa4cmxSnB6nRsjMPhJJhVboLNQ+a7m24NhjbTCj12qVuKtwSFpMInzs6Ndu9CFA+JPfbjRoWrqaZtSzEOxsTDx2GTUGrHm3ofbEUNJwEjoC7KWBwreBQGd5ErD4U59B0WS4w2Y4kM8Z3aqIa329oeaYGMm+OW5Ywr+qKw1zXFAI8edRjvB/h13UuXkL4dw4SPuHehmVQS4un68M9hn5Xp6LzVEDxReGfo5EzisOzatj5qzhpRU7mu+pFimJK4WqfSE6bXyTy2zY/QEfYdz17tQ5J4f7aFi1yhtilmpLXSsGQDJRWns2aOTUv24dTp3bz1EZgdpckf87FHDSC49Mh9lR4Jd5PtayhQvWlE5CjAFFvC7q9rDdwc7C1L8xGHi5MMHIREmxlYBPzkhEBGoQyplfyau1mTQTmIsksStShl8h+YoQPIQCuFHZ3M7lUwFhYN3qbFPqPwbBcrztzeqxZoQCynTNV8c4cnqvBfswcmaoSAB9/VjlgClWu1m4FjVSUmandrR9cdfSoGKLJnNkzWOJ15oh3KMA0sG+c9ouGykoc0+OCOjoqFxLwhtrq5DiJXtOFRwyncxccEZ2FkvY9KuAZek6BZaljH6Q/zUsPdQafWa1C8KSkp5YdZwx9oyy8391uJKQjU+dFYag8IqCyaBSwSknCM1lCeeOxQUhofpJutlm9EEks6DxQdvIXcR0txJ5rOHJpUiFrTeteM0hjQFpC9kBDUxnoZTA54/gQXPB2Sr6paO9JfTB8zC7iHKwBNhR7sZUCQErv5aMdtRJPBBro3NfmP/9wZVkYuRykLgArxNqyGKL9HDg3QQHPu9tPAoFaWhEeMMvneGib0j8h/1R0DLZaB7LDSCn6WkiiLVBmSq3USZY2rQd6imjOg3qKeE3gvrEFZEmmjiQYzD7td76po+eKWms83qKHsaJhtmFQ8yBtKDQXlxJk7sRqa0GSyKRm64sY0mih5ruX9kmlViiyg1SuLfoE6o1XH/r5F2hv1d0Dz8mhlXroGa68Yr3tVWOIYq+Wla1OgpVWbophE/kmYXkO08eJt9PP0gMNHdWrpwl7+F88z3ax'
PASS = ['PASS']

def _load_actions() -> tuple[dict[str, Any], ...]:
    payload = MODEL_PAYLOAD
    if payload is None:
        model = json.loads(MODEL_PATH.read_text(encoding='utf-8'))
        payload = str(model['actions_zlib_b64'])
    compressed = base64.b64decode(payload)
    actions = json.loads(zlib.decompress(compressed).decode('utf-8'))
    if len(actions) != 720:
        raise ValueError('Distilled elite-pasture calendar must contain 720 records')
    return tuple(actions)
CALENDAR_ACTIONS = _load_actions()

def elite_pasture_decide(observation: dict[str, Any]) -> dict[str, Any]:
    next_record = int(observation.get('step', 0)) + 1
    if next_record >= len(CALENDAR_ACTIONS):
        return {'farmer': PASS, 'hands': [], 'market': []}
    planned = CALENDAR_ACTIONS[next_record]
    return {'farmer': list(planned.get('farmer', PASS)), 'hands': [list(action) for action in planned.get('hands', [])], 'market': [list(order) for order in planned.get('market', [])]}
elite_pasture_route = elite_pasture_decide
calendar_route = build_candidate_b_agent()
'Candidate C: public-state route portfolio over complete route experts.\n\nStatus: two validated routes. `elite_pasture` is the new default -- see\n`rl/GOAL.md` section 9c for the full account. Four candidates were\nrejected before it by direct measurement: two hand-built strategies\n(`experimental_center_out_agent.py`; the best homegrown lineage,\n`gated-late-strawberry`/`tiered-fertilizer`), and two real-replay clones\nsourced from this project\'s own Kaggle match history\n(`experimental_distilled_pasture_agent.py`, kept rejected). The pattern\nthat broke the streak: Kaggle\'s ladder pairs similarly-rated opponents, so\nthis project\'s own match history never contained a genuinely elite\nreplay to clone -- a real Kaggle API token unblocked pulling one directly\nfrom the leaderboard instead of from this project\'s own games.\n\n`elite_pasture` (`experimental_distilled_elite_pasture_agent.py`) clones\nepisode 105144807, player "fog flower" (public leaderboard score 2882.6),\nwho beat the leaderboard\'s #2 team (2965.4) in that game. Wrapped in the\nsame guard and market-timing layers as Candidate A/B\n(`build_candidate_b_agent(baseline=build_candidate_a_agent(baseline=...))`),\nit beat Candidate B 10-0 and Candidate A 4-0 across fresh seeds neither\nwas recorded on, both seats -- the first candidate tested this way to\nwin convincingly instead of losing decisively. `calendar` (Candidate B)\nis kept as the second route, both as a documented fallback and because\nnothing yet justifies discarding a submission with its own extensive\nvalidation history.\n\nThis module still cannot legally choose between them: both are\nstep-indexed scripted replays with no live-opponent signal available at\nepisode start (see the non-reentrant rule below), so `_select_route_name`\nremains a placeholder returning whichever route is listed first --\ncurrently `elite_pasture`, because it is the better-measured of the two,\nnot because a real per-opponent selection rule exists yet. Hard\ninvariants, per `rl/GOAL.md` section 9 ("Selector"):\n\n  - Only public/legal state is ever read by `_select_route_name` -- it\n    receives nothing but the live `observation` dict, which never contains\n    team name, rank, submission ID, replay ID, or seed (those live only in\n    a replay file\'s `info` block, never in what an agent is called with).\n    There is no field for those to leak in through even by accident.\n  - A scripted, step-indexed route -- both routes here are, since each\n    wraps a frozen 720-step replay with no awareness of a board state it\n    did not itself create -- can only be entered at episode start. This\n    module enforces that as a hard, checked, one-way transition\n    (`RouteExpert.reentrant = False`), not just a convention a future edit\n    could quietly break.\n  - Hysteresis: once committed, a route is never reconsidered for the rest\n    of the episode. This is the strictest possible reading of "latch with\n    hysteresis; do not oscillate," and is the correct starting point before\n    any evidence exists that switching mid-episode is safe for a given\n    route pair -- switching a *reactive* route out mid-game may be safe\n    (it just looks at the current board), but nothing here has been\n    measured yet, so nothing here claims otherwise.\n'
from dataclasses import dataclass
from typing import Any, Callable
RouteFn = Callable[[dict[str, Any]], AgentAction]
SelectRouteName = Callable[[dict[str, Any], 'tuple[RouteExpert, ...]'], str]

@dataclass(frozen=True)
class RouteExpert:
    """One complete, standalone agent callable and its safety metadata."""
    name: str
    decide: RouteFn
    reentrant: bool
ELITE_PASTURE = RouteExpert(name='elite_pasture', decide=build_candidate_b_agent(baseline=build_candidate_a_agent(baseline=elite_pasture_route)), reentrant=False)
CALENDAR = RouteExpert(name='calendar', decide=calendar_route, reentrant=False)
ROUTES: tuple[RouteExpert, ...] = (ELITE_PASTURE, CALENDAR)

def _select_route_name(observation: dict[str, Any], routes: tuple[RouteExpert, ...]) -> str:
    """Pick a route name using only the live observation's public state.

    Placeholder: always the first configured route. There is currently
    only one validated route, so there is nothing to select between yet --
    this function exists so the selection *point* and its signature are
    fixed now, and a real rule can replace this body later without
    touching the executor.
    """
    del observation
    return routes[0].name

@dataclass
class CandidateCState:
    committed_route: str | None = None
    last_step: int = -1

class CandidateCExecutor:
    """Commits once, per episode, to exactly one complete route expert."""

    def __init__(self, routes: tuple[RouteExpert, ...]=ROUTES, *, select_route_name: SelectRouteName=_select_route_name) -> None:
        if not routes:
            raise ValueError('Candidate C needs at least one route')
        self._routes: dict[str, RouteExpert] = {route.name: route for route in routes}
        self._order = routes
        self._select = select_route_name
        self._states: dict[int, CandidateCState] = {}

    def _state(self, player: int, step: int) -> CandidateCState:
        state = self._states.setdefault(player, CandidateCState())
        if step == 0 or step <= state.last_step:
            state = CandidateCState()
            self._states[player] = state
        state.last_step = step
        return state

    def decide(self, observation: dict[str, Any]) -> AgentAction:
        player = int(observation['player'])
        step = int(observation.get('step', 0))
        state = self._state(player, step)
        if state.committed_route is None:
            name = self._select(observation, self._order)
            if name not in self._routes:
                raise ValueError(f'Unknown route selected: {name!r}')
            route = self._routes[name]
            if step > 0 and (not route.reentrant):
                raise ValueError(f'Route {name!r} is not reentrant and cannot be selected after episode start (step={step})')
            state.committed_route = name
        return self._routes[state.committed_route].decide(observation)

def build_candidate_c_agent(routes: tuple[RouteExpert, ...]=ROUTES) -> RouteFn:
    """Create the Candidate C route-portfolio agent."""
    executor = CandidateCExecutor(routes=routes)

    def decide(observation: dict[str, Any]) -> AgentAction:
        return executor.decide(observation)
    return decide
agent = build_candidate_c_agent()
