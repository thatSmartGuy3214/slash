import pygame
import random
import math
from scripts.Engine import blit_center, Timer
from scripts.vfx import SlashVFX
from scripts.projectile import *


class Slash(SlashVFX):
    def __init__(self, owner, damage, crit, lifetime, flip, x, y, width, height, speed, slash_size, slash_size_change, roll_down_speed, color, radius, angle, shape="circle", truncation=0, cutout_radius=-1, cutout_center=[-1, -1], roll_down_axis="vertical"):
        super().__init__(x, y, width, height, speed, slash_size, slash_size_change, roll_down_speed, color, radius, angle, lifetime, shape, truncation, cutout_radius, cutout_center, roll_down_axis)

        self.owner = owner
        self.damage = damage
        self.is_crit = crit
        self.flip = flip
    
    def draw(self, surf, scroll):
        super().draw(surf, scroll)

    def did_collide(self, entity_rect: pygame.Rect, entity_mask):
        mask = pygame.mask.from_surface(pygame.transform.rotate(pygame.transform.flip(self.surface, False, self.flip), self.angle))

        if mask.overlap(entity_mask, [entity_rect.x-(self.x-self.width/2), entity_rect.y-(self.y-self.height/2)]) != None:
            return True
        
        return False

    def handle_collision(self, entity):
        if entity == self.owner:
            return

        mask = pygame.mask.from_surface(entity.image)
        collision = self.did_collide(entity.rect, mask)

        if collision:
            entity.damage(self.damage, self)

class Weapon:
    def __init__(self, name, image: pygame.Surface, data):
        surf = pygame.Surface((image.get_width()*2, image.get_height()))
        surf.blit(image, (image.get_width(), 0))
        surf.set_colorkey(image.get_colorkey())

        self.image = surf
        self.data = data
        self.name = name

        self.dmg = data["damage"]
        self.crit_rate = data["crit_rate"]
        self.attack_cooldown = data["attack_cooldown"]
        self.can_attack = True
        self.cooldown_timer = Timer(self.attack_cooldown)

        self.slash_info = data["slash_info"]

    def attack(self, pos, angle, owner, slash_list: list, flip=False):
        if self.can_attack:
            is_crit = random.random() < self.crit_rate
            slash = Slash(owner, self.dmg, is_crit, self.slash_info["lifetime"], flip, pos[0], pos[1], random.randint(self.slash_info["width"][0], self.slash_info["width"][1]), random.randint(self.slash_info["height"][0], self.slash_info["height"][1]), self.slash_info["speed"], random.randint(self.slash_info["slash_size"][0], self.slash_info["slash_size"][1]), self.slash_info["slash_change_size"], self.slash_info["roll_down_speed"], self.slash_info["color"], self.slash_info["radius"], angle, self.slash_info["shape"], self.slash_info["truncation"], cutout_radius=self.slash_info["cutout_radius"], cutout_center=self.slash_info["cutout_center"], roll_down_axis=self.slash_info["roll_down_axis"])

            slash_list.append(slash)
            self.can_attack = False
            self.cooldown_timer.set()

    def draw(self, pos, angle, surf, scroll):
        blit_center(surf, pygame.transform.rotate(self.image, angle), [pos[0]-scroll[0], pos[1]-scroll[1]])

    def update(self):
        self.cooldown_timer.update()

        if self.cooldown_timer.timed_out():
            self.can_attack = True