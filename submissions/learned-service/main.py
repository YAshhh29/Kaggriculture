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
'Investment-focused land, labor, and livestock expansion candidate.'
from collections import Counter
from typing import Any
TARGET_DAILY_HANDS = 10
TARGET_WHEAT_TILES = 12
TARGET_COWS = 6
TARGET_SHEEP = 12
TARGET_EXTRA_LAND = 3
TARGET_TOTAL_MARKET_ANIMALS = 18

def _animal_count(farm: dict[str, Any]) -> int:
    return sum((isinstance(tile, dict) and bool(tile.get('animal')) for row in farm.get('tiles', []) for tile in row))

def _animal_counts(farm: dict[str, Any]) -> Counter[str]:
    return Counter((str(tile['animal']) for row in farm.get('tiles', []) for tile in row if isinstance(tile, dict) and tile.get('animal')))

def _pressure_targets(observation: dict[str, Any], player: int, maximum_hands: int, target_market_animals: int=TARGET_TOTAL_MARKET_ANIMALS) -> tuple[int, int, int, int]:
    opponent = observation['farms'][1 - player]
    own_counts = _animal_counts(observation['farms'][player])
    opponent_animals = _animal_count(opponent)
    target_animals = max(8, target_market_animals - opponent_animals, sum(own_counts.values()))
    target_cows = max(own_counts['COW'], min(6, max(4, (target_animals + 2) // 3)))
    target_sheep = max(own_counts['SHEEP'], target_animals - target_cows)
    target_hands = min(maximum_hands, 8 + max(0, target_animals - 8 + 4) // 5)
    plans = _staged_animal_plans(29, target_cows, target_sheep)
    land_order = {'NE': 1, 'SW': 2, 'SE': 3}
    target_land = max((land_order.get(_quadrant(plan['position'], 10), 0) for plan in plans), default=0)
    return (target_cows, target_sheep, target_hands, target_land)

def _investment_livestock_orders(animal_plans: tuple[dict[str, Any], ...], day: int, farm: dict[str, Any], private: dict[str, Any]) -> tuple[list[list[Any]], list[list[Any]]]:
    tiles = farm['tiles']
    shed = private.get('shed', {})
    carried = Counter()
    for inventory in private.get('inventories', []):
        if isinstance(inventory, dict):
            carried.update(inventory)
    urgent: list[list[Any]] = []
    sales: list[list[Any]] = []
    if day <= 20:
        desired = Counter((str(plan['animal']) for plan in animal_plans))
        present = Counter((str(plan['animal']) for plan in animal_plans if _plan_is_active(plan, tiles)))
        for animal in ('COW', 'SHEEP'):
            missing = max(0, desired[animal] - present[animal] - int(shed.get(animal, 0)) - int(carried.get(animal, 0)))
            if missing > 0:
                urgent.append(['BUY_ANIMAL', animal, min(missing, 2)])
    feed_needed = sum((_feed_due(day, tiles[plan['position'][1]][plan['position'][0]], True) for plan in animal_plans if _plan_is_active(plan, tiles)))
    available_feed = int(shed.get('WHEAT', 0)) + int(carried.get('WHEAT', 0))
    if feed_needed > available_feed:
        urgent.append(['BUY_PRODUCT', 'WHEAT', feed_needed - available_feed])
    for item in ('MILK', 'WOOL', 'FERTILIZER'):
        quantity = int(shed.get(item, 0))
        if quantity > 0:
            sales.append(['SELL', item, quantity])
    return (urgent, sales)

def _investment_market_orders(sales: list[list[Any]], urgent: list[list[Any]], land: list[list[Any]], hires: list[list[Any]], baseline: list[list[Any]]) -> list[list[Any]]:
    orders = [*sales, *urgent, *land, *hires, *baseline]
    priority = {'SELL': 0, 'BUY_PRODUCT': 1, 'BUY_LAND': 2, 'BUY_ANIMAL': 3, 'HIRE': 4, 'BUY_SEED': 5}
    ranked = sorted(enumerate(orders), key=lambda entry: (priority.get(str(entry[1][0]), 99), entry[0]))
    return [order for _, order in ranked[:MAX_MARKET_ORDERS]]

def decide(observation: dict[str, Any], target_wheat_tiles: int=TARGET_WHEAT_TILES, target_daily_hands: int=TARGET_DAILY_HANDS, pressure_aware: bool=True, target_market_animals: int=TARGET_TOTAL_MARKET_ANIMALS) -> dict[str, Any]:
    """Invest in all land, replay-staged livestock, and adaptive labor."""
    player = int(observation['player'])
    farm = observation['farms'][player]
    private = observation['private']
    day = int(observation['day'])
    hour = int(observation['hour'])
    if pressure_aware:
        target_cows, target_sheep, target_daily_hands, target_extra_land = _pressure_targets(observation, player, target_daily_hands, target_market_animals)
    else:
        target_cows = TARGET_COWS
        target_sheep = TARGET_SHEEP
        target_extra_land = TARGET_EXTRA_LAND
    desired_plans = _staged_animal_plans(day, target_cows, target_sheep)
    active_plans = _unlocked_animal_plans(desired_plans, farm)
    baseline = decide_wheat(observation, target_wheat_tiles=target_wheat_tiles, last_planting_day=LAST_WHEAT_PLANTING_DAY)
    baseline_market = _protect_feed_reserve(baseline['market'], active_plans, day, farm, private, True)
    farmer_action, hands_actions = _worker_actions(active_plans, {plan['position'] for plan in desired_plans}, day, farm, private, True, True)
    urgent, sales = _investment_livestock_orders(active_plans, day, farm, private)
    market = _investment_market_orders(sales, urgent, _land_orders(day, hour, farm, target_extra_land), _scale_hire_orders(day, hour, farm, target_daily_hands, True), baseline_market)
    return {'farmer': farmer_action, 'hands': hands_actions, 'market': market}
'Center-first crop layout with persistent near and far worker zones.'
from typing import Any
NEAR_CREW_SIZE = 5
SHED_CENTER = (4, 4)

def _zoned_hire_orders(farm: dict[str, Any], target_daily_hands: int) -> list[list[str]]:
    missing = max(0, target_daily_hands - len(farm.get('hands', [])))
    return [['HIRE'] for _ in range(missing)]

def _unlocked(position: tuple[int, int], farm: dict[str, Any]) -> bool:
    x, y = position
    half = len(farm['tiles']) // 2
    quadrant = ('N' if y < half else 'S') + ('W' if x < half else 'E')
    return quadrant in farm.get('unlocked_quadrants', [])

def _crop_priority(position: tuple[int, int], zone: str) -> tuple[int, int, int, int]:
    x, y = position
    half = 5
    preferred = zone == 'near' and x < half and (y < half) or (zone == 'far' and x >= half and (y < half))
    return (0 if preferred else 1, _distance(position, SHED_CENTER), abs(y - 4), abs(x - 4))

def _zoned_task_groups(day: int, farm: dict[str, Any], private: dict[str, Any], livestock_tiles: set[tuple[int, int]], zone: str) -> list[list[tuple[tuple[int, int], list[str]]]]:
    urgent_water: list[tuple[tuple[int, int], list[str]]] = []
    daily_water: list[tuple[tuple[int, int], list[str]]] = []
    harvest: list[tuple[tuple[int, int], list[str]]] = []
    empty: list[tuple[tuple[int, int], list[str]]] = []
    for y, row in enumerate(farm['tiles']):
        for x, tile in enumerate(row):
            position = (x, y)
            if position in livestock_tiles or not _unlocked(position, farm):
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
    global_key = lambda task: (_distance(task[0], SHED_CENTER), task[0][1], task[0][0])
    urgent_water.sort(key=global_key)
    daily_water.sort(key=global_key)
    harvest.sort(key=global_key)
    key = lambda task: _crop_priority(task[0], zone)
    empty.sort(key=key)
    planting_open = day <= LAST_WHEAT_PLANTING_DAY
    available_seeds = int(private.get('seeds', {}).get('WHEAT', 0))
    plants = empty[:available_seeds] if planting_open else []
    return [urgent_water, daily_water, harvest, plants]

def _assign_zoned_crops(day: int, farm: dict[str, Any], private: dict[str, Any], positions: list[tuple[int, int]], actions: list[list[str] | None], livestock_tiles: set[tuple[int, int]]) -> None:
    reserved: set[tuple[int, int]] = set()
    for worker, position in enumerate(positions):
        if actions[worker] is not None:
            continue
        zone = 'near' if worker < NEAR_CREW_SIZE else 'far'
        groups = _zoned_task_groups(day, farm, private, livestock_tiles, zone)
        group = next((tasks for tasks in groups[:-1] if any((target not in reserved for target, _ in tasks))), [])
        available = [task for task in group if task[0] not in reserved]
        if not available:
            continue
        target, operation = min(available, key=lambda task: (_crop_priority(task[0], zone) if task[1][0] == 'PLANT' else (0, 0, 0, 0), _distance(position, task[0])))
        reserved.add(target)
        actions[worker] = _act_at_or_move(position, target, operation)
    available_seeds = int(private.get('seeds', {}).get('WHEAT', 0))
    for zone in ('near', 'far'):
        workers = [worker for worker, action in enumerate(actions) if action is None and ('near' if worker < NEAR_CREW_SIZE else 'far') == zone]
        while len(workers) >= 2 and available_seeds > 0:
            planter, waterer = workers[:2]
            workers = workers[2:]
            plants = _zoned_task_groups(day, farm, private, livestock_tiles, zone)[-1]
            candidates = [task for task in plants if task[0] not in reserved]
            if not candidates:
                break
            target, _ = min(candidates, key=lambda task: (_crop_priority(task[0], zone), max(_distance(positions[planter], task[0]), _distance(positions[waterer], task[0])), _distance(positions[planter], task[0]) + _distance(positions[waterer], task[0])))
            reserved.add(target)
            if positions[planter] == target and positions[waterer] == target:
                actions[planter] = ['PLANT', 'WHEAT']
                actions[waterer] = ['WATER']
                available_seeds -= 1
                continue
            actions[planter] = ['PASS'] if positions[planter] == target else _act_at_or_move(positions[planter], target, ['PASS'])
            actions[waterer] = ['PASS'] if positions[waterer] == target else _act_at_or_move(positions[waterer], target, ['PASS'])
    for worker, action in enumerate(actions):
        if action is None:
            actions[worker] = ['PASS']

def _zoned_worker_actions(animal_plans: tuple[dict[str, Any], ...], livestock_tiles: set[tuple[int, int]], day: int, farm: dict[str, Any], private: dict[str, Any]) -> tuple[list[str], list[list[str]]]:
    positions = [tuple(farm['farmer']), *(tuple(position) for position in farm.get('hands', []))]
    inventories = _inventories(private, len(positions))
    actions: list[list[str] | None] = [None for _ in positions]
    _assign_urgent_feeding(animal_plans, day, farm, private, positions, inventories, actions, True)
    _assign_setup(animal_plans, farm, private, positions, inventories, actions)
    _assign_animal_services(animal_plans, day, farm, positions, actions, True)
    _assign_zoned_crops(day, farm, private, positions, actions, livestock_tiles)
    resolved = [action or ['PASS'] for action in actions]
    return (resolved[0], resolved[1:])

def decide(observation: dict[str, Any], target_wheat_tiles: int=TARGET_WHEAT_TILES, target_daily_hands: int=TARGET_DAILY_HANDS, target_extra_land: int=0, target_cows: int=TARGET_COWS, target_sheep: int=TARGET_SHEEP) -> dict[str, Any]:
    """Run pressure-aware investment with center-first zoned crop crews."""
    player = int(observation['player'])
    farm = observation['farms'][player]
    private = observation['private']
    day = int(observation['day'])
    hour = int(observation['hour'])
    desired_plans = _staged_animal_plans(day, target_cows, target_sheep)
    active_plans = _unlocked_animal_plans(desired_plans, farm)
    baseline = decide_wheat(observation, target_wheat_tiles=target_wheat_tiles, last_planting_day=LAST_WHEAT_PLANTING_DAY)
    baseline_market = _protect_feed_reserve(baseline['market'], active_plans, day, farm, private, True)
    farmer_action, hands_actions = _zoned_worker_actions(active_plans, {plan['position'] for plan in desired_plans}, day, farm, private)
    urgent, sales = _investment_livestock_orders(active_plans, day, farm, private)
    market = _investment_market_orders(sales, urgent, _land_orders(day, hour, farm, target_extra_land), _zoned_hire_orders(farm, target_daily_hands), baseline_market)
    return {'farmer': farmer_action, 'hands': hands_actions, 'market': market}
'Measured NE expansion bundle using safe zoned crop routing.'
from typing import Any
'Deadline-aware farming with stable animal and crop crew ownership.'
from collections import Counter
from typing import Any
ANIMAL_CREW_SIZE = 7
CROP_PAIR_COUNT = 3
MAX_WHEAT_PER_PAIR = 6
MAX_ASSIST_DISTANCE = 2
TARGET_DAILY_HANDS = 12
TARGET_COWS = 6
TARGET_SHEEP = 8
TARGET_EXTRA_LAND = 1
WHEAT_DEMAND_SHOPS = {'BAKERY', 'BRUNCH_SPOT', 'FARMERS_MARKET', 'ICE_CREAM_SHOP', 'PIZZA_SHOP'}

def _pair_owner(position: tuple[int, int], pair_count: int) -> int:
    x, _ = position
    return min(pair_count - 1, x * pair_count // 10)

def _effective_pair_count(target_daily_hands: int, animal_crew_size: int) -> int:
    total_workers = 1 + target_daily_hands
    crop_workers = max(0, total_workers - animal_crew_size)
    return min(CROP_PAIR_COUNT, crop_workers // 2)

def _plant_priority(position: tuple[int, int], pair: int, pair_count: int) -> tuple[int, int, int]:
    center_x = min(9, (2 * pair + 1) * 10 // (2 * pair_count))
    return (_distance(position, (center_x, 4)), abs(position[1] - 4), position[0])

def _demand_capacity(observation: dict[str, Any]) -> int:
    shops = observation.get('town', {}).get('unlocked_shops', [])
    wheat_shops = sum((shop in WHEAT_DEMAND_SHOPS for shop in shops))
    wheat_price = int(observation.get('market', {}).get('prices', {}).get('WHEAT', 0))
    return 6 if wheat_shops >= 2 or wheat_price >= 35 else 5

def _daily_hand_target(day: int, maximum_hands: int) -> int:
    if day >= 29:
        return min(maximum_hands, 2)
    if day == 28:
        return min(maximum_hands, 5)
    if day >= 26:
        return min(maximum_hands, 8)
    if day == 25:
        return min(maximum_hands, 10)
    return maximum_hands

def _crop_task_groups(day: int, farm: dict[str, Any], livestock_tiles: set[tuple[int, int]], *, pair: int, pair_count: int, max_wheat_per_pair: int=MAX_WHEAT_PER_PAIR) -> dict[str, list[tuple[int, int]]]:
    groups: dict[str, list[tuple[int, int]]] = {'urgent_water': [], 'deadline_harvest': [], 'harvest': [], 'yield_water': [], 'plant': []}
    active_wheat = 0
    ages: dict[tuple[int, int], int] = {}
    for y, row in enumerate(farm['tiles']):
        for x, tile in enumerate(row):
            position = (x, y)
            if position in livestock_tiles or not _unlocked(position, farm) or _pair_owner(position, pair_count) != pair:
                continue
            if _is_wheat(tile):
                active_wheat += 1
                age = day - int(tile['planted_day'])
                ages[position] = age
                if _is_mature_wheat(tile, day) and age >= 5:
                    groups['deadline_harvest'].append(position)
                elif not tile.get('watered_today', False):
                    if int(tile.get('consecutive_unwatered', 0)) >= 1:
                        groups['urgent_water'].append(position)
                    elif 2 <= age <= 4:
                        groups['yield_water'].append(position)
                elif _is_mature_wheat(tile, day):
                    groups['harvest'].append(position)
            elif tile is None:
                groups['plant'].append(position)
    task_key = lambda position: (_plant_priority(position, pair, pair_count), position[1], position[0])
    groups['urgent_water'].sort(key=lambda position: (-ages[position], task_key(position)))
    groups['deadline_harvest'].sort(key=lambda position: (-ages[position], task_key(position)))
    groups['harvest'].sort(key=lambda position: (-ages[position], task_key(position)))
    groups['yield_water'].sort(key=lambda position: (-ages[position], task_key(position)))
    groups['plant'].sort(key=task_key)
    if active_wheat >= max_wheat_per_pair or day > LAST_WHEAT_PLANTING_DAY:
        groups['plant'] = []
    return groups

def _assign_tasks(workers: list[int], positions: list[tuple[int, int]], actions: list[list[str] | None], targets: list[tuple[int, int]], operation: list[str], reserved: set[tuple[int, int]]) -> None:
    for worker in workers:
        if actions[worker] is not None:
            continue
        available = [target for target in targets if target not in reserved]
        if not available:
            return
        target = min(available, key=lambda candidate: (_distance(positions[worker], candidate), candidate[1], candidate[0]))
        reserved.add(target)
        actions[worker] = _act_at_or_move(positions[worker], target, operation)

def _assign_lifecycle_crops(day: int, farm: dict[str, Any], private: dict[str, Any], positions: list[tuple[int, int]], actions: list[list[str] | None], livestock_tiles: set[tuple[int, int]], *, animal_crew_size: int, max_wheat_per_pair: int) -> None:
    crop_workers = list(range(animal_crew_size, len(positions)))
    pair_count = min(CROP_PAIR_COUNT, len(crop_workers) // 2)
    if pair_count <= 0:
        return
    reserved: set[tuple[int, int]] = set()
    pair_groups = [_crop_task_groups(day, farm, livestock_tiles, pair=pair, pair_count=pair_count, max_wheat_per_pair=max_wheat_per_pair) for pair in range(pair_count)]
    operation_by_group = {'urgent_water': ['WATER'], 'deadline_harvest': ['HARVEST'], 'harvest': ['HARVEST'], 'yield_water': ['WATER']}
    for pair, groups in enumerate(pair_groups):
        workers = crop_workers[2 * pair:2 * pair + 2]
        for group_name in ('urgent_water', 'deadline_harvest', 'harvest', 'yield_water'):
            _assign_tasks(workers, positions, actions, groups[group_name], operation_by_group[group_name], reserved)
    urgent_targets = [target for groups in pair_groups for target in groups['urgent_water'] if target not in reserved]
    for worker, action in enumerate(actions):
        if action is not None:
            continue
        nearby = [target for target in urgent_targets if target not in reserved and _distance(positions[worker], target) <= MAX_ASSIST_DISTANCE]
        if not nearby:
            continue
        target = min(nearby, key=lambda candidate: (_distance(positions[worker], candidate), candidate[1], candidate[0]))
        reserved.add(target)
        actions[worker] = _act_at_or_move(positions[worker], target, ['WATER'])
    seed_budget = int(private.get('seeds', {}).get('WHEAT', 0))
    for pair, groups in enumerate(pair_groups):
        workers = crop_workers[2 * pair:2 * pair + 2]
        if len(workers) < 2 or any((actions[worker] is not None for worker in workers)):
            continue
        candidates = [target for target in groups['plant'] if target not in reserved]
        if seed_budget <= 0:
            continue
        if not candidates:
            continue
        target = min(candidates, key=lambda candidate: (max(_distance(positions[workers[0]], candidate), _distance(positions[workers[1]], candidate)), sum((_distance(positions[worker], candidate) for worker in workers)), candidate[1], candidate[0]))
        reserved.add(target)
        if all((positions[worker] == target for worker in workers)):
            actions[workers[0]] = ['PLANT', 'WHEAT']
            actions[workers[1]] = ['WATER']
            seed_budget -= 1
        else:
            for worker in workers:
                actions[worker] = ['PASS'] if positions[worker] == target else _act_at_or_move(positions[worker], target, ['PASS'])

def _assign_idle_current_animal_services(animal_plans: tuple[dict[str, Any], ...], day: int, farm: dict[str, Any], positions: list[tuple[int, int]], actions: list[list[str] | None], *, first_assistant: int) -> None:
    reserved: set[str] = set()
    for worker in range(first_assistant, len(positions)):
        if actions[worker] is not None:
            continue
        candidates: list[tuple[int, int, dict[str, Any], list[str]]] = []
        for order, plan in enumerate(animal_plans):
            if str(plan['id']) in reserved or not _plan_is_active(plan, farm['tiles']):
                continue
            distance = _distance(positions[worker], plan['position'])
            if distance > MAX_ASSIST_DISTANCE:
                continue
            tile = _tile_at(farm['tiles'], plan['position'])
            operation = None
            priority = 99
            if tile.get('fertilizer_available', False) and day <= 28:
                operation = ['COLLECT_FERTILIZER']
                priority = 0
            elif int(tile.get('yield_units', 0)) >= int(plan['max_held']):
                operation = ['HARVEST']
                priority = 1
            elif day <= 27 and tile.get('fed_today', False) and (not tile.get('cared_today', False)):
                operation = ['CARE']
                priority = 2
            if operation is not None:
                candidates.append((priority, distance, plan, operation))
        if not candidates:
            continue
        _, _, plan, operation = min(candidates, key=lambda candidate: (candidate[0], candidate[1], candidate[2]['position'][1], candidate[2]['position'][0]))
        reserved.add(str(plan['id']))
        actions[worker] = _act_at_or_move(positions[worker], plan['position'], operation)

def _final_day_liquidation_actions(animal_plans: tuple[dict[str, Any], ...], hour: int, farm: dict[str, Any], private: dict[str, Any], market: dict[str, Any]) -> tuple[list[str], list[list[str]]]:
    positions = [tuple(farm['farmer']), *(tuple(position) for position in farm.get('hands', []))]
    tiles = farm['tiles']
    shed_tiles = _shed_access_tiles(len(tiles))
    inventories = _inventories(private, len(positions))
    prices = market.get('prices', {})
    reserved: set[tuple[str, str]] = set()
    actions: list[list[str]] = []
    for position, inventory in zip(positions, inventories):
        candidates: list[tuple[float, int, int, str, tuple[int, int], list[str]]] = []
        for plan in animal_plans:
            if not _plan_is_active(plan, tiles):
                continue
            target = tuple(plan['position'])
            distance = _distance(position, target)
            return_distance = min((_distance(target, shed_tile) for shed_tile in shed_tiles))
            if hour + distance + 1 + return_distance > 22:
                continue
            tile = _tile_at(tiles, target)
            plan_id = str(plan['id'])
            units = int(tile.get('yield_units', 0))
            if units > 0 and (plan_id, 'HARVEST') not in reserved:
                product = str(plan['product'])
                value = int(prices.get(product, 0)) * units
                candidates.append((value / (distance + 1), value, -distance, plan_id, target, ['HARVEST']))
            if tile.get('fertilizer_available', False) and (plan_id, 'COLLECT_FERTILIZER') not in reserved:
                value = int(prices.get('FERTILIZER', 0))
                candidates.append((value / (distance + 1), value, -distance, plan_id, target, ['COLLECT_FERTILIZER']))
        if candidates:
            _, _, _, plan_id, target, operation = max(candidates, key=lambda candidate: (candidate[0], candidate[1], candidate[2], -candidate[4][1], -candidate[4][0]))
            reserved.add((plan_id, operation[0]))
            actions.append(_act_at_or_move(position, target, operation))
            continue
        carried = sum((int(inventory.get(item, 0)) for item in ('MILK', 'WOOL', 'FERTILIZER')))
        if carried <= 0:
            actions.append(['PASS'])
            continue
        target = min(shed_tiles, key=lambda shed_tile: (_distance(position, shed_tile), shed_tile[1], shed_tile[0]))
        if position == target:
            actions.append(['DROP'])
        elif hour + _distance(position, target) <= 22:
            actions.append(_act_at_or_move(position, target, ['DROP']))
        else:
            actions.append(['PASS'])
    return (actions[0], actions[1:])

def _lifecycle_worker_actions(animal_plans: tuple[dict[str, Any], ...], livestock_tiles: set[tuple[int, int]], day: int, farm: dict[str, Any], private: dict[str, Any], max_wheat_per_pair: int, animal_crew_size: int) -> tuple[list[str], list[list[str]]]:
    positions = [tuple(farm['farmer']), *(tuple(position) for position in farm.get('hands', []))]
    inventories = _inventories(private, len(positions))
    actions: list[list[str] | None] = [None for _ in positions]
    tiles = farm['tiles']
    emergency_plans = tuple((plan for plan in animal_plans if _plan_is_active(plan, tiles) and _feed_due(day, _tile_at(tiles, plan['position']), False)))
    emergency_ids = {str(plan['id']) for plan in emergency_plans}
    _assign_urgent_feeding(emergency_plans, day, farm, private, positions, inventories, actions, False)
    crew_count = min(animal_crew_size, len(positions))
    crew_positions = positions[:crew_count]
    crew_inventories = inventories[:crew_count]
    crew_actions = actions[:crew_count]
    normal_plans = tuple((plan for plan in animal_plans if str(plan['id']) not in emergency_ids))
    _assign_urgent_feeding(normal_plans, day, farm, private, crew_positions, crew_inventories, crew_actions, True)
    _assign_setup(animal_plans, farm, private, crew_positions, crew_inventories, crew_actions)
    _assign_animal_services(animal_plans, day, farm, crew_positions, crew_actions, True)
    actions[:crew_count] = crew_actions
    _assign_lifecycle_crops(day, farm, private, positions, actions, livestock_tiles, animal_crew_size=animal_crew_size, max_wheat_per_pair=max_wheat_per_pair)
    _assign_idle_current_animal_services(animal_plans, day, farm, positions, actions, first_assistant=crew_count)
    resolved = [action or ['PASS'] for action in actions]
    return (resolved[0], resolved[1:])

def _lifecycle_livestock_orders(animal_plans: tuple[dict[str, Any], ...], day: int, farm: dict[str, Any], private: dict[str, Any], *, projected_drop_workers: set[int] | None=None) -> tuple[list[list[Any]], list[list[Any]]]:
    tiles = farm['tiles']
    shed = private.get('shed', {})
    carried = Counter()
    for inventory in private.get('inventories', []):
        if isinstance(inventory, dict):
            carried.update(inventory)
    urgent: list[list[Any]] = []
    sales: list[list[Any]] = []
    if day <= 20:
        desired = Counter((str(plan['animal']) for plan in animal_plans))
        present = Counter((str(plan['animal']) for plan in animal_plans if _plan_is_active(plan, tiles)))
        for animal in ('COW', 'SHEEP'):
            missing = max(0, desired[animal] - present[animal] - int(shed.get(animal, 0)) - int(carried.get(animal, 0)))
            if missing > 0:
                urgent.append(['BUY_ANIMAL', animal, min(missing, 2)])
    feed_needed = sum((_feed_due(day, _tile_at(tiles, plan['position']), True) for plan in animal_plans if _plan_is_active(plan, tiles)))
    available_feed = int(shed.get('WHEAT', 0)) + int(carried.get('WHEAT', 0))
    if feed_needed > available_feed:
        urgent.append(['BUY_PRODUCT', 'WHEAT', feed_needed - available_feed])
    for item in ('MILK', 'WOOL', 'FERTILIZER'):
        quantity = int(shed.get(item, 0))
        inventories = private.get('inventories', [])
        for worker in projected_drop_workers or set():
            if worker < len(inventories) and isinstance(inventories[worker], dict):
                quantity += int(inventories[worker].get(item, 0))
        if quantity > 0:
            sales.append(['SELL', item, quantity])
    return (urgent, sales)

def decide(observation: dict[str, Any], max_wheat_per_pair: int=MAX_WHEAT_PER_PAIR, target_daily_hands: int=TARGET_DAILY_HANDS, target_extra_land: int=TARGET_EXTRA_LAND, target_cows: int=TARGET_COWS, target_sheep: int=TARGET_SHEEP, animal_crew_size: int=ANIMAL_CREW_SIZE) -> dict[str, Any]:
    """Run stable crews with crop lifecycle admission control."""
    player = int(observation['player'])
    farm = observation['farms'][player]
    private = observation['private']
    day = int(observation['day'])
    hour = int(observation['hour'])
    target_wheat_tiles = max(0, _effective_pair_count(target_daily_hands, animal_crew_size) * max_wheat_per_pair)
    desired_plans = _staged_animal_plans(day, target_cows, target_sheep)
    final_plans = _staged_animal_plans(29, target_cows, target_sheep)
    active_plans = _unlocked_animal_plans(desired_plans, farm)
    baseline = decide_wheat(observation, target_wheat_tiles=target_wheat_tiles, last_planting_day=LAST_WHEAT_PLANTING_DAY)
    baseline_market = _protect_feed_reserve(baseline['market'], active_plans, day, farm, private, True)
    if day == 29:
        farmer_action, hands_actions = _final_day_liquidation_actions(active_plans, hour, farm, private, observation.get('market', {}))
    else:
        farmer_action, hands_actions = _lifecycle_worker_actions(active_plans, {plan['position'] for plan in final_plans}, day, farm, private, max_wheat_per_pair, animal_crew_size)
    worker_actions = [farmer_action, *hands_actions]
    urgent, sales = _lifecycle_livestock_orders(active_plans, day, farm, private, projected_drop_workers={worker for worker, action in enumerate(worker_actions) if action == ['DROP']})
    market = _investment_market_orders(sales, urgent, _land_orders(day, hour, farm, target_extra_land), _zoned_hire_orders(farm, _daily_hand_target(day, target_daily_hands)), baseline_market)
    return {'farmer': farmer_action, 'hands': hands_actions, 'market': market}
'Compact lifecycle candidate matching the submitted NE labor footprint.'
from typing import Any
'Center-out, diversified farming challenger.'
from collections import Counter
from typing import Any
BOARD_SIZE = 10
LAND_SEQUENCE = ('NW', 'NE', 'SW')
MAX_STRAWBERRIES = 4
MAX_MELONS = 2
MAX_CROP_SLOTS_PER_QUADRANT = 6
ANIMAL_CREW_SIZE = 6
TARGET_DAILY_HANDS = 12
TARGET_EXTRA_LAND = 2
MAX_MARKET_ORDERS = 10
FERTILIZER_RESERVE_PER_STRAWBERRY = 2
CROP_DATA = {'WHEAT': {'seed_cost': 10, 'first_yield': 2, 'harvest_age': 4, 'last_plant_day': 22, 'productive_ages': {2, 3, 4}, 'ongoing': False}, 'CARROT': {'seed_cost': 20, 'first_yield': 2, 'harvest_age': 3, 'last_plant_day': 22, 'productive_ages': {2, 3}, 'ongoing': False}, 'TOMATO': {'seed_cost': 50, 'first_yield': 8, 'harvest_age': 11, 'last_plant_day': 17, 'productive_ages': {7, 8, 9, 10}, 'spent_age': 12, 'ongoing': True}, 'STRAWBERRY': {'seed_cost': 100, 'first_yield': 10, 'harvest_age': 16, 'last_plant_day': 12, 'productive_ages': {9, 11, 13, 15}, 'spent_age': 17, 'ongoing': True}, 'MELON': {'seed_cost': 80, 'first_yield': 10, 'harvest_age': 10, 'last_plant_day': 18, 'productive_ages': {6, 7, 8, 9, 10}, 'ongoing': False}}
ANIMAL_DATA = {'GOOSE': {'structure': 'COOP', 'product': 'EGG', 'cost': 300, 'max_held': 4}, 'COW': {'structure': 'PASTURE', 'product': 'MILK', 'cost': 400, 'max_held': 6}, 'SHEEP': {'structure': 'PASTURE', 'product': 'WOOL', 'cost': 500, 'max_held': 6}}
CORE_ANIMAL_BLOCKS = {'NW': (34, 35, 44, 45), 'NE': (36, 37, 46, 47), 'SW': (54, 55, 64, 65)}
CENTER_OUT_BLOCKS = {'NW': (25, 24, 23, 33, 43, 15, 14, 13, 12, 22, 32, 42, 5, 4, 3, 2, 1, 11, 21, 31, 41), 'NE': (26, 27, 28, 38, 48, 16, 17, 18, 19, 29, 39, 49, 6, 7, 8, 9, 10, 20, 30, 40, 50), 'SW': (53, 63, 73, 74, 75, 52, 62, 72, 82, 83, 84, 85, 51, 61, 71, 81, 91, 92, 93, 94, 95)}
ANIMAL_BLOCK_LAYOUT = {'NW': ((45, 'COW'), (44, 'COW'), (35, 'SHEEP'), (34, 'SHEEP')), 'NE': ((46, 'COW'), (47, 'COW'), (36, 'SHEEP'), (37, 'SHEEP')), 'SW': ((55, 'COW'), (65, 'COW'), (54, 'SHEEP'), (64, 'SHEEP'))}
CROP_BLOCK_LAYOUT = {'NW': ((25, 'WHEAT'), (24, 'WHEAT'), (43, 'CARROT'), (15, 'TOMATO'), (14, 'STRAWBERRY'), (13, 'MELON')), 'NE': ((26, 'WHEAT'), (27, 'WHEAT'), (48, 'CARROT'), (16, 'TOMATO'), (17, 'STRAWBERRY'), (18, 'MELON')), 'SW': ((53, 'STRAWBERRY'), (63, 'STRAWBERRY'), (73, 'WHEAT'), (74, 'WHEAT'), (75, 'CARROT'), (52, 'TOMATO'))}

def block_to_position(block: int) -> tuple[int, int]:
    """Convert a one-based row-major block number into an (x, y) tile."""
    if not 1 <= block <= BOARD_SIZE * BOARD_SIZE:
        raise ValueError(f'Block must be between 1 and 100: {block}')
    index = block - 1
    return (index % BOARD_SIZE, index // BOARD_SIZE)

def _animal_plan(quadrant: str, block: int, animal: str, index: int) -> dict[str, Any]:
    data = ANIMAL_DATA[animal]
    return {'id': f'{quadrant.lower()}_{animal.lower()}_{index}', 'quadrant': quadrant, 'block': block, 'position': block_to_position(block), 'animal': animal, **data}
ANIMAL_PLANS = tuple((_animal_plan(quadrant, block, animal, index) for quadrant in LAND_SEQUENCE for index, (block, animal) in enumerate(ANIMAL_BLOCK_LAYOUT[quadrant], start=1)))
CROP_PLANS = tuple(({'id': f'{quadrant.lower()}_{crop.lower()}_{index}', 'quadrant': quadrant, 'block': block, 'position': block_to_position(block), 'crop': crop} for quadrant in LAND_SEQUENCE for index, (block, crop) in enumerate(CROP_BLOCK_LAYOUT[quadrant], start=1)))

def _active_plans(plans: tuple[dict[str, Any], ...], farm: dict[str, Any]) -> tuple[dict[str, Any], ...]:
    unlocked = set(farm.get('unlocked_quadrants', []))
    return tuple((plan for plan in plans if plan['quadrant'] in unlocked))

def _is_crop(tile: Any, crop: str | None=None) -> bool:
    return isinstance(tile, dict) and tile.get('kind') == 'PLANT' and (crop is None or tile.get('crop') == crop)

def _managed_crop_plans(farm: dict[str, Any], *, crop_plans: tuple[dict[str, Any], ...]=CROP_PLANS, max_slots_per_quadrant: int | None=MAX_CROP_SLOTS_PER_QUADRANT) -> tuple[dict[str, Any], ...]:
    unlocked = set(farm.get('unlocked_quadrants', []))
    managed: list[dict[str, Any]] = []
    for quadrant in LAND_SEQUENCE:
        if quadrant not in unlocked:
            continue
        quadrant_plans = tuple((candidate for candidate in crop_plans if candidate['quadrant'] == quadrant))
        if max_slots_per_quadrant is not None:
            quadrant_plans = quadrant_plans[:max_slots_per_quadrant]
        managed.extend(quadrant_plans)
    return tuple(managed)

def _crop_operations(day: int, tile: dict[str, Any]) -> set[str]:
    if not _is_crop(tile):
        return set()
    crop = str(tile['crop'])
    data = CROP_DATA[crop]
    age = day - int(tile['planted_day'])
    operations: set[str] = set()
    productive = age in data['productive_ages']
    if data['ongoing'] and age >= int(data['spent_age']):
        return {'HARVEST'} if int(tile.get('yield_units', 0)) > 0 else {'DIG'}
    if not data['ongoing'] and age > int(data['harvest_age']) and (int(tile.get('yield_units', 0)) > 0):
        return {'HARVEST'}
    if not tile.get('watered_today', False) and (int(tile.get('consecutive_unwatered', 0)) >= 1 or productive):
        operations.add('WATER')
    if data['ongoing']:
        if int(tile.get('yield_units', 0)) > 0:
            operations.add('HARVEST')
        if crop == 'STRAWBERRY' and productive and (int(tile.get('fertilized_until_day', -1)) < day):
            operations.add('FERTILIZE')
    elif age >= int(data['harvest_age']) and int(tile.get('yield_units', 0)) > 0 and (not (productive and (not tile.get('watered_today', False)))):
        operations.add('HARVEST')
    return operations

def _crop_task_groups(day: int, farm: dict[str, Any], plans: tuple[dict[str, Any], ...], *, unrestricted_one_time: bool=False) -> dict[str, list[dict[str, Any]]]:
    groups: dict[str, list[dict[str, Any]]] = {'urgent_water': [], 'deadline_harvest': [], 'harvest': [], 'dig': [], 'fertilize_water': [], 'productive_water': [], 'plant': []}
    active_one_time = sum((_is_crop(_tile_at(farm['tiles'], plan['position']), str(plan['crop'])) and (not CROP_DATA[str(plan['crop'])]['ongoing']) for plan in plans))
    for plan in plans:
        position = tuple(plan['position'])
        tile = _tile_at(farm['tiles'], position)
        crop = str(plan['crop'])
        data = CROP_DATA[crop]
        if tile is None:
            capacity_open = unrestricted_one_time or (not (plan['quadrant'] == 'NW' and crop in {'WHEAT', 'CARROT'} and (active_one_time >= 2)) and (not (crop == 'CARROT' and active_one_time >= 3)))
            last_plant_day = int(plan.get('last_plant_day', data['last_plant_day']))
            if day <= last_plant_day and capacity_open:
                groups['plant'].append(plan)
            continue
        if not _is_crop(tile, crop):
            groups['dig'].append(plan)
            continue
        operations = _crop_operations(day, tile)
        age = day - int(tile['planted_day'])
        if 'WATER' in operations and int(tile.get('consecutive_unwatered', 0)) >= 1:
            groups['urgent_water'].append(plan)
        if 'HARVEST' in operations:
            target_age = int(data['harvest_age'])
            group = 'deadline_harvest' if age > target_age else 'harvest'
            groups[group].append(plan)
        if 'DIG' in operations:
            groups['dig'].append(plan)
        if 'FERTILIZE' in operations and 'WATER' in operations:
            groups['fertilize_water'].append(plan)
            if plan in groups['urgent_water']:
                groups['urgent_water'].remove(plan)
        elif 'WATER' in operations and plan not in groups['urgent_water']:
            groups['productive_water'].append(plan)
    return groups

def _assign_group(workers: list[int], positions: list[tuple[int, int]], actions: list[list[str] | None], plans: list[dict[str, Any]], operation: list[str], reserved: set[tuple[int, int]]) -> None:
    for worker in workers:
        if actions[worker] is not None:
            continue
        available = [plan for plan in plans if tuple(plan['position']) not in reserved]
        if not available:
            return
        plan = min(available, key=lambda candidate: (_distance(positions[worker], candidate['position']), candidate['block']))
        target = tuple(plan['position'])
        reserved.add(target)
        actions[worker] = _act_at_or_move(positions[worker], target, operation)

def _assign_fertilized_strawberry(workers: list[int], plan: dict[str, Any], farm: dict[str, Any], private: dict[str, Any], positions: list[tuple[int, int]], inventories: list[dict[str, Any]], actions: list[list[str] | None]) -> bool:
    if len(workers) < 2 or any((actions[worker] is not None for worker in workers)):
        return False
    target = tuple(plan['position'])
    fertilizer_workers = [worker for worker in workers if int(inventories[worker].get('FERTILIZER', 0)) > 0]
    if fertilizer_workers:
        fertilizer_worker = fertilizer_workers[0]
        water_worker = next((worker for worker in workers if worker != fertilizer_worker))
        if all((positions[worker] == target for worker in workers)):
            actions[fertilizer_worker] = ['FERTILIZE']
            actions[water_worker] = ['WATER']
        else:
            for worker in workers:
                actions[worker] = _act_at_or_move(positions[worker], target, ['PASS'])
        return True
    if int(private.get('shed', {}).get('FERTILIZER', 0)) > 0:
        access_tiles = _shed_access_tiles(len(farm['tiles']))
        pickup_worker = min(workers, key=lambda worker: min((_distance(positions[worker], access) for access in access_tiles)))
        route_worker = next((worker for worker in workers if worker != pickup_worker))
        access = min(access_tiles, key=lambda candidate: _distance(positions[pickup_worker], candidate))
        actions[pickup_worker] = _act_at_or_move(positions[pickup_worker], access, ['PICKUP', 'FERTILIZER', 1])
        actions[route_worker] = _act_at_or_move(positions[route_worker], target, ['PASS'])
        return True
    water_worker = min(workers, key=lambda worker: _distance(positions[worker], target))
    actions[water_worker] = _act_at_or_move(positions[water_worker], target, ['WATER'])
    return True

def _assign_dual_crop_operation(workers: list[int], plan: dict[str, Any], positions: list[tuple[int, int]], actions: list[list[str] | None], first: list[str], second: list[str]) -> bool:
    if len(workers) < 2 or any((actions[worker] is not None for worker in workers)):
        return False
    target = tuple(plan['position'])
    if all((positions[worker] == target for worker in workers)):
        actions[workers[0]] = first
        actions[workers[1]] = second
    else:
        for worker in workers:
            actions[worker] = _act_at_or_move(positions[worker], target, ['PASS'])
    return True

def _assign_center_out_crops(day: int, farm: dict[str, Any], private: dict[str, Any], positions: list[tuple[int, int]], inventories: list[dict[str, Any]], actions: list[list[str] | None], *, animal_crew_size: int, crop_plans: tuple[dict[str, Any], ...] | None=None, unrestricted_one_time: bool=False, pair_quadrants: tuple[str, ...]=LAND_SEQUENCE) -> None:
    crop_workers = list(range(animal_crew_size, len(positions)))
    pair_count = min(len(pair_quadrants), len(crop_workers) // 2)
    reserved: set[tuple[int, int]] = set()
    seed_budget = Counter(private.get('seeds', {}))
    managed_plans = crop_plans or _managed_crop_plans(farm)
    for pair in range(pair_count):
        quadrant = pair_quadrants[pair]
        if quadrant not in farm.get('unlocked_quadrants', []):
            continue
        workers = crop_workers[2 * pair:2 * pair + 2]
        plans = tuple((plan for plan in managed_plans if plan['quadrant'] == quadrant))
        groups = _crop_task_groups(day, farm, plans, unrestricted_one_time=unrestricted_one_time)
        for group_name, operation in (('deadline_harvest', ['HARVEST']), ('dig', ['DIG'])):
            _assign_group(workers, positions, actions, groups[group_name], operation, reserved)
        tomato_dual = [plan for plan in groups['harvest'] if plan['crop'] == 'TOMATO' and plan in groups['urgent_water'] and (tuple(plan['position']) not in reserved)]
        if tomato_dual and _assign_dual_crop_operation(workers, tomato_dual[0], positions, actions, ['WATER'], ['HARVEST']):
            reserved.add(tuple(tomato_dual[0]['position']))
        for group_name, operation in (('urgent_water', ['WATER']), ('harvest', ['HARVEST'])):
            _assign_group(workers, positions, actions, groups[group_name], operation, reserved)
        combos = [plan for plan in groups['fertilize_water'] if tuple(plan['position']) not in reserved]
        if combos and _assign_fertilized_strawberry(workers, combos[0], farm, private, positions, inventories, actions):
            reserved.add(tuple(combos[0]['position']))
        _assign_group(workers, positions, actions, groups['productive_water'], ['WATER'], reserved)
        if len(workers) < 2 or any((actions[worker] is not None for worker in workers)):
            continue
        candidates = [plan for plan in groups['plant'] if seed_budget[str(plan['crop'])] > 0 and tuple(plan['position']) not in reserved]
        if not candidates:
            continue
        plan = candidates[0]
        target = tuple(plan['position'])
        reserved.add(target)
        if all((positions[worker] == target for worker in workers)):
            actions[workers[0]] = ['PLANT', str(plan['crop'])]
            actions[workers[1]] = ['WATER']
            seed_budget[str(plan['crop'])] -= 1
        else:
            for worker in workers:
                actions[worker] = _act_at_or_move(positions[worker], target, ['PASS'])
    urgent_targets = [tuple(plan['position']) for plan in managed_plans if _is_crop(_tile_at(farm['tiles'], plan['position'])) and (not _tile_at(farm['tiles'], plan['position']).get('watered_today', False)) and (int(_tile_at(farm['tiles'], plan['position']).get('consecutive_unwatered', 0)) >= 1)]
    for worker, action in enumerate(actions):
        if action is not None:
            continue
        nearby = [target for target in urgent_targets if target not in reserved and _distance(positions[worker], target) <= 2]
        if not nearby:
            continue
        target = min(nearby, key=lambda candidate: (_distance(positions[worker], candidate), candidate[1], candidate[0]))
        reserved.add(target)
        actions[worker] = _act_at_or_move(positions[worker], target, ['WATER'])

def _assign_global_crop_deadlines(day: int, farm: dict[str, Any], positions: list[tuple[int, int]], actions: list[list[str] | None], crop_plans: tuple[dict[str, Any], ...] | None=None) -> None:
    tasks: list[tuple[int, tuple[int, int], list[str]]] = []
    for plan in crop_plans or _managed_crop_plans(farm):
        position = tuple(plan['position'])
        tile = _tile_at(farm['tiles'], position)
        if not _is_crop(tile, str(plan['crop'])):
            continue
        operations = _crop_operations(day, tile)
        crop = str(plan['crop'])
        age = day - int(tile['planted_day'])
        if 'HARVEST' in operations and (not CROP_DATA[crop]['ongoing'] and age > int(CROP_DATA[crop]['harvest_age'])):
            tasks.append((0, position, ['HARVEST']))
        elif 'DIG' in operations:
            tasks.append((1, position, ['DIG']))
        elif 'WATER' in operations and int(tile.get('consecutive_unwatered', 0)) >= 1 and ('FERTILIZE' not in operations):
            tasks.append((2, position, ['WATER']))
    reserved: set[tuple[int, int]] = set()
    for worker, action in enumerate(actions):
        if action is not None:
            continue
        available = [task for task in tasks if task[1] not in reserved]
        if not available:
            return
        _, target, operation = min(available, key=lambda task: (task[0], _distance(positions[worker], task[1]), task[1][1], task[1][0]))
        reserved.add(target)
        actions[worker] = _act_at_or_move(positions[worker], target, operation)

def _assign_generic_setup(animal_plans: tuple[dict[str, Any], ...], farm: dict[str, Any], private: dict[str, Any], positions: list[tuple[int, int]], inventories: list[dict[str, Any]], actions: list[list[str] | None]) -> None:
    tiles = farm['tiles']
    reserved: set[str] = set()
    for worker, inventory in enumerate(inventories):
        if actions[worker] is not None:
            continue
        for animal in ANIMAL_DATA:
            if int(inventory.get(animal, 0)) <= 0:
                continue
            plan = next((candidate for candidate in animal_plans if candidate['animal'] == animal and candidate['id'] not in reserved and (not _plan_is_active(candidate, tiles)) and isinstance(_tile_at(tiles, candidate['position']), dict) and (_tile_at(tiles, candidate['position']).get('kind') == candidate['structure']) and ('animal' not in _tile_at(tiles, candidate['position']))), None)
            if plan is None:
                continue
            actions[worker] = _act_at_or_move(positions[worker], plan['position'], ['PLACE', animal])
            reserved.add(str(plan['id']))
            break
    for plan in animal_plans:
        if _plan_is_active(plan, tiles) or plan['id'] in reserved:
            continue
        tile = _tile_at(tiles, plan['position'])
        structure_ready = isinstance(tile, dict) and tile.get('kind') == plan['structure'] and ('animal' not in tile)
        if structure_ready:
            continue
        operation = [f"BUILD_{plan['structure']}"] if tile is None else ['DIG']
        if _assign_nearest(positions, actions, plan['position'], operation) is not None:
            reserved.add(str(plan['id']))
    virtual_shed = Counter(private.get('shed', {}))
    for inventory in inventories:
        for animal in ANIMAL_DATA:
            virtual_shed[animal] -= int(inventory.get(animal, 0))
    access_tiles = _shed_access_tiles(len(tiles))
    for plan in animal_plans:
        if _plan_is_active(plan, tiles) or plan['id'] in reserved:
            continue
        tile = _tile_at(tiles, plan['position'])
        if not (isinstance(tile, dict) and tile.get('kind') == plan['structure'] and ('animal' not in tile) and (virtual_shed[str(plan['animal'])] > 0)):
            continue
        available = [worker for worker, action in enumerate(actions) if action is None]
        if not available:
            break
        worker = min(available, key=lambda index: min((_distance(positions[index], access) for access in access_tiles)))
        access = min(access_tiles, key=lambda candidate: _distance(positions[worker], candidate))
        actions[worker] = _act_at_or_move(positions[worker], access, ['PICKUP', str(plan['animal']), 1])
        virtual_shed[str(plan['animal'])] -= 1
        reserved.add(str(plan['id']))

def _worker_actions(animal_plans: tuple[dict[str, Any], ...], day: int, farm: dict[str, Any], private: dict[str, Any], *, animal_crew_size: int=ANIMAL_CREW_SIZE, crop_plans: tuple[dict[str, Any], ...] | None=None, unrestricted_one_time: bool=False, pair_quadrants: tuple[str, ...]=LAND_SEQUENCE) -> tuple[list[str], list[list[str]]]:
    positions = [tuple(farm['farmer']), *(tuple(position) for position in farm.get('hands', []))]
    inventories = _inventories(private, len(positions))
    actions: list[list[str] | None] = [None for _ in positions]
    tiles = farm['tiles']
    emergency = tuple((plan for plan in animal_plans if _plan_is_active(plan, tiles) and _feed_due(day, _tile_at(tiles, plan['position']), False)))
    emergency_ids = {str(plan['id']) for plan in emergency}
    _assign_urgent_feeding(emergency, day, farm, private, positions, inventories, actions, False)
    crew_count = min(animal_crew_size, len(positions))
    crew_positions = positions[:crew_count]
    crew_inventories = inventories[:crew_count]
    crew_actions = actions[:crew_count]
    normal = tuple((plan for plan in animal_plans if str(plan['id']) not in emergency_ids))
    _assign_urgent_feeding(normal, day, farm, private, crew_positions, crew_inventories, crew_actions, True)
    _assign_generic_setup(animal_plans, farm, private, crew_positions, crew_inventories, crew_actions)
    _assign_animal_services(animal_plans, day, farm, crew_positions, crew_actions, True)
    actions[:crew_count] = crew_actions
    _assign_global_crop_deadlines(day, farm, positions, actions, crop_plans)
    _assign_center_out_crops(day, farm, private, positions, inventories, actions, animal_crew_size=animal_crew_size, crop_plans=crop_plans, unrestricted_one_time=unrestricted_one_time, pair_quadrants=pair_quadrants)
    _assign_idle_current_animal_services(animal_plans, day, farm, positions, actions, first_assistant=crew_count)
    resolved = [action or ['PASS'] for action in actions]
    return (resolved[0], resolved[1:])

def _daily_hand_target(day: int, farm: dict[str, Any], maximum_hands: int) -> int:
    if day >= 29:
        return min(maximum_hands, 4)
    return min(maximum_hands, 11)

def _land_orders(day: int, farm: dict[str, Any], target_extra_land: int) -> list[list[str]]:
    unlocked_extra = max(0, len(farm.get('unlocked_quadrants', [])) - 1)
    if unlocked_extra >= min(target_extra_land, 2) or day > 20:
        return []
    earliest = (6, 11)
    costs = (1000, 2000)
    reserves = (1200, 2200)
    if day < earliest[unlocked_extra]:
        return []
    if float(farm['money']) < costs[unlocked_extra] + reserves[unlocked_extra]:
        return []
    return [['BUY_LAND']]

def _livestock_orders(animal_plans: tuple[dict[str, Any], ...], day: int, farm: dict[str, Any], private: dict[str, Any]) -> list[list[Any]]:
    tiles = farm['tiles']
    shed = private.get('shed', {})
    carried = Counter()
    for inventory in private.get('inventories', []):
        if isinstance(inventory, dict):
            carried.update(inventory)
    orders: list[list[Any]] = []
    if day <= 20:
        desired = Counter((str(plan['animal']) for plan in animal_plans))
        present = Counter((str(plan['animal']) for plan in animal_plans if _plan_is_active(plan, tiles)))
        for animal in ANIMAL_DATA:
            missing = max(0, desired[animal] - present[animal] - int(shed.get(animal, 0)) - int(carried.get(animal, 0)))
            if missing > 0:
                orders.append(['BUY_ANIMAL', animal, min(missing, 2)])
    feed_needed = sum((_feed_due(day, _tile_at(tiles, plan['position']), True) for plan in animal_plans if _plan_is_active(plan, tiles)))
    available_feed = int(shed.get('WHEAT', 0)) + int(carried.get('WHEAT', 0))
    if feed_needed > available_feed:
        orders.insert(0, ['BUY_PRODUCT', 'WHEAT', feed_needed - available_feed])
    return orders

def _crop_seed_orders(day: int, farm: dict[str, Any], private: dict[str, Any], *, crop_plans: tuple[dict[str, Any], ...] | None=None, unrestricted_one_time: bool=False) -> list[list[Any]]:
    seeds = Counter(private.get('seeds', {}))
    orders: list[list[Any]] = []
    managed_plans = crop_plans or _managed_crop_plans(farm)
    for quadrant in LAND_SEQUENCE:
        if quadrant not in farm.get('unlocked_quadrants', []):
            continue
        plans = [plan for plan in managed_plans if plan['quadrant'] == quadrant]
        next_plan = next(iter(_crop_task_groups(day, farm, tuple(plans), unrestricted_one_time=unrestricted_one_time)['plant']), None)
        if next_plan is None:
            continue
        crop = str(next_plan['crop'])
        if seeds[crop] <= 0:
            orders.append(['BUY_SEED', crop, 1])
            seeds[crop] += 1
    return orders

def _fertilizer_reserve(day: int, farm: dict[str, Any]) -> int:
    if day >= 28:
        return 0
    strawberries = sum((plan['crop'] == 'STRAWBERRY' and day <= int(CROP_DATA['STRAWBERRY']['last_plant_day']) + 16 for plan in _active_plans(CROP_PLANS, farm)))
    return strawberries * FERTILIZER_RESERVE_PER_STRAWBERRY

def _sales_orders(day: int, farm: dict[str, Any], private: dict[str, Any], animal_plans: tuple[dict[str, Any], ...], projected_drop_workers: set[int] | None=None) -> list[list[Any]]:
    shed = private.get('shed', {})
    quantities = Counter({item: int(shed.get(item, 0)) for item in ('WHEAT', 'CARROT', 'TOMATO', 'STRAWBERRY', 'MELON', 'EGG', 'MILK', 'WOOL', 'FERTILIZER')})
    inventories = private.get('inventories', [])
    for worker in projected_drop_workers or set():
        if worker < len(inventories) and isinstance(inventories[worker], dict):
            quantities.update(inventories[worker])
    active_animals = sum((_plan_is_active(plan, farm['tiles']) for plan in animal_plans))
    feed_reserve = 0 if day >= 28 else 2 * active_animals
    quantities['WHEAT'] = max(0, quantities['WHEAT'] - feed_reserve)
    quantities['FERTILIZER'] = max(0, quantities['FERTILIZER'] - _fertilizer_reserve(day, farm))
    return [['SELL', item, quantities[item]] for item in ('MELON', 'STRAWBERRY', 'WOOL', 'MILK', 'EGG', 'TOMATO', 'CARROT', 'FERTILIZER', 'WHEAT') if quantities[item] > 0]

def _final_day_actions(animal_plans: tuple[dict[str, Any], ...], hour: int, farm: dict[str, Any], private: dict[str, Any], market: dict[str, Any]) -> tuple[list[str], list[list[str]]]:
    positions = [tuple(farm['farmer']), *(tuple(position) for position in farm.get('hands', []))]
    inventories = _inventories(private, len(positions))
    shed_tiles = _shed_access_tiles(len(farm['tiles']))
    prices = market.get('prices', {})
    products = {str(plan['product']) for plan in animal_plans}
    reserved: set[tuple[str, str]] = set()
    actions: list[list[str]] = []
    for position, inventory in zip(positions, inventories):
        candidates: list[tuple[float, int, int, str, tuple[int, int], list[str]]] = []
        for plan in animal_plans:
            if not _plan_is_active(plan, farm['tiles']):
                continue
            target = tuple(plan['position'])
            distance = _distance(position, target)
            return_distance = min((_distance(target, shed_tile) for shed_tile in shed_tiles))
            if hour + distance + 1 + return_distance > 22:
                continue
            tile = _tile_at(farm['tiles'], target)
            plan_id = str(plan['id'])
            units = int(tile.get('yield_units', 0))
            if units > 0 and (plan_id, 'HARVEST') not in reserved:
                value = int(prices.get(plan['product'], 0)) * units
                candidates.append((value / (distance + 1), value, -distance, plan_id, target, ['HARVEST']))
            if tile.get('fertilizer_available', False) and (plan_id, 'COLLECT_FERTILIZER') not in reserved:
                value = int(prices.get('FERTILIZER', 0))
                candidates.append((value / (distance + 1), value, -distance, plan_id, target, ['COLLECT_FERTILIZER']))
        if candidates:
            _, _, _, plan_id, target, operation = max(candidates, key=lambda candidate: (candidate[0], candidate[1], candidate[2], -candidate[4][1], -candidate[4][0]))
            reserved.add((plan_id, operation[0]))
            actions.append(_act_at_or_move(position, target, operation))
            continue
        carried = sum((int(inventory.get(item, 0)) for item in products | {'FERTILIZER'}))
        if carried <= 0:
            actions.append(['PASS'])
            continue
        target = min(shed_tiles, key=lambda candidate: (_distance(position, candidate), candidate[1], candidate[0]))
        if position == target:
            actions.append(['DROP'])
        elif hour + _distance(position, target) <= 22:
            actions.append(_act_at_or_move(position, target, ['DROP']))
        else:
            actions.append(['PASS'])
    return (actions[0], actions[1:])

def decide(observation: dict[str, Any], *, target_daily_hands: int=TARGET_DAILY_HANDS, target_extra_land: int=TARGET_EXTRA_LAND) -> dict[str, Any]:
    """Run diversified center-out cores through NW, NE, then SW."""
    player = int(observation['player'])
    farm = observation['farms'][player]
    private = observation['private']
    day = int(observation['day'])
    active_animals = _active_plans(ANIMAL_PLANS, farm)
    if day == 29:
        farmer_action, hands_actions = _final_day_actions(active_animals, int(observation['hour']), farm, private, observation.get('market', {}))
    else:
        farmer_action, hands_actions = _worker_actions(active_animals, day, farm, private)
    worker_actions = [farmer_action, *hands_actions]
    drop_workers = {worker for worker, action in enumerate(worker_actions) if action == ['DROP']}
    market = _investment_market_orders(_sales_orders(day, farm, private, active_animals, drop_workers), _livestock_orders(active_animals, day, farm, private), _land_orders(day, farm, target_extra_land), _zoned_hire_orders(farm, _daily_hand_target(day, farm, target_daily_hands)), _crop_seed_orders(day, farm, private))
    return {'farmer': farmer_action, 'hands': hands_actions, 'market': market[:MAX_MARKET_ORDERS]}
'Replay-grounded dense crop throughput challenger.'
from typing import Any
MAX_WHEAT_PER_PAIR = 18
TARGET_COWS = 6
TARGET_SHEEP = 6
TARGET_EXTRA_LAND = 2
MAX_MARKET_ORDERS = 10
HAND_TARGETS = (4, 4, 4, 4, 4, 4, 8, 8, 9, 10, 11, 12, 12, 12, 12, 12, 12, 12, 12, 12, 12, 12, 12, 12, 12, 12, 12, 12, 10, 8)
HIRE_COSTS = (1, 1, 2, 3, 5, 8, 13, 21, 34, 55, 89, 144, 233)
LAND_COSTS = (1000, 2000, 4000)
ANIMAL_COSTS = {'COW': 400, 'SHEEP': 500, 'GOOSE': 300}
SEED_COSTS = {'WHEAT': 10, 'CARROT': 20, 'TOMATO': 50, 'STRAWBERRY': 100, 'MELON': 80}

def _hand_target(day: int) -> int:
    return HAND_TARGETS[min(max(day, 0), len(HAND_TARGETS) - 1)]

def _animal_crew_size(day: int) -> int:
    if day < 6:
        return 3
    if day < 9:
        return 4
    if day < 11:
        return 5
    return 6

def _purchase_cost(order: list[Any], observation: dict[str, Any], hire_index: int) -> int:
    operation = str(order[0])
    if operation == 'HIRE':
        return HIRE_COSTS[min(hire_index, len(HIRE_COSTS) - 1)]
    if operation == 'BUY_LAND':
        player = int(observation['player'])
        unlocked = len(observation['farms'][player].get('unlocked_quadrants', []))
        return LAND_COSTS[min(max(0, unlocked - 1), len(LAND_COSTS) - 1)]
    if len(order) < 3:
        return 0
    item = str(order[1])
    quantity = int(order[2])
    if operation == 'BUY_ANIMAL':
        return ANIMAL_COSTS[item] * quantity
    if operation == 'BUY_SEED':
        return SEED_COSTS[item] * quantity
    if operation == 'BUY_PRODUCT':
        price = int(observation.get('market', {}).get('prices', {}).get(item, 0))
        return price * quantity
    return 0

def _affordable_market_orders(observation: dict[str, Any], orders: list[list[Any]]) -> list[list[Any]]:
    player = int(observation['player'])
    farm = observation['farms'][player]
    current_hands = len(farm.get('hands', []))
    prices = observation.get('market', {}).get('prices', {})
    priority = {'SELL': 0, 'BUY_PRODUCT': 1, 'HIRE': 2, 'BUY_LAND': 3, 'BUY_SEED': 4, 'BUY_ANIMAL': 5}
    ranked = sorted(enumerate(orders), key=lambda entry: (priority.get(str(entry[1][0]), 99), entry[0]))
    budget = float(farm.get('money', 0))
    selected: list[list[Any]] = []
    selected_hires = 0
    for _, order in ranked:
        if len(selected) >= MAX_MARKET_ORDERS:
            break
        operation = str(order[0])
        if operation == 'SELL':
            selected.append(order)
            if len(order) >= 3:
                item = str(order[1])
                quantity = int(order[2])
                budget += 0.75 * int(prices.get(item, 0)) * quantity
            continue
        hire_index = current_hands + selected_hires
        cost = _purchase_cost(order, observation, hire_index)
        if cost <= budget:
            selected.append(order)
            budget -= cost
            if operation == 'HIRE':
                selected_hires += 1
            continue
        if operation not in {'BUY_ANIMAL', 'BUY_SEED', 'BUY_PRODUCT'}:
            continue
        unit_order = [operation, order[1], 1]
        unit_cost = _purchase_cost(unit_order, observation, hire_index)
        affordable_quantity = min(int(order[2]), int(budget // unit_cost) if unit_cost > 0 else 0)
        if affordable_quantity <= 0:
            continue
        selected.append([operation, order[1], affordable_quantity])
        budget -= unit_cost * affordable_quantity
    return selected

def decide(observation: dict[str, Any]) -> dict[str, Any]:
    """Scale crop pairs, workers, livestock, and land on explicit day gates."""
    day = int(observation['day'])
    decision = decide_lifecycle(observation, max_wheat_per_pair=MAX_WHEAT_PER_PAIR, target_daily_hands=_hand_target(day), target_extra_land=TARGET_EXTRA_LAND, target_cows=TARGET_COWS, target_sheep=TARGET_SHEEP, animal_crew_size=_animal_crew_size(day))
    decision['market'] = _affordable_market_orders(observation, decision['market'])
    return decision
'Premium-crop throughput challenger derived from current top replays.'
from collections import Counter
from typing import Any
TARGET_EXTRA_LAND = 2
FERTILIZER_RESERVE = 0
HAND_TARGETS = (5, 4, 4, 4, 4, 4, 9, 9, 9, 12, 12, 12, 12, 12, 12, 12, 12, 12, 12, 12, 12, 12, 12, 12, 12, 12, 12, 12, 10, 8)
DENSE_CROP_TYPES = {'NW': (*('MELON' for _ in range(5)), *('STRAWBERRY' for _ in range(8)), *('WHEAT' for _ in range(8))), 'NE': (*('MELON' for _ in range(5)), *('STRAWBERRY' for _ in range(14)), *('WHEAT' for _ in range(2))), 'SW': (*('STRAWBERRY' for _ in range(13)), *('WHEAT' for _ in range(8)))}
LAST_PLANT_DAYS = {'MELON': 7, 'STRAWBERRY': 11, 'WHEAT': 22, 'CARROT': 22}
DENSE_CROP_PLANS = tuple(({'id': f'dense_{quadrant.lower()}_{crop.lower()}_{index}', 'quadrant': quadrant, 'block': block, 'position': block_to_position(block), 'crop': crop, 'first_plant_day': 23 if quadrant == 'SW' and crop == 'WHEAT' else 23 if quadrant == 'NE' and crop == 'WHEAT' else 4 if quadrant == 'NW' and crop == 'WHEAT' and (block in {1, 3, 4, 11}) else 0, **({'rotation_crop': 'STRAWBERRY', 'opening_last_plant_day': 1} if quadrant == 'NW' and crop == 'WHEAT' else {}), 'last_plant_day': 0 if crop == 'MELON' and quadrant == 'NW' else LAST_PLANT_DAYS[crop]} for quadrant in LAND_SEQUENCE for index, (block, crop) in enumerate(zip(CENTER_OUT_BLOCKS[quadrant], DENSE_CROP_TYPES[quadrant]), start=1)))

def _dense_crop_plans(farm: dict[str, Any], day: int=0, reserved_positions: set[tuple[int, int]] | None=None, rotation_crop: str='STRAWBERRY', late_rotation_crop: str | None=None, rotation_last_plant_day: int | None=None, late_rotation_last_plant_day: int | None=None, lifecycle_windows: bool=False, lifecycle_deadlines_only: bool=False) -> tuple[dict[str, Any], ...]:
    managed = _managed_crop_plans(farm, crop_plans=DENSE_CROP_PLANS, max_slots_per_quadrant=None)
    reserved_positions = reserved_positions or set()
    rotation_deadline = LAST_PLANT_DAYS[rotation_crop] if rotation_last_plant_day is None else rotation_last_plant_day
    late_rotation_deadline = LAST_PLANT_DAYS[late_rotation_crop] if late_rotation_crop is not None and late_rotation_last_plant_day is None else late_rotation_last_plant_day
    plans: list[dict[str, Any]] = []
    for plan in managed:
        if tuple(plan['position']) in reserved_positions:
            continue
        tile = _tile_at(farm['tiles'], plan['position'])
        current_crop = str(tile.get('crop')) if isinstance(tile, dict) and tile.get('kind') == 'PLANT' else None
        late_rotation_active = late_rotation_crop is not None and current_crop == late_rotation_crop
        late_rotation_due = late_rotation_crop is not None and tile is None and (day > int(plan['last_plant_day']) or int(plan.get('first_plant_day', 0)) > int(plan['last_plant_day']) or (plan.get('rotation_crop') is not None and day > rotation_deadline)) and (late_rotation_deadline is not None) and (day <= late_rotation_deadline)
        if late_rotation_active or late_rotation_due:
            plans.append({**plan, 'crop': late_rotation_crop, 'first_plant_day': 0, 'last_plant_day': late_rotation_deadline})
            continue
        if plan.get('rotation_crop') is None:
            plans.append(plan)
            continue
        if current_crop in {str(plan['crop']), str(rotation_crop)}:
            crop = current_crop
        elif 4 <= day <= rotation_deadline:
            crop = rotation_crop
        else:
            crop = str(plan['crop'])
        plans.append({**plan, 'crop': crop, 'last_plant_day': int(plan['opening_last_plant_day']) if crop == str(plan['crop']) and 'opening_last_plant_day' in plan else rotation_deadline if crop == rotation_crop else LAST_PLANT_DAYS[crop]})
    if not lifecycle_windows and (not lifecycle_deadlines_only):
        return tuple(plans)
    cashable_day = 28
    return tuple(({**plan, 'first_plant_day': int(plan.get('first_plant_day', 0)) if lifecycle_deadlines_only else 0, 'last_plant_day': cashable_day - int(CROP_DATA[str(plan['crop'])]['harvest_age'])} for plan in plans))

def _hand_target(day: int, hand_targets: tuple[int, ...]=HAND_TARGETS) -> int:
    return hand_targets[min(max(day, 0), len(hand_targets) - 1)]

def _pair_quadrants(day: int, farm: dict[str, Any]) -> tuple[str, ...]:
    unlocked = set(farm.get('unlocked_quadrants', []))
    if 'SW' in unlocked:
        return ('NW', 'NE', 'SW')
    if 'NE' in unlocked:
        if day <= 7:
            return ('NW', 'NW', 'NE')
        return ('NW', 'NE', 'NE')
    return ('NW', 'NW', 'NW')

def _crop_priority(day: int, crop: str) -> int:
    if day <= 1:
        return {'MELON': 0, 'WHEAT': 1, 'CARROT': 1, 'STRAWBERRY': 2}[crop]
    return {'STRAWBERRY': 0, 'MELON': 1, 'CARROT': 2, 'WHEAT': 3}[crop]

def _projected_sale_value(sales: list[list[Any]], market: dict[str, Any]) -> float:
    prices = market.get('prices', {})
    return sum((0.75 * int(prices.get(str(order[1]), 0)) * int(order[2]) for order in sales if len(order) >= 3 and order[0] == 'SELL'))

def _seed_orders(day: int, farm: dict[str, Any], private: dict[str, Any], crop_plans: tuple[dict[str, Any], ...], animal_crew_size: int, pair_quadrants: tuple[str, ...], seed_buffer_multiplier: int=1, wheat_seed_buffer_multiplier: int | None=None, extra_wheat_seed_buffer: int=0, reserve_seeds_per_quadrant: bool=False, max_active_crops_per_quadrant: int | None=None) -> list[list[Any]]:
    available_crop_workers = max(0, 1 + len(farm.get('hands', [])) - animal_crew_size)
    pair_count = min(len(pair_quadrants), available_crop_workers // 2)
    pairs_by_quadrant = Counter(pair_quadrants[:pair_count])
    seeds = Counter(private.get('seeds', {}))
    orders: list[list[Any]] = []
    remaining_wheat_extra = max(0, extra_wheat_seed_buffer)
    reserved_targets: Counter[str] = Counter()
    total_needed: Counter[str] = Counter()
    for quadrant in LAND_SEQUENCE:
        pair_capacity = pairs_by_quadrant[quadrant]
        if pair_capacity <= 0:
            continue
        plans = tuple((plan for plan in crop_plans if plan['quadrant'] == quadrant))
        remaining_capacity = None if max_active_crops_per_quadrant is None else max(0, max_active_crops_per_quadrant - sum((_is_crop(_tile_at(farm['tiles'], plan['position'])) for plan in plans)))
        plantable = [plan for plan in plans if _tile_at(farm['tiles'], plan['position']) is None and day >= int(plan.get('first_plant_day', 0)) and (day <= int(plan['last_plant_day']))]
        if remaining_capacity is not None:
            plantable = plantable[:remaining_capacity]
        needed = Counter((str(plan['crop']) for plan in plantable))
        total_needed.update(needed)
        crops = sorted(('MELON', 'STRAWBERRY', 'CARROT', 'WHEAT'), key=lambda crop: _crop_priority(day, crop))
        for crop in crops:
            if crop == 'STRAWBERRY' and day < 2:
                continue
            base_target = pair_capacity * (wheat_seed_buffer_multiplier if crop == 'WHEAT' and wheat_seed_buffer_multiplier is not None else seed_buffer_multiplier)
            extra_target = min(remaining_wheat_extra, needed[crop]) if crop == 'WHEAT' else 0
            target_buffer = min(needed[crop], base_target + extra_target)
            if crop == 'WHEAT':
                remaining_wheat_extra -= max(0, target_buffer - base_target)
            if reserve_seeds_per_quadrant:
                reserved_targets[crop] += target_buffer
                continue
            missing = max(0, target_buffer - seeds[crop])
            if missing <= 0:
                continue
            orders.append(['BUY_SEED', crop, missing])
            seeds[crop] += missing
    if reserve_seeds_per_quadrant:
        reserved_targets['WHEAT'] = min(total_needed['WHEAT'], reserved_targets['WHEAT'] + remaining_wheat_extra)
        crops = sorted(('MELON', 'STRAWBERRY', 'CARROT', 'WHEAT'), key=lambda crop: _crop_priority(day, crop))
        return [['BUY_SEED', crop, reserved_targets[crop] - seeds[crop]] for crop in crops if reserved_targets[crop] > seeds[crop]]
    return orders

def _assign_crop_tasks(day: int, farm: dict[str, Any], crop_plans: tuple[dict[str, Any], ...], positions: list[tuple[int, int]], actions: list[list[str] | None], *, critical: bool, prioritize_mature_harvest: bool=False, excluded_targets: set[tuple[int, int]] | None=None) -> set[tuple[int, int]]:
    tasks: list[tuple[int, tuple[int, int], list[str]]] = []
    for plan in crop_plans:
        target = tuple(plan['position'])
        tile = _tile_at(farm['tiles'], target)
        if tile is None:
            continue
        if not _is_crop(tile, str(plan['crop'])):
            if critical:
                tasks.append((0, target, ['DIG']))
            continue
        operations = _crop_operations(day, tile)
        age = day - int(tile['planted_day'])
        data = CROP_DATA[str(plan['crop'])]
        final_ongoing_age = bool(data['ongoing']) and age >= int(data['spent_age']) - 1
        proactive_dig = final_ongoing_age and int(tile.get('yield_units', 0)) <= 0
        overdue_harvest = 'HARVEST' in operations and (not bool(str(plan['crop']) in {'STRAWBERRY', 'TOMATO'})) and (age > 4)
        urgent_water = 'WATER' in operations and int(tile.get('consecutive_unwatered', 0)) >= 1
        if critical:
            if 'DIG' in operations or proactive_dig:
                tasks.append((0, target, ['DIG']))
            elif prioritize_mature_harvest and 'HARVEST' in operations and (not bool(data['ongoing'])) or overdue_harvest or (final_ongoing_age and 'HARVEST' in operations):
                tasks.append((0, target, ['HARVEST']))
            elif urgent_water:
                tasks.append((1, target, ['WATER']))
            continue
        if 'HARVEST' in operations:
            tasks.append((0, target, ['HARVEST']))
        elif 'WATER' in operations:
            tasks.append((1, target, ['WATER']))
    reserved = set(excluded_targets or ())
    for worker, action in enumerate(actions):
        if action is not None:
            continue
        available = [task for task in tasks if task[1] not in reserved]
        if not available:
            break
        _, target, operation = min(available, key=lambda task: (task[0], _distance(positions[worker], task[1]), task[1][1], task[1][0]))
        reserved.add(target)
        actions[worker] = _act_at_or_move(positions[worker], target, operation)
    return reserved

def _assign_paired_planting(day: int, farm: dict[str, Any], private: dict[str, Any], crop_plans: tuple[dict[str, Any], ...], positions: list[tuple[int, int]], actions: list[list[str] | None], seed_budget: Counter[str] | None=None, max_active_crops: int | None=None) -> None:
    free_workers = [worker for worker, action in enumerate(actions) if action is None]
    if seed_budget is None:
        seed_budget = Counter(private.get('seeds', {}))
    candidates = [plan for plan in crop_plans if _tile_at(farm['tiles'], plan['position']) is None and day >= int(plan.get('first_plant_day', 0)) and (day <= int(plan['last_plant_day'])) and (seed_budget[str(plan['crop'])] > 0)]
    plan_order = {str(plan['id']): index for index, plan in enumerate(crop_plans)}
    candidates.sort(key=lambda plan: (_crop_priority(day, str(plan['crop'])), plan_order[str(plan['id'])]))
    active_crops = sum((_is_crop(_tile_at(farm['tiles'], plan['position'])) for plan in crop_plans))
    remaining_capacity = len(candidates) if max_active_crops is None else max(0, max_active_crops - active_crops)
    reserved: set[tuple[int, int]] = set()
    while len(free_workers) >= 2 and remaining_capacity > 0:
        available = [plan for plan in candidates if tuple(plan['position']) not in reserved and seed_budget[str(plan['crop'])] > 0]
        if not available:
            break
        plan = available[0]
        target = tuple(plan['position'])
        workers = sorted(free_workers, key=lambda worker: (_distance(positions[worker], target), worker))[:2]
        if all((positions[worker] == target for worker in workers)):
            actions[workers[0]] = ['PLANT', str(plan['crop'])]
            actions[workers[1]] = ['WATER']
            seed_budget[str(plan['crop'])] -= 1
            remaining_capacity -= 1
        else:
            for worker in workers:
                actions[worker] = _act_at_or_move(positions[worker], target, ['PASS'])
        reserved.add(target)
        free_workers = [worker for worker in free_workers if worker not in workers]

def _assign_limited_animal_services(animal_plans: tuple[dict[str, Any], ...], day: int, farm: dict[str, Any], positions: list[tuple[int, int]], actions: list[list[str] | None], *, crop_worker_reserve: int=2, care_enabled: bool=True, anticipate_daily_feed: bool=False) -> None:
    free_workers = [worker for worker, action in enumerate(actions) if action is None]
    service_count = max(0, len(free_workers) - crop_worker_reserve)
    if service_count <= 0:
        return
    active_plans = tuple((plan for plan in animal_plans if _plan_is_active(plan, farm['tiles'])))
    if not active_plans:
        return
    service_workers = sorted(free_workers, key=lambda worker: (min((_distance(positions[worker], plan['position']) for plan in active_plans)), worker))[:service_count]
    service_positions = [positions[worker] for worker in service_workers]
    service_actions = [actions[worker] for worker in service_workers]
    _assign_animal_services(active_plans, day, farm, service_positions, service_actions, care_enabled)
    if care_enabled and anticipate_daily_feed and (day <= LAST_FEEDING_DAY):
        for plan in active_plans:
            tile = _tile_at(farm['tiles'], plan['position'])
            if not tile.get('cared_today', False):
                _assign_nearest(service_positions, service_actions, plan['position'], ['CARE'])
    for service_worker, worker in enumerate(service_workers):
        actions[worker] = service_actions[service_worker]

def _assign_colocated_feed_care(animal_plans: tuple[dict[str, Any], ...], day: int, farm: dict[str, Any], positions: list[tuple[int, int]], inventories: list[dict[str, Any]], actions: list[list[str] | None]) -> set[str]:
    paired: set[str] = set()
    if day > LAST_FEEDING_DAY:
        return paired
    for plan in animal_plans:
        tile = _tile_at(farm['tiles'], plan['position'])
        if not _plan_is_active(plan, farm['tiles']) or tile.get('fed_today', False) or tile.get('cared_today', False):
            continue
        target = tuple(plan['position'])
        colocated = [worker for worker, position in enumerate(positions) if actions[worker] is None and position == target]
        feeder = next((worker for worker in colocated if int(inventories[worker].get('WHEAT', 0)) > 0), None)
        if feeder is None:
            continue
        caregiver = next((worker for worker in colocated if worker != feeder), None)
        if caregiver is None:
            continue
        actions[feeder] = ['FEED']
        actions[caregiver] = ['CARE']
        paired.add(str(plan['id']))
    return paired

def _assign_animal_care(animal_plans: tuple[dict[str, Any], ...], day: int, farm: dict[str, Any], positions: list[tuple[int, int]], actions: list[list[str] | None]) -> None:
    if day > LAST_FEEDING_DAY:
        return
    tiles = farm['tiles']
    for plan in animal_plans:
        if not _plan_is_active(plan, tiles):
            continue
        tile = _tile_at(tiles, plan['position'])
        if tile.get('fed_today', False) and (not tile.get('cared_today', False)):
            _assign_nearest(positions, actions, plan['position'], ['CARE'])

def _assign_crop_fertilization(day: int, farm: dict[str, Any], private: dict[str, Any], crop_plans: tuple[dict[str, Any], ...], positions: list[tuple[int, int]], inventories: list[dict[str, Any]], actions: list[list[str] | None], limit: int | None=None, carried_only: bool=False) -> None:
    candidates = []
    for plan in crop_plans:
        tile = _tile_at(farm['tiles'], plan['position'])
        if not _is_crop(tile, 'STRAWBERRY'):
            continue
        operations = _crop_operations(day, tile)
        if {'FERTILIZE', 'WATER'}.issubset(operations):
            candidates.append(plan)
    candidates.sort(key=lambda plan: (min((_distance(tuple(plan['position']), access) for access in ((4, 4), (5, 4), (4, 5), (5, 5)))), int(plan['position'][1]), int(plan['position'][0])))
    if limit is not None:
        candidates = candidates[:max(0, limit)]
    for plan in candidates:
        free_workers = [worker for worker, action in enumerate(actions) if action is None]
        if len(free_workers) < 2:
            return
        target = tuple(plan['position'])
        carriers = [worker for worker in free_workers if int(inventories[worker].get('FERTILIZER', 0)) > 0]
        if carried_only and (not carriers):
            continue
        if carriers:
            fertilizer_worker = min(carriers, key=lambda worker: (_distance(positions[worker], target), worker))
            water_worker = min((worker for worker in free_workers if worker != fertilizer_worker), key=lambda worker: (_distance(positions[worker], target), worker))
            workers = [fertilizer_worker, water_worker]
        else:
            workers = sorted(free_workers, key=lambda worker: (_distance(positions[worker], target), worker))[:2]
        _assign_fertilized_strawberry(workers, plan, farm, private, positions, inventories, actions)

def _effective_crop_worker_reserve(day: int, farm: dict[str, Any], private: dict[str, Any], crop_plans: tuple[dict[str, Any], ...], configured_reserve: int, *, actionable_only: bool=False, scale_to_due_work: bool=False) -> int:
    due_work = sum((bool(_crop_operations(day, tile)) for plan in crop_plans if _is_crop((tile := _tile_at(farm['tiles'], plan['position'])), str(plan['crop']))))
    if scale_to_due_work and due_work > 0:
        return min(configured_reserve + 1, max(1, due_work))
    if not actionable_only:
        plantable = any((_tile_at(farm['tiles'], plan['position']) is None and day >= int(plan.get('first_plant_day', 0)) and (day <= int(plan['last_plant_day'])) for plan in crop_plans))
        if plantable:
            return configured_reserve
        active_crops = any((_is_crop(_tile_at(farm['tiles'], plan['position'])) for plan in crop_plans))
        return min(configured_reserve, 1) if active_crops else 0
    seeds = Counter(private.get('seeds', {}))
    plantable = any((_tile_at(farm['tiles'], plan['position']) is None and day >= int(plan.get('first_plant_day', 0)) and (day <= int(plan['last_plant_day'])) and (seeds[str(plan['crop'])] > 0) for plan in crop_plans))
    if plantable:
        return min(configured_reserve, 2)
    actionable_crops = sum((bool(_crop_operations(day, tile)) for plan in crop_plans if _is_crop((tile := _tile_at(farm['tiles'], plan['position'])), str(plan['crop']))))
    return min(configured_reserve, actionable_crops)

def _worker_actions(animal_plans: tuple[dict[str, Any], ...], day: int, farm: dict[str, Any], private: dict[str, Any], crop_plans: tuple[dict[str, Any], ...], crop_worker_reserve: int, release_idle_crop_reserve: bool, actionable_crop_reserve: bool, prioritize_mature_harvest: bool, fertilize_strawberries: bool, fertilized_strawberries_per_quadrant: int | None, cross_quadrant_crop_rescue: bool, crop_before_routine_animals: bool=False, crops_before_care_only: bool=False, plant_before_care: bool=False, scale_crop_reserve_to_due_work: bool=False, cross_quadrant_routine_rescue: bool=False, carried_fertilizer_only: bool=False, max_active_crops_per_quadrant: int | None=None, pair_colocated_feed_care: bool=False, anticipate_daily_feed_for_care: bool=False) -> tuple[list[str], list[list[str]]]:
    positions = [tuple(farm['farmer']), *(tuple(position) for position in farm.get('hands', []))]
    inventories = _inventories(private, len(positions))
    actions: list[list[str] | None] = [None for _ in positions]
    unlocked = [quadrant for quadrant in LAND_SEQUENCE if quadrant in farm.get('unlocked_quadrants', [])]
    worker_groups = {quadrant: list(range(index, len(positions), len(unlocked))) for index, quadrant in enumerate(unlocked)}
    seed_budget = Counter(private.get('seeds', {}))
    assigned_crop_targets: set[tuple[int, int]] = set()
    for quadrant in unlocked:
        workers = worker_groups[quadrant]
        local_positions = [positions[worker] for worker in workers]
        local_inventories = [inventories[worker] for worker in workers]
        local_actions = [actions[worker] for worker in workers]
        local_animals = tuple((plan for plan in animal_plans if plan['quadrant'] == quadrant))
        local_crops = tuple((plan for plan in crop_plans if plan['quadrant'] == quadrant))
        emergency = tuple((plan for plan in local_animals if _plan_is_active(plan, farm['tiles']) and _feed_due(day, _tile_at(farm['tiles'], plan['position']), False)))
        emergency_ids = {str(plan['id']) for plan in emergency}
        normal = tuple((plan for plan in local_animals if str(plan['id']) not in emergency_ids))
        paired_feed_care = _assign_colocated_feed_care(local_animals, day, farm, local_positions, local_inventories, local_actions) if pair_colocated_feed_care else set()
        emergency = tuple((plan for plan in emergency if str(plan['id']) not in paired_feed_care))
        normal = tuple((plan for plan in normal if str(plan['id']) not in paired_feed_care))
        _assign_urgent_feeding(emergency, day, farm, private, local_positions, local_inventories, local_actions, False)
        assigned_crop_targets.update(_assign_crop_tasks(day, farm, local_crops, local_positions, local_actions, critical=True, prioritize_mature_harvest=prioritize_mature_harvest))
        _assign_urgent_feeding(normal, day, farm, private, local_positions, local_inventories, local_actions, True)
        _assign_generic_setup(local_animals, farm, private, local_positions, local_inventories, local_actions)
        if fertilize_strawberries:
            _assign_crop_fertilization(day, farm, private, local_crops, local_positions, local_inventories, local_actions, fertilized_strawberries_per_quadrant, carried_fertilizer_only)
        effective_reserve = _effective_crop_worker_reserve(day, farm, private, local_crops, crop_worker_reserve, actionable_only=actionable_crop_reserve, scale_to_due_work=scale_crop_reserve_to_due_work) if release_idle_crop_reserve else crop_worker_reserve
        if crops_before_care_only:
            _assign_limited_animal_services(local_animals, day, farm, local_positions, local_actions, crop_worker_reserve=effective_reserve, care_enabled=False, anticipate_daily_feed=anticipate_daily_feed_for_care)
        if crop_before_routine_animals or crops_before_care_only:
            assigned_crop_targets.update(_assign_crop_tasks(day, farm, local_crops, local_positions, local_actions, critical=False))
        if crops_before_care_only and plant_before_care:
            _assign_paired_planting(day, farm, private, local_crops, local_positions, local_actions, seed_budget, max_active_crops_per_quadrant)
        if crops_before_care_only:
            _assign_animal_care(local_animals, day, farm, local_positions, local_actions)
        else:
            _assign_limited_animal_services(local_animals, day, farm, local_positions, local_actions, crop_worker_reserve=effective_reserve, anticipate_daily_feed=anticipate_daily_feed_for_care)
        if not crop_before_routine_animals and (not crops_before_care_only):
            assigned_crop_targets.update(_assign_crop_tasks(day, farm, local_crops, local_positions, local_actions, critical=False))
        if not (crops_before_care_only and plant_before_care):
            _assign_paired_planting(day, farm, private, local_crops, local_positions, local_actions, seed_budget, max_active_crops_per_quadrant)
        for local_worker, worker in enumerate(workers):
            actions[worker] = local_actions[local_worker]
    if cross_quadrant_crop_rescue:
        _assign_crop_tasks(day, farm, crop_plans, positions, actions, critical=True, prioritize_mature_harvest=prioritize_mature_harvest, excluded_targets=assigned_crop_targets)
    if cross_quadrant_routine_rescue:
        _assign_crop_tasks(day, farm, crop_plans, positions, actions, critical=False, prioritize_mature_harvest=prioritize_mature_harvest, excluded_targets=assigned_crop_targets)
    resolved = [action or ['PASS'] for action in actions]
    return (resolved[0], resolved[1:])

def _land_orders(day: int, farm: dict[str, Any], market: dict[str, Any], sales: list[list[Any]], target_extra_land: int=TARGET_EXTRA_LAND, reserves: tuple[int, int]=(300, 700), dynamic_expansion: bool=False, expansion_occupancy_threshold: float=0.64) -> list[list[str]]:
    unlocked_extra = max(0, len(farm.get('unlocked_quadrants', [])) - 1)
    if unlocked_extra >= target_extra_land:
        return []
    costs = (1000, 2000)
    if dynamic_expansion:
        frontier = LAND_SEQUENCE[unlocked_extra]
        half = len(farm['tiles']) // 2
        x_start = half if frontier.endswith('E') else 0
        y_start = half if frontier.startswith('S') else 0
        tiles = [farm['tiles'][y][x] for y in range(y_start, y_start + half) for x in range(x_start, x_start + half)]
        productive = sum((isinstance(tile, dict) and tile.get('kind') in {'PLANT', 'COOP', 'PASTURE'} for tile in tiles))
        occupancy = productive / len(tiles)
        degraded = any((isinstance(tile, dict) and tile.get('kind') == 'WEED' for tile in tiles))
        animal_emergency = any((tile.get('kind') in {'COOP', 'PASTURE'} and tile.get('animal') is not None and (int(tile.get('consecutive_unfed', 0)) >= 2) for tile in tiles if isinstance(tile, dict)))
        if occupancy < expansion_occupancy_threshold or degraded or animal_emergency:
            return []
    else:
        earliest_days = (5, 9)
        if day < earliest_days[unlocked_extra]:
            return []
    available = float(farm.get('money', 0)) + _projected_sale_value(sales, market)
    if available < costs[unlocked_extra] + reserves[unlocked_extra]:
        return []
    return [['BUY_LAND']]

def _sales_orders(day: int, farm: dict[str, Any], private: dict[str, Any], animal_plans: tuple[dict[str, Any], ...], projected_drop_workers: set[int], crop_plans: tuple[dict[str, Any], ...]=(), fertilizer_reserve_per_strawberry: int=0, fertilizer_reserve_limit: int | None=None, wheat_market_price: int | None=None, wheat_trade_target: int=0, wheat_trade_sell_price: int | None=None) -> list[list[Any]]:
    items = ('MELON', 'STRAWBERRY', 'WOOL', 'MILK', 'EGG', 'TOMATO', 'CARROT', 'FERTILIZER', 'WHEAT')
    shed = private.get('shed', {})
    quantities = Counter({item: int(shed.get(item, 0)) for item in items})
    inventories = private.get('inventories', [])
    for worker in projected_drop_workers:
        if worker < len(inventories) and isinstance(inventories[worker], dict):
            quantities.update(inventories[worker])
    active_animals = sum((_plan_is_active(plan, farm['tiles']) for plan in animal_plans))
    feed_reserve = 0 if day >= 28 else 2 * active_animals
    wheat_reserve = feed_reserve
    if day < 28 and wheat_trade_target > 0 and (wheat_trade_sell_price is not None) and (wheat_market_price is not None) and (wheat_market_price < wheat_trade_sell_price):
        wheat_reserve = max(wheat_reserve, wheat_trade_target)
    quantities['WHEAT'] = max(0, quantities['WHEAT'] - wheat_reserve)
    active_strawberries = sum((_is_crop(_tile_at(farm['tiles'], plan['position']), 'STRAWBERRY') for plan in crop_plans))
    fertilizer_reserve = 0 if day >= 28 else max(FERTILIZER_RESERVE, fertilizer_reserve_per_strawberry * active_strawberries)
    if fertilizer_reserve_limit is not None:
        fertilizer_reserve = min(fertilizer_reserve, max(0, fertilizer_reserve_limit))
    quantities['FERTILIZER'] = max(0, quantities['FERTILIZER'] - fertilizer_reserve)
    return [['SELL', item, quantities[item]] for item in items if quantities[item] > 0]

def _wheat_trade_orders(day: int, farm: dict[str, Any], private: dict[str, Any], market: dict[str, Any], sales: list[list[Any]], target: int, buy_price: int | None, cash_reserve: int) -> list[list[Any]]:
    if target <= 0 or buy_price is None or day >= 27 or (len(farm.get('unlocked_quadrants', [])) < 3) or any((order[:2] == ['SELL', 'WHEAT'] for order in sales)):
        return []
    price = int(market.get('prices', {}).get('WHEAT', 0))
    if price <= 0 or price > buy_price:
        return []
    shed_wheat = int(private.get('shed', {}).get('WHEAT', 0))
    missing = max(0, target - shed_wheat)
    spendable = max(0, int(farm.get('money', 0)) - cash_reserve)
    quantity = min(missing, spendable // price)
    return [['BUY_PRODUCT', 'WHEAT', quantity]] if quantity > 0 else []

def decide(observation: dict[str, Any], target_extra_land: int=TARGET_EXTRA_LAND, animal_plans: tuple[dict[str, Any], ...]=ANIMAL_PLANS, rotation_crop: str='STRAWBERRY', land_reserves: tuple[int, int]=(300, 700), crop_worker_reserve: int=2, late_rotation_crop: str | None=None, rotation_last_plant_day: int | None=None, late_rotation_last_plant_day: int | None=None, release_idle_crop_reserve: bool=False, actionable_crop_reserve: bool=False, prioritize_mature_harvest: bool=False, fertilize_strawberries: bool=False, fertilized_strawberries_per_quadrant: int | None=None, cross_quadrant_crop_rescue: bool=False, crop_before_routine_animals: bool=False, crops_before_care_only: bool=False, plant_before_care: bool=False, scale_crop_reserve_to_due_work: bool=False, cross_quadrant_routine_rescue: bool=False, carried_fertilizer_only: bool=False, fertilizer_reserve_per_strawberry: int=0, fertilizer_reserve_limit: int | None=None, hand_targets: tuple[int, ...]=HAND_TARGETS, seed_buffer_multiplier: int=1, wheat_seed_buffer_multiplier: int | None=None, extra_wheat_seed_buffer: int=0, reserve_seeds_per_quadrant: bool=False, dynamic_land_expansion: bool=False, expansion_occupancy_threshold: float=0.64, dynamic_lifecycle_windows: bool=False, dynamic_lifecycle_deadlines_only: bool=False, max_active_crops_per_quadrant: int | None=None, wheat_trade_target: int=0, wheat_trade_buy_price: int | None=None, wheat_trade_sell_price: int | None=None, wheat_trade_cash_reserve: int=3000, pair_colocated_feed_care: bool=False, anticipate_daily_feed_for_care: bool=False) -> dict[str, Any]:
    """Fill paid land with replay-grounded premium crops and stable crews."""
    player = int(observation['player'])
    farm = observation['farms'][player]
    private = observation['private']
    market_state = observation.get('market', {})
    day = int(observation['day'])
    desired_animals = tuple((plan for plan in animal_plans if day >= int(plan.get('activation_day', 0))))
    active_animals = _active_plans(desired_animals, farm)
    crop_plans = _dense_crop_plans(farm, day, {tuple(plan['position']) for plan in desired_animals}, rotation_crop, late_rotation_crop, rotation_last_plant_day, late_rotation_last_plant_day, dynamic_lifecycle_windows, dynamic_lifecycle_deadlines_only)
    animal_crew_size = _animal_crew_size(day)
    pair_quadrants = _pair_quadrants(day, farm)
    if day == 29:
        farmer_action, hands_actions = _final_day_actions(active_animals, int(observation['hour']), farm, private, market_state)
    else:
        farmer_action, hands_actions = _worker_actions(active_animals, day, farm, private, crop_plans, crop_worker_reserve, release_idle_crop_reserve, actionable_crop_reserve, prioritize_mature_harvest, fertilize_strawberries, fertilized_strawberries_per_quadrant, cross_quadrant_crop_rescue, crop_before_routine_animals, crops_before_care_only, plant_before_care, scale_crop_reserve_to_due_work, cross_quadrant_routine_rescue, carried_fertilizer_only, max_active_crops_per_quadrant, pair_colocated_feed_care, anticipate_daily_feed_for_care)
    worker_actions = [farmer_action, *hands_actions]
    drop_workers = {worker for worker, action in enumerate(worker_actions) if action == ['DROP']}
    sales = _sales_orders(day, farm, private, active_animals, drop_workers, crop_plans, fertilizer_reserve_per_strawberry, fertilizer_reserve_limit, int(market_state.get('prices', {}).get('WHEAT', 0)), wheat_trade_target, wheat_trade_sell_price)
    market = _affordable_market_orders(observation, [*sales, *_livestock_orders(active_animals, day, farm, private), *_wheat_trade_orders(day, farm, private, market_state, sales, wheat_trade_target, wheat_trade_buy_price, wheat_trade_cash_reserve), *_land_orders(day, farm, market_state, sales, target_extra_land, land_reserves, dynamic_land_expansion, expansion_occupancy_threshold), *_zoned_hire_orders(farm, _hand_target(day, hand_targets)), *_seed_orders(day, farm, private, crop_plans, animal_crew_size, pair_quadrants, seed_buffer_multiplier, wheat_seed_buffer_multiplier, extra_wheat_seed_buffer, reserve_seeds_per_quadrant, max_active_crops_per_quadrant)])
    return {'farmer': farmer_action, 'hands': hands_actions, 'market': market}
decide_premium = decide
'Opponent- and demand-aware counterpolicy for direct market matchups.'
from collections import Counter
from typing import Any
ONE_LAND_ANIMAL_PLANS: tuple[dict[str, Any], ...] = tuple((plan for plan in ANIMAL_PLANS if plan['quadrant'] in {'NW', 'NE'}))

def _opponent_crop_counts(observation: dict[str, Any]) -> Counter[str]:
    player = int(observation['player'])
    farms = observation.get('farms', [])
    opponent = farms[1 - player] if len(farms) == 2 else {}
    counts: Counter[str] = Counter()
    for row in opponent.get('tiles', []):
        for tile in row:
            if isinstance(tile, dict) and tile.get('kind') == 'PLANT':
                counts[str(tile.get('crop', 'UNKNOWN'))] += 1
    return counts

def _is_wheat_specialist(observation: dict[str, Any]) -> bool:
    if int(observation.get('day', 0)) < 4:
        return False
    crops = _opponent_crop_counts(observation)
    return sum((quantity for crop, quantity in crops.items() if crop != 'WHEAT')) == 0

def _strategy_parameters(observation: dict[str, Any]) -> tuple[int, tuple[dict[str, Any], ...], str]:
    if not _is_wheat_specialist(observation):
        return (2, ANIMAL_PLANS, 'STRAWBERRY')
    return (1, ONE_LAND_ANIMAL_PLANS, 'STRAWBERRY')

def decide(observation: dict[str, Any]) -> dict[str, Any]:
    """Select land and livestock pressure from the opponent footprint."""
    target_extra_land, animal_plans, rotation_crop = _strategy_parameters(observation)
    return decide_premium(observation, target_extra_land=target_extra_land, animal_plans=animal_plans, rotation_crop=rotation_crop)
'Wheat-capacity policy tapered around the final harvest deadline.'
from typing import Any
DEADLINE_HAND_TARGETS = (*HAND_TARGETS[:23], 10, 10, 10, 10, 8, 4, 3)

def decide(observation: dict[str, Any]) -> dict[str, Any]:
    """Protect the last wheat cohort, then taper for liquidation."""
    return decide_premium(observation, target_extra_land=2, rotation_crop='WHEAT', land_reserves=(300, 300), late_rotation_crop='WHEAT', release_idle_crop_reserve=True, prioritize_mature_harvest=True, hand_targets=DEADLINE_HAND_TARGETS)
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
'Safe animal-service templates for contextual policy selection.'
from typing import Any
ARM_BASELINE = 0
ARM_PAIRED = 1
SERVICE_ARMS = (ARM_BASELINE, ARM_PAIRED)
ARM_NAMES = {ARM_BASELINE: 'deadline-baseline', ARM_PAIRED: 'colocated-feed-care'}

def decide_service_arm(observation: dict[str, Any], arm: int) -> dict[str, Any]:
    """Execute one service template through deterministic safety."""
    if arm not in SERVICE_ARMS:
        raise ValueError(f'Unknown service arm: {arm}')
    return decide_premium(observation, target_extra_land=2, rotation_crop='WHEAT', land_reserves=(300, 300), late_rotation_crop='WHEAT', release_idle_crop_reserve=True, prioritize_mature_harvest=True, hand_targets=DEADLINE_HAND_TARGETS, pair_colocated_feed_care=arm == ARM_PAIRED)
SERVICE_MODEL = {'feature': 'player', 'threshold': 0.5, 'left': {'arm': 1, 'samples': 40, 'arm_wins': {'0': 33, '1': 34}, 'arm_utilities': {'0': 26378.387, '1': 28401.136}}, 'right': {'feature': 'opponent_wheat', 'threshold': 8.0, 'left': {'arm': 0, 'samples': 30, 'arm_wins': {'0': 24, '1': 23}, 'arm_utilities': {'0': 18130.453, '1': 16167.703}}, 'right': {'arm': 1, 'samples': 10, 'arm_wins': {'0': 10, '1': 10}, 'arm_utilities': {'0': 10219.0, '1': 10231.97}}, 'samples': 40}, 'samples': 80}
'Learned day-1 selector over safe animal-service templates.'
from typing import Any
SELECTION_DAY = 1
MIN_MODELED_OPPONENT_MONEY_K = 0.5
_SELECTED_ARMS: dict[int, int] = {}

def _selected_arm(observation: dict[str, Any]) -> int:
    player = int(observation['player'])
    day = int(observation.get('day', 0))
    hour = int(observation.get('hour', 0))
    if day == 0 and hour == 0:
        _SELECTED_ARMS.pop(player, None)
    if day < SELECTION_DAY:
        return ARM_BASELINE
    if player not in _SELECTED_ARMS:
        features = extract_macro_features(observation)
        _SELECTED_ARMS[player] = ARM_BASELINE if features['opponent_money_k'] < MIN_MODELED_OPPONENT_MONEY_K else select_macro_arm(SERVICE_MODEL, features)
    return _SELECTED_ARMS[player]

def decide(observation: dict[str, Any]) -> dict[str, Any]:
    """Select one service template, then execute deterministic safety."""
    return decide_service_arm(observation, _selected_arm(observation))

def agent(observation: dict[str, Any]) -> dict[str, Any]:
    """Run the learned service policy."""
    return decide(observation)
