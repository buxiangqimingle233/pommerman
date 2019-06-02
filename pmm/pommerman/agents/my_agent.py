'''The base simple agent use to train agents.
This agent is also the benchmark for other agents.
'''
from collections import defaultdict, Counter
from copy import deepcopy
import queue
import random

import numpy as np

from . import BaseAgent
from .. import constants
from .. import utility

# BFS Section

BFS_EPISODES = 4

class Bomb:
    def __init__(self, obs, exist_bombs):
        self.position = exist_bombs['position']
        self.blast_strength = exist_bombs['blast_strength']
        self.life = obs['bomb_life'][self.position]


def GenMyBombs(obs, exist_bombs):
    ret = []
    for bomb in exist_bombs:
        ret.append(Bomb(obs, bomb))
    return ret


class BFSNode:
    def __init__(self, obs, bombs, my_position, first_step, steps):
        self.obs = obs
        self.board = obs['board']
        self.bombs = bombs
        self.my_position = my_position
        self.first_step = first_step
        self.steps = steps

    def dist_from_start(self):
        stop_num = Counter(self.taken_action)[constants.Action.Stop]
        return self.steps - stop_num + 1

    def first_action(self):
        return self.first_step


def In_range_of_bomb(board, bombs, position, danger_bomb_list):
    position_x, position_y = position
    for bomb in bombs:
        bomb_x, bomb_y = bomb.position
        safe_from_bomb = False
        # if bomb.life > bomb.blast_strength + 3:
        #     safe_from_bomb = True
        if (bomb_x == position_x and abs(bomb_y - position_y) <= bomb.blast_strength):
            for pix_y in range(min(bomb_y, position_y), max(bomb_y, position_y)):
                if utility.position_is_wall(board, (position_x, pix_y)):
                    safe_from_bomb = True           
        elif (bomb_y == position_y and abs(bomb_x - position_x) <= bomb.blast_strength):
            for pix_x in range(min(bomb_x, position_x), max(bomb_x, position_x)):
                if utility.position_is_wall(board, (pix_x, position_y)):
                    safe_from_bomb = True
        else:
            safe_from_bomb = True
        if not safe_from_bomb:
            danger_bomb_list.append(bomb)
    return len(danger_bomb_list)>0

            
def isWell(board, my_position,enemies):
    cnt = 0
    for move in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
        new_position = (my_position[0]+move[0], my_position[1]+move[1])
        if utility.position_on_board(board, new_position) and utility.position_is_passable(board, new_position,enemies):
            cnt += 1
    if cnt <= 1:
        return True
    else:
        return False


def isSecondWell(board , my_position,enemies):
    cnt = 0
    for move in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
        new_position = (my_position[0] + move[0], my_position[1] + move[1])
        if utility.position_on_board(board, new_position) and utility.position_is_passable(board, new_position,
                                                                                           enemies):
            cnt += 1
    if cnt != 2:
        return False
    for move in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
        new_position = (my_position[0] + move[0], my_position[1] + move[1])
        if utility.position_on_board(board, new_position) and utility.position_is_passable(board, new_position,
                                                                                               enemies):
            if isWell(board, new_position, enemies):
                return True
    else:
        return False


def Change_bombs_life(board, bombs):
    # 修改能够连锁爆炸的炸弹life
    new_bombs = []
    for bomb in bombs:
        bomb_position = bomb.position
        danger_bomb_list = []
        if In_range_of_bomb(board, bombs, bomb_position, danger_bomb_list):
            for other_bomb in danger_bomb_list:
                if other_bomb.position == bomb.position: continue
                bomb.life = min(bomb.life, other_bomb.life)
        new_bombs.append(bomb)
    return new_bombs


def CanGo(bfs_node, action, enemies):
    my_position = bfs_node.my_position
    new_position = utility.get_next_position(my_position, action)
    if not utility.is_valid_direction(bfs_node.board, my_position, action):
        return False
    if not utility.position_is_passable(bfs_node.board, new_position, enemies):
        return False
    board = bfs_node.board
    bombs = bfs_node.bombs
    new_bombs = Change_bombs_life(board, bombs)
    danger_bomb_list = []
    In_range_of_bomb(board, new_bombs, new_position, danger_bomb_list)
    for bomb in danger_bomb_list:
        if bomb.life < 4:
            return False
    return True


def Step_forward(board, bombs):
    new_board, new_bombs = deepcopy(board), deepcopy(bombs)
    for bomb in new_bombs:
        if bomb.life > 0:
            bomb.life -= 1
    return new_board, bombs
    

def BFS_when_unsafe(my_position, obs, bombs, enemies, trained_num=0):
    q = queue.Queue()
    q.put(BFSNode(obs, bombs, my_position, -1, 0))
    vote = {
            constants.Action.Stop: 0, constants.Action.Up: 0,
            constants.Action.Down: 0, constants.Action.Left: 0,
            constants.Action.Right: 0
        }
    have_ret = False
    while not q.empty():
        temp_node = q.get()
        if temp_node.steps >= BFS_EPISODES:
            vote[temp_node.first_step] += 1
            have_ret = True
            continue
        for row, col in [(0, 0), (-1, 0), (1, 0), (0, -1), (0, 1)]:
            new_position = (temp_node.my_position[0] + row, temp_node.my_position[1] + col)
            if row == 0 and col == 0:
                action = constants.Action.Stop
            else:
                action = utility.get_direction(temp_node.my_position, new_position)
            if CanGo(temp_node, action, enemies):
                new_board, new_bombs = Step_forward(temp_node.board, temp_node.bombs)
                if temp_node.steps == 0:
                    q.put(BFSNode(temp_node.obs, new_bombs, new_position, action, temp_node.steps+1))
                else:
                    q.put(BFSNode(temp_node.obs, new_bombs, new_position, temp_node.first_step, temp_node.steps+1))   

    if not have_ret:
        return None
    else:
        return max(vote, key=vote.get)

# End of BFS Section

def Try_to_kick(my_position, can_kick, bombs):
    if not can_kick:
        return None
    for move in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
        new_position = (my_position[0]+move[0], my_position[1]+move[1])
        if utility.position_is_bomb(bombs, new_position):
            return utility.get_direction(my_position, new_position)
    return None


class MyAgent(BaseAgent):
    """This is a baseline agent. After you can beat it, submit your agent to
    compete.
    """

    def __init__(self, *args, **kwargs):
        super(MyAgent, self).__init__(*args, **kwargs)

        # Keep track of recently visited uninteresting positions so that we
        # don't keep visiting the same places.
        self._recently_visited_positions = []
        self._recently_visited_length = 6
        # Keep track of the previous direction to help with the enemy standoffs.
        self._prev_direction = None
        self.BFS_call_count = 0

    def act(self, obs, action_space, trained_num=0):
        def convert_bombs(bomb_map):
            '''Flatten outs the bomb array'''
            ret = []
            locations = np.where(bomb_map > 0)
            for r, c in zip(locations[0], locations[1]):
                ret.append({
                    'position': (r, c),
                    'blast_strength': int(bomb_map[(r, c)])
                })
            return ret

        my_position = tuple(obs['position'])
        board = np.array(obs['board'])
        bombs = convert_bombs(np.array(obs['bomb_blast_strength']))
        enemies = []
        realenemies = []
        teammate = 0
        for e in obs['enemies']:
            enemies.append(constants.Item(e))
            if constants.Item(e) == constants.Item.AgentDummy:
                teammate = constants.Item.AgentDummy
            else:
                realenemies.append(constants.Item(e))
        ammo = int(obs['ammo'])
        blast_strength = int(obs['blast_strength'])
        items, dist, prev = self._djikstra(
            board, my_position, bombs, enemies, depth=10)


        my_bombs = GenMyBombs(obs, bombs)
        # 当处于危险位置 & 采取某个移动后仍可能处于危险位置
        unsafe_directions = self._directions_in_range_of_bomb(
            board, my_position, bombs, dist)    
        is_unsafe_after_action = self._is_unsafe_after_action(
            board, my_position, bombs, dist)
        if unsafe_directions or is_unsafe_after_action:
            action = BFS_when_unsafe(my_position, obs, my_bombs, enemies, trained_num=trained_num)
            #action = None
            directions = self._find_safe_directions(
            board, my_position, unsafe_directions, bombs, enemies, dist)
            # print(len(ret))
            if action is not None:
                return action.value
            else:
                alter_choice = random.choice(directions)
                if alter_choice == constants.Action.Stop:
                    kick_action = Try_to_kick(my_position, obs['can_kick'], my_bombs)
                    if kick_action is not None:
                        return kick_action.value
                else:
                    return alter_choice.value

        if len(realenemies) == 1:
            for enemy in realenemies:
                for enemy_pos in items.get(enemy, []):
                    for bomb in bombs:
                        if (enemy_pos[0] <= bomb['position'][0]+bomb['blast_strength']
                        and my_position[0]<=bomb['position'][0]+bomb['blast_strength']
                        and (my_position[1] -bomb['position'][1])*(enemy_pos[1]-bomb['position'][1])<=0
                        and (my_position[1] -bomb['position'][1])*(enemy_pos[1]-bomb['position'][1])>-2)\
                        or  (enemy_pos[0] >= bomb['position'][0]-bomb['blast_strength']
                        and my_position[0]>=bomb['position'][0]-bomb['blast_strength']
                        and (my_position[1] -bomb['position'][1])*(enemy_pos[1]-bomb['position'][1])<=0
                        and (my_position[1] -bomb['position'][1])*(enemy_pos[1]-bomb['position'][1])>-2) \
                        or (enemy_pos[1] >= bomb['position'][1] + bomb['blast_strength']
                        and my_position[1] >= bomb['position'][1] + bomb['blast_strength']
                        and (my_position[0] - bomb['position'][0]) * (enemy_pos[0] - bomb['position'][0]) <= 0
                        and (my_position[0] - bomb['position'][0]) * (enemy_pos[0] - bomb['position'][0]) > -2)\
                        or (enemy_pos[1] <= bomb['position'][1] - bomb['blast_strength']
                        and my_position[1] <= bomb['position'][1] - bomb['blast_strength']
                        and (my_position[0] - bomb['position'][0]) * (enemy_pos[0] - bomb['position'][0]) <= 0
                        and (my_position[0] - bomb['position'][0]) * (enemy_pos[0] - bomb['position'][0]) > -2):
                            direction = constants.Action.Stop
                            return direction.value
              
        # Move towards a good item if there is one within two reachable spaces.
        direction = self._near_good_powerup(my_position, items, dist, prev, 5)
        if direction is not None:
            if not In_range_of_bomb(board, Change_bombs_life(board, GenMyBombs(obs,bombs)), utility.get_next_position(my_position,direction), []):
                return direction.value


        # Maybe lay a bomb if we are within a space of a wooden wall.
        if self._near_wood(my_position, items, dist, prev, 1):
            if self._maybe_bomb(ammo, blast_strength, items, dist, my_position):
                return constants.Action.Bomb.value
            else:
                return constants.Action.Stop.value

        # Move towards a wooden wall if there is one within two reachable spaces and you have a bomb.
        direction = self._near_wood(my_position, items, dist, prev, 3)
        if direction is not None:
            directions = self._filter_unsafe_directions(board, my_position,
                                                        [direction], GenMyBombs(obs,bombs))
            if directions:
                return directions[0].value

        # Move backwards an enemy if there are two in exactly five reachable spaces.
        direction = self._near_enemy(my_position, items, dist, prev, realenemies, 5)
        if direction is not None and self._near_enemy_cnt(dist, items, 3, enemies) > 1:
            directions = [constants.Action.Down,constants.Action.Up,constants.Action.Left,constants.Action.Right]
            directions = self._filter_invalid_directions(board,my_position,directions,enemies)
            directions = self._filter_unsafe_directions(board,my_position,directions,GenMyBombs(obs,bombs))
            if(direction == constants.Action.Down) and constants.Action.Up in directions:
                direction =constants.Action.Up
            elif (direction == constants.Action.Up) and constants.Action.Down in directions:
                direction = constants.Action.Down
            elif (direction == constants.Action.Left) and constants.Action.Right in directions:
                direction = constants.Action.Right
            elif (direction == constants.Action.Right) and constants.Action.Left in directions:
                direction = constants.Action.Left
            else:
                direction = None
            if (self._prev_direction != direction or random.random() < .5) and direction is not None:
                self._prev_direction = direction
                return direction.value

        # Lay pomme if we are adjacent to an enemy.
        if self._is_adjacent_enemy(items, dist, realenemies, blast_strength//3 + 1 ,my_position) and self._maybe_bomb(
        ammo, blast_strength, items, dist, my_position):
            return constants.Action.Bomb.value

        # Move towards an enemy if there is one in exactly three reachable spaces.
        direction = self._near_enemy(my_position, items, dist, prev, realenemies, 3)
        if direction is not None and (self._prev_direction != direction or
        random.random() < .5):
            if not In_range_of_bomb(board, Change_bombs_life(board, GenMyBombs(obs, bombs)),
                                    utility.get_next_position(my_position, direction), []):
                self._prev_direction = direction
                return direction.value


        # Choose a random but valid direction.
        directions = [
            constants.Action.Stop, constants.Action.Left,
            constants.Action.Right, constants.Action.Up, constants.Action.Down
        ]
        valid_directions = self._filter_invalid_directions(
            board, my_position, directions, enemies)
        directions = self._filter_unsafe_directions(board, my_position,
                                                    valid_directions, GenMyBombs(obs,bombs))

        directions = self._filter_recently_visited(
            directions, my_position, self._recently_visited_positions)
        if len(directions) > 1:
            directions = [k for k in directions if k != constants.Action.Stop]
        if len(directions):
            new_directions = []
            for direction in directions:
                if not (isWell(board, utility.get_next_position(my_position, direction), enemies) or isSecondWell(board,
                                                                                                                  utility.get_next_position(
                                                                                                                          my_position,
                                                                                                                          direction),
                                                                                                                  enemies)):
                    new_directions.append(direction)
            if not len(new_directions):
                new_directions = [constants.Action.Stop]
            directions = new_directions[:]
        else:
            directions = [constants.Action.Stop]

        # Add this position to the recently visited uninteresting positions so we don't return immediately.
        self._recently_visited_positions.append(my_position)
        self._recently_visited_positions = self._recently_visited_positions[
            -self._recently_visited_length:]
        random.shuffle(directions)
        #for direction in directions:
        #    if not isWell(board, utility.get_next_position(my_position, direction), enemies) and not isSecondWell(board,utility.get_next_position(my_position, direction),enemies):
        #        return direction.value
        return directions[0].value

    @staticmethod
    def _djikstra(board, my_position, bombs, enemies, depth=None, exclude=None):
        assert (depth is not None)

        if exclude is None:
            exclude = [
                constants.Item.Fog, constants.Item.Rigid, constants.Item.Flames
            ]

        def out_of_range(p_1, p_2):
            '''Determines if two points are out of rang of each other'''
            x_1, y_1 = p_1
            x_2, y_2 = p_2
            return abs(y_2 - y_1) + abs(x_2 - x_1) > depth

        items = defaultdict(list)
        dist = {}
        prev = {}
        Q = queue.Queue()

        my_x, my_y = my_position
        for r in range(max(0, my_x - depth), min(len(board), my_x + depth)):
            for c in range(max(0, my_y - depth), min(len(board), my_y + depth)):
                position = (r, c)
                if any([
                        out_of_range(my_position, position),
                        utility.position_in_items(board, position, exclude),
                ]):
                    continue

                prev[position] = None
                item = constants.Item(board[position])
                items[item].append(position)
                
                if position == my_position:
                    Q.put(position)
                    dist[position] = 0
                else:
                    dist[position] = np.inf


        for bomb in bombs:
            if bomb['position'] == my_position:
                items[constants.Item.Bomb].append(my_position)

        while not Q.empty():
            position = Q.get()

            if utility.position_is_passable(board, position, enemies):
                x, y = position
                val = dist[(x, y)] + 1
                for row, col in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                    new_position = (row + x, col + y)
                    if new_position not in dist:
                        continue

                    if val < dist[new_position]:
                        dist[new_position] = val
                        prev[new_position] = position
                        Q.put(new_position)
                    elif (val == dist[new_position] and random.random() < .5):
                        dist[new_position] = val
                        prev[new_position] = position   


        return items, dist, prev

    def _is_dangerous_pos(self,board,my_position,bombs,dist):
        danger = False
        x,y = my_position
        for bomb in bombs:
            position = bomb['position']
            distance = dist.get(position)
            if distance is None:
                continue
            bomb_range = bomb['blast_strength']
            if distance > bomb_range:
                continue
            if x == position[0] or y == position[1]:
                danger = True
        return danger

    def _is_unsafe_after_action(self, board, my_position, bombs, dist):
        alternative_actions = [
            constants.Action.Up,
            constants.Action.Down,
            constants.Action.Left,
            constants.Action.Right
        ]
        for action in alternative_actions:
            next_position = utility.get_next_position(my_position, action)
            if not utility.is_valid_direction(board, my_position, action):
                continue
            if self._is_dangerous_pos(board, next_position, bombs, dist):
                return True
        return False

    def _directions_in_range_of_bomb(self, board, my_position, bombs, dist):
        ret = defaultdict(int)

        x, y = my_position
        for bomb in bombs:
            position = bomb['position']
            distance = dist.get(position)
            if distance is None:
                continue

            bomb_range = bomb['blast_strength']
            if distance > bomb_range:
                continue

            if my_position == position:
                # We are on a bomb. All directions are in range of bomb.
                for direction in [
                        constants.Action.Right,
                        constants.Action.Left,
                        constants.Action.Up,
                        constants.Action.Down,
                ]:
                    ret[direction] = max(ret[direction], bomb['blast_strength'])
            elif x == position[0]:
                if y < position[1]:
                    # Bomb is right.
                    ret[constants.Action.Right] = max(
                        ret[constants.Action.Right], bomb['blast_strength'])
                else:
                    # Bomb is left.
                    ret[constants.Action.Left] = max(ret[constants.Action.Left],
                                                     bomb['blast_strength'])
            elif y == position[1]:
                if x < position[0]:
                    # Bomb is down.
                    ret[constants.Action.Down] = max(ret[constants.Action.Down],
                                                     bomb['blast_strength'])
                else:
                    # Bomb is down.
                    ret[constants.Action.Up] = max(ret[constants.Action.Up],
                                                   bomb['blast_strength'])
        return ret

    def _find_safe_directions(self, board, my_position, unsafe_directions,
                              bombs,enemies, dist):

        def is_stuck_direction(next_position, bomb_range, next_board, enemies):
            '''Helper function to do determine if the agents next move is possible.'''
            Q = queue.PriorityQueue()
            Q.put((0, next_position))
            seen = set()

            next_x, next_y = next_position
            is_stuck = True
            while not Q.empty():
                dist, position = Q.get()
                seen.add(position)

                position_x, position_y = position
                if next_x != position_x and next_y != position_y:
                    is_stuck = False
                    break

                if dist > bomb_range:
                    is_stuck = False
                    break

                for row, col in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                    new_position = (row + position_x, col + position_y)
                    if new_position in seen:
                        continue

                    if not utility.position_on_board(next_board, new_position):
                        continue

                    if not utility.position_is_passable(next_board,
                                                        new_position, enemies):
                        continue

                    dist = abs(row + position_x - next_x) + abs(col + position_y - next_y)
                    Q.put((dist, new_position))
            return is_stuck

        # All directions are unsafe. Return a position that won't leave us locked.
        safe = []

        if len(unsafe_directions) == 4:
            next_board = board.copy()
            next_board[my_position] = constants.Item.Bomb.value

            for direction, bomb_range in unsafe_directions.items():
                next_position = utility.get_next_position(
                    my_position, direction)
                next_x, next_y = next_position
                if not utility.position_on_board(next_board, next_position) or \
                   not utility.position_is_passable(next_board, next_position, enemies):
                    continue

                if not is_stuck_direction(next_position, bomb_range, next_board,
                                          enemies):
                    # We found a direction that works. The .items provided
                    # a small bit of randomness. So let's go with this one.
                    return [direction]
            if not safe:
                safe = [constants.Action.Stop]
            return safe

        x, y = my_position
        disallowed = []  # The directions that will go off the board.

        for row, col in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            position = (x + row, y + col)
            direction = utility.get_direction(my_position, position)

            # Don't include any direction that will go off of the board.
            if not utility.position_on_board(board, position):
                disallowed.append(direction)
                continue

            # Don't include any direction that we know is unsafe.
            if direction in unsafe_directions:
                continue

            if utility.position_is_passable(board, position,
            enemies) or utility.position_is_fog(
            board, position) and not _is_dangerous_pos(self,board,position,bombs,dist):
                safe.append(direction)

        if not safe:
            # We don't have any safe directions, so return something that is allowed.
            safe = [k for k in unsafe_directions if k not in disallowed]

        if not safe:
            # We don't have ANY directions. So return the stop choice.
            return [constants.Action.Stop]

        return safe

    @staticmethod
    def _is_adjacent_enemy(items, dist, enemies, blast_strength, my_position):
        for enemy in enemies:
            for position in items.get(enemy, []):
                if dist[position] <= blast_strength and (my_position[0] == position[0] or my_position[1] == position[1]):
                    return True
        return False

    @staticmethod
    def _has_bomb(obs):
        return obs['ammo'] >= 1

    @staticmethod
    def _maybe_bomb(ammo, blast_strength, items, dist, my_position):
        """Returns whether we can safely bomb right now.

        Decides this based on:
        1. Do we have ammo?
        2. If we laid a bomb right now, will we be stuck?
        """
        # Do we have ammo?
        if ammo < 1:
            return False

        # Will we be stuck?
        x, y = my_position
        for position in items.get(constants.Item.Passage):
            if dist[position] == np.inf:
                continue

            # We can reach a passage that's outside of the bomb strength.
            if dist[position] > blast_strength:
                return True

            # We can reach a passage that's outside of the bomb scope.
            position_x, position_y = position
            if position_x != x and position_y != y:
                return True

        return False
    @staticmethod
    def _near_enemy_cnt(dist,items,radius,enemies):
        cnt=0
        for enemy in enemies:
            for position in items.get(enemy,[]):
                if dist[position]<=radius:
                    cnt+=1
        return cnt

    @staticmethod
    def _nearest_position(dist, objs, items, radius):
        nearest = None
        dist_to = max(dist.values())

        for obj in objs:
            for position in items.get(obj, []):
                d = dist[position]
                if d <= radius and d <= dist_to:
                    nearest = position
                    dist_to = d

        return nearest

    @staticmethod
    def _get_direction_towards_position(my_position, position, prev):
        if not position:
            return None

        next_position = position
        while prev[next_position] != my_position:
            next_position = prev[next_position]
            if not next_position:
                return None

        return utility.get_direction(my_position, next_position)


    @classmethod
    def _near_enemy(cls, my_position, items, dist, prev, enemies, radius):
        nearest_enemy_position = cls._nearest_position(dist, enemies, items,
                                                       radius)
        return cls._get_direction_towards_position(my_position,
                                                   nearest_enemy_position, prev)


    @classmethod
    def _near_good_powerup(cls, my_position, items, dist, prev, radius):
        objs = [
            constants.Item.ExtraBomb, constants.Item.IncrRange,
            constants.Item.Kick
        ]
        nearest_item_position = cls._nearest_position(dist, objs, items, radius)
        return cls._get_direction_towards_position(my_position,
                                                   nearest_item_position, prev)

    @classmethod
    def _near_wood(cls, my_position, items, dist, prev, radius):
        objs = [constants.Item.Wood]
        nearest_item_position = cls._nearest_position(dist, objs, items, radius)
        return cls._get_direction_towards_position(my_position,
                                                   nearest_item_position, prev)

    @staticmethod
    def _filter_invalid_directions(board, my_position, directions, enemies):
        ret = []
        for direction in directions:
            position = utility.get_next_position(my_position, direction)
            if utility.position_on_board(
                    board, position) and utility.position_is_passable(
                        board, position, enemies):
                ret.append(direction)
        return ret

    @staticmethod
    def _filter_unsafe_directions(board, my_position, directions, bombs):
        ret = []
        for direction in directions:
            x, y = utility.get_next_position(my_position, direction)
            if not In_range_of_bomb(board, Change_bombs_life(board, bombs), (x, y), []):
            #is_bad = False
            #for bomb in bombs:
            #    bomb_x, bomb_y = bomb['position']
            #    blast_strength = bomb['blast_strength']
            #    if (x == bomb_x and abs(bomb_y - y) <= blast_strength) or \
            #       (y == bomb_y and abs(bomb_x - x) <= blast_strength):
            #        is_bad = True
            #        break
            #if not is_bad:
                ret.append(direction)
        return ret

    @staticmethod
    def _filter_recently_visited(directions, my_position,
                                 recently_visited_positions):
        ret = []
        for direction in directions:
            if not utility.get_next_position(
                    my_position, direction) in recently_visited_positions:
                ret.append(direction)

        if not ret:
            ret = directions
        return ret

