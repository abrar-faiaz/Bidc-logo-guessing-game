import gradio as gr
import random
import os
from PIL import Image, ImageFilter

# Use the current directory instead of the 'images' directory
# Handle both uppercase and lowercase extensions
image_files = [f for f in os.listdir('.') if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
image_names = [os.path.splitext(f)[0] for f in image_files]

# Custom CSS for styling
custom_css = """
<style>
    .big-text {
        font-size: 2em;
        color: green;
        font-weight: bold;
        text-shadow: 0 0 10px lime;
    }
    .wrong-text, .correct-text {
        font-size: 2em;
        font-weight: bold;
    }
    .correct-text {
        color: green;
        text-shadow: 0 0 10px lime;
    }
    .wrong-text {
        color: red;
    }
    .big-hearts {
        font-size: 2em;
    }
    .big-status {
        font-size: 1.5em;
    }
    .message-container {
        margin-top: 20px;
    }
</style>
"""

def get_partial_blurred_image(image_path, level):
    """Returns a partially shown and blurred image with difficulty based on level."""
    img = Image.open(image_path).convert('RGB')  # Ensure the image is in RGB mode
    width, height = img.size

    # Increase fraction to show more of the image at the start
    fraction = max(0.3, 0.5 - 0.07 * (level - 1))
    blur_radius = max(0, min((level - 1) * 2, 10))  # Increase blur as level increases

    crop_height = int(height * fraction)
    crop_width = int(width * fraction)
    left = random.randint(0, max(0, width - crop_width))
    top = random.randint(0, max(0, height - crop_height))
    img_cropped = img.crop((left, top, left + crop_width, top + crop_height))

    # Resize and blur
    img_resized = img_cropped.resize((width, height), Image.LANCZOS)
    img_resized = img_resized.convert('RGB')  # Ensure compatibility with filters
    if blur_radius > 0:
        img_blurred = img_resized.filter(ImageFilter.GaussianBlur(radius=blur_radius))
    else:
        img_blurred = img_resized  # No blur at the start

    return img_blurred

def init_game():
    """Initializes the game state."""
    return {
        'level': 1,
        'lives': 4,
        'correct_guesses': 0,
        'images_used': [],
        'current_image': None,
        'current_options': [],
        'original_image': None,
        'high_score': 1,
    }

def get_new_image_and_options(state):
    """Selects a new image and generates options."""
    available_images = list(set(image_names) - set(state['images_used']))
    if not available_images:
        state['images_used'] = []
        available_images = image_names.copy()

    state['current_image'] = random.choice(available_images)
    state['images_used'].append(state['current_image'])

    # Get the correct image file extension (handling case sensitivity)
    image_file = None
    for ext in ['.png', '.PNG', '.jpg', '.JPG', '.jpeg', '.JPEG']:
        possible_file = state['current_image'] + ext
        if os.path.exists(possible_file):
            image_file = possible_file
            break
    if image_file is None:
        raise FileNotFoundError(f"Image file for {state['current_image']} not found.")

    # Open and convert the original image to RGB
    state['original_image'] = Image.open(image_file).convert('RGB')
    partial_image = get_partial_blurred_image(image_file, state['level'])

    # Adjust to show 6 options instead of 4
    options = [state['current_image']]
    distractors = list(set(image_names) - set([state['current_image']]))
    options += random.sample(distractors, min(5, len(distractors)))  # Select 5 distractors to make 6 total options
    random.shuffle(options)
    state['current_options'] = options

    return partial_image, options

def game_step(user_choice, state):
    """Processes the user's choice and updates the game state."""
    message = ""
    original_image = None  # Initialize the original image as None

    if user_choice is None:
        # First run initialization
        partial_image, options = get_new_image_and_options(state)
        lives_display = f"<span class='big-hearts'>Lives: {'❤️' * state['lives']}{'🖤' * (4 - state['lives'])}</span>"
        level_display = f"<span class='big-status'>Level: {state['level']}</span>"
        high_score_display = f"<span class='big-status'>High Score: {state['high_score']}</span>"
    else:
        if user_choice == state['current_image']:
            state['correct_guesses'] += 1
            message = "<span class='correct-text'>🎉 Correct! Well done!</span>"
        else:
            state['lives'] -= 1
            message = f"<span class='wrong-text'>❌ Wrong! It was {state['current_image']}.</span>"
        
        if state['lives'] <= 0:
            message += " 💀 Game Over! Restarting..."
            if state['level'] > state.get('high_score', 1):
                state['high_score'] = state['level']
            state = init_game()
        elif state['correct_guesses'] >= 3:
            state['level'] += 1
            state['correct_guesses'] = 0
            message += f" 🆙 Level Up! Welcome to Level {state['level']}!"
            if state['level'] > state.get('high_score', 1):
                state['high_score'] = state['level']
        
        original_image = state['original_image']

        partial_image, options = get_new_image_and_options(state)
        lives_display = f"<span class='big-hearts'>Lives: {'❤️' * state['lives']}{'🖤' * (4 - state['lives'])}</span>"
        level_display = f"<span class='big-status'>Level: {state['level']}</span>"
        high_score_display = f"<span class='big-status'>High Score: {state['high_score']}</span>"

    return (
        partial_image,
        gr.update(choices=state['current_options'], value=None),
        gr.update(value=message),
        gr.update(value=lives_display),
        gr.update(value=level_display),
        gr.update(value=high_score_display),
        original_image,
        state,
    )

# The opening "Start Game" screen
def start_game(state):
    """Preload the first image and options before game UI shows."""
    partial_image, options = get_new_image_and_options(state)
    lives_display = f"<span class='big-hearts'>Lives: {'❤️' * state['lives']}{'🖤' * (4 - state['lives'])}</span>"
    level_display = f"<span class='big-status'>Level: {state['level']}</span>"
    high_score_display = f"<span class='big-status'>High Score: {state['high_score']}</span>"
    message = ""  # Initial message
    return (
        gr.update(visible=False),  # Hide start screen
        gr.update(visible=True),   # Show game UI
        partial_image,             # Set the first image
        gr.update(choices=options, value=None),  # Update options
        gr.update(value=lives_display),
        gr.update(value=level_display),
        gr.update(value=high_score_display),
        gr.update(value=message),
        state                      # Return updated state
    )

with gr.Blocks(css=custom_css) as demo:

    state = gr.State(init_game())

    # Start screen before the game
    with gr.Row(visible=True) as start_screen:
        gr.Markdown("""
        # 🎮 **Welcome to the Logo Detector Game!**
        *Press the button below to start.*
        """)
        start_button = gr.Button("Start Game", variant="primary")

    # Actual game UI
    with gr.Row(visible=False) as game_ui:
        with gr.Column(scale=4):
            image_output = gr.Image(label="Guess the Logo", interactive=False)
            original_image_output = gr.Image(label="Original Logo", visible=False, interactive=False)
        with gr.Column(scale=1):
            lives_output = gr.HTML(value="Lives: ❤️❤️❤️❤️", label="Lives")
            level_output = gr.HTML(value="Level: 1", label="Level")
            high_score_output = gr.HTML(value="High Score: 1", label="High Score")
    
        options_output = gr.Radio(choices=[], label="Select the correct logo")
        submit_button = gr.Button("Submit", variant="primary")
        message_output = gr.HTML(label="Message", elem_classes="message-container")

        def on_submit(user_choice, state):
            return game_step(user_choice, state)

        submit_button.click(
            on_submit,
            inputs=[options_output, state],
            outputs=[
                image_output,          # Update partial image for the next round
                options_output,        # Update options for the next round
                message_output,        # Display message (now moved below Submit button)
                lives_output,          # Update lives display
                level_output,          # Update level display
                high_score_output,     # Update high score display
                original_image_output, # Show original image after submission
                state,                 # Update state
            ],
        )

    # Start button to transition from the start screen to the game
    start_button.click(
        start_game,
        inputs=[state],
        outputs=[
            start_screen,
            game_ui,
            image_output,
            options_output,
            lives_output,
            level_output,
            high_score_output,
            message_output,
            state
        ]
    )

demo.launch()
