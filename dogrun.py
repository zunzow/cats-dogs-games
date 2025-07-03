import pyxel
import random

class Dog:
    def __init__(self, app_instance, start_at_horizon=True):
        self.app = app_instance
        self.x = random.uniform(0, pyxel.width)
        self.off_screen = False
        self.screen_y = 0
        self.size = 0

        if start_at_horizon:
            self.z = 0.0  # Start at the horizon
            # 0: bottom-left, 1: bottom-right (coming towards viewer)
            self.movement_mode = random.randint(0, 1)
        else:
            self.z = random.uniform(0.8, 1.0) # Start at the foreground
            # 2: top-right, 3: top-left (going away from viewer)
            self.movement_mode = random.randint(2, 3)

        self.direction_x = 0
        self.direction_z = 0
        self.horizontal_speed = 0.5

    def change_direction(self):
        """Cycles through the four diagonal movement directions."""
        self.movement_mode = (self.movement_mode + 1) % 4

    def update(self):
        # Set direction vectors based on the current mode
        if self.movement_mode == 0: # bottom-left
            self.direction_x, self.direction_z = -1, 1
        elif self.movement_mode == 1: # bottom-right
            self.direction_x, self.direction_z = 1, 1
        elif self.movement_mode == 2: # top-right
            self.direction_x, self.direction_z = 1, -1
        elif self.movement_mode == 3: # top-left
            self.direction_x, self.direction_z = -1, -1

        # Update position
        self.z += 0.005 * self.direction_z
        self.x += self.horizontal_speed * self.direction_x

        # Determine current size based on Z position
        if self.z < 0.33:
            self.size = 8
        elif self.z < 0.66:
            self.size = 12
        else:
            self.size = 16

        # Calculate screen Y for drawing and click detection
        self.screen_y = self.app.HORIZON_Y + (self.z * (pyxel.height - self.app.HORIZON_Y - self.size))

        # Check if dog is off-screen
        if self.x < -self.size or self.x > pyxel.width + self.size or self.z < 0 or self.z > 1:
            self.off_screen = True

    def draw(self):
        # Determine sprite_y_offset based on Z position
        if self.z < 0.33:
            sprite_y_offset = 32
        elif self.z < 0.66:
            sprite_y_offset = 16
        else:
            sprite_y_offset = 0

        anim_frame = (pyxel.frame_count // 8) % 2

        if self.direction_z == 1:  # Coming (moving towards bottom)
            sprite_x = anim_frame * 16
        else:  # Going (moving towards top)
            sprite_x = 32 + (anim_frame * 16)

        w = self.size if self.direction_x == 1 else -self.size
        pyxel.blt(self.x - self.size / 2, self.screen_y, 0, sprite_x, sprite_y_offset, w, self.size, 0)

class App:
    def __init__(self):
        pyxel.init(120, 160, title="Dog Run 3D")
        pyxel.load("dogrun.pyxres")
        pyxel.mouse(False) # Hide mouse cursor

        self.HORIZON_Y = 60
        self.dogs = []
        self.max_dogs = 20
        self.dog_spawn_timer = 0

        self.create_dithered_background()
        pyxel.run(self.update, self.draw)

    def create_dithered_background(self):
        bg_img = pyxel.images[2]

        sky_base_color = 12
        sky_dither_color = 7
        ground_base_color = 3
        ground_dither_color = 11

        # 1. Fill sky and ground with solid base colors
        bg_img.rect(0, 0, pyxel.width, self.HORIZON_Y, sky_base_color)
        bg_img.rect(0, self.HORIZON_Y, pyxel.width, pyxel.height - self.HORIZON_Y, ground_base_color)

        # 2. Draw gradients: dense near horizon, sparse further away
        num_grads = 4
        grad_height = 6

        # Draw ground and sky gradients in the same loop
        for i in range(num_grads):
            # As i (distance from horizon) increases, alpha decreases.
            # This makes the pattern dense near the horizon and sparse further away.
            alpha = 1.0 - (i / num_grads)
            pyxel.dither(alpha)

            # Ground: Draw a band downwards from the horizon
            y_ground = self.HORIZON_Y + i * grad_height
            bg_img.rect(0, y_ground, pyxel.width, grad_height, ground_dither_color)

            # Sky: Draw a band upwards from the horizon
            y_sky = self.HORIZON_Y - (i + 1) * grad_height
            bg_img.rect(0, y_sky, pyxel.width, grad_height, sky_dither_color)

        # 3. Reset dither to solid to not affect other drawings
        pyxel.dither(1.0)

    def update(self):
        # --- Collision Detection ---
        collided_dogs = set()
        for i in range(len(self.dogs)):
            for j in range(i + 1, len(self.dogs)):
                dog1 = self.dogs[i]
                dog2 = self.dogs[j]

                if abs(dog1.z - dog2.z) < 0.05:
                    if abs(dog1.x - dog2.x) < (dog1.size + dog2.size) / 2:
                        if dog1 not in collided_dogs:
                            dog1.change_direction()
                            collided_dogs.add(dog1)
                        if dog2 not in collided_dogs:
                            dog2.change_direction()
                            collided_dogs.add(dog2)

        # --- Mouse Click Detection (still active even if cursor is hidden) ---
        if pyxel.btnp(pyxel.MOUSE_BUTTON_LEFT):
            for dog in sorted(self.dogs, key=lambda d: d.z, reverse=True):
                if (dog.x - dog.size / 2 <= pyxel.mouse_x < dog.x + dog.size / 2 and
                        dog.screen_y <= pyxel.mouse_y < dog.screen_y + dog.size):
                    dog.change_direction()
                    break

        # --- Update and remove dogs ---
        dogs_to_keep = []
        for dog in self.dogs:
            dog.update()
            if not dog.off_screen:
                dogs_to_keep.append(dog)
        self.dogs = dogs_to_keep

        # --- Spawn new dogs ---
        self.dog_spawn_timer -= 1
        if self.dog_spawn_timer <= 0 and len(self.dogs) < self.max_dogs:
            self.dogs.append(Dog(self, random.choice([True, False])))
            self.dog_spawn_timer = 60

    def draw(self):
        pyxel.blt(0, 0, 2, 0, 0, pyxel.width, pyxel.height)
        self.dogs.sort(key=lambda dog: dog.z)
        for dog in self.dogs:
            dog.draw()

App()
