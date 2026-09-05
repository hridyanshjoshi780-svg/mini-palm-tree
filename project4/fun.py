#!/usr/bin/env python3
"""
EVOLIFE — a terminal ecosystem where creatures evolve to survive.

Genes control speed, vision, size, and metabolism. Creatures hunt food,
reproduce with mutation, and die of starvation or old age. Watch natural
selection happen in your terminal.

Run:  python3 evolife.py
Keys: SPACE pause | +/- speed | s save | l load | q quit
"""

import curses
import random
import json
import time
import math
import os
from dataclasses import dataclass, field, asdict
from typing import List, Tuple, Optional

SAVE_FILE = "evolife_save.json"

# ----------------------------- Config -----------------------------

@dataclass
class Config:
    width: int = 90
    height: int = 30
    initial_creatures: int = 25
    initial_food: int = 60
    food_spawn_rate: float = 0.35
    mutation_rate: float = 0.15
    mutation_strength: float = 0.2
    max_age: int = 400
    reproduction_energy: float = 60.0
    reproduction_cost: float = 35.0
    starting_energy: float = 40.0


CFG = Config()


def clamp(v, lo, hi):
    return max(lo, min(hi, v))


def mutate(value, lo, hi):
    if random.random() < CFG.mutation_rate:
        delta = random.gauss(0, CFG.mutation_strength) * (hi - lo)
        value = clamp(value + delta, lo, hi)
    return value


# ----------------------------- Genome -----------------------------

@dataclass
class Genome:
    speed: float = 1.0        # tiles per tick, 0.5-2.5
    vision: float = 5.0       # sense radius, 2-12
    size: float = 1.0         # affects energy cost & max energy, 0.5-2.0
    metabolism: float = 1.0   # energy burn multiplier, 0.5-2.0
    aggression: float = 0.0   # 0=herbivore, 1=will eat other creatures
    hue: int = 1              # color pair id

    @staticmethod
    def random():
        return Genome(
            speed=random.uniform(0.5, 2.5),
            vision=random.uniform(2, 12),
            size=random.uniform(0.5, 2.0),
            metabolism=random.uniform(0.5, 2.0),
            aggression=random.choice([0.0, 0.0, 0.0, 1.0]),
            hue=random.randint(1, 6),
        )

    def child(self, other: "Genome") -> "Genome":
        g = Genome(
            speed=random.choice([self.speed, other.speed]),
            vision=random.choice([self.vision, other.vision]),
            size=random.choice([self.size, other.size]),
            metabolism=random.choice([self.metabolism, other.metabolism]),
            aggression=random.choice([self.aggression, other.aggression]),
            hue=random.choice([self.hue, other.hue]),
        )
        g.speed = mutate(g.speed, 0.3, 3.0)
        g.vision = mutate(g.vision, 1, 15)
        g.size = mutate(g.size, 0.3, 2.5)
        g.metabolism = mutate(g.metabolism, 0.3, 2.5)
        if random.random() < CFG.mutation_rate * 0.5:
            g.aggression = 1.0 - g.aggression
        if random.random() < 0.05:
            g.hue = random.randint(1, 6)
        return g


# ----------------------------- Entities -----------------------------

_id_counter = 0


def next_id():
    global _id_counter
    _id_counter += 1
    return _id_counter


@dataclass
class Creature:
    x: float
    y: float
    genome: Genome
    energy: float = field(default_factory=lambda: CFG.starting_energy)
    age: int = 0
    id: int = field(default_factory=next_id)
    generation: int = 1
    target: Optional[Tuple[int, int]] = None

    @property
    def max_energy(self):
        return 50 + self.genome.size * 40

    @property
    def alive(self):
        return self.energy > 0 and self.age < CFG.max_age

    def upkeep_cost(self):
        return 0.15 * self.genome.metabolism * self.genome.size * (
            1 + self.genome.speed * 0.3
        )

    def symbol(self):
        if self.genome.aggression >= 0.5:
            return "X" if self.energy > self.max_energy * 0.4 else "x"
        return "O" if self.energy > self.max_energy * 0.4 else "o"


@dataclass
class Food:
    x: int
    y: int
    energy: float = 20.0


# ----------------------------- World -----------------------------

class World:
    def __init__(self):
        self.creatures: List[Creature] = []
        self.food: List[Food] = []
        self.tick = 0
        self.history: List[int] = []
        self.deaths_starve = 0
        self.deaths_age = 0
        self.deaths_eaten = 0
        self.births = 0
        self.max_generation = 1
        self._seed_initial()

    def _seed_initial(self):
        for _ in range(CFG.initial_creatures):
            self.creatures.append(Creature(
                x=random.uniform(0, CFG.width),
                y=random.uniform(0, CFG.height),
                genome=Genome.random(),
            ))
        for _ in range(CFG.initial_food):
            self.spawn_food()

    def spawn_food(self):
        self.food.append(Food(
            x=random.randint(0, CFG.width - 1),
            y=random.randint(0, CFG.height - 1),
        ))

    def nearest_food(self, c: Creature) -> Optional[Food]:
        best, best_d = None, c.genome.vision ** 2
        for f in self.food:
            d = (f.x - c.x) ** 2 + (f.y - c.y) ** 2
            if d < best_d:
                best, best_d = f, d
        return best

    def nearest_prey(self, c: Creature) -> Optional[Creature]:
        best, best_d = None, c.genome.vision ** 2
        for other in self.creatures:
            if other.id == c.id or other.genome.aggression >= 0.5:
                continue
            d = (other.x - c.x) ** 2 + (other.y - c.y) ** 2
            if d < best_d:
                best, best_d = other, d
        return best

    def step(self):
        self.tick += 1
        if random.random() < CFG.food_spawn_rate:
            self.spawn_food()

        for c in self.creatures:
            self._act(c)

        # resolve deaths
        survivors = []
        eaten_ids = set()
        for c in self.creatures:
            if c.id in eaten_ids:
                self.deaths_eaten += 1
                continue
            c.age += 1
            c.energy -= c.upkeep_cost()
            if c.energy <= 0:
                self.deaths_starve += 1
                continue
            if c.age >= CFG.max_age:
                self.deaths_age += 1
                continue
            survivors.append(c)
        self.creatures = survivors

        # reproduction
        newborns = []
        for c in self.creatures:
            if c.energy >= CFG.reproduction_energy and random.random() < 0.08:
                mate = self._find_mate(c)
                genome = c.genome.child(mate.genome) if mate else c.genome.child(c.genome)
                c.energy -= CFG.reproduction_cost
                gen = max(c.generation, mate.generation if mate else c.generation) + 1
                self.max_generation = max(self.max_generation, gen)
                newborns.append(Creature(
                    x=clamp(c.x + random.uniform(-2, 2), 0, CFG.width - 1),
                    y=clamp(c.y + random.uniform(-2, 2), 0, CFG.height - 1),
                    genome=genome,
                    generation=gen,
                ))
        self.creatures.extend(newborns)
        self.births += len(newborns)
        self.history.append(len(self.creatures))
        if len(self.history) > 200:
            self.history.pop(0)

        # predator eating prey (mark for removal next step)
        for c in self.creatures:
            if c.genome.aggression >= 0.5:
                prey = self.nearest_prey(c)
                if prey and (prey.x - c.x) ** 2 + (prey.y - c.y) ** 2 < 1.0:
                    prey.energy = -1  # dies of "starvation" bucket, close enough
                    c.energy = min(c.max_energy, c.energy + prey.max_energy * 0.6)

    def _find_mate(self, c: Creature) -> Optional[Creature]:
        candidates = [
            o for o in self.creatures
            if o.id != c.id and o.genome.aggression == c.genome.aggression
            and (o.x - c.x) ** 2 + (o.y - c.y) ** 2 < 9
        ]
        return random.choice(candidates) if candidates else None

    def _act(self, c: Creature):
        if c.genome.aggression >= 0.5:
            target = self.nearest_prey(c)
            tx, ty = (target.x, target.y) if target else (None, None)
        else:
            target = self.nearest_food(c)
            tx, ty = (target.x, target.y) if target else (None, None)

        if tx is None:
            dx, dy = random.uniform(-1, 1), random.uniform(-1, 1)
        else:
            dx, dy = tx - c.x, ty - c.y
            dist = math.hypot(dx, dy) or 1
            dx, dy = dx / dist, dy / dist

        c.x = clamp(c.x + dx * c.genome.speed, 0, CFG.width - 1)
        c.y = clamp(c.y + dy * c.genome.speed, 0, CFG.height - 1)

        if not c.genome.aggression >= 0.5:
            for f in list(self.food):
                if abs(f.x - c.x) < 1 and abs(f.y - c.y) < 1:
                    c.energy = min(c.max_energy, c.energy + f.energy)
                    self.food.remove(f)
                    break

    def stats(self):
        n = len(self.creatures)
        if n == 0:
            return dict(n=0, avg_speed=0, avg_vision=0, avg_size=0, predators=0)
        return dict(
            n=n,
            avg_speed=sum(c.genome.speed for c in self.creatures) / n,
            avg_vision=sum(c.genome.vision for c in self.creatures) / n,
            avg_size=sum(c.genome.size for c in self.creatures) / n,
            predators=sum(1 for c in self.creatures if c.genome.aggression >= 0.5),
        )

    def save(self, path=SAVE_FILE):
        data = dict(
            tick=self.tick,
            creatures=[
                dict(x=c.x, y=c.y, energy=c.energy, age=c.age,
                     generation=c.generation, genome=asdict(c.genome))
                for c in self.creatures
            ],
            food=[dict(x=f.x, y=f.y, energy=f.energy) for f in self.food],
            history=self.history,
        )
        with open(path, "w") as fh:
            json.dump(data, fh)

    def load(self, path=SAVE_FILE):
        if not os.path.exists(path):
            return False
        with open(path) as fh:
            data = json.load(fh)
        self.tick = data["tick"]
        self.creatures = [
            Creature(x=d["x"], y=d["y"], energy=d["energy"], age=d["age"],
                      generation=d["generation"], genome=Genome(**d["genome"]))
            for d in data["creatures"]
        ]
        self.food = [Food(**d) for d in data["food"]]
        self.history = data.get("history", [])
        return True


# ----------------------------- Rendering -----------------------------

def init_colors():
    curses.start_color()
    curses.use_default_colors()
    pairs = [
        curses.COLOR_GREEN, curses.COLOR_CYAN, curses.COLOR_YELLOW,
        curses.COLOR_MAGENTA, curses.COLOR_BLUE, curses.COLOR_WHITE,
    ]
    for i, color in enumerate(pairs, start=1):
        curses.init_pair(i, color, -1)
    curses.init_pair(10, curses.COLOR_RED, -1)      # predator
    curses.init_pair(11, curses.COLOR_GREEN, -1)    # food


def draw_sparkline(win, y, x, values, width, height=4):
    if not values:
        return
    vmax = max(values) or 1
    step = max(1, len(values) // width)
    sampled = values[::step][-width:]
    for row in range(height):
        threshold = vmax * (height - row) / height
        line = "".join("#" if v >= threshold else " " for v in sampled)
        try:
            win.addstr(y + row, x, line[:width])
        except curses.error:
            pass


def render(stdscr, world: World, paused: bool, speed: float):
    stdscr.erase()
    h, w = stdscr.getmaxyx()

    for f in world.food:
        if f.y + 1 < h and f.x < w:
            try:
                stdscr.addch(int(f.y) + 1, int(f.x), ord("."),
                             curses.color_pair(11))
            except curses.error:
                pass

    for c in world.creatures:
        if c.y + 1 < h and c.x < w:
            pair = 10 if c.genome.aggression >= 0.5 else c.genome.hue
            try:
                stdscr.addch(int(c.y) + 1, int(c.x), ord(c.symbol()),
                             curses.color_pair(pair) | curses.A_BOLD)
            except curses.error:
                pass

    st = world.stats()
    status = (
        f" tick {world.tick:5d} | pop {st['n']:3d} | predators {st['predators']:2d} "
        f"| avg spd {st['avg_speed']:.2f} vis {st['avg_vision']:.1f} size {st['avg_size']:.2f} "
        f"| births {world.births} deaths(starve/age/eaten) {world.deaths_starve}/{world.deaths_age}/{world.deaths_eaten} "
        f"| gen max {world.max_generation} | speed x{speed:.1f} {'[PAUSED]' if paused else ''}"
    )
    try:
        stdscr.addstr(0, 0, status[:w - 1], curses.A_REVERSE)
        draw_sparkline(stdscr, CFG.height + 2, 0, world.history, min(w - 1, 120))
        stdscr.addstr(CFG.height + 7, 0,
                      "SPACE pause  +/- speed  s save  l load  r reset  q quit"[:w - 1])
    except curses.error:
        pass
    stdscr.refresh()


# ----------------------------- Main loop -----------------------------

def main(stdscr):
    curses.curs_set(0)
    stdscr.nodelay(True)
    init_colors()

    world = World()
    paused = False
    speed = 1.0
    tick_interval = 0.08
    last_step = time.time()

    while True:
        try:
            key = stdscr.getch()
        except curses.error:
            key = -1

        if key in (ord("q"), ord("Q")):
            break
        elif key == ord(" "):
            paused = not paused
        elif key in (ord("+"), ord("=")):
            speed = clamp(speed * 1.5, 0.1, 20)
        elif key == ord("-"):
            speed = clamp(speed / 1.5, 0.1, 20)
        elif key in (ord("s"), ord("S")):
            world.save()
        elif key in (ord("l"), ord("L")):
            world.load()
        elif key in (ord("r"), ord("R")):
            world = World()

        now = time.time()
        if not paused and now - last_step >= tick_interval / speed:
            world.step()
            last_step = now
            if len(world.creatures) == 0:
                # extinction: reseed a fresh batch to keep it interesting
                for _ in range(CFG.initial_creatures // 2):
                    world.creatures.append(Creature(
                        x=random.uniform(0, CFG.width),
                        y=random.uniform(0, CFG.height),
                        genome=Genome.random(),
                    ))

        render(stdscr, world, paused, speed)
        time.sleep(0.02)


if __name__ == "__main__":
    curses.wrapper(main)