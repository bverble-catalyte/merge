import os
import sys
import time
import random

# --- Tuning & Speeds ---
PLAYER_SPEED = 2        # Rows moved per keypress
BULLET_SPEED = 3        # Columns light beams travel per frame
FRAME_DELAY = 0.04      # ~25 FPS

# --- Cross-Platform Non-Blocking Keyboard Input ---
try:
    import msvcrt
    def get_key():
        if msvcrt.kbhit():
            key = msvcrt.getch()
            if key in (b'\xe0', b'\x00'):
                key = msvcrt.getch()
                if key == b'H': return 'up'
                if key == b'P': return 'down'
                if key == b'M': return 'fire'
            elif key.lower() == b'w': return 'up'
            elif key.lower() == b's': return 'down'
            elif key in (b' ', b'd', b'D'): return 'fire'
            elif key.lower() == b'q': return 'quit'
            elif key == b'\r': return 'enter'
        return None
except ImportError:
    import select
    import termios
    import tty
    def get_key():
        dr, _, _ = select.select([sys.stdin], [], [], 0)
        if dr:
            key = sys.stdin.read(1)
            if key == '\x1b':
                seq = sys.stdin.read(2)
                if seq == '[A': return 'up'
                if seq == '[B': return 'down'
                if seq == '[C': return 'fire'
            elif key.lower() == 'w': return 'up'
            elif key.lower() == 's': return 'down'
            elif key in (' ', 'd', 'D'): return 'fire'
            elif key.lower() == 'q': return 'quit'
            elif key == '\n': return 'enter'
        return None

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def get_dimensions():
    try:
        cols, lines = os.get_terminal_size()
        return max(35, cols - 2), max(12, lines - 3)
    except OSError:
        return 65, 20

def wait_for_key():
    while get_key() is not None:
        pass
    while True:
        key = get_key()
        if key is not None:
            return key
        time.sleep(0.05)

def draw_cutscene(title, lines):
    clear_screen()
    width, height = get_dimensions()
    print("+" + "-" * width + "+")
    
    box_height = len(lines) + 4
    start_y = (height - box_height) // 2
    
    for y in range(height):
        if y == start_y:
            print("|" + f"=== {title} ===".center(width) + "|")
        elif start_y < y <= start_y + len(lines):
            line_idx = y - start_y - 1
            print("|" + lines[line_idx].center(width) + "|")
        elif y == start_y + len(lines) + 2:
            print("|" + " [ Press any key to continue... ] ".center(width) + "|")
        else:
            print("|" + " " * width + "|")
    print("+" + "-" * width + "+")
    wait_for_key()

def draw_menu(width, height):
    clear_screen()
    title = "=== KINGDOM HEARTS: GUMMI SHIP ODYSSEY ==="
    subtitle = "The Heartless are invading the corridors between worlds!"
    start_msg = "Press [SPACE] or [D] to Launch Gummi Ship"
    quit_msg = "Press [Q] to Quit"
    controls_msg = "Controls: [W/S] or [Up/Down] Fly | [SPACE/D] Fire Light Beam"
    
    print("+" + "-" * width + "+")
    for y in range(height):
        if y == height // 2 - 3:
            print("|" + title.center(width) + "|")
        elif y == height // 2 - 1:
            print("|" + subtitle.center(width) + "|")
        elif y == height // 2 + 1:
            print("|" + start_msg.center(width) + "|")
        elif y == height // 2 + 2:
            print("|" + quit_msg.center(width) + "|")
        elif y == height - 2:
            print("|" + controls_msg.center(width) + "|")
        else:
            print("|" + " " * width + "|")
    print("+" + "-" * width + "+")

def play_world(world_num, world_name, target_kills, enemy_char, enemy_speed, spawn_rate, is_boss=False):
    WIDTH, HEIGHT = get_dimensions()
    player_y = HEIGHT // 2
    player_x = 2
    player_hp = 5
    score = 0
    kills = 0

    bullets = []
    enemies = []
    spawn_timer = 0

    # Boss variables
    boss = None
    boss_hp = 25
    boss_dir = 1

    if is_boss:
        boss = [HEIGHT // 2, WIDTH - 6]

    clear_screen()

    while player_hp > 0:
        WIDTH, HEIGHT = get_dimensions()
        player_y = min(max(0, player_y), HEIGHT - 1)

        # 1. Input
        key = get_key()
        if key == 'up':
            player_y = max(0, player_y - PLAYER_SPEED)
        elif key == 'down':
            player_y = min(HEIGHT - 1, player_y + PLAYER_SPEED)
        elif key == 'fire':
            bullets.append([player_y, player_x + 2])
        elif key == 'quit':
            return 'quit', score

        # 2. Update Bullets
        for b in bullets[:]:
            b[1] += BULLET_SPEED
            if b[1] >= WIDTH:
                bullets.remove(b)

        # 3. Boss Logic
        if is_boss and boss:
            # Boss vertical movement
            boss[0] += boss_dir
            if boss[0] <= 0 or boss[0] >= HEIGHT - 1:
                boss_dir *= -1
            
            # Boss spawns minions
            spawn_timer += 1
            if spawn_timer >= spawn_rate:
                enemies.append([random.randint(0, HEIGHT - 1), WIDTH - 8, 0])
                spawn_timer = 0

            # Boss collision with bullets
            for b in bullets[:]:
                if abs(b[0] - boss[0]) <= 1 and b[1] >= boss[1] - 1:
                    if b in bullets:
                        bullets.remove(b)
                    boss_hp -= 1
                    score += 50
                    if boss_hp <= 0:
                        return 'win', score
        else:
            # Normal World Spawning
            spawn_timer += 1
            if spawn_timer >= spawn_rate:
                enemies.append([random.randint(0, HEIGHT - 1), WIDTH - 2, 0])
                spawn_timer = 0

        # 4. Update Enemies
        for e in enemies[:]:
            e[2] += 1
            if e[2] >= enemy_speed:
                e[1] -= 1
                e[2] = 0

            # Enemy reaches left border
            if e[1] <= 0:
                if e in enemies:
                    enemies.remove(e)
                player_hp -= 1
                continue

            # Collision with Player
            if abs(e[0] - player_y) <= 1 and e[1] <= player_x + 1:
                if e in enemies:
                    enemies.remove(e)
                player_hp -= 1
                continue

        # 5. Bullet-Enemy Collisions
        for e in enemies[:]:
            for b in bullets[:]:
                if e[0] == b[0] and abs(e[1] - b[1]) <= BULLET_SPEED:
                    if e in enemies:
                        enemies.remove(e)
                    if b in bullets:
                        bullets.remove(b)
                    score += 20
                    kills += 1
                    break

        if not is_boss and kills >= target_kills:
            return 'win', score

        # 6. Build Frame
        grid = [[' ' for _ in range(WIDTH)] for _ in range(HEIGHT)]

        # Bullets (*)
        for by, bx in bullets:
            if 0 <= by < HEIGHT and 0 <= bx < WIDTH:
                grid[by][bx] = '*'

        # Enemies
        for ey, ex, _ in enemies:
            if 0 <= ey < HEIGHT and 0 <= ex < WIDTH:
                grid[ey][ex] = enemy_char

        # Boss (#M#)
        if is_boss and boss:
            by, bx = boss
            boss_sprite = ["#", "M", "#"]
            for i, char in enumerate(boss_sprite):
                target_x = bx + i
                if 0 <= by < HEIGHT and 0 <= target_x < WIDTH:
                    grid[by][target_x] = char

        # Player (E0>)
        if 0 <= player_y < HEIGHT:
            grid[player_y][player_x] = '>'
            if player_x - 1 >= 0: grid[player_y][player_x - 1] = '0'
            if player_x - 2 >= 0: grid[player_y][player_x - 2] = 'E'

        # 7. Render Screen
        hp_display = "♥" * player_hp
        boss_status = f" | ANSEM HP: {boss_hp}" if is_boss else f" | HEARTLESS LEFT: {target_kills - kills}"
        hud = f" {world_name} | HP: {hp_display:<5} | SCORE: {score}{boss_status}"
        
        frame_lines = [
            hud[:WIDTH].ljust(WIDTH),
            "+" + "-" * WIDTH + "+"
        ]
        for row in grid:
            frame_lines.append("|" + "".join(row) + "|")
        frame_lines.append("+" + "-" * WIDTH + "+")

        sys.stdout.write("\033[H" + "\n".join(frame_lines) + "\n")
        sys.stdout.flush()

        time.sleep(FRAME_DELAY)

    return 'game_over', score

def main():
    old_settings = None
    if 'termios' in sys.modules:
        old_settings = termios.tcgetattr(sys.stdin)
        tty.setcbreak(sys.stdin.fileno())

    try:
        while True:
            width, height = get_dimensions()
            draw_menu(width, height)
            
            selection = None
            while selection not in ('fire', 'enter', 'quit'):
                selection = get_key()
                time.sleep(0.05)

            if selection == 'quit':
                break

            # --- WORLD 1: TRAVERSE TOWN ---
            draw_cutscene("WORLD 1: TRAVERSE TOWN", [
                "Sora: 'The Gummi Ship is ready! Donald, Goofy, let's go!'",
                "Donald: 'Wak! Watch out for those Shadow Heartless!'",
                "Goofy: 'Gawrsh, shoot 'em with your Keyblade beam, Sora!'"
            ])
            status, w1_score = play_world(1, "TRAVERSE TOWN", target_kills=10, enemy_char="<", enemy_speed=5, spawn_rate=15)
            if status in ('quit', 'game_over'):
                break

            # --- WORLD 2: HOLLOW BASTION ---
            draw_cutscene("WORLD 2: HOLLOW BASTION", [
                "Goofy: 'Look out! The castle is swarming with flying Heartless!'",
                "Donald: 'They're faster here! Don't let them hit the ship!'",
                "Sora: 'My friends are my power! Let's clear a path!'"
            ])
            status, w2_score = play_world(2, "HOLLOW BASTION", target_kills=15, enemy_char="W", enemy_speed=3, spawn_rate=12)
            if status in ('quit', 'game_over'):
                break

            # --- WORLD 3: END OF THE WORLD ---
            draw_cutscene("WORLD 3: END OF THE WORLD", [
                "Ansem: 'Behold the endless abyss! All worlds begin in darkness...'",
                "Sora: 'You're wrong! I know now, without a doubt...'",
                "Sora: 'KINGDOM HEARTS IS LIGHT!'",
                "Ansem: 'SUBMIT TO DARKNESS!'"
            ])
            status, w3_score = play_world(3, "END OF THE WORLD", target_kills=1, enemy_char="x", enemy_speed=4, spawn_rate=18, is_boss=True)
            
            # --- VICTORY / GAME OVER SCREEN ---
            clear_screen()
            width, height = get_dimensions()
            total_score = w1_score + w2_score + w3_score

            print("+" + "-" * width + "+")
            if status == 'win':
                print("|" + " CONGRATULATIONS! YOU SAVED KINGDOM HEARTS! ".center(width) + "|")
                print("|" + " 'King Mickey and Riku seal the Door to Darkness.' ".center(width) + "|")
            else:
                print("|" + " YOUR HEART WAS CONSUMED BY DARKNESS... ".center(width) + "|")
            print("|" + f" Final Score: {total_score} ".center(width) + "|")
            print("|" + " Press any key to return to Main Menu... ".center(width) + "|")
            print("+" + "-" * width + "+")
            
            time.sleep(1)
            wait_for_key()

    finally:
        if old_settings:
            termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)
        clear_screen()
        print("May your heart be your guiding key!")

if __name__ == "__main__":
    main()