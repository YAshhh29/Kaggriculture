from __future__ import annotations
'A deterministic, submission-ready baseline agent for Kaggriculture.'
from typing import Any
TARGET_WHEAT_TILES = 6
WHEAT_SEED_COST = 10
WHEAT_MAX_YIELD_AGE = 4
LAST_WHEAT_PLANTING_DAY = 24
MINIMUM_WHEAT_SALE_PRICE = 35
MAXIMUM_WHEAT_HOLDINGS = 72
WHEAT_LIQUIDATION_DAY = 25

def _market_orders(day: int, market: dict[str, Any], farm: dict[str, Any], private: dict[str, Any], target_wheat_tiles: int, last_planting_day: int | None, minimum_wheat_sale_price: int | None, maximum_wheat_holdings: int | None, wheat_liquidation_day: int | None) -> list[list[Any]]:
    orders: list[list[Any]] = []
    wheat_in_shed = int(private.get('shed', {}).get('WHEAT', 0))
    wheat_price = int(market.get('prices', {}).get('WHEAT', 0))
    price_is_good = minimum_wheat_sale_price is None or wheat_price >= minimum_wheat_sale_price
    inventory_is_full = maximum_wheat_holdings is not None and wheat_in_shed >= maximum_wheat_holdings
    liquidation_started = wheat_liquidation_day is not None and day >= wheat_liquidation_day
    if wheat_in_shed > 0 and (price_is_good or inventory_is_full or liquidation_started):
        orders.append(['SELL', 'WHEAT', wheat_in_shed])
    planted_wheat = sum((1 for row in farm['tiles'] for tile in row if _is_wheat(tile)))
    wheat_seeds = int(private.get('seeds', {}).get('WHEAT', 0))
    seeds_needed = max(0, target_wheat_tiles - planted_wheat - wheat_seeds)
    affordable_seeds = int(float(farm['money']) // WHEAT_SEED_COST)
    seeds_to_buy = min(seeds_needed, affordable_seeds)
    if seeds_to_buy > 0 and _planting_is_open(day, last_planting_day):
        orders.append(['BUY_SEED', 'WHEAT', seeds_to_buy])
    return orders

def _farmer_action(day: int, farm: dict[str, Any], private: dict[str, Any], last_planting_day: int | None, harvest_watered_current_first: bool) -> list[str]:
    tiles = farm['tiles']
    position = tuple(farm['farmer'])
    urgent_water = _positions(tiles, lambda tile: _is_wheat(tile) and (not tile.get('watered_today', False)) and (int(tile.get('consecutive_unwatered', 0)) >= 1))
    if urgent_water:
        target = _nearest(position, urgent_water)
        return _act_at_or_move(position, target, ['WATER'])
    current_tile = tiles[position[1]][position[0]]
    if harvest_watered_current_first and _is_mature_wheat(current_tile, day) and current_tile.get('watered_today', False):
        return ['HARVEST']
    daily_water = _positions(tiles, lambda tile: _is_wheat(tile) and (not tile.get('watered_today', False)))
    if daily_water:
        target = _nearest(position, daily_water)
        return _act_at_or_move(position, target, ['WATER'])
    mature_wheat = _positions(tiles, lambda tile: _is_mature_wheat(tile, day))
    if mature_wheat:
        target = _nearest(position, mature_wheat)
        return _act_at_or_move(position, target, ['HARVEST'])
    wheat_seeds = int(private.get('seeds', {}).get('WHEAT', 0))
    if wheat_seeds > 0 and _planting_is_open(day, last_planting_day):
        empty_tiles = _positions(tiles, lambda tile: tile is None)
        if empty_tiles:
            return _act_at_or_move(position, _nearest(position, empty_tiles), ['PLANT', 'WHEAT'])
    return ['PASS']

def _planting_is_open(day: int, last_planting_day: int | None) -> bool:
    return last_planting_day is None or day <= last_planting_day

def _is_wheat(tile: Any) -> bool:
    return isinstance(tile, dict) and tile.get('kind') == 'PLANT' and (tile.get('crop') == 'WHEAT')

def _is_mature_wheat(tile: Any, day: int) -> bool:
    return _is_wheat(tile) and day - int(tile['planted_day']) >= WHEAT_MAX_YIELD_AGE and (int(tile.get('yield_units', 0)) > 0)

def _positions(tiles: list[list[Any]], predicate: Any) -> list[tuple[int, int]]:
    return [(x, y) for y, row in enumerate(tiles) for x, tile in enumerate(row) if predicate(tile)]

def _nearest(origin: tuple[int, int], positions: list[tuple[int, int]]) -> tuple[int, int]:
    origin_x, origin_y = origin
    return min(positions, key=lambda position: (abs(position[0] - origin_x) + abs(position[1] - origin_y), position[1], position[0]))

def _act_at_or_move(origin: tuple[int, int], target: tuple[int, int], action: list[str]) -> list[str]:
    if origin == target:
        return action
    origin_x, origin_y = origin
    target_x, target_y = target
    if target_x < origin_x:
        return ['WEST']
    if target_x > origin_x:
        return ['EAST']
    if target_y < origin_y:
        return ['NORTH']
    return ['SOUTH']

def decide(observation: dict[str, Any], target_wheat_tiles: int=TARGET_WHEAT_TILES, last_planting_day: int | None=LAST_WHEAT_PLANTING_DAY, harvest_watered_current_first: bool=False, minimum_wheat_sale_price: int | None=MINIMUM_WHEAT_SALE_PRICE, maximum_wheat_holdings: int | None=MAXIMUM_WHEAT_HOLDINGS, wheat_liquidation_day: int | None=WHEAT_LIQUIDATION_DAY) -> dict[str, Any]:
    """Choose actions using a specific wheat workload target."""
    player = observation['player']
    farm = observation['farms'][player]
    private = observation['private']
    day = observation['day']
    market = _market_orders(day, observation['market'], farm, private, target_wheat_tiles, last_planting_day, minimum_wheat_sale_price, maximum_wheat_holdings, wheat_liquidation_day)
    farmer_action = _farmer_action(day, farm, private, last_planting_day, harvest_watered_current_first)
    return {'farmer': farmer_action, 'hands': [], 'market': market}
decide_wheat = decide

def _shed_access_tiles(board_size: int) -> list[tuple[int, int]]:
    half = board_size // 2
    return [(half - 1, half - 1), (half, half - 1), (half - 1, half), (half, half)]

def _distance(origin: tuple[int, int], target: tuple[int, int]) -> int:
    return abs(origin[0] - target[0]) + abs(origin[1] - target[1])

def _task_groups(day: int, farm: dict[str, Any], private: dict[str, Any], blocked_tiles: set[tuple[int, int]] | None=None) -> list[list[tuple[tuple[int, int], list[str]]]]:
    tiles = farm['tiles']
    blocked_tiles = blocked_tiles or set()
    urgent_water: list[tuple[tuple[int, int], list[str]]] = []
    daily_water: list[tuple[tuple[int, int], list[str]]] = []
    harvest: list[tuple[tuple[int, int], list[str]]] = []
    empty: list[tuple[tuple[int, int], list[str]]] = []
    for y, row in enumerate(tiles):
        for x, tile in enumerate(row):
            position = (x, y)
            if position in blocked_tiles:
                continue
            if _is_wheat(tile) and (not tile.get('watered_today', False)):
                target = (position, ['WATER'])
                if int(tile.get('consecutive_unwatered', 0)) >= 1:
                    urgent_water.append(target)
                else:
                    daily_water.append(target)
            elif _is_mature_wheat(tile, day):
                harvest.append((position, ['HARVEST']))
            elif tile is None:
                empty.append((position, ['PLANT', 'WHEAT']))
    planting_open = day <= LAST_WHEAT_PLANTING_DAY
    available_seeds = int(private.get('seeds', {}).get('WHEAT', 0))
    plant_tasks = empty[:available_seeds] if planting_open else []
    return [urgent_water, daily_water, harvest, plant_tasks]
'Development-only replay-inspired labor and livestock scaling policy.'
from collections import Counter
from typing import Any
TARGET_DAILY_HANDS = 8
TARGET_WHEAT_TILES = 16
TARGET_COWS = 4
TARGET_SHEEP = 4
CARE_ENABLED = True
FEED_DAILY = True
LAST_WHEAT_PLANTING_DAY = 21
LAST_FEEDING_DAY = 27
LAST_COLLECTION_DAY = 28
MAX_MARKET_ORDERS = 10
LAND_PRICES = (1000, 2000, 4000)
LAND_CASH_RESERVE = 1000
LEADER_HAND_TARGETS = (5, 0, 4, 5, 5, 4, 4, 8, 11, 12, 11, 12, 10, 11, 8, 12, 9, 12, 12, 12, 12, 12, 12, 12, 11, 11, 11, 11, 10, 8)
ANIMAL_PLANS = ({'id': 'cow_1', 'animal': 'COW', 'structure': 'PASTURE', 'position': (4, 4), 'product': 'MILK', 'cost': 400, 'max_held': 6}, {'id': 'cow_2', 'animal': 'COW', 'structure': 'PASTURE', 'position': (3, 4), 'product': 'MILK', 'cost': 400, 'max_held': 6}, {'id': 'sheep_1', 'animal': 'SHEEP', 'structure': 'PASTURE', 'position': (4, 3), 'product': 'WOOL', 'cost': 500, 'max_held': 6}, {'id': 'sheep_2', 'animal': 'SHEEP', 'structure': 'PASTURE', 'position': (3, 3), 'product': 'WOOL', 'cost': 500, 'max_held': 6})
EXPANSION_ANIMAL_PLANS = (*ANIMAL_PLANS, {'id': 'cow_3', 'animal': 'COW', 'structure': 'PASTURE', 'position': (2, 4), 'product': 'MILK', 'cost': 400, 'max_held': 6}, {'id': 'cow_4', 'animal': 'COW', 'structure': 'PASTURE', 'position': (4, 2), 'product': 'MILK', 'cost': 400, 'max_held': 6}, {'id': 'sheep_3', 'animal': 'SHEEP', 'structure': 'PASTURE', 'position': (2, 3), 'product': 'WOOL', 'cost': 500, 'max_held': 6}, {'id': 'sheep_4', 'animal': 'SHEEP', 'structure': 'PASTURE', 'position': (3, 2), 'product': 'WOOL', 'cost': 500, 'max_held': 6})
LIVESTOCK_TILES = {plan['position'] for plan in ANIMAL_PLANS}
COW_POSITION_PREFERENCE = ((4, 4), (3, 4), (2, 4), (4, 2), (2, 3), (3, 2), (4, 3), (3, 3), (5, 4), (5, 3), (6, 4), (6, 3), (5, 2), (7, 4), (4, 5), (3, 5), (6, 5), (6, 6), (5, 6), (5, 7))
SHEEP_POSITION_PREFERENCE = ((4, 3), (3, 3), (2, 3), (3, 2), (2, 4), (4, 2), (4, 4), (3, 4), (5, 4), (5, 3), (6, 4), (6, 3), (5, 2), (7, 4), (4, 5), (3, 5), (6, 5), (6, 6), (5, 6), (5, 7))

def _selected_animal_plans(target_cows: int, target_sheep: int) -> tuple[dict[str, Any], ...]:
    selected: list[dict[str, Any]] = []
    occupied: set[tuple[int, int]] = set()
    for animal, target, preferences in (('COW', target_cows, COW_POSITION_PREFERENCE), ('SHEEP', target_sheep, SHEEP_POSITION_PREFERENCE)):
        product = 'MILK' if animal == 'COW' else 'WOOL'
        cost = 400 if animal == 'COW' else 500
        placed = 0
        for position in preferences:
            if position in occupied:
                continue
            selected.append({'id': f'{animal.lower()}_{placed + 1}', 'animal': animal, 'structure': 'PASTURE', 'position': position, 'product': product, 'cost': cost, 'max_held': 6})
            occupied.add(position)
            placed += 1
            if placed == target:
                break
    return tuple(selected)

def _staged_animal_plans(day: int, target_cows: int, target_sheep: int) -> tuple[dict[str, Any], ...]:
    staged_cows = min(target_cows, 2 + int(day >= 3) + int(day >= 5) + 2 * int(day >= 7))
    staged_sheep = min(target_sheep, 2 + 2 * int(day >= 7) + 2 * int(day >= 9) + 2 * int(day >= 11) + 2 * int(day >= 12) + 2 * int(day >= 13))
    final_plans = _selected_animal_plans(target_cows, target_sheep)
    selected = []
    remaining = {'COW': staged_cows, 'SHEEP': staged_sheep}
    for plan in final_plans:
        animal = str(plan['animal'])
        if remaining[animal] <= 0:
            continue
        selected.append(plan)
        remaining[animal] -= 1
    return tuple(selected)

def _inventories(private: dict[str, Any], worker_count: int) -> list[dict[str, Any]]:
    inventories = private.get('inventories', [])
    return [inventory if isinstance(inventory, dict) else {} for inventory in inventories[:worker_count]] + [{} for _ in range(max(0, worker_count - len(inventories)))]

def _tile_at(tiles: list[list[Any]], position: tuple[int, int]) -> Any:
    return tiles[position[1]][position[0]]

def _plan_is_active(plan: dict[str, Any], tiles: list[list[Any]]) -> bool:
    tile = _tile_at(tiles, plan['position'])
    return isinstance(tile, dict) and tile.get('animal') == plan['animal']

def _quadrant(position: tuple[int, int], board_size: int) -> str:
    x, y = position
    half = board_size // 2
    return ('N' if y < half else 'S') + ('W' if x < half else 'E')

def _unlocked_animal_plans(animal_plans: tuple[dict[str, Any], ...], farm: dict[str, Any]) -> tuple[dict[str, Any], ...]:
    unlocked = set(farm.get('unlocked_quadrants', []))
    board_size = len(farm['tiles'])
    return tuple((plan for plan in animal_plans if _quadrant(plan['position'], board_size) in unlocked))

def _feed_due(day: int, tile: dict[str, Any], feed_daily: bool=False) -> bool:
    return day <= LAST_FEEDING_DAY and (not tile.get('fed_today', False)) and (feed_daily or int(tile.get('consecutive_unfed', 0)) >= 1)

def _assign_nearest(positions: list[tuple[int, int]], actions: list[list[str] | None], target: tuple[int, int], operation: list[str]) -> int | None:
    available = [index for index, action in enumerate(actions) if action is None]
    if not available:
        return None
    worker = min(available, key=lambda index: (_distance(positions[index], target), index))
    actions[worker] = _act_at_or_move(positions[worker], target, operation)
    return worker

def _assign_carried_animals(animal_plans: tuple[dict[str, Any], ...], tiles: list[list[Any]], positions: list[tuple[int, int]], inventories: list[dict[str, Any]], actions: list[list[str] | None], reserved_plans: set[str]) -> None:
    for worker, inventory in enumerate(inventories):
        if actions[worker] is not None:
            continue
        for animal in ('COW', 'SHEEP'):
            if int(inventory.get(animal, 0)) <= 0:
                continue
            target_plan = next((plan for plan in animal_plans if plan['animal'] == animal and plan['id'] not in reserved_plans and (not _plan_is_active(plan, tiles)) and isinstance(_tile_at(tiles, plan['position']), dict) and (_tile_at(tiles, plan['position']).get('kind') == plan['structure']) and ('animal' not in _tile_at(tiles, plan['position']))), None)
            if target_plan is None:
                continue
            target = target_plan['position']
            actions[worker] = _act_at_or_move(positions[worker], target, ['PLACE', animal])
            reserved_plans.add(str(target_plan['id']))
            break

def _assign_urgent_feeding(animal_plans: tuple[dict[str, Any], ...], day: int, farm: dict[str, Any], private: dict[str, Any], positions: list[tuple[int, int]], inventories: list[dict[str, Any]], actions: list[list[str] | None], feed_daily: bool) -> None:
    tiles = farm['tiles']
    due = [plan for plan in animal_plans if _plan_is_active(plan, tiles) and _feed_due(day, _tile_at(tiles, plan['position']), feed_daily)]
    reserved: set[str] = set()
    for worker, inventory in enumerate(inventories):
        if actions[worker] is not None or int(inventory.get('WHEAT', 0)) <= 0:
            continue
        available = [plan for plan in due if plan['id'] not in reserved]
        if not available:
            break
        plan = min(available, key=lambda candidate: (_distance(positions[worker], candidate['position']), candidate['position'][1], candidate['position'][0]))
        actions[worker] = _act_at_or_move(positions[worker], plan['position'], ['FEED'])
        reserved.add(str(plan['id']))
    remaining = [plan for plan in due if plan['id'] not in reserved]
    available_wheat = int(private.get('shed', {}).get('WHEAT', 0))
    access_tiles = _shed_access_tiles(len(tiles))
    while remaining and available_wheat > 0:
        available_workers = [index for index, action in enumerate(actions) if action is None]
        if not available_workers:
            break
        worker = min(available_workers, key=lambda index: min((_distance(positions[index], access) for access in access_tiles)))
        access = min(access_tiles, key=lambda target: _distance(positions[worker], target))
        actions[worker] = _act_at_or_move(positions[worker], access, ['PICKUP', 'WHEAT', 1])
        available_wheat -= 1
        remaining.pop(0)

def _assign_setup(animal_plans: tuple[dict[str, Any], ...], farm: dict[str, Any], private: dict[str, Any], positions: list[tuple[int, int]], inventories: list[dict[str, Any]], actions: list[list[str] | None]) -> None:
    tiles = farm['tiles']
    reserved_plans: set[str] = set()
    _assign_carried_animals(animal_plans, tiles, positions, inventories, actions, reserved_plans)
    for plan in animal_plans:
        if _plan_is_active(plan, tiles) or plan['id'] in reserved_plans:
            continue
        tile = _tile_at(tiles, plan['position'])
        structure_ready = isinstance(tile, dict) and tile.get('kind') == plan['structure'] and ('animal' not in tile)
        if structure_ready:
            continue
        operation = [f"BUILD_{plan['structure']}"] if tile is None else ['DIG']
        if _assign_nearest(positions, actions, plan['position'], operation) is not None:
            reserved_plans.add(str(plan['id']))
    virtual_shed = Counter(private.get('shed', {}))
    for inventory in inventories:
        for animal in ('COW', 'SHEEP'):
            virtual_shed[animal] -= int(inventory.get(animal, 0))
    access_tiles = _shed_access_tiles(len(tiles))
    for plan in animal_plans:
        if _plan_is_active(plan, tiles) or plan['id'] in reserved_plans:
            continue
        tile = _tile_at(tiles, plan['position'])
        if not (isinstance(tile, dict) and tile.get('kind') == plan['structure'] and ('animal' not in tile) and (virtual_shed[plan['animal']] > 0)):
            continue
        available_workers = [index for index, action in enumerate(actions) if action is None]
        if not available_workers:
            break
        worker = min(available_workers, key=lambda index: min((_distance(positions[index], access) for access in access_tiles)))
        access = min(access_tiles, key=lambda target: _distance(positions[worker], target))
        actions[worker] = _act_at_or_move(positions[worker], access, ['PICKUP', str(plan['animal']), 1])
        virtual_shed[plan['animal']] -= 1
        reserved_plans.add(str(plan['id']))

def _assign_animal_services(animal_plans: tuple[dict[str, Any], ...], day: int, farm: dict[str, Any], positions: list[tuple[int, int]], actions: list[list[str] | None], care_enabled: bool) -> None:
    tiles = farm['tiles']
    active = [plan for plan in animal_plans if _plan_is_active(plan, tiles)]
    if day <= LAST_COLLECTION_DAY:
        for plan in active:
            tile = _tile_at(tiles, plan['position'])
            if tile.get('fertilizer_available', False):
                _assign_nearest(positions, actions, plan['position'], ['COLLECT_FERTILIZER'])
    for plan in active:
        tile = _tile_at(tiles, plan['position'])
        harvest_due = day <= LAST_COLLECTION_DAY and int(tile.get('yield_units', 0)) > 0 and (day == LAST_COLLECTION_DAY or int(tile.get('yield_units', 0)) >= int(plan['max_held']))
        if harvest_due:
            _assign_nearest(positions, actions, plan['position'], ['HARVEST'])
    if care_enabled and day <= LAST_FEEDING_DAY:
        for plan in active:
            tile = _tile_at(tiles, plan['position'])
            if tile.get('fed_today', False) and (not tile.get('cared_today', False)):
                _assign_nearest(positions, actions, plan['position'], ['CARE'])

def _assign_crop_tasks(livestock_tiles: set[tuple[int, int]], day: int, farm: dict[str, Any], private: dict[str, Any], positions: list[tuple[int, int]], actions: list[list[str] | None]) -> None:
    reserved: set[tuple[int, int]] = set()
    task_groups = _task_groups(day, farm, private, livestock_tiles)
    for worker, position in enumerate(positions):
        if actions[worker] is not None:
            continue
        group = next((tasks for tasks in task_groups if any((target not in reserved for target, _ in tasks))), [])
        available = [task for task in group if task[0] not in reserved]
        if not available:
            actions[worker] = ['PASS']
            continue
        target, operation = min(available, key=lambda task: (_distance(position, task[0]), task[0][1], task[0][0]))
        reserved.add(target)
        actions[worker] = _act_at_or_move(position, target, operation)

def _worker_actions(animal_plans: tuple[dict[str, Any], ...], livestock_tiles: set[tuple[int, int]], day: int, farm: dict[str, Any], private: dict[str, Any], care_enabled: bool, feed_daily: bool) -> tuple[list[str], list[list[str]]]:
    positions = [tuple(farm['farmer']), *(tuple(position) for position in farm.get('hands', []))]
    inventories = _inventories(private, len(positions))
    actions: list[list[str] | None] = [None for _ in positions]
    _assign_urgent_feeding(animal_plans, day, farm, private, positions, inventories, actions, feed_daily)
    _assign_setup(animal_plans, farm, private, positions, inventories, actions)
    _assign_animal_services(animal_plans, day, farm, positions, actions, care_enabled)
    _assign_crop_tasks(livestock_tiles, day, farm, private, positions, actions)
    resolved = [action or ['PASS'] for action in actions]
    return (resolved[0], resolved[1:])

def _scale_hire_orders(day: int, hour: int, farm: dict[str, Any], target_daily_hands: int, adaptive_hands: bool) -> list[list[str]]:
    if not adaptive_hands and hour != 0:
        return []
    daily_target = min(target_daily_hands, LEADER_HAND_TARGETS[min(day, 29)]) if adaptive_hands else target_daily_hands
    missing = max(0, daily_target - len(farm.get('hands', [])))
    return [['HIRE'] for _ in range(missing)]

def _livestock_orders(animal_plans: tuple[dict[str, Any], ...], day: int, hour: int, farm: dict[str, Any], private: dict[str, Any], feed_daily: bool) -> tuple[list[list[Any]], list[list[Any]]]:
    tiles = farm['tiles']
    shed = private.get('shed', {})
    inventories = private.get('inventories', [])
    carried = Counter()
    for inventory in inventories:
        if isinstance(inventory, dict):
            carried.update(inventory)
    urgent: list[list[Any]] = []
    deferred_sales: list[list[Any]] = []
    if hour == 0 and day <= 20:
        desired = Counter((str(plan['animal']) for plan in animal_plans))
        present = Counter((str(plan['animal']) for plan in animal_plans if _plan_is_active(plan, tiles)))
        for animal in ('COW', 'SHEEP'):
            missing = max(0, desired[animal] - present[animal] - int(shed.get(animal, 0)) - int(carried.get(animal, 0)))
            if missing > 0:
                urgent.append(['BUY_ANIMAL', animal, missing])
    feed_needed = sum((_feed_due(day, _tile_at(tiles, plan['position']), feed_daily) for plan in animal_plans if _plan_is_active(plan, tiles)))
    available_feed = int(shed.get('WHEAT', 0)) + int(carried.get('WHEAT', 0))
    if feed_needed > available_feed:
        urgent.append(['BUY_PRODUCT', 'WHEAT', feed_needed - available_feed])
    for item in ('MILK', 'WOOL', 'FERTILIZER'):
        quantity = int(shed.get(item, 0))
        if quantity > 0:
            deferred_sales.append(['SELL', item, quantity])
    return (urgent, deferred_sales)

def _scale_market_orders(hires: list[list[str]], urgent_livestock: list[list[Any]], land_orders: list[list[Any]], baseline: list[list[Any]], livestock_sales: list[list[Any]]) -> list[list[Any]]:
    orders = [*hires, *urgent_livestock, *land_orders, *baseline, *livestock_sales]
    operation_priority = {'SELL': 0, 'BUY_PRODUCT': 1, 'HIRE': 2, 'BUY_ANIMAL': 3, 'BUY_LAND': 4, 'BUY_SEED': 5}
    ranked = sorted(enumerate(orders), key=lambda entry: (operation_priority.get(str(entry[1][0]), 99), entry[0]))
    return [order for _, order in ranked[:MAX_MARKET_ORDERS]]

def _land_orders(day: int, hour: int, farm: dict[str, Any], target_extra_land: int) -> list[list[str]]:
    unlocked_extra = max(0, len(farm.get('unlocked_quadrants', [])) - 1)
    earliest_days = (6, 11, 12)
    if unlocked_extra >= min(target_extra_land, len(LAND_PRICES)) or day < earliest_days[min(unlocked_extra, 2)] or day > 20:
        return []
    cost = LAND_PRICES[unlocked_extra]
    if float(farm['money']) < cost + LAND_CASH_RESERVE:
        return []
    return [['BUY_LAND']]

def _protect_feed_reserve(baseline_orders: list[list[Any]], animal_plans: tuple[dict[str, Any], ...], day: int, farm: dict[str, Any], private: dict[str, Any], feed_daily: bool) -> list[list[Any]]:
    tiles = farm['tiles']
    carried_wheat = sum((int(inventory.get('WHEAT', 0)) for inventory in private.get('inventories', []) if isinstance(inventory, dict)))
    feed_needed = sum((_feed_due(day, _tile_at(tiles, plan['position']), feed_daily) for plan in animal_plans if _plan_is_active(plan, tiles)))
    shed_reserve = max(0, feed_needed - carried_wheat)
    protected: list[list[Any]] = []
    for order in baseline_orders:
        if len(order) >= 3 and order[0] == 'SELL' and (order[1] == 'WHEAT'):
            sellable = max(0, int(order[2]) - shed_reserve)
            if sellable > 0:
                protected.append(['SELL', 'WHEAT', sellable])
            continue
        protected.append(order)
    return protected

def decide(observation: dict[str, Any], target_wheat_tiles: int=TARGET_WHEAT_TILES, target_daily_hands: int=TARGET_DAILY_HANDS, care_enabled: bool=CARE_ENABLED, target_cows: int=TARGET_COWS, target_sheep: int=TARGET_SHEEP, feed_daily: bool=FEED_DAILY, target_extra_land: int=0, adaptive_hands: bool=False) -> dict[str, Any]:
    """Run a replay-inspired five-hand, four-animal opening."""
    player = int(observation['player'])
    farm = observation['farms'][player]
    private = observation['private']
    day = int(observation['day'])
    hour = int(observation['hour'])
    desired_animal_plans = _staged_animal_plans(day, target_cows, target_sheep)
    animal_plans = _unlocked_animal_plans(desired_animal_plans, farm)
    baseline = decide_wheat(observation, target_wheat_tiles=target_wheat_tiles, last_planting_day=LAST_WHEAT_PLANTING_DAY)
    baseline_market = _protect_feed_reserve(baseline['market'], animal_plans, day, farm, private, feed_daily)
    farmer_action, hands_actions = _worker_actions(animal_plans, {plan['position'] for plan in desired_animal_plans}, day, farm, private, care_enabled, feed_daily)
    urgent_livestock, livestock_sales = _livestock_orders(animal_plans, day, hour, farm, private, feed_daily)
    market = _scale_market_orders(_scale_hire_orders(day, hour, farm, target_daily_hands, adaptive_hands), urgent_livestock, _land_orders(day, hour, farm, target_extra_land), baseline_market, livestock_sales)
    return {'farmer': farmer_action, 'hands': hands_actions, 'market': market}

def agent(observation: dict[str, Any]) -> dict[str, Any]:
    """Run the default replay-inspired scale candidate."""
    return decide(observation)
