import pygame as pg
from settings import *
from components import Player

pg.init()
screen = pg.display.set_mode((WIDTH, HEIGHT), pg.RESIZABLE)

clock = pg.time.Clock()


font = pg.font.SysFont("sans-serif", 50)
smallfont = pg.font.SysFont("sans-serif", 30)

def reset(level):
    global score_loc, player, world, signs, BRICK_W, BRICK_H
    LAYOUT = LEVELS[level-1]
    player = Player([WIDTH/2, HEIGHT/2], screen)
    player.level = level
    BRICK_W = WIDTH/len(LAYOUT[0])
    BRICK_H = HEIGHT/len(LAYOUT)
    world = []
    signs = []
    columns = [
        {} for char in LAYOUT[0]
    ]
    for y_idx in range(len(LAYOUT)):
        row = LAYOUT[y_idx]
        row_ents = {}
        y = y_idx*BRICK_H
        for x_idx in range(len(row)):
            column = columns[x_idx]
            x = x_idx*BRICK_W
            if row[x_idx] in LAYOUT_KEY.keys():
                item = LAYOUT_KEY[row[x_idx]]
                if item["merge"]:
                    # Merge adjacent bricks so they're single entities
                    # This prevents weird skipping along the floor and walls
                    if row[x_idx] in row_ents and row_ents[row[x_idx]][-1].rect.right == x and row_ents[row[x_idx]][-1].rect.height == BRICK_H:
                        row_ents[row[x_idx]][-1].rect.width += BRICK_W
                    elif row[x_idx] in column and column[row[x_idx]][-1].rect.bottom == y and column[row[x_idx]][-1].rect.width == BRICK_W:
                        column[row[x_idx]][-1].rect.height += BRICK_H
                    else:
                        if row[x_idx] not in column:
                            column[row[x_idx]] = []
                        if row[x_idx] not in row_ents:
                            row_ents[row[x_idx]] = []
                        e = item["type"]([x, y], screen)
                        column[row[x_idx]].append(e)
                        row_ents[row[x_idx]].append(e)
                        # Merging items are added to the beginning so they're always rendered and updated before everything else
                        # This probably doesn't really matter anymore but I'm keeping it just in case
                        world.insert(0, e)
                else:
                    world.append(item["type"]([x,y], screen))
            elif row[x_idx] == LAYOUT_KEY["player"]:
                player.rect.topleft = [x, y]
            elif row[x_idx] == LAYOUT_KEY["score"]:
                score_loc = [x, y]
            elif row[x_idx] == LAYOUT_KEY["sign"]:
                signs.append([LEVEL_SIGNS[level-1][len(signs)], x, y])
world = []
player = None
signs = []
score_loc = [0,0]
reset(1)

# Game loop
playing = True
while playing:
    # Event loop
    for event in pg.event.get():
        if event.type == pg.QUIT:
            playing = False
        elif event.type == pg.WINDOWSIZECHANGED:
            WIDTH = event.x
            HEIGHT = event.y
            reset(1)
        elif event.type == pg.KEYDOWN:
            if event.key == pg.K_q:
                playing = False
            elif event.key == pg.K_r:
                reset(player.level)

    # Update
    player.update_time(clock)
    player.update(world)
    if player.remove:
        reset(player.level)
        continue
    elif player.next_level:
        player.level += 1
        reset(player.level)
        continue
    new_world = []
    world_plus_player = [player, *world]
    for item in world:
        item.update(world_plus_player)
        if not item.remove and type(item) is not Player:
            new_world.append(item)
    world = new_world

    # Rendering
    screen.fill(COLORS["background"])

    ## signs
    for text, x, y, in signs:
        screen.blit(smallfont.render(text, True, COLORS["sign"]), (x, y))

    for item in world:
        item.render()
    player.render()

    ## HUD
    ### score
    screen.blit(font.render(str(player.level), True, COLORS["score"]), score_loc)
    ### fps
    if DEBUG:
        screen.blit(smallfont.render(str(round(clock.get_fps())), True, GRAY), (30, HEIGHT-40))

    pg.display.flip()

    # Delay
    clock.tick(FPS)


pg.quit()