import pygame
import random

import scripts.Engine as E
from scripts.entity import HurtableEntity
from scripts.weapon import Slash
from scripts.misc import Coin
from scripts.projectile import *

vec2 = pygame.Vector2

class Enemy(HurtableEntity):
    def __init__(self, game, x, y, width, height, vel, jump_height, gravity, health, anim_obj=None, hurt_time=0.3):
        super().__init__(x, y, width, height, vel, jump_height, gravity, health, anim_obj, hurt_time)
        self.game = game

        self.attacking = False
        self.attack_timer = E.Timer(0, self.can_attack)
        self.flip = False

        self.max_vel_y = 7
        self.jump_count = 0
        self.max_jumps = 1
        self.grounded = False
        self.retardation = 0.2
        self.state = "idle"
        self.battle_enemy = False
        self.enemy_type = "base"

        self.coin_drop = 0
        self.dmg = 0
        self.exp_gain = 0
    
    def can_attack(self):
        self.attacking = False

    def move(self, tiles, ramps):
        self.movement = [0, 0]
        self.grounded = False
        if self.left:
            self.movement[0] = -self.vel
            self.flip = True
        if self.right:
            self.movement[0] = self.vel
            self.flip = False

        self.vel_y += self.gravity
        if self.vel_y > self.max_vel_y:
            self.vel_y = self.max_vel_y

        self.movement[1] = self.vel_y

        self.collisions = self.physics_obj.movement(self.movement, tiles, 1.0, ramps[0], ramps[1])
        self.rect.x = self.physics_obj.rect.x
        self.rect.y = self.physics_obj.rect.y

        if self.collisions["bottom"]:
            self.vel_y = 1
            self.grounded = True

        if self.collisions["top"]:
            self.vel_y = 1

    def run_ai(self, target, tiles):
        pass

    def update(self, target, tiles=[], ramps=[]):
        super().update()
        self.run_ai(target, tiles)
        self.move(tiles, ramps)

        self.attack_timer.update()


class Drone(Enemy):
    def __init__(self, game, x, y, width, height, image):
        super().__init__(game, x, y, width, height, 0.7, 0, 0, 1, None, 0.1)

        self.image = image
        self.coin_drop = 5
        self.exp_gain = 2
        self.dmg = 2
        self.attack_timer.set_cooldown(3)
        self.attack_timer.set()
        self.attacking = True
        self.enemy_type = "drone"

        self.clear_to_attack = True

        self.area_rect = pygame.Rect(0, 0, 960, 960) # 60 tiles range

        self.area_rect.x = self.rect.x-self.area_rect.width/2
        self.area_rect.y = self.rect.y-self.area_rect.height/2

    def draw(self, surf, scroll):
        if not self.hurt:
            color = (255, 0, 0)
        else:
            color = (255, 255, 255)

        E.perfect_outline(self.image, surf, (self.rect.x-scroll[0], self.rect.y-scroll[1]), color)
        surf.blit(self.image, (self.rect.x-scroll[0], self.rect.y-scroll[1]))
        #pygame.draw.rect(surf, (0, 255, 0), (self.rect.x-scroll[0], self.rect.y-scroll[1], self.rect.width, self.rect.height), 1)

        self.draw_damage_mask(surf, scroll)
    
    def move(self, tiles, ramps):
        if len(E.collision_test(self.rect, tiles)) == 0:
            self.clear_to_attack = True
        else:
            self.clear_to_attack = False

    def run_ai(self, target, tiles):
        rect = target.rect

        if not self.area_rect.colliderect(rect):
            return

        target_pos = vec2(rect.centerx+random.randint(-10, 10), rect.centery)
        pos = vec2(self.rect.centerx, self.rect.centery)

        if E.dis_between_points_opt(target_pos, pos) <= pow(120, 2):
            target_pos.y -= 16*4

        dir = target_pos-pos
        dir = dir.normalize()

        if E.dis_between_points_opt(target_pos, pos) <= pow(150, 2) and self.rect.y < rect.y - 8:
            direction = 1
            if dir.x < 0:
                direction = -1

            self.attack(direction)

        dir *= self.vel

        self.rect.x += dir.x
        self.rect.y += dir.y

        self.area_rect.x = self.rect.x-self.area_rect.width/2
        self.area_rect.y = self.rect.y-self.area_rect.height/2
    
    def attack(self, direction):
        if not self.attacking and self.clear_to_attack:
            surf = pygame.Surface((10, 10))
            surf.fill((255, 0, 0))
            self.game.projectiles.append(PhysicsProjectile(surf, self, self.dmg, self.rect.centerx, self.rect.centery, 10, 10, 0.2, [2.7*direction, 1.2]))
            self.attack_timer.set()
            self.attacking = True


class Dummy(Enemy):
    def __init__(self, game, x, y, width, height, anim_obj):
        super().__init__(game, x, y, width, height, 0, 0, 0, 4000, anim_obj, 0.3)

        self.hurt_timer.set_callback(self.set_idle)
        self.animation.set_loop(False)

        self.coin_drop = 2100
        self.enemy_type = "dummy"
        self.draw_mask = False

    def set_idle(self):
        self.state = "idle"

    def draw(self, surf, scroll):
        self.image = self.animation.animate(self.state, True)
        self.image = pygame.transform.flip(pygame.transform.scale(self.image, (self.image.get_width()*2, self.image.get_height()*2)), self.flip, False)

        #E.perfect_outline(pygame.transform.scale(self.image, (self.image.get_width()*2, self.image.get_height()*2)), surf, (self.x-scroll[0], self.y-scroll[1]-14), (255, 0, 0))
        surf.blit(self.image, (self.x-scroll[0], self.y-scroll[1]-14))
        #pygame.draw.rect(surf, (0, 255, 0), (self.x-scroll[0], self.y-scroll[1], self.rect.width, self.rect.height), 1)
    
    def damage(self, dmg, cause = None):
        super().damage(dmg)
        if self.hurt:
            self.state = "hurt"

        if(type(cause) == Slash):
            self.flip = cause.flip


class Roller(Enemy):
    def __init__(self, game, x, y, width, height, anim_obj=None):
        super().__init__(game, x, y, width, height, 0.5, 4, 0.2, 15, anim_obj)

        self.rolling_vel = 4
        self.state = "idle"
        self.enemy_type = "roller"
        self.idle_timer = E.Timer(random.randint(4, 8))
        self.attack_timer.set_cooldown(4)
        self.roll_timer = E.Timer(2.2)
        self.stun_timer = E.Timer(1.5)
        self.retardation = 0.06

        self.idle_timer.set()
        self.direction = "left"
        self.acceleration = 0.11

        self.line_of_sight_rect = pygame.FRect(self.rect.left-(16*10), self.rect.centery-8, 16*10, 20)

        self.coin_drop = 20
        self.dmg = 20
        self.exp_gain = 20
    
    def draw(self, surf, scroll):
        super().draw(surf, scroll)

        pygame.draw.rect(surf, (255, 0, 0), (self.line_of_sight_rect.x-scroll[0], self.line_of_sight_rect.y-scroll[1], self.line_of_sight_rect.width, self.line_of_sight_rect.height), 1)

        self.draw_damage_mask(surf, scroll)
    
    def move(self, tiles, ramps):
        self.movement = [0, 0]
        self.grounded = False
        if self.left:
            self.vel_x = -self.vel
            self.flip = True
        if self.right:
            self.vel_x = self.vel
            self.flip = False

        self.vel_y += self.gravity
        if self.vel_y > self.max_vel_y:
            self.vel_y = self.max_vel_y

        if self.state == "attack":
            if self.direction == "left":
                self.vel_x -= self.acceleration
                self.flip = True

            if self.direction == "right":
                self.vel_x += self.acceleration
                self.flip = False
        
        self.movement[0] = self.vel_x
        self.movement[1] = self.vel_y

        self.collisions = self.physics_obj.movement(self.movement, tiles, 1.0, ramps[0], ramps[1])
        self.rect.x = self.physics_obj.rect.x
        self.rect.y = self.physics_obj.rect.y

        if self.flip:
            self.line_of_sight_rect.x = self.rect.left-(16*10)
        if not self.flip:
            self.line_of_sight_rect.x = self.rect.right

        self.line_of_sight_rect.y = self.rect.centery-8
        

        if self.collisions["bottom"]:
            self.vel_y = 1
            self.grounded = True

        if self.collisions["top"]:
            self.vel_y = 1

        if self.state == "attack":
            if self.collisions["left"]:
                self.state = "stunned"
                self.vel_x = 2
                self.vel_y = -2.3
                self.stun_timer.set()

            if self.collisions["right"]:
                self.state = "stunned"
                self.vel_x = -2
                self.vel_y = -2.3
                self.stun_timer.set()
        else:
            if self.collisions["left"]:
                self.state = "right"
                
            if self.collisions["right"]:
                self.state = "left"
        
        if self.vel_x < 0:
            self.vel_x = min(self.vel_x+self.retardation, 0)
        if self.vel_x > 0:
            self.vel_x = max(self.vel_x-self.retardation, 0)
    
    def run_ai(self, target, tiles):

        if self.state == "right":
            if self.hurt and target.rect.x < self.rect.centerx:
                self.attack(target)
        elif self.state == "left":
            if self.hurt and target.rect.x > self.rect.centerx:
                self.attack(target)
        elif self.state == "idle":
            if self.hurt and self.attacking == False:
                self.attack(target)

        if self.state == "idle":
            self.left = False
            self.right = False
        
        if self.state == "left":
            self.left = True
            self.right = False

        if self.state == "right":
            self.right = True
            self.left = False
        
        if self.line_of_sight_rect.colliderect(target.rect) and self.state != "attack" and self.attacking == False:
            self.attack(target)
        
        if self.rect.colliderect(target.rect):
            knockback = [0, 0]
            if target.rect.x < self.rect.centerx:
                knockback[0] = -6
                knockback[1] = -4
            if target.rect.x > self.rect.centerx:
                knockback[0] = 6
                knockback[1] = -4
            
            target.damage(self.dmg, self, knockback)

    def attack(self, target):
        if target.rect.x < self.rect.x:
            self.direction = "left"
        if target.rect.x > self.rect.x:
            self.direction = "right"

        self.state = "attack"
        self.left = False 
        self.right = False
        self.attacking = True
        self.vel_y = -self.jump_height
        self.attack_timer.set()
        self.roll_timer.set()
        self.retardation = 0.06

    def update(self, target, tiles=[], ramps=[]):
        super().update(target, tiles, ramps)

        self.idle_timer.update()
        self.roll_timer.update()
        self.stun_timer.update()

        if self.roll_timer.timed_out() and self.state == "attack":
            self.state = "idle"
            self.retardation = 0.11
            self.idle_timer.set_cooldown(random.randint(4, 7))
            self.idle_timer.set()

        if self.idle_timer.timed_out() and self.state != "attack" and self.stun_timer.timed_out():
            if self.state == "idle":
                self.idle_timer.set_cooldown(random.randint(4, 12))
                self.state = random.choice(["left", "right"])
            else:
                self.idle_timer.set_cooldown(random.randint(8, 13))
                self.state = "idle"
            
            self.idle_timer.set()



class LazerOrb(Enemy):
    def __init__(self, game, x, y, width, height):
        super().__init__(game, x, y, width, height, 0, 0, 0, 5)
        
        self.enemy_type = "lazer orb"
        self.coin_drop = 0
        self.dmg = 20
        self.exp_gain = 5

        self.image.fill((255, 0, 0))

        self.attack_timer.set_cooldown(4)
        self.attack_timer.set()
        self.aim_timer = E.Timer(3.9)

        self.aim_timer.set()

        self.aiming = True
        self.attacking = False

        self.target_pos = [0, 0]

    def draw(self, surf, scroll):
        super().draw(surf, scroll)

        color = (255, 255, 0)
        pygame.draw.line(surf, color, (self.rect.centerx-scroll[0], self.rect.centery-scroll[1]), (self.target_pos[0]-scroll[0], self.target_pos[1]-scroll[1]), 1)

        self.draw_damage_mask(surf, scroll)

    def run_ai(self, target, tiles=[]):
        if self.aiming:
            self.target_pos = list(target.rect.center)
        
        if self.attack_timer.timed_out():
            self.attack(target)
            self.aiming = True
            self.aim_timer.set()
            self.attack_timer.set()
            
    
    def attack(self, target):
        _, collided = E.line_to_rect_collide(self.rect.center, self.target_pos, target.rect)

        if collided:
            knockback = [0, 0]
            if target.rect.x < self.rect.centerx:
                knockback[0] = -6
                knockback[1] = -4
            if target.rect.x > self.rect.centerx:
                knockback[0] = 6
                knockback[1] = -4

            target.damage(self.dmg, self, knockback)



    def update(self, target, tiles, ramps):
        super().update(target, ramps = [[], []])

        self.aim_timer.update()

        if self.aim_timer.timed_out():
            self.aiming = False

    




