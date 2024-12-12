import pygame as pg
import math
from settings import *

def add_vectors(v1, v2):
    return [v1[0]+v2[0], v1[1]+v2[1]]
def mul_vectors(v1, m):
    return [v1[0]*m, v1[1]*m]

class Entity:
    def __init__(self, pos, size, sprites, display):
        self.remove = False
        self.rect = pg.Rect(*pos, *size)
        # Mass currently doesn't really matter but the idea was that collisions would distribute energy according to the ratio of the masses
        self.mass = math.log(size[0]*size[1]/100)+1
        self.vel = [0.0,0.0]
        self.acc = [0.0,0.0]
        self.on_ground = False
        self.collided = []

        self.set_animation(sprites)
        self.display = display
    
    def set_animation(self, sprites):
        self.animation = [pg.transform.scale(sprite, self.rect.size) for sprite in sprites]
        self.active_sprite = 0
        self.last_rotation = 0

    # each class should override handle_collision with its particular collision logic
    def handle_collision(self, item, collision_data):
        pass

    def handle_collisions(self, world):
        self.collided = []
        new_on_ground = False
        for item in world:
            # Never collide twice with the same item in the same frame
            if item is self or item in self.collided or self in item.collided:
                continue
            should_bounce = type(item).bounces
            intersection = self.rect.clip(item.rect)
            if intersection.width == 0 or intersection.height == 0:
                continue
            
            # collision_data format:
            # intersection: pg.Rect representing the overlap of the two entity's Rects
            # should_bounce: Boolean for whether one entity should bounce off the other, or just stop colliding
            # direction: "left" | "right" | "top" | "bottom" | "both"; direction of collision (eg. "left" means the left side of the other entity is hitting the right side of this entity)
            # axis: "x" | "y" | "both"; which axis the collision is on; "both" means a corner collision
            collision_data = {
                "intersection": intersection,
                "should_bounce": should_bounce,
            }
            if intersection.height-intersection.width > 2:
                collision_data["axis"] = "x"
                if should_bounce:
                    item.acc[0] += self.vel[0]*self.mass
                    self.vel[0] *= -1
                if self.rect.x < item.rect.x:
                    if should_bounce:
                        self.rect.x = item.rect.x-self.rect.width
                    collision_data["direction"] = "left"
                else:
                    if should_bounce:
                        self.rect.x = item.rect.right
                    collision_data["direction"] = "right"
            elif intersection.width-intersection.height > 2:
                collision_data["axis"] = "y"
                if self.rect.y < item.rect.y:
                    collision_data["direction"] = "top"
                    if should_bounce:
                        self.rect.y = item.rect.y-self.rect.height
                        self.vel[1] = 0
                        new_on_ground = True
                else:
                    collision_data["direction"] = "bottom"
                    if should_bounce:
                        self.rect.y = item.rect.bottom
                        self.vel[1] = 0
            else:
                collision_data["axis"] = "both"
                collision_data["direction"] = "both"
            self.handle_collision(item, collision_data)
            if should_bounce:
                self.collided.append(item)
                item.collided.append(self)
                opposite_dirs = {
                    "left": "right",
                    "right": "left",
                    "top": "bottom",
                    "bottom": "top",
                    "both": "both"
                }
                # on collision, have the other entity handle a collision with us
                # that way we know both entities handle the collision exactly once
                item.handle_collision(self, {
                    "intersection": collision_data["intersection"],
                    "axis": collision_data["axis"],
                    "direction": opposite_dirs[collision_data["direction"]],
                    "should_bounce": True,
                })
        self.on_ground = new_on_ground
    def add_gravity(self):
        # the player has a different gravity when jumping than when falling
        # it helps make the jump feel better
        # this should probably be in the Player class instead but whatever
        if self.vel[1] < 0:
            self.acc[1] += GRAVITY_JUMPING*self.mass
        else:
            self.acc[1] += GRAVITY*self.mass

    def update(self, world):
        self.add_gravity()
        self.vel = add_vectors(self.vel, mul_vectors(self.acc, 1/self.mass))
        # No-one's going to accelerate past the TERMINAL_VEL in the x direction right
        if self.vel[1] > TERMINAL_VEL:
            self.vel[1] = TERMINAL_VEL
        self.rect.x += self.vel[0]
        self.rect.y += self.vel[1]
        self.handle_collisions(world)
        self.acc = [0,0]
    
    # Since we merge adjacent bricks, we have to do fancy things to the sprite to make it look right
    def resize_sprite(self):
        new_animation = []
        for sprite in self.animation:
            sprite_rect = sprite.get_rect()
            new_sprite = sprite
            if self.rect.width > sprite_rect.width:
                new_sprite = pg.Surface(self.rect.size, sprite.get_flags())
                x = 0
                while x <= self.rect.width:
                    new_sprite.blit(sprite, (x, 0))
                    x += sprite_rect.width
            elif self.rect.height > sprite_rect.height:
                new_sprite = pg.Surface(self.rect.size, sprite.get_flags())
                y = 0
                while y <= self.rect.height:
                    new_sprite.blit(sprite, (0,y))
                    y += sprite_rect.height
            new_animation.append(new_sprite)
        self.animation = new_animation

    def reset_animation(self):
        self.active_sprite = 0
        self.last_rotation = 0
    # go to the next frame of your animation, but only if rate milliseconds have passed since you last switched
    # time_passed is the number of milliseconds elapsed this frame
    # also reset to animation frame 1 so frame 0 can be used for the resting sprite (eg. player/front.png)
    def rotate_animation(self, rate, time_passed):
        self.last_rotation += time_passed
        if self.last_rotation > rate:
            self.last_rotation = 0
            self.active_sprite += 1
            if self.active_sprite >= len(self.animation):
                self.active_sprite = 1

    def render(self):
        sprite = self.animation[self.active_sprite]
        if sprite.get_width() != self.rect.width or sprite.get_height() != self.rect.height:
            self.resize_sprite()
        sprite = self.animation[self.active_sprite]
        # assume sprites are oriented right by default, so flip them if moving left
        if self.vel[0] < 0:
            sprite = pg.transform.flip(sprite, True, False)
        self.display.blit(sprite, self.rect)
        if DEBUG:
            color = RED
            if self.on_ground:
                color = GREEN
            elif type(self) is Player and self.jumping:
                color = BLUE
            pg.draw.rect(self.display, color, self.rect, 1)

class Player(Entity):
    bounces = True
    def __init__(self, pos, display):
        super().__init__(pos, [PLAYER_W, PLAYER_H], SPRITES["player"], display)
        self.speed = PLAYER_SPEED
        self.next_level = False
        self.level = 1
        self.ground = None
        self.last_on_ground = 0
        self.jumping = False
        self.dt = 0

    
    def handle_collision(self, item, collision_data):
        if type(item) is Enemy:
            if not self.on_ground:
                item.remove = True
                self.vel[1] = -JUMP_STRENGTH
            else:
                self.remove = True
        elif collision_data["direction"] == "top":
            self.ground = item
    
    def update_time(self, clock):
        self.dt = clock.get_time()

    def update(self, world):
        self.handle_keys()

        friction = MOVING_FRICT
        if self.acc[0] == 0:
            friction = GROUND_FRICT
        target_vel = 0
        if self.ground is not None:
            # on moving blocks, friction pulls the player to the block's velocity rather than to 0
            target_vel = self.ground.vel[0]
        self.acc[0] += (target_vel-self.vel[0])*friction*self.mass

        super().update(world)

        if self.on_ground:
            self.last_on_ground = 0
            self.jumping = False
            # compare to target vel so we're not constantly walking on moving platforms
            if abs(self.vel[0]-target_vel) > 0.1:
                # 20 milliseconds is only slightly more than one frame but it makes it look a little better I think
                self.rotate_animation(20, self.dt)
            else:
                self.reset_animation()
        else:
            self.groud = None
            self.last_on_ground += 1

    def handle_keys(self):
        keys = pg.key.get_pressed()
        if keys[pg.K_LEFT]:
            self.acc[0] -= self.speed*self.mass 
        if keys[pg.K_RIGHT]:
            self.acc[0] += self.speed*self.mass 
        if keys[pg.K_SPACE]:
            # we implement long jumping by continue to apply a slight upward acceleration for a bit
            # if the user continues pressing space after jumping
            if not self.jumping and self.last_on_ground < COYOTE:
                self.jumping = True
                self.acc[1] = -JUMP_STRENGTH*self.mass
            elif self.jumping and self.last_on_ground < LONG_JUMP:
                self.acc[1] -= JUMP_STRENGTH*self.mass/15
        elif self.jumping:
            self.last_on_ground = LONG_JUMP+1
        

class Box(Entity):
    bounces = True
    def __init__(self, pos, display):
        super().__init__(pos, [BOX_W, BOX_W], SPRITES["box"], display)
    def update(self, world):
        self.acc[0] -= self.vel[0]*GROUND_FRICT*self.mass
        super().update(world)

    
class Brick(Entity):
    bounces = True
    def __init__(self, pos, display):
        super().__init__(pos, [BRICK_W, BRICK_H], SPRITES["brick"], display)
        self.init_pos = list(pos)
    # all of this just makes sure Bricks never move
    def handle_collision(self, item, collision_data):
        self.vel = [0,0]
        self.acc = [0,0]
        self.rect.topleft = list(self.init_pos)
    def update(self, world):
        self.rect.topleft = list(self.init_pos)
        self.vel = [0,0]
        self.acc = [0,0]
        self.handle_collisions(world)

class GrassBrick(Brick):
    bounces = True
    def __init__(self, *args):
        super().__init__(*args)
        self.set_animation(SPRITES["grass"])

class SlidingBrick(Entity):
    bounces = True
    def __init__(self, pos, display):
        super().__init__(pos, [BRICK_W, BRICK_H], SPRITES["platform"], display)
        self.init_y = pos[1]
        self.vel = [-1, 0]
    def handle_collision(self, item, collision_data):
        # We could allow the default behavior to bounce us around but then the player can
        # speed it up or slow it down with strategic bounces off the side
        if type(item) is SlidingBrickBouncer:
            self.vel[0] *= -1
            self.switched = True
            if self.rect.x < item.rect.x:
                self.rect.x = item.rect.x-self.rect.width
            else:
                self.rect.x = item.rect.right
        elif collision_data["axis"] == "x" and collision_data["should_bounce"]:
            self.vel[0] *= -1
    def add_gravity(self):
        pass
    def update(self, world):
        self.vel[1] = 0
        if self.vel[0] < 0:
            self.vel[0] = -1
        else:
            self.vel[0] = 1
        self.acc = [0, 0]
        super().update(world)
        self.rect.top = self.init_y

class SlidingBrickBouncer(Brick):
    bounces = False
    def render(self):
        pass


class Lava(Brick):
    bounces = True
    def __init__(self, pos, display):
        super().__init__(pos, display)
        self.animation = SPRITES["lava"]
        frames = len(self.animation)
        size = self.animation[0].get_rect()
        # basically each frame is a version of the image shifted over to the left a bit, with the part that "falls off" the left edge wrapped around to the right
        # like, if the image is divided into five chunks:
        # 1 2 3 4 5
        # the frames are:
        # 2 3 4 5 1
        # 3 4 5 1 2
        # etc
        # this gives the effect of the lava flowing, albeit choppily
        for i in range(1, frames):
            new_sprite = pg.Surface(size.size, self.animation[i].get_flags())
            blit_width = size.width-(i/frames)*size.width
            new_sprite.blit(self.animation[0], (size.width-blit_width-1,0), pg.Rect(0,0,blit_width+2,size.height))
            new_sprite.blit(self.animation[0], (0,0), pg.Rect(blit_width-1,0,size.width-blit_width+2,size.height))
            self.animation[i] = new_sprite
    def handle_collision(self, item, collision_data):
        if type(item) is Player:
            item.remove = True
        return super().handle_collision(item, collision_data)
    def update(self, world):
        self.rotate_animation(300, world[0].dt)
        super().update(world)

class Goal(Entity):
    bounces = False
    def __init__(self, pos, display):
        super().__init__(pos, [GOLD_W,GOLD_H], SPRITES["gold"], display)
    def handle_collision(self, item, collision_data):
        if type(item) is Player:
            item.next_level = True
            self.remove = True
        return super().handle_collision(item, collision_data)

class Enemy(Entity):
    bounces = False
    def __init__(self, pos, display):
        super().__init__(pos, [ENEMY_W, ENEMY_H], SPRITES["enemy"], display)
        self.vel = [-1, 0]
    
    def handle_collision(self, item, collision_data):
        if type(item) is not Brick and type(item) is not GrassBrick:
            return
        # enemies walk back and forth across platforms by detecting when they start colliding with the corner instead of the top
        # or falling off the edge
        if collision_data["direction"] == "top":
            if self.rect.x < item.rect.x or self.rect.right > item.rect.right:
                self.vel[0] *= -1
        else:
            self.vel[0] *= -1
