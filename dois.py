import pygame
import sys
import math
import time

# Initialize Pygame
pygame.init()

# Set up the display
width, height = 800, 600
screen = pygame.display.set_mode((width, height))
pygame.display.set_caption('3D Sphere Physics with Enhanced Lighting')

# Constants
G = 6.67430e+1  # Adjusted gravitational constant for simulation scale
background_color = (0, 0, 0)
text_color = (255, 255, 255)
menu_background = (50, 50, 50)
restitution = 0.9  # Damping factor for collisions

# Camera settings
camera_angle_x = 0
camera_angle_y = 0
camera_rotation_speed = 0.0005

# Light direction (normalized)
light_direction = (0.5, 0.5, -1)  # Example direction

# Store spheres
spheres = []

# Font for rendering text
font = pygame.font.Font(None, 36)

# Input mode flag and data
input_mode = False
input_text = ''
property_names = ['radius', 'mass', 'velocity magnitude', 'velocity angle', 'emits light (1 or 0)']
property_index = 0
properties = {'radius': 0, 'mass': 1, 'velocity magnitude': 0, 'velocity angle': 0, 'emits light': 0}

# Time control variables
last_time = time.time()

def handle_collision(sphere1, sphere2):
    # Calculate the normal vector of the collision
    dx, dy, dz = [s2 - s1 for s1, s2 in zip(sphere1['position'], sphere2['position'])]
    dist = math.sqrt(dx**2 + dy**2 + dz**2)
    
    # Normalizing the normal vector
    nx, ny, nz = dx / dist, dy / dist, dz / dist
    
    # Calculate relative velocity
    vx, vy, vz = [v2 - v1 for v1, v2 in zip(sphere1['velocity'], sphere2['velocity'])]
    
    # Calculate velocity along the normal (dot product)
    vel_along_normal = vx * nx + vy * ny + vz * nz
    
    # Do not resolve if velocities are separating
    if vel_along_normal > 0:
        return
    
    # Calculate impulse scalar
    j = -(1 + restitution) * vel_along_normal
    j /= (1 / sphere1['mass'] + 1 / sphere2['mass'])
    
    # Apply impulse
    impulse = (j * nx, j * ny, j * nz)
    sphere1['velocity'] = tuple(v1 - i / sphere1['mass'] * restitution for v1, i in zip(sphere1['velocity'], impulse))
    sphere2['velocity'] = tuple(v2 + i / sphere2['mass'] * restitution for v2, i in zip(sphere2['velocity'], impulse))

def draw_lit_sphere(screen, x, y, radius, base_color, light_positions):
    if not light_positions:
        # If no light sources, draw a default dark sphere
        pygame.draw.circle(screen, base_color, (x, y), radius)
        return

    num_layers = 10  # Number of layers to create the gradient effect
    for i in range(num_layers, 0, -1):
        layer_radius = radius - (i * (radius / num_layers))
        alpha = int(255 * (1 - (i / num_layers)))

        temp_surface = pygame.Surface((layer_radius * 2, layer_radius * 2), pygame.SRCALPHA)
        pygame.draw.circle(temp_surface, base_color + (alpha,), (layer_radius, layer_radius), layer_radius)

        # Calculate light effects based on light positions
        if light_positions:
            light_effect_x = sum(light_x - x for light_x, light_y, _ in light_positions) / len(light_positions)
            light_effect_y = sum(light_y - y for light_x, light_y, _ in light_positions) / len(light_positions)
            light_distance = math.sqrt(light_effect_x**2 + light_effect_y**2)

            if light_distance > 0:
                light_effect_x, light_effect_y = light_effect_x / light_distance, light_effect_y / light_distance
                offset_x = light_effect_x * (radius / num_layers) * i
                offset_y = light_effect_y * (radius / num_layers) * i
            else:
                offset_x, offset_y = 0, 0  # No offset if the light distance is zero
        else:
            offset_x, offset_y = 0, 0  # Default to no offset if no lights

        screen.blit(temp_surface, (x + offset_x - layer_radius, y + offset_y - layer_radius))



# Main loop
running = True
while running:
    current_time = time.time()
    delta_time = current_time - last_time
    last_time = current_time

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.MOUSEBUTTONDOWN and not input_mode:
            input_mode = True
            input_text = ''
            property_index = 0
            mouse_x, mouse_y = pygame.mouse.get_pos()
            click_x, click_y = mouse_x - width // 2, mouse_y - height // 2
        elif event.type == pygame.KEYDOWN and input_mode:
            if event.key == pygame.K_RETURN:
                properties[property_names[property_index]] = float(input_text)
                property_index += 1
                input_text = ''
                if property_index >= len(property_names):
                    velocity_magnitude = properties['velocity magnitude']
                    velocity_angle = math.radians(properties['velocity angle'])
                    velocity = (velocity_magnitude * math.cos(velocity_angle), velocity_magnitude * math.sin(velocity_angle), 0)
                    z = (height // 2 - mouse_y) / 3
                    position = (click_x + width // 2, click_y + height // 2, z)
                    emits_light = properties['emits light (1 or 0)'] > 0
                    color = (255, 255, 255) if emits_light else (100, 100, 100)
                    new_sphere = {'position': position, 'radius': properties['radius'], 'mass': properties['mass'], 
                                  'velocity': velocity, 'acceleration': (0, 0, 0), 'emits light': emits_light, 'color': color}
                    spheres.append(new_sphere)
                    input_mode = False
                    property_index = 0  # Reset for the next input
            elif event.key == pygame.K_BACKSPACE:
                input_text = input_text[:-1]
            else:
                input_text += event.unicode

    # Calculate gravitational forces and handle collisions
    for i, sphere1 in enumerate(spheres):
        sphere1['acceleration'] = (0, 0, 0)  # Reset acceleration
        for j, sphere2 in enumerate(spheres):
            if i != j:
                dx, dy, dz = [s2 - s1 for s1, s2 in zip(sphere1['position'], sphere2['position'])]
                distance = math.sqrt(dx**2 + dy**2 + dz**2)
                if distance < sphere1['radius'] + sphere2['radius']:
                    handle_collision(sphere1, sphere2)
                elif distance > 0:
                    force_magnitude = G * sphere1['mass'] * sphere2['mass'] / (distance**2)
                    force_direction = (dx / distance, dy / distance, dz / distance)
                    acceleration = tuple(f * force_magnitude / sphere1['mass'] for f in force_direction)
                    sphere1['acceleration'] = tuple(a1 + a2 for a1, a2 in zip(sphere1['acceleration'], acceleration))

    # Update velocity and position based on acceleration
    for sphere in spheres:
        sphere['velocity'] = tuple(v + a * delta_time for v, a in zip(sphere['velocity'], sphere['acceleration']))
        sphere['position'] = tuple(p + v * delta_time for p, v in zip(sphere['position'], sphere['velocity']))

    # Check for key presses to rotate the camera
    keys = pygame.key.get_pressed()
    if keys[pygame.K_LEFT]:
        camera_angle_y += camera_rotation_speed
    if keys[pygame.K_RIGHT]:
        camera_angle_y -= camera_rotation_speed
    if keys[pygame.K_UP]:
        camera_angle_x += camera_rotation_speed
    if keys[pygame.K_DOWN]:
        camera_angle_x -= camera_rotation_speed

    # Clear screen
    screen.fill(background_color)

    # Draw all spheres adjusted for camera rotation
    # Update positions and handle rotations
    for sphere in spheres:
        # Calculate transformed coordinates for sorting
        x, y, z = sphere['position']
        x -= width // 2
        y -= height // 2

        # Apply rotation around Y-axis
        temp_x = x * math.cos(camera_angle_y) - z * math.sin(camera_angle_y)
        temp_z = x * math.sin(camera_angle_y) + z * math.cos(camera_angle_y)
        x, z = temp_x, temp_z

        # Apply rotation around X-axis
        temp_y = y * math.cos(camera_angle_x) - z * math.sin(camera_angle_x)
        temp_z = y * math.sin(camera_angle_x) + z * math.cos(camera_angle_x)
        y, z = temp_y, temp_z

        # Store transformed coordinates back in the sphere dictionary
        sphere['transformed_position'] = (x, y, z)

    # Sort spheres by z-coordinate in descending order
    spheres.sort(key=lambda s: s['transformed_position'][2], reverse=True)

    # Draw spheres based on sorted order
    for sphere in spheres:
        x, y, z = sphere['transformed_position']
        projected_x = int(width / 2 + x)
        projected_y = int(height / 2 + y)

        light_positions = [(ls['transformed_position'][0] + width / 2, ls['transformed_position'][1] + height / 2, ls['transformed_position'][2]) 
                        for ls in spheres if ls['emits light'] and ls is not sphere]

        # If the sphere emits light, draw it fully white
        if sphere['emits light']:
            pygame.draw.circle(screen, (255, 255, 255), (projected_x, projected_y), sphere['radius'])
        else:
            # For non-light emitting spheres, calculate lighting based on other light sources
            draw_lit_sphere(screen, projected_x, projected_y, sphere['radius'], (100, 100, 100), light_positions)


    # Display input menu if in input mode
    if input_mode:
        pygame.draw.rect(screen, menu_background, (width // 2 - 100, height // 2 - 60, 200, 50))
        text_surface = font.render(f'{property_names[property_index].capitalize()}: {input_text}', True, text_color)
        screen.blit(text_surface, (width // 2 - 90, height // 2 - 50))

    # Update the display
    pygame.display.flip()

# Quit Pygame
pygame.quit()
sys.exit()
