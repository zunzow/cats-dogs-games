import pyxel
import random

class Dog:
    def __init__(self, app_instance):
        self.app = app_instance
        self.x = random.uniform(0, pyxel.width)  # Start at random X position
        self.z = 0.0  # Start at the horizon
        self.direction_x = random.choice([-1, 1]) # -1 for left, 1 for right
        self.horizontal_speed = 0.5 # Base horizontal speed
        self.off_screen = False # Flag to mark if dog is off-screen horizontally

    def update(self):
        # Move forward (towards the foreground)
        self.z = min(self.z + 0.005, 1.0) # Adjust speed as needed

        # Determine current size based on Z position
        if self.z < 0.33:
            size = 8
        elif self.z < 0.66:
            size = 12
        else:
            size = 16

        # Horizontal movement
        self.x += self.horizontal_speed * self.direction_x

        # Check if dog is off-screen horizontally
        if self.x < -size or self.x > pyxel.width + size:
            self.off_screen = True

    def draw(self):
        # Determine which sprite to use based on Z position
        if self.z < 0.33:
            size = 8
            sprite_y_offset = 32
        elif self.z < 0.66:
            size = 12
            sprite_y_offset = 16
        else:
            size = 16
            sprite_y_offset = 0

        # Calculate screen Y position from Z
        screen_y = self.app.HORIZON_Y + (self.z * (pyxel.height - self.app.HORIZON_Y - size))

        # Animation frame
        anim_frame = (pyxel.frame_count // 8) % 2
        sprite_x = anim_frame * 16

        # Draw the dog
        w = size if self.direction_x == 1 else -size
        pyxel.blt(self.x - size / 2, screen_y, 0, sprite_x, sprite_y_offset, w, size, 0)


class App:
    def __init__(self):
        pyxel.init(120, 160, title="Dog Run 3D")
        pyxel.load("dogrun.pyxres")

        # Constants
        self.HORIZON_Y = 60

        # List to hold active dogs
        self.dogs = []
        self.max_dogs = 5 # Target number of dogs on screen
        self.dog_spawn_timer = 0 # Timer to control dog spawning

        # Create the dithered background at startup
        self.create_dithered_background()

        pyxel.run(self.update, self.draw)

    def create_dithered_background(self):
        # Use image bank 2 for the pre-rendered background
        bg_img = pyxel.image(2)
        bg_img.cls(0) # Clear it first

        # Sky: Dither between light blue (12) and white (7)
        sky_c1, sky_c2 = 12, 7
        for y in range(self.HORIZON_Y):
            for x in range(pyxel.width):
                color = sky_c1 if (x + y) % 2 == 0 else sky_c2
                bg_img.pset(x, y, color)

        # Ground: Dither between green (3) and a darker green/blue (11)
        ground_c1, ground_c2 = 3, 11
        for y in range(self.HORIZON_Y, pyxel.height):
            for x in range(pyxel.width):
                color = ground_c1 if (x + y) % 2 == 0 else ground_c2
                bg_img.pset(x, y, color)

    def update(self):
        # Update existing dogs and remove those that are off-screen
        dogs_to_keep = []
        for dog in self.dogs:
            dog.update()
            if dog.z < 1.0 and not dog.off_screen: # Keep if not yet at the foreground and not off-screen
                dogs_to_keep.append(dog)
        self.dogs = dogs_to_keep

        # Spawn new dogs if needed
        self.dog_spawn_timer -= 1
        if self.dog_spawn_timer <= 0 and len(self.dogs) < self.max_dogs:
            self.dogs.append(Dog(self))
            self.dog_spawn_timer = 60 # Spawn a new dog every 1 second (60 frames)

    def draw(self):
        # Draw the pre-rendered background
        pyxel.blt(0, 0, 2, 0, 0, pyxel.width, pyxel.height)

        # Draw all active dogs
        # Sort dogs by Z-position so closer dogs are drawn on top
        self.dogs.sort(key=lambda dog: dog.z)
        for dog in self.dogs:
            dog.draw()

App()