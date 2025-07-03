import pyxel
import random

class Dog:
    def __init__(self, app_instance, start_at_horizon=True):
        self.app = app_instance
        self.x = random.uniform(0, pyxel.width)
        self.off_screen = False
        self.screen_y = 0
        self.size = 0

        self.state = 'running'
        self.state_timer = self.get_new_timer()
        self.collision_cooldown = 0

        if start_at_horizon:
            self.z = 0.0
            self.movement_mode = random.randint(0, 1)
        else:
            self.z = random.uniform(0.8, 1.0)
            self.movement_mode = random.randint(2, 3)

        self.direction_x, self.direction_z = 0, 0
        self.facing_direction = 1
        self.horizontal_speed = 0.5

    def get_new_timer(self): return random.randint(180, 360)
    def change_direction(self):
        self.movement_mode = (self.movement_mode + 1) % 4
        if self.state != 'running':
            self.start_running()
    def start_running(self): self.state = 'running'; self.state_timer = self.get_new_timer()

    def update(self):
        if self.collision_cooldown > 0: self.collision_cooldown -= 1
        if self.state != 'lying_down': self.state_timer -= 1
        if self.state_timer <= 0:
            if self.state == 'running': self.state = 'sitting'; self.facing_direction = random.choice([-1, 1]); self.state_timer = self.get_new_timer()
            elif self.state == 'sitting': self.state = 'lying_down'
        if self.state == 'running':
            if self.movement_mode == 0: self.direction_x, self.direction_z = -1, 1
            elif self.movement_mode == 1: self.direction_x, self.direction_z = 1, 1
            elif self.movement_mode == 2: self.direction_x, self.direction_z = 1, -1
            elif self.movement_mode == 3: self.direction_x, self.direction_z = -1, -1
            self.z += 0.005 * self.direction_z
            self.x += self.horizontal_speed * self.direction_x
            self.facing_direction = 1 if self.direction_x >= 0 else -1
        else: self.direction_x = 0
        if self.z < 0.33: self.size = 8
        elif self.z < 0.66: self.size = 12
        else: self.size = 16
        self.screen_y = self.app.HORIZON_Y + (self.z * (pyxel.height - self.app.HORIZON_Y - self.size))
        if self.x < -self.size or self.x > pyxel.width + self.size or self.z < 0 or self.z > 1: self.off_screen = True

    def draw(self):
        if self.state == 'running':
            if self.z < 0.33: y_base = 32
            elif self.z < 0.66: y_base = 16
            else: y_base = 0
            run_anim_frame = (pyxel.frame_count // 8) % 2
            sprite_x = (run_anim_frame * 16) if self.direction_z >= 0 else (32 + run_anim_frame * 16)
        else:
            if self.z < 0.33: y_base = 80
            elif self.z < 0.66: y_base = 64
            else: y_base = 48
            anim_frame = (pyxel.frame_count // 20) % 2
            sprite_x = anim_frame * 16 if self.state == 'sitting' else 32 + (anim_frame * 16)
        w = self.size * self.facing_direction
        pyxel.blt(self.x - self.size / 2, self.screen_y, 0, sprite_x, y_base, w, self.size, 0)

class Bone:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.is_active = True

    def draw(self):
        if not self.is_active:
            return

        # 骨の形 (横5ピクセル、縦3ピクセル、白ドット)
        # 四隅
        pyxel.pset(self.x, self.y, 7)
        pyxel.pset(self.x + 4, self.y, 7)
        pyxel.pset(self.x, self.y + 2, 7)
        pyxel.pset(self.x + 4, self.y + 2, 7)
        # 真ん中3つ
        pyxel.pset(self.x + 1, self.y + 1, 7)
        pyxel.pset(self.x + 2, self.y + 1, 7)
        pyxel.pset(self.x + 3, self.y + 1, 7)

class App:
    def __init__(self):
        pyxel.init(159, 254, title="Dog Run 3D")
        pyxel.load("dogrun.pyxres")
        pyxel.mouse(False)
        self.HORIZON_Y = 95
        self.dogs = []
        self.max_dogs = 10
        self.dog_spawn_timer = 0
        self.bones = []
        self.max_bones = 3
        self.create_dithered_background()
        pyxel.run(self.update, self.draw)

    def create_dithered_background(self):
        bg_img = pyxel.images[2]
        sky_base_color, sky_dither_color = 12, 7
        ground_base_color, ground_dither_color = 3, 11
        bg_img.rect(0, 0, pyxel.width, self.HORIZON_Y, sky_base_color)
        bg_img.rect(0, self.HORIZON_Y, pyxel.width, pyxel.height - self.HORIZON_Y, ground_base_color)
        num_grads, grad_height = 10, 3
        for i in range(num_grads):
            alpha = 1.0 - (i / num_grads)
            pyxel.dither(alpha)
            bg_img.rect(0, self.HORIZON_Y + i * grad_height, pyxel.width, grad_height, ground_dither_color)
            bg_img.rect(0, self.HORIZON_Y - (i + 1) * grad_height, pyxel.width, grad_height, sky_dither_color)
        pyxel.dither(1.0)

    def update(self):
        # --- Collision: Dog vs Dog ---
        for i in range(len(self.dogs)):
            for j in range(i + 1, len(self.dogs)):
                dog1, dog2 = self.dogs[i], self.dogs[j]
                if dog1.collision_cooldown > 0 or dog2.collision_cooldown > 0: continue
                if abs(dog1.z - dog2.z) < 0.05 and abs(dog1.x - dog2.x) < (dog1.size + dog2.size) / 2:
                    dog1.collision_cooldown = dog2.collision_cooldown = 30
                    if dog1.state == 'running' and dog2.state != 'running': dog2.start_running()
                    dog1.change_direction(); dog2.change_direction()

        # --- Mouse Click Logic ---
        if pyxel.btnp(pyxel.MOUSE_BUTTON_LEFT):
            mx, my = pyxel.mouse_x, pyxel.mouse_y
            bone_clicked = False
            # Check if an existing bone was clicked
            for bone in self.bones:
                # Simple bounding box check for bone click (5x3 pixels)
                if bone.is_active and \
                   mx >= bone.x and mx < bone.x + 5 and \
                   my >= bone.y and my < bone.y + 3:
                    bone.is_active = False
                    bone_clicked = True
                    break # Only remove one bone per click

            # Dog click logic (still applies)
            for dog in sorted(self.dogs, key=lambda d: d.z, reverse=True):
                if (dog.x - dog.size / 2 <= mx < dog.x + dog.size / 2 and dog.screen_y <= my < dog.screen_y + dog.size):
                    dog.change_direction(); break
            
            # Place a new bone if max_bones not reached, no bone was clicked, and click is on grass
            if not bone_clicked and len(self.bones) < self.max_bones and my >= self.HORIZON_Y and not any(dog.x - dog.size / 2 <= mx < dog.x + dog.size / 2 and dog.screen_y <= my < dog.screen_y + dog.size for dog in self.dogs):
                self.bones.append(Bone(mx - 2, my - 1)) # Adjust for bone center

        # --- Update states and remove off-screen dogs ---
        for dog in self.dogs: dog.update()
        self.dogs = [dog for dog in self.dogs if not dog.off_screen]

        # --- Dog-Bone Interaction ---
        for dog in self.dogs:
            if dog.state == 'running': # Only running dogs interact with bones
                for bone in self.bones:
                    if bone.is_active:
                        # Check for collision between dog and bone
                        if (dog.x - dog.size / 2 < bone.x + 5 and
                            dog.x + dog.size / 2 > bone.x and
                            dog.screen_y < bone.y + 3 and
                            dog.screen_y + dog.size > bone.y):
                            # Collision detected!
                            dog.state = 'sitting' # Dog sits
                            dog.state_timer = 180 # Sit for a while (e.g., 3 seconds)
                            bone.is_active = False # Bone disappears
                            break # Dog found a bone, no need to check other bones for this dog

        self.bones = [bone for bone in self.bones if bone.is_active] # Filter inactive bones again after dog interaction

        # --- Spawn new dogs ---
        if len(self.dogs) < self.max_dogs and pyxel.frame_count % 60 == 0:
            self.dogs.append(Dog(self, random.choice([True, False])))

    def draw(self):
        pyxel.blt(0, 0, 2, 0, 0, pyxel.width, pyxel.height)
        self.dogs.sort(key=lambda dog: dog.z)
        for dog in self.dogs:
            dog.draw()
        for bone in self.bones:
            bone.draw()

        # Check if all dogs are sitting or lying down
        all_dogs_stopped = all(dog.state != 'running' for dog in self.dogs)
        if all_dogs_stopped and len(self.dogs) == self.max_dogs: # Only show if all max_dogs are stopped
            message = "A quiet moment, a happy dog run"
            text_width = len(message) * pyxel.FONT_WIDTH # Approximate width
            text_x = (pyxel.width - text_width) // 2
            text_y = self.HORIZON_Y // 2 - pyxel.FONT_HEIGHT // 2 # Center in sky
            pyxel.text(text_x, text_y, message, 7) # Color 7 is white

App()
