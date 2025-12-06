import pygame
from scripts.Engine import Entity, Timer


class HurtableEntity(Entity):
    def __init__(self, x, y, width, height, vel, jump_height, gravity, health, anim_obj=None, hurt_time=0.3):
        super().__init__(x, y, width, height, vel, jump_height, gravity, anim_obj)
        self.health = health

        self.hurt = False
        self.draw_mask = True
        self.invulnerable = False
        self.hurt_time = hurt_time
        self.hurt_display_count = 0
        self.hurt_timer = Timer(self.hurt_time)
        self.alive = True

    def draw_damage_mask(self, surf, scroll=[0, 0]):
        # Damage mask
        if self.hurt and self.draw_mask:
            mask = pygame.mask.from_surface(self.image)
            img = mask.to_surface(unsetcolor=(0, 0, 0, 0), setcolor=(255, 255, 255, 255))
            surf.blit(img, (self.rect.x-scroll[0], self.rect.y-scroll[1]))
    
    def die(self):
        self.alive = False
    
    def set_invulnerability(self, bool):
        self.invulnerable = bool
    
    def apply_knockback(self, movement):
        self.movement[0] = movement[0]
        self.vel_x = movement[0]
        self.vel_y = movement[1]
    
    def damage(self, dmg, cause = None, knockback=None):
        if not self.hurt and not self.invulnerable:
            self.health -= dmg
            if self.health <= 0:
                self.health = 0
                self.die()

            self.hurt = True
            self.hurt_timer.set()

            if knockback != None:
                self.apply_knockback(knockback)
    
    def update(self):
        self.hurt_timer.update()

        if self.hurt_timer.timed_out():
            self.hurt = False
