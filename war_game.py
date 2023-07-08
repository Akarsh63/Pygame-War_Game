import pygame, sys
import os
from pygame.locals import *
import math
from constants import *
from bomb import Bomb, generate_bomb_coordinates
from civilian import Civilian
from bonus import Bonus
from enemy import calculate_new_xy,bullet_speed
from soldier import *
from sliders import *
from draw_functions import *
from game_buttons import create_button_func, create_button_center
from buttons import *
from load_image import load_image
from groups import (
    explosion_group,
    projectile_group,
    enemy_explosion_group,
    bonus_animation_group,
)
from game_stats import display_stats, stats

if not pygame.font:
    print("Warning, fonts disabled")
if not pygame.mixer:
    print("Warning, sound disabled")
pygame.init()

main_dir = os.path.split(os.path.abspath(__file__))[0]
data_dir = os.path.join(main_dir, "data")
sound_dir = os.path.join(main_dir, "sounds")
screen_shots_dir = os.path.join(main_dir, "saved_games_screen_shots")


def get_full_path(file):
    fullname = os.path.join(data_dir, file)
    return fullname


def get_full_path_ss(file):
    fullname = os.path.join(screen_shots_dir, file)
    return fullname


# Define Constants
FPS = pygame.time.Clock()
begin = False
checked = True

#Define Save Button in Game Page
saved_games = {}
#saved games number
count=1


e_slider = EnemySlider()
c_slider = CivilianSlider()
b_slider = BonusSlider()
ct_slider = CivilianTargetSlider(c_slider)
bt_slider = BonusTargetSlider(b_slider)
all_sliders = [e_slider, c_slider, b_slider, ct_slider, bt_slider]


def create_button(x, y, w, h, font, text, k, g, color=WHITE):
    button = pygame.Rect(x, y, w, h)
    pygame.draw.rect(DISPLAYSURF, color, button)
    button_text = font.render(text, True, BLACK)
    text_rect = button_text.get_rect(center=(x + (w / 2), y + (h / 2)))
    DISPLAYSURF.blit(button_text, text_rect)
    return button


def create_button_new(
    x, y, w, h, font, text, k, g, color=(0, 0, 0), back_col=(255, 255, 255)
):
    button = pygame.Rect(x, y, w, h)
    pygame.draw.rect(DISPLAYSURF, back_col, button)
    button_text = font.render(text, True, color)
    text_rect = button_text.get_rect(center=(x + (w / 2), y + (h / 2)))
    DISPLAYSURF.blit(button_text, text_rect)
    return button


class Target(pygame.sprite.Sprite):
    def __init__(self):
        pygame.sprite.Sprite.__init__(self)
        self.image, self.rect = load_image("target.png", -1, 0.1)
        screen = pygame.display.get_surface()
        # new_rect = pygame.Rect(surf_rect.x, surf_rect.y, surf_rect.width * 0.8, surf_rect.height)
        self.area = screen.get_rect()
        self.rect.topleft = (
            0.8*screen.get_width() - self.image.get_width() - 10,
            10,
        )
        self.mask = pygame.mask.from_surface(self.image)
        # NOTE: Draw border around rect
        # pygame.draw.rect(self.image, "red", self.image.get_rect(), 2)

        # NOTE: Color the rect
        # colorImage = pygame.Surface(self.image.get_size()).convert_alpha()
        # colorImage.fill("#848787")
        # self.image.blit(colorImage, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)

    def location(self):
        return self.rect.left, self.rect.top


def check_collision(new_x, new_y, ew, eh, targ):
    if new_x + ew > targ.rect.left - 2 and new_x + ew < targ.rect.right + 2:
        if new_y + eh > targ.rect.top - 2 and new_y + eh < targ.rect.bottom + 2:
            return True
        if new_y > targ.rect.top - 2 and new_y < targ.rect.bottom + 2:
            return True

    if new_x > targ.rect.left - 2 and new_x < targ.rect.right + 2:
        if new_y + eh > targ.rect.top - 2 and new_y + eh < targ.rect.bottom + 2:
            return True
        if new_y > targ.rect.top - 2 and new_y < targ.rect.bottom + 2:
            return True
    return False


def move_entities(object1, object2):
    pos = pygame.mouse.get_pos()
    new_x = pos[0] - (object1.rect.width / 2)
    new_y = pos[1] - (object1.rect.height / 2)
    ew = object1.rect.width
    eh = object1.rect.height
    if not check_collision(new_x, new_y, ew, eh, object2):
        object1.left = pos[0] - (object1.rect.width / 2)
        object1.top = pos[1] - (object1.rect.height / 2)
        object1.rect.topleft = pos[0] - (object1.rect.width / 2), pos[1] - (
            object1.rect.height / 2
        )

def save_screenshot(game_name,game_screen_copy):
    # Save the current display surface as a screenshot
    pygame.image.save(game_screen_copy,get_full_path_ss(str(game_name)+".png"))
    return get_full_path_ss(str(game_name)+".png")

def save_game(game_screen_copy,event,):
   global slider_value,count
   game_name='Game '+str(count)
   screenshot=save_screenshot(game_name,game_screen_copy)
   parameters={}
   parameters['obstacles']=e_slider.slider_value
   parameters['civilians']=c_slider.slider_value
   parameters['civilians_target']=ct_slider.slider_value
   parameters['bonus']=b_slider.slider_value
   parameters['bous_target']=bt_slider.slider_value
   parameters["screenshot"]=screenshot
   parameters["check"]=checked
   saved_games[str(game_name)]=parameters
   count+=1
   new_main_menu()

class Bullet(pygame.sprite.Sprite):
    def __init__(
        self,
        enemy,
    ):
        self.enemy = enemy
        self.angle = self.enemy.angle
        pygame.sprite.Sprite.__init__(self)
        self.image, self.rect = load_image("bullet.png", -1, 0.02, self.angle)
        screen = pygame.display.get_surface()
        self.area = screen.get_rect()
        self.rect.center = (
            self.enemy.rect.center[0]
            + (self.enemy.rect.width / 2) * math.cos(math.radians(self.angle)),
            self.enemy.rect.center[1]
            - (self.enemy.rect.height / 2) * math.sin(math.radians(self.angle))
            - (self.rect.height / 2) * math.sin(math.radians(self.angle)),
        )
        self.isRandom = enemy.isRandom
        self.positionx = self.rect.center[0]
        self.positiony = self.rect.center[1]

    def update(self, dt, x, y, surf):
        global show_image
        pygame.draw.line(
            surf, WHITE, (self.rect.center[0], self.rect.center[1]), (x, y)
        )
        center = calculate_new_xy(
            (self.positionx, self.positiony), bullet_speed, math.radians(self.angle), dt
        )
        self.positionx = center[0]
        self.positiony = center[1]
        self.rect.center = (round(self.positionx), round(self.positiony))
        # print(self.rect.center)
        # NOTE: Bullet leaves the screen
        # Get the rect of the surf surface
        surf_rect = surf.get_rect()

        # Create a new rect that is 80% of the width of the surf rect
        new_rect = pygame.Rect(surf_rect.x, surf_rect.y, surf_rect.width * 0.8, surf_rect.height)
        if not new_rect.contains(self.rect):
            # Check if this is the last bullet in the group and print message if true
            bullet_group = self.groups()[0]
            if self == bullet_group.sprites()[0]:
                show_image=False
            self.kill()

show_image=False
def start():
    global begin,show_image
    show_image=False
    # Bullet Event
    milliseconds_delay = 2000  # 0.5 seconds
    bullet_event = pygame.USEREVENT + 1
    pygame.time.set_timer(bullet_event, milliseconds_delay)

    # Bomb Event
    bomb_delay = 3000
    bomb_event = pygame.USEREVENT + 2
    pygame.time.set_timer(bomb_event, bomb_delay)

    # Display parameters
    pygame.display.set_caption("War")
    pygame.mouse.set_visible(True)
    DISPLAYSURF.fill("#aaeebb")

    # Create The Background
    background = pygame.Surface(DISPLAYSURF.get_size())
    background.fill("#aaeebb")

    # Add bushes
    bush_img = pygame.image.load(get_full_path("bush.png"))
    # bush_img.convert_alpha() # bush_img.convert()
    bush_img = bush_img.copy()
    alpha = 128
    bush_img.fill((255, 255, 255, alpha), None, pygame.BLEND_RGBA_MULT)
    bush_img = pygame.transform.scale(bush_img, (60, 40))
    for y in range(0, 600, 40):
        for x in range(0, 900, 60):
            background.blit(bush_img, (x, y))
    pygame.display.flip()

    # Display The Background
    DISPLAYSURF.blit(background, (0, 0))
    pygame.display.flip()

    enemies = draw_enemies(e_slider.slider_value)
    civilians = draw_civilians(c_slider.slider_value)
    bonuses = draw_bonuses(b_slider.slider_value)
    civilian_target = ct_slider.slider_value
    bonus_target = bt_slider.slider_value

    soldier = Soldier(civilian_target, bonus_target)
    target = Target()
    soldier_group = pygame.sprite.Group((soldier))
    target_group = pygame.sprite.Group((target))
    enemy_group = pygame.sprite.Group(tuple(enemies))

    civilian_group = pygame.sprite.Group(tuple(civilians))
    bonus_group = pygame.sprite.Group(tuple(bonuses))
    bullet_group = pygame.sprite.Group()
    bomb_group = pygame.sprite.Group()

    if soldier.bonus >= soldier.bon_target:
        stats.task1 = True

    if soldier.civilians >= soldier.civ_target:
        stats.task2 = True

    # create_button(550, 10, 120, 50, font, "Quit", 580, 15)

    game = True
    won = False
    killed = False
    displayed = False
    is_selected = False
    selected_enemy = None
    direction = -1
    global begin
    begin_button = None
    restart_button = None
    rotate_left_button = None
    rotate_right_button = None
    menu_button = None
    flip_button = None
    random_button = None
    back_button = None
    info_button = None
    bomb_iteration = 0
    start_time = pygame.time.get_ticks()

    lost1="Commander : You have been hit by a bullet."
    lost2="Commander : You have been hit by a bomb."
    won1="Commander : Target Reached!You completed the task."
    lines1=split(lost1,DISPLAYSURF.get_width())
    lines2=split(lost2,DISPLAYSURF.get_width())
    lines3=split(won1,DISPLAYSURF.get_width())
    logo=pygame.image.load(get_full_path("settings_logo.png"))
    logo= pygame.transform.scale(logo, (40,40))
    button_rect = logo.get_rect()
    button_rect.x=0.93*disp_width
    button_rect.y=0.056*disp_height
    index=0
    j=0
    t=0
    surfaces=[]   
    paused=False
    rect_set = pygame.Rect(260,30, 200, 240)
    rect_set_surf = pygame.Surface((rect_set.width, rect_set.height), pygame.SRCALPHA)
    game_screen_copy=DISPLAYSURF.copy()
    bullets=0
    bombs=0
    # Load the image
    image = pygame.image.load(get_full_path("warning.png"))
    image = pygame.transform.scale(image, (50,50))
    # Create The Background
    background3 = pygame.Surface((0.2*(DISPLAYSURF.get_size()[0]),DISPLAYSURF.get_size()[1]))
    background3.fill("#6e6e80")

    while game:
        direction = -1
                # Time Elapsed
        dt = FPS.tick_busy_loop(60)  # CHANGE
        # Game Won
        if pygame.sprite.collide_mask(soldier, target):
            stats.time = (pygame.time.get_ticks() - start_time) / 1000.0
            stats.based_reached = True
            won = True

        number_of_strikes = 0
        if (
            number_of_strikes := len(
                pygame.sprite.spritecollide(soldier, bullet_group, True)
            )
        ) > 0:
            soldier.health -= number_of_strikes
            if soldier.health <= 0:
                stats.time = (pygame.time.get_ticks() - start_time) / 1000.0
                killed = True
                bullets=1
        if soldier.health<=0 and soldier.killed_bomb:
            killed = True
            stats.time = (pygame.time.get_ticks() - start_time) / 1000.0
            bombs=1

        for event in pygame.event.get():
            if event.type == pygame.MOUSEBUTTONDOWN:
                # Check if the save button was clicked
                    if button_rect.collidepoint(pygame.mouse.get_pos()):
                       game_screen_copy = DISPLAYSURF.copy()
                       paused=True

                    elif paused and begin:
                        if save.collidepoint(pygame.mouse.get_pos()):
                            save_game(game_screen_copy,event)
                        elif menu.collidepoint(pygame.mouse.get_pos()):
                            new_main_menu()
                        elif back.collidepoint(pygame.mouse.get_pos()):
                            paused=False
            if event.type == pygame.QUIT:
                game = False
            # Make new bullets
            if (event.type == bullet_event) and begin and (not won) and (not killed) and (not paused):
                sold_y = soldier.rect.center[1]
                sold_x = soldier.rect.center[0]
                for enemy in enemy_group:
                    enemy.random_reorientation(sold_x, sold_y)
                    bullet = Bullet(enemy)
                    bullet_group.add(bullet)
                    show_image=True
            # Make new bombs
            if (event.type == bomb_event) and begin and (not won) and (not killed) and (not paused):
                if bomb_iteration == 0:
                    coordinate_x, coordinate_y = generate_bomb_coordinates()
                    sold_y = soldier.rect.center[1]
                    sold_x = soldier.rect.center[0]

                    bomb = Bomb(
                        coordinate_x,
                        coordinate_y,
                        DISPLAYSURF,
                        sold_x,
                        sold_y,
                    )
                    bomb_group.add(bomb)
                # else:
                # bomb_iteration += 1
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    direction = 0
                elif event.key == pygame.K_DOWN:
                    direction = 1
                elif event.key == pygame.K_LEFT:
                    direction = 2
                elif event.key == pygame.K_RIGHT:
                    direction = 3
                elif event.key == pygame.K_SPACE:
                    if projectile_group.sprite == None:
                        soldier.throw(pygame.time.get_ticks())
                elif event.key == pygame.K_r:
                    for civ in civilian_group:
                        if civ.incident:
                            civ.rescued()
                            soldier.add_civilian()
                            stats.civ += 1
                            if soldier.civilians >= soldier.civ_target:
                                stats.task2 = True
            elif event.type == pygame.MOUSEBUTTONDOWN:
                pos = pygame.mouse.get_pos()
                x = pos[0]
                y = pos[1]
                if event.button == 1:
                    for enemy in enemy_group:
                        if enemy.rect.collidepoint(pos):
                            enemy.clicked = True
                            enemy.selected = not enemy.selected
                            is_selected = enemy.selected
                            if is_selected:
                                selected_enemy = enemy
                            else:
                                selected_enemy = None
                        else:
                            enemy.selected = False
                    for civ in civilian_group:
                        if civ.rect.collidepoint(pos):
                            civ.clicked = True
                    for bon in bonus_group:
                        if bon.rect.collidepoint(pos):
                            bon.clicked = True
                if (begin_button != None) and (
                    begin_button.collidepoint(pygame.mouse.get_pos())
                ):
                    begin = True
                    begin_button = None
                    restart_button = None
                    rotate_left_button = None
                    rotate_right_button = None
                    flip_button = None
                    back_button = None
                    info_button = None
                    random_button = None
                if (restart_button != None) and (
                    restart_button.collidepoint(pygame.mouse.get_pos())
                ):
                    paused=False
                    begin = True
                    won = False
                    killed = False
                    show_image=False
                    index=0
                    j=0
                    t=0
                    surfaces=[]
                    bullets=0
                    bombs=0
                    displayed = False
                    soldier.restart()
                    bomb_group.empty()
                    explosion_group.empty()
                    enemy_explosion_group.empty()
                    bullet_group.empty()
                    restart_button = None
                if (
                    (rotate_left_button != None)
                    and is_selected
                    and rotate_left_button.collidepoint(pygame.mouse.get_pos())
                ):
                    selected_enemy.change_angle(1)
                if (
                    (rotate_right_button != None)
                    and is_selected
                    and rotate_right_button.collidepoint(pygame.mouse.get_pos())
                ):
                    selected_enemy.change_angle(-1)
                if (
                    (flip_button != None)
                    and is_selected
                    and flip_button.collidepoint(pygame.mouse.get_pos())
                ):
                    selected_enemy.flip_enemy()
                if (back_button != None) and (
                    back_button.collidepoint(pygame.mouse.get_pos())
                ):
                    begin = False
                    won = False
                    killed = False
                    bomb_group.empty()
                    explosion_group.empty()
                    enemy_explosion_group.empty()
                    bullet_group.empty()
                if (info_button != None) and (
                    info_button.collidepoint(pygame.mouse.get_pos())
                ):
                    pass
                if (random_button != None) and (
                    random_button.collidepoint(pygame.mouse.get_pos())
                ):
                    if selected_enemy != None:
                        selected_enemy.isRandom = not selected_enemy.isRandom
            elif event.type == pygame.MOUSEBUTTONUP:
                for enemy in enemy_group:
                    enemy.clicked = False
                for civ in civilian_group:
                    civ.clicked = False
                for bon in bonus_group:
                    bon.clicked = False

        # Move the enemies, civilians and bonuses to desired position
        if not begin:
            for enemy in enemy_group:
                if enemy.clicked:
                    move_entities(enemy, target)
            for civ in civilian_group:
                if civ.clicked:
                    move_entities(civ, target)
            for bon in bonus_group:
                if bon.clicked:
                    move_entities(bon, target)

        # update bomb target coordinates
        for b in bomb_group:
            b.lim_x = soldier.rect.center[0]
            b.lim_y = soldier.rect.center[1]

        # Draw Everything
        DISPLAYSURF.blit(background, (0, 0))
        DISPLAYSURF.blit(background3, (0.8*DISPLAYSURF.get_size()[0], 0))
        if begin:
            background3.blit(logo, (0.13*disp_width, 0.053*disp_height))
        if not killed:
            soldier_group.draw(DISPLAYSURF)
        if not killed:
            soldier_group.draw(DISPLAYSURF)
        display_health(soldier)
        target_group.draw(DISPLAYSURF)
        enemy_group.draw(DISPLAYSURF)
        bonus_group.draw(DISPLAYSURF)
        civilian_group.draw(DISPLAYSURF)
        bullet_group.draw(DISPLAYSURF)
        bomb_group.draw(DISPLAYSURF)
        explosion_group.draw(DISPLAYSURF)
        enemy_explosion_group.draw(DISPLAYSURF)
        bonus_animation_group.draw(DISPLAYSURF)
        projectile_group.draw(DISPLAYSURF)

        # Call Update Function of all Sprites
        # Don't draw buttons if game has begun
        if (begin) and (not won) and (not killed) and (not paused):
            if show_image:
                 DISPLAYSURF.blit(image, (1000, 520))
            soldier_group.update(direction)
            projectile_group.update(pygame.time.get_ticks(), dt)
            bullet_group.update(
                dt, soldier.rect.center[0], soldier.rect.center[1], DISPLAYSURF
            )
            bomb_group.update(dt)
            enemy_group.update(
                soldier.rect.center[0], soldier.rect.center[1], DISPLAYSURF
            )
            for civ in civilian_group:
                if civ.rect.colliderect(soldier.rect):
                    civ.incident = True
                else:
                    civ.incident = False
            for p in projectile_group:  # enemy explosions
                for e in pygame.sprite.spritecollide(p, enemy_group, False):
                    p.enemy_explosion(e.location()[0], e.location()[1])
                    e.killed()
            for bon in pygame.sprite.spritecollide(soldier, bonus_group, False):
                bon.collected()
                soldier.add_bonus()
                stats.bon += 1
                pygame.mixer.Sound.play(clink_sound)
                if soldier.bonus >= soldier.bon_target:
                    stats.task1 = True
                # pygame.mixer.Sound.stop(clink_sound)
                # pygame.mixer.Sound.play(bonus_sound)
            for particle in bonus_animation_group:
                particle.emit()

        if begin and (not won):
            explosion_group.update(soldier, soldier.location_center())
            bonus_animation_group.update()
            enemy_explosion_group.update(soldier, soldier.location_center())

        # Buttons to start the game and change parameters
        if not begin:
            begin_button = ext_begin_button_gray()
            back_button = ext_back_button()
            info_button = ext_info_button()
            if is_selected:
                rotate_left_button = ext_rotate_left_button_gray()
                rotate_right_button = ext_rotate_right_button_gray()
                flip_button = ext_flip_button_gray()
                if selected_enemy.isRandom:
                    random_button = ext_random_button_gray()
                else:
                    random_button = ext_random_button_green()
            else:
                rotate_left_button = ext_rotate_left_button_green()
                rotate_right_button = ext_rotate_right_button_green()
                flip_button = ext_flip_button_green()
                random_button = ext_random_button_green()
        
# Display restart button if game has ended
        if paused :
            DISPLAYSURF.blit(rect_set_surf, (350, 160))
            pygame.draw.rect(rect_set_surf, (51,51,51, 180),pygame.Rect(0, 0, rect_set_surf.get_width(), rect_set_surf.get_height()))
            save=create_button_func(385, 180, 130, 40, pygame.font.SysFont("Arial", 27), "SAVE",DISPLAYSURF,WHITE,(51,51,51,240))
            menu=create_button_func(385, 260, 130, 40, pygame.font.SysFont("Arial", 22), "HOME PAGE",DISPLAYSURF,WHITE,(51,51,51,240))
            back=create_button_func(385, 340, 130, 40, pygame.font.SysFont("Arial", 24), "CONTINUE",DISPLAYSURF,WHITE,(51,51,51,240))

        # Display restart button if game has ended
        if won or killed:
            restart_button = ext_restart_button()
            if not displayed:
                displayed = True
                display_stats()
        if won:
                print("won")
                lines=lines3
                index += 1
                    
                if(j<len(lines)):
                        if index > len(lines[j]):
                                index = 0
                                j+=1
                        if (j<len(lines)):
                                text_surface = pygame.font.SysFont("couriernew", 16).render(lines[j][:index], True, "#ffffff")
                        
                if(len(surfaces)>0):
                        for k in range(len(surfaces)):
                                DISPLAYSURF.blit(surfaces[k],(int(0.81*DISPLAYSURF.get_size()[0]),80+40*k))
                                t=k+1
                if j<len(lines):
                        if index+1 > len(lines[j]):
                                surfaces+=[text_surface]
                if(j<len(lines)):
                            DISPLAYSURF.blit(text_surface,(int(0.81*DISPLAYSURF.get_size()[0]),80+40*t))

        if killed:
            if bullets==1:
                      lines=lines1
            elif bombs==1:
                      lines=lines2
            index += 1
                    
            if(j<len(lines)):
                        if index > len(lines[j]):
                                index = 0
                                j+=1
                        if (j<len(lines)):
                                text_surface = pygame.font.SysFont('Arial',23).render(lines[j][:index], True, "#ffffff")
                        
            if(len(surfaces)>0):
                        for k in range(len(surfaces)):
                                DISPLAYSURF.blit(surfaces[k],(int(0.81*DISPLAYSURF.get_size()[0]),80+40*k))
                                t=k+1
            if j<len(lines):
                        if index+1 > len(lines[j]):
                                surfaces+=[text_surface]
            if(j<len(lines)):
                            DISPLAYSURF.blit(text_surface,(int(0.81*DISPLAYSURF.get_size()[0]),80+40*t))

        
        pygame.display.flip()

    pygame.quit()


def go_settings():
    pygame.display.set_caption("Settings")

    global checked

    # Load the background image
    background_image = pygame.image.load(get_full_path("backl.jpg"))
    background_image.set_alpha(150)
    background_image = pygame.transform.scale(background_image, (900, 600))
    background = pygame.Surface(DISPLAYSURF.get_size())
    background.blit(background_image, (0, 0))

    # Define the rectangles
    rect = pygame.Rect(0, disp_height / 7, disp_width, 5 * disp_height / 7)
    rect_surf = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
    apply = pygame.Rect(
        disp_width / 8 - 75, (5 * disp_height / 7 + disp_height / 14) - 20, 150, 40
    )
    apply_surf = pygame.Surface((apply.width, apply.height), pygame.SRCALPHA)
    cancel = pygame.Rect(
        3 * disp_width / 8 - 75, (5 * disp_height / 7 + disp_height / 14) - 20, 150, 40
    )
    cancel_surf = pygame.Surface((cancel.width, cancel.height), pygame.SRCALPHA)
    apply_text = font.render("APPLY", True, (255, 255, 255))
    apply_text_rect = apply_text.get_rect(center=(apply.width // 2, apply.height // 2))
    cancel_text = font.render("BACK", True, (255, 255, 255))
    cancel_text_rect = cancel_text.get_rect(
        center=(cancel.width // 2, cancel.height // 2)
    )
    checkbox_rect = pygame.Rect(
        15 * disp_width / 16 - 15,
        (5 * disp_height / 7) + (disp_height / 14) - 15,
        30,
        30,
    )

    # Define the checkbox colors
    unchecked_color = (255, 255, 255)
    checked_color = (0, 255, 0)
    border_color = (0, 0, 0)

    # Set the initial checkbox state to unchecked
    running = True
    temp_checked = checked
    menu_btn_width = 150

    # CONSTANTS
    top_margin = disp_height / 7
    division = disp_height / 7
    slider_row_height = (4 * division) / 3
    slider_row_width = (2 * disp_width) / 5

    while running:
        DISPLAYSURF.blit(background, (0, 0))
        for sl in all_sliders:
            draw_slider(sl)
        pygame.draw.line(
            DISPLAYSURF,
            "white",
            (0, 5 * disp_height / 7),
            (disp_width, 5 * disp_height / 7),
        )  # DEBUG

        DISPLAYSURF.blit(
            rect_surf, (0, disp_height / 7)
        )  # this is the light background

        settings_ui(top_margin, slider_row_height, rect_surf, apply_surf, cancel_surf)
        for s in all_sliders:
            draw_slider(s)

        draw_text_right_align(
            "Show Tutorial",
            pygame.font.SysFont("BOLD", 30),
            "#ffffff",
            (7 * disp_width / 8),
            (5 * disp_height / 7 + disp_height / 14),
            DISPLAYSURF,
        )

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEMOTION:
                if event.buttons[0] == 1:  # if left button is pressed
                    if e_slider.slider_rect.collidepoint(pygame.mouse.get_pos()):
                        e_slider.slider_value = e_slider.find_value(event)
                    if b_slider.slider_rect.collidepoint(pygame.mouse.get_pos()):
                        b_slider.slider_value = b_slider.find_value(event)
                        bt_slider.update()
                    if c_slider.slider_rect.collidepoint(pygame.mouse.get_pos()):
                        c_slider.slider_value = c_slider.find_value(event)
                        ct_slider.update()
                    if ct_slider.slider_rect.collidepoint(pygame.mouse.get_pos()):
                        ct_slider.slider_value = ct_slider.find_value(event)
                    if bt_slider.slider_rect.collidepoint(pygame.mouse.get_pos()):
                        bt_slider.slider_value = bt_slider.find_value(event)

            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                # Check if the mouse click was inside the checkbox
                if checkbox_rect.collidepoint(event.pos):
                    temp_checked = not temp_checked
                if apply.collidepoint(event.pos):
                    checked = temp_checked
                    new_main_menu()
                if cancel.collidepoint(event.pos):
                    #   slider_value=temp_value
                    new_main_menu()

        # Draw the checkbox
        if temp_checked:
            pygame.draw.rect(DISPLAYSURF, checked_color, checkbox_rect)
            pygame.draw.line(
                DISPLAYSURF,
                border_color,
                (checkbox_rect.left + 10, checkbox_rect.centery),
                (checkbox_rect.centerx, checkbox_rect.bottom - 10),
                3,
            )
            pygame.draw.line(
                DISPLAYSURF,
                border_color,
                (checkbox_rect.centerx, checkbox_rect.bottom - 10),
                (checkbox_rect.right - 10, checkbox_rect.top + 10),
                3,
            )
        else:
            pygame.draw.rect(DISPLAYSURF, unchecked_color, checkbox_rect)
        pygame.draw.rect(DISPLAYSURF, border_color, checkbox_rect, 3)

        cancel_surf.blit(cancel_text, cancel_text_rect)
        DISPLAYSURF.blit(
            cancel_surf,
            (3 * disp_width / 8 - 75, (5 * disp_height / 7 + disp_height / 14) - 20),
        )
        apply_surf.blit(apply_text, apply_text_rect)
        DISPLAYSURF.blit(
            apply_surf,
            (disp_width / 8 - 75, (5 * disp_height / 7 + disp_height / 14) - 20),
        )
        pygame.display.update()

    pygame.quit()


def intermediate():
    # Set up the screen
    screen = pygame.display.set_mode(DISPLAYSURF.get_size())
    pygame.display.set_caption("Get Ready to War!")
    text = "Commander : Welcome Soldier!Here is your mission, you have to reach the target which is located at (,) and you are at (,).Reach the target and escape from the enemy base at the same time.The target is surrounded by the red rectance in the picture."
    intro_img = pygame.image.load(get_full_path("intro.png"))
    intro_img = pygame.transform.scale(intro_img, (0.8*DISPLAYSURF.get_size()[0],0.9*DISPLAYSURF.get_size()[1]))

    # Split the text into lines based on screen width
    words = text.split()
    lines = []
    line = ""
    for word in words:
        if pygame.font.SysFont("couriernew", 20).size(line + " " + word)[0] > 0.19*DISPLAYSURF.get_size()[0]:
            lines.append(line.strip())
            line = ""
        line += " " + word
    lines.append(line.strip())
    clock = pygame.time.Clock()
    index = 0
    j = 0
    surfaces = []
    y = 0
    while True:
        screen.fill("#353740")
        clock.tick(50)
        Play = create_button_func(
            400,
            545,
            120,
            50,
            pygame.font.SysFont(None, 36),
            "Play!",
            screen,
            WHITE,
            "#964F4CFF",
        )
        if Play.collidepoint(pygame.mouse.get_pos()):
            Play = create_button_func(
                400,
                545,
                120,
                50,
                pygame.font.SysFont(None, 38),
                "Play",
                screen,
                "#696667FF",
                WHITE,
            )
        else:
            Play = create_button_func(
                400,
                545,
                120,
                50,
                pygame.font.SysFont(None, 36),
                "Play",
                screen,
                WHITE,
                "#964F4CFF",
            )
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                quit()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if Play.collidepoint(pygame.mouse.get_pos()):
                    # Start the game
                    start()

        # Draw the text surface to the screen

        # Update the text surface
        index += 1
        screen.blit(intro_img, (0, 0))
        if j < len(lines):
            if index > len(lines[j]):
                index = 0
                j += 1
            if j < len(lines):
                text_surface = pygame.font.SysFont("couriernew", 18).render(lines[j][:index], True, (255,255,255))

        if len(surfaces) > 0:
            for k in range(len(surfaces)):
                screen.blit(surfaces[k], (0.81*DISPLAYSURF.get_size()[0], 30 + 30 * k))
                y = k + 1
        if j < len(lines):
            if index + 1 > len(lines[j]):
                surfaces += [text_surface]
        if j < len(lines):
            screen.blit(text_surface, (0.81*DISPLAYSURF.get_size()[0], 30 + 30 * y))

        pygame.display.update()


def load_screenshot(game_name):
    image = pygame.image.load(get_full_path_ss(str(game_name) + '.png'))

    # Set the size for the image
    DEFAULT_IMAGE_SIZE = (240, 160)
    # Scale the image to your needed size
    image = pygame.transform.scale(image, DEFAULT_IMAGE_SIZE)
    return image

class ScrollBar():
    def __init__(self,screen1_height):
        self.y_axis = 0
        self.screen1_height = screen1_height
        self.change_y = 0
        
        bar_height = int((disp_height-100 - 40) / (screen1_height / ((disp_height-100) * 1.0)))
        self.bar_rect = pygame.Rect(disp_width- 20,20,20,bar_height)
        self.bar_up = pygame.Rect(disp_width - 20,0,20,20)
        self.bar_down = pygame.Rect(disp_width - 20,disp_height - 120,20,20)
        
        self.bar_up_image = pygame.image.load(get_full_path("up.png")).convert()
        self.bar_down_image = pygame.image.load(get_full_path("down.png")).convert()
        
        self.on_bar = False
        self.mouse_diff = 0
        
    def update(self):
        self.y_axis += self.change_y
        
        if self.y_axis > 0:
            self.y_axis = 0
        elif (self.y_axis + self.screen1_height) < disp_height-100:
            self.y_axis = disp_height-100 - self.screen1_height
            
        height_diff = self.screen1_height - disp_height+100
        
        scroll_length = disp_height-100- self.bar_rect.height - 40
        bar_half_lenght = self.bar_rect.height / 2 + 20
        
        if self.on_bar:
            pos = pygame.mouse.get_pos()
            self.bar_rect.y = pos[1] - self.mouse_diff
            if self.bar_rect.top < 20:
                self.bar_rect.top = 20
            elif self.bar_rect.bottom > (disp_height -100- 20):
                self.bar_rect.bottom = disp_height -100- 20
            
            self.y_axis = int(height_diff / (scroll_length * 1.0) * (self.bar_rect.centery - bar_half_lenght) * -1)
        else:
            self.bar_rect.centery =  scroll_length / (height_diff * 1.0) * (self.y_axis * -1) + bar_half_lenght
             
        
    def event_handler(self,event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            pos = pygame.mouse.get_pos()
            if self.bar_rect.collidepoint(pos):
                self.mouse_diff = pos[1] - self.bar_rect.y
                self.on_bar = True
            elif self.bar_up.collidepoint(pos):
                self.change_y = 5
            elif self.bar_down.collidepoint(pos):
                self.change_y = -5
                
        if event.type == pygame.MOUSEBUTTONUP:
            self.change_y = 0
            self.on_bar = False
        
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP:
                self.change_y = 5
            elif event.key == pygame.K_DOWN:
                self.change_y = -5
                
        if event.type == pygame.KEYUP:
            if event.key == pygame.K_UP:
                self.change_y = 0
            elif event.key == pygame.K_DOWN:
                self.change_y = 0
                
    def draw(self,screen2):
        pygame.draw.rect(screen2,GRAY,self.bar_rect)
        
        screen2.blit(self.bar_up_image,(disp_width - 20,0))
        screen2.blit(self.bar_down_image,(disp_width- 20,disp_height - 120))


def go_saved_games(saved_games):
    global checked
    # Set the width and height of the screen [width, height]
    screen = pygame.display.set_mode((disp_width,disp_height))
    # Set the current window caption
    pygame.display.set_caption("Saved Games")
    # Used to manage how fast the screen updates
    clock = pygame.time.Clock()
    # -------- Main Program Loop -----------
        #number of rows of saved_games in screen1 
    if (len(saved_games)%3==0):
        rows=len(saved_games)//3
    else:
        rows=(len(saved_games)//3)+1

    saved_game_button_height=200
    saved_game_button_width=50

    if (rows*250<=disp_height-100):
        SCREEN_HEIGHT_UPDATE=disp_height-100
    else:
        SCREEN_HEIGHT_UPDATE=rows*250
    screen1=pygame.Surface((disp_width,SCREEN_HEIGHT_UPDATE))
    screen1.fill("#9BA4B5")
    
    # 61876E
    # screen1.fill("#285430")
    # Create scrollbar object 
    scrollbar = ScrollBar(screen1.get_height())
    # To display saved games as buttons on main menu
    pygame.display.flip()
    # Load the background image
    background_image = pygame.image.load(get_full_path("back2.png"))
    background_image.set_alpha(100)
    background_image = pygame.transform.scale(background_image, (disp_width, SCREEN_HEIGHT_UPDATE))
    background = pygame.Surface(screen1.get_size())
    background.blit(background_image, (0, 0))
    while True:
        screen.fill("#577D86")
        screen1.blit(background,(0,0))
        # screen.fill("#285430")
        back=create_button_func(500,525,120,50,pygame.font.SysFont(None, 36),"Menu",screen,WHITE,"#2C3333")
        if back.collidepoint(pygame.mouse.get_pos()):
                back=create_button_func(500,525,120,50,pygame.font.SysFont(None, 38),"Menu",screen,"#2E4F4F",WHITE)
        else:
                back=create_button_func(500,525,120,50,pygame.font.SysFont(None, 36),"Menu",screen,WHITE,"#2C3333")
        games=[]
        count_saved_games_x=0
        count_saved_games_y=0
        for game in saved_games:
            screen_shot=load_screenshot(game)
            current_game=create_button_func(saved_game_button_width+count_saved_games_x*400+50,saved_game_button_height+count_saved_games_y*250,100,30,pygame.font.SysFont("Arial", 23),game,screen1,WHITE,BLACK)
            screen1.blit(screen_shot,(saved_game_button_width+count_saved_games_x*400,20+count_saved_games_y*250))
            games.append(current_game)
            count_saved_games_x+=1
            if (count_saved_games_x==3):
                    count_saved_games_y+=1
                    count_saved_games_x=0
        # screen.blit(screen1, (0, 0))
        for event in pygame.event.get():
            if event.type == QUIT:
                pygame.quit()
                sys.exit()
            
            if event.type==MOUSEBUTTONDOWN:
                if back.collidepoint(pygame.mouse.get_pos()):
                    new_main_menu()
                for i in range(len(games)):
                    if games[i].collidepoint((pygame.mouse.get_pos()[0],pygame.mouse.get_pos()[1]-scrollbar.y_axis)):
                        e_slider.slider_value=saved_games['Game '+str(i+1)]['obstacles']
                        b_slider.slider_value=saved_games['Game '+str(i+1)]['bonus']
                        c_slider.slider_value=saved_games['Game '+str(i+1)]['civilians']
                        bt_slider.update()
                        ct_slider.update()
                        bt_slider.slider_value=saved_games['Game '+str(i+1)]['bous_target']
                        ct_slider.slider_value=saved_games['Game '+str(i+1)]['civilians_target']
                        checked=saved_games['Game '+str(i+1)]['check']
                        for s in all_sliders:
                            s.update_slider()
                        
                        start()
            if  SCREEN_HEIGHT_UPDATE!=disp_height-100:
                  scrollbar.event_handler(event)
            if event.type==MOUSEBUTTONDOWN:
                for i in range(len(games)):
                    if games[i].collidepoint((pygame.mouse.get_pos()[0],pygame.mouse.get_pos()[1]+scrollbar.y_axis)):
                        e_slider.slider_value=saved_games['Game '+str(i+1)]['obstacles']
                        b_slider.slider_value=saved_games['Game '+str(i+1)]['bonus']
                        c_slider.slider_value=saved_games['Game '+str(i+1)]['civilians']
                        bt_slider.update()
                        ct_slider.update()
                        bt_slider.slider_value=saved_games['Game '+str(i+1)]['bous_target']
                        ct_slider.slider_value=saved_games['Game '+str(i+1)]['civilians_target']
                        for s in all_sliders:
                            s.update_slider()
                        
                        start()
        # --- Game logic should go here
        if  SCREEN_HEIGHT_UPDATE!=disp_height-100:
            scrollbar.update()
        # First, clear the screen to white. Don't put other drawing commands
        # above this, or they will be erased with this command.
        screen.blit(screen1,(0,0),(0, -scrollbar.y_axis, disp_width-20, disp_height - 100))
        # --- Drawing code should go here
        scrollbar.draw(screen)
        # --- Go ahead and update the screen with what we've drawn.
        pygame.display.flip()
        # --- Limit to 30 frames per second
        clock.tick(30)   
    pygame.quit()


def new_main_menu():
    global checked

    pygame.display.set_caption("Main Page")
    background = pygame.Surface(DISPLAYSURF.get_size())
    background = background.convert()
    background.fill((0, 0, 0))
    DISPLAYSURF.blit(background, (0, 0))

    home_img = pygame.image.load(get_full_path("soldier_home.png"))
    home_img = pygame.transform.scale(home_img, (disp_width / 2, 0.8 * disp_height))
    icon_img = pygame.image.load(get_full_path("icon.png"))
    icon_img = pygame.transform.scale(icon_img, (130, 80))
    background1 = pygame.Surface((disp_width, 0.85 * disp_height))
    background1.fill("#333333")

    while True:
        DISPLAYSURF.blit(background, (0, 0))
        DISPLAYSURF.blit(background1, (0, 0.15 * disp_height))
        background1.blit(home_img, (25, 10))
        DISPLAYSURF.blit(icon_img, (10, upper_strip / 2 - icon_img.get_height() / 2))
        starts = ext_start_button()
        if starts.collidepoint(pygame.mouse.get_pos()):
            starts = ext_start_button_hover()
        settings = ext_settings_button()
        if settings.collidepoint(pygame.mouse.get_pos()):
            settings = ext_settings_button_hover()
        about = ext_about_button()
        if about.collidepoint(pygame.mouse.get_pos()):
            about = ext_about_button_hover()
        games = create_button_new(
            430, 460, 160, 32, pygame.font.SysFont("Arial", 23), "Saved Games", 450, 465
        )

        buttons = [starts, games, settings, about]
        main_menu_ui()
        draw_text_left_align(
            str(e_slider.slider_value),
            pygame.font.SysFont("BOLD", 30),
            "#ffffff",
            disp_width / 3
            + pygame.font.SysFont("BOLD", 30)
            .render("OBSTACLES : ", True, WHITE)
            .get_width(),
            disp_height / 2 + 35 / 2,
            DISPLAYSURF,
        )
        for event in pygame.event.get():
            if event.type == QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == MOUSEBUTTONDOWN:
                for btn in buttons:
                    if btn.collidepoint(pygame.mouse.get_pos()):
                        if btn == starts:
                            if checked:
                                intermediate()
                            else:
                                start()
                        elif btn == about:
                            # about_us()
                            pass
                            pygame.display.set_caption("Main Page")
                        elif btn == games:
                            go_saved_games(saved_games)
                            pygame.display.set_caption("Main Page")
                        elif btn == settings:
                            go_settings()
                            pygame.display.set_caption("Main Page")

        pygame.display.update()


for file_name in os.listdir(screen_shots_dir):
    # construct full file path
    file = os.path.join(screen_shots_dir,file_name)

    if os.path.isfile(file):
        print('Deleting file:',file)
        os.remove(file)

new_main_menu()