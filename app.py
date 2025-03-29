from flask import Flask, render_template, request, jsonify, send_from_directory
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import os
import cv2
from sklearn.cluster import KMeans

app = Flask(__name__)

# Ensure output directory exists
os.makedirs('static/output', exist_ok=True)
os.makedirs('static/uploads', exist_ok=True)

# Global variables to store current pattern and colors
current_pattern = None
current_colors = []
current_indices = None

def process_image(image_path, grid_size, num_colors):
    """Process input image to create knitting pattern."""
    # Load and process image
    image = cv2.imread(image_path)
    if image is None:
        raise ValueError(f"Could not load image: {image_path}")
    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    
    # Convert grid_size to integers and ensure positive values
    width, height = map(int, grid_size)
    if width <= 0 or height <= 0:
        raise ValueError("Width and height must be positive numbers")
    
    # Resize the image
    grid_size = (width, height)  # Already integers from map(int, grid_size)
    resized_image = cv2.resize(image, grid_size, interpolation=cv2.INTER_AREA)
    
    # Color clustering
    pixels = resized_image.reshape((-1, 3))
    kmeans = KMeans(n_clusters=int(num_colors), random_state=42, n_init=10)
    kmeans.fit(pixels)
    clustered_pixels = kmeans.cluster_centers_[kmeans.labels_]
    
    # Create pattern grid with color indices
    pattern_indices = kmeans.labels_.reshape(height, width).astype(np.int32)
    pattern = clustered_pixels.reshape(resized_image.shape).astype(np.uint8)
    
    # Generate color mapping
    colors = []
    for i, center in enumerate(kmeans.cluster_centers_):
        colors.append({
            'number': i + 1,
            'rgb': [int(x) for x in center]
        })
    
    return pattern, pattern_indices, colors

def save_pattern_image(pattern, pattern_indices, colors, output_path='static/output/pattern.png', scale=20, show_numbers=True):
    """Convert pattern array to image and save it."""
    # Ensure dimensions are integers
    height, width = int(pattern_indices.shape[0]), int(pattern_indices.shape[1])
    # Create a larger image to accommodate ticks
    margin = int(80)  # Increased margin
    bottom_margin = int(50)  # Reduced bottom margin since we don't need space for rotated numbers
    img_width = int(width * scale + margin * 2)
    img_height = int(height * scale + margin + bottom_margin)
    image = Image.new('RGB', (img_width, img_height), 'white')
    draw = ImageDraw.Draw(image)
    
    # Draw the pattern and color numbers
    font_small = ImageFont.truetype("arial.ttf", int(scale * 0.4))  # Adjusted font size
    for y in range(height):
        for x in range(width):
            color_idx = int(pattern_indices[y, x])  # Ensure color index is integer
            rgb = tuple(map(int, colors[color_idx]['rgb']))  # Ensure RGB values are integers
            # Draw a filled rectangle for each pixel
            rect = [
                (int(x * scale + margin), int(y * scale + margin)),
                (int((x + 1) * scale + margin - 1), int((y + 1) * scale + margin - 1))
            ]
            draw.rectangle(rect, fill=rgb, outline='black')  # Added black outline
            
            # Add color number if enabled
            if show_numbers:
                number = str(colors[color_idx]['number'])
                # Get text size for centering
                text_bbox = draw.textbbox((0, 0), number, font=font_small)
                text_width = int(text_bbox[2] - text_bbox[0])
                text_height = int(text_bbox[3] - text_bbox[1])
                
                # Calculate center position for text
                text_x = int(x * scale + margin + (scale - text_width) // 2)
                text_y = int(y * scale + margin + (scale - text_height) // 2)
                
                # Draw number with white background for better visibility
                padding = 2
                bg_rect = [
                    int(text_x - padding), int(text_y - padding),
                    int(text_x + text_width + padding), int(text_y + text_height + padding)
                ]
                draw.rectangle(bg_rect, fill='white')
                
                # Then draw the number in black
                draw.text((text_x, text_y), number, fill='black', font=font_small)
    
    # Draw tick marks and numbers
    font = ImageFont.truetype("arial.ttf", 10)  # Reduced font size from 14 to 10
    
    # Vertical ticks (for rows) - on the right side, counting from bottom to top
    for i in range(height):
        y_pos = int((height - i - 1) * scale + margin)  # Reverse the y-position
        number = str(i + 1)  # Start from 1
        
        # Draw tick mark in the middle of the bin
        tick_y = int(y_pos + scale // 2)
        draw.line([
            (int(width * scale + margin), tick_y),
            (int(width * scale + margin + 5), tick_y)
        ], fill='black')
        
        # Draw number
        text_bbox = draw.textbbox((0, 0), number, font=font)
        text_width = int(text_bbox[2] - text_bbox[0])
        draw.text(
            (int(width * scale + margin + 10), int(tick_y - 5)),  # Adjusted y offset for smaller font
            number,
            fill='black',
            font=font
        )
    
    # Horizontal ticks (for columns) - at the bottom, counting from right to left
    for i in range(width):
        x_pos = int((width - i - 1) * scale + margin)  # Reverse the x-position
        number = str(i + 1)  # Start from 1
        
        # Draw tick mark in the middle of the bin
        tick_x = int(x_pos + scale // 2)
        draw.line([
            (tick_x, int(height * scale + margin)),
            (tick_x, int(height * scale + margin + 5))
        ], fill='black')
        
        # Draw number horizontally
        text_bbox = draw.textbbox((0, 0), number, font=font)
        text_width = int(text_bbox[2] - text_bbox[0])
        text_height = int(text_bbox[3] - text_bbox[1])
        
        # Center the number under the tick mark
        text_x = int(tick_x - text_width // 2)
        text_y = int(height * scale + margin + 8)  # Adjusted spacing for smaller font
        
        draw.text((text_x, text_y), number, fill='black', font=font)
    
    # Draw border
    draw.rectangle([
        (margin, margin),
        (int(width * scale + margin - 1), int(height * scale + margin - 1))
    ], outline='black', width=2)  # Made border thicker
    
    image.save(output_path)
    return output_path

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/generate', methods=['POST'])
def generate():
    global current_pattern, current_colors, current_indices
    
    if 'image' not in request.files:
        return jsonify({'error': 'No image uploaded'}), 400
    
    file = request.files['image']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    # Save uploaded image
    image_path = os.path.join('static/uploads', file.filename)
    file.save(image_path)
    
    # Get parameters and convert to integers
    try:
        width = int(float(request.form.get('width', 110)))
        height = int(float(request.form.get('height', 110)))
        grid_size = (width, height)  # OpenCV resize expects (width, height)
        num_colors = int(request.form.get('num_colors', 7))
        
        if width <= 0 or height <= 0:
            return jsonify({'error': 'Width and height must be positive numbers'}), 400
            
        # Process image and generate pattern
        current_pattern, current_indices, current_colors = process_image(image_path, grid_size, num_colors)
        
        # Save the pattern as an image
        output_path = save_pattern_image(current_pattern, current_indices, current_colors)
        
        return jsonify({
            'colors': current_colors,
            'pattern_path': output_path
        })
    except ValueError as e:
        return jsonify({'error': 'Invalid dimensions or number of colors. Please enter valid numbers.'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/update_color', methods=['POST'])
def update_color():
    global current_pattern, current_colors, current_indices
    
    data = request.get_json()
    old_color = data.get('old_color')
    new_color = data.get('new_color')
    
    # Find and update the color
    for color in current_colors:
        if color['rgb'] == old_color:
            color['rgb'] = new_color
            break
    
    # Update the pattern array with new colors
    height, width = current_indices.shape
    for y in range(height):
        for x in range(width):
            color_idx = current_indices[y, x]
            current_pattern[y, x] = current_colors[color_idx]['rgb']
    
    # Update the pattern image
    save_pattern_image(current_pattern, current_indices, current_colors)
    
    return jsonify({
        'colors': current_colors
    })

@app.route('/clear', methods=['POST'])
def clear():
    global current_pattern, current_colors, current_indices
    current_pattern = None
    current_colors = []
    current_indices = None
    
    # Create an empty pattern image
    image = Image.new('RGB', (100, 100), 'white')
    image.save('static/output/pattern.png')
    
    return jsonify({
        'success': True
    })

# Clean up function to remove old files
def cleanup_old_files():
    """Remove old pattern and upload files."""
    for directory in ['static/output', 'static/uploads']:
        for filename in os.listdir(directory):
            file_path = os.path.join(directory, filename)
            try:
                if os.path.isfile(file_path):
                    os.unlink(file_path)
            except Exception as e:
                print(f'Error deleting {file_path}: {e}')

@app.route('/toggle_numbers', methods=['POST'])
def toggle_numbers():
    """Toggle the visibility of color numbers"""
    try:
        data = request.get_json()
        show_numbers = data.get('show_numbers', True)
        if save_pattern_to_file(show_numbers):
            return jsonify({'success': True})
        return jsonify({'success': False, 'error': 'No pattern to update'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

# Call cleanup when starting the app
cleanup_old_files()

def save_pattern_to_file(show_numbers=True):
    """Save the current pattern as an image"""
    global current_pattern, current_colors, current_indices
    if current_pattern is None:
        return False
    
    # Create a new image with white background
    scale = int(30)  # Increased from 20 to 30 pixels per bin
    margin = int(100)  # Increased margin to accommodate larger pattern
    bottom_margin = int(50)  # Reduced bottom margin since numbers are horizontal
    pattern_width = int(current_pattern.shape[1] * scale)
    pattern_height = int(current_pattern.shape[0] * scale)
    img_width = int(pattern_width + 2 * margin)
    img_height = int(pattern_height + margin + bottom_margin)
    
    img = Image.new('RGB', (img_width, img_height), 'white')
    draw = ImageDraw.Draw(img)
    
    # Draw the pattern
    for y in range(current_pattern.shape[0]):
        for x in range(current_pattern.shape[1]):
            color_idx = int(current_indices[y, x])
            if color_idx < len(current_colors):
                color = tuple(map(int, current_colors[color_idx]['rgb']))
                # Draw rectangle with black outline
                x1 = int(margin + x * scale)
                y1 = int(margin + y * scale)
                x2 = int(margin + (x + 1) * scale - 1)
                y2 = int(margin + (y + 1) * scale - 1)
                draw.rectangle([x1, y1, x2, y2], fill=color, outline='black')
                
                # Draw color number if enabled
                if show_numbers:
                    number = str(color_idx + 1)
                    # Create a white background for the number
                    font = ImageFont.truetype("arial.ttf", int(scale * 0.5))  # Increased font size
                    text_bbox = draw.textbbox((0, 0), number, font=font)
                    text_width = int(text_bbox[2] - text_bbox[0])
                    text_height = int(text_bbox[3] - text_bbox[1])
                    
                    # Calculate text position
                    text_x = int(margin + x * scale + (scale - text_width) // 2)
                    text_y = int(margin + y * scale + (scale - text_height) // 2)
                    
                    # Draw white background
                    padding = int(3)  # Increased padding
                    bg_x1 = int(text_x - padding)
                    bg_y1 = int(text_y - padding)
                    bg_x2 = int(text_x + text_width + padding)
                    bg_y2 = int(text_y + text_height + padding)
                    draw.rectangle([bg_x1, bg_y1, bg_x2, bg_y2], fill='white')
                    
                    # Draw the number
                    draw.text((text_x, text_y), number, fill='black', font=font)
    
    # Draw grid lines
    for x in range(current_pattern.shape[1] + 1):
        x_pos = int(margin + x * scale)
        draw.line([x_pos, margin, x_pos, int(margin + pattern_height)], fill='black', width=2)  # Increased line width
    for y in range(current_pattern.shape[0] + 1):
        y_pos = int(margin + y * scale)
        draw.line([margin, y_pos, int(margin + pattern_width), y_pos], fill='black', width=2)  # Increased line width
    
    # Draw border
    border_width = int(3)  # Increased border width
    draw.rectangle([
        int(margin - border_width), int(margin - border_width),
        int(margin + pattern_width + border_width), int(margin + pattern_height + border_width)
    ], outline='black', width=border_width)
    
    # Draw y-axis numbers (starting from bottom)
    font = ImageFont.truetype("arial.ttf", 16)  # Increased font size
    for y in range(current_pattern.shape[0]):
        # Calculate row number (starting from bottom)
        row_number = current_pattern.shape[0] - y
        number = str(row_number)
        text_bbox = draw.textbbox((0, 0), number, font=font)
        text_width = int(text_bbox[2] - text_bbox[0])
        text_height = int(text_bbox[3] - text_bbox[1])
        
        text_x = int(margin + pattern_width + 15)  # Increased spacing
        text_y = int(margin + y * scale + (scale - text_height) // 2)
        draw.text((text_x, text_y), number, fill='black', font=font)
    
    # Draw x-axis numbers (starting from right)
    for x in range(current_pattern.shape[1]):
        # Calculate column number (starting from right)
        col_number = current_pattern.shape[1] - x
        number = str(col_number)
        
        # Get text dimensions
        text_bbox = draw.textbbox((0, 0), number, font=font)
        text_width = int(text_bbox[2] - text_bbox[0])
        text_height = int(text_bbox[3] - text_bbox[1])
        
        # Draw tick mark
        tick_x = int(margin + x * scale + scale // 2)
        draw.line([
            (tick_x, int(margin + pattern_height)),
            (tick_x, int(margin + pattern_height + 5))
        ], fill='black', width=2)
        
        # Draw number horizontally
        text_x = int(margin + x * scale + (scale - text_width) // 2)
        text_y = int(margin + pattern_height + 10)  # Small gap after tick mark
        draw.text((text_x, text_y), number, fill='black', font=font)
    
    # Save the pattern image
    img.save('static/output/pattern.png')
    return True

def save_color_list_image():
    """Save the color list as an image"""
    global current_colors
    if not current_colors:
        return False
    
    # Create a new image with white background
    img_width = 400
    img_height = 100 + len(current_colors) * 60
    img = Image.new('RGB', (img_width, img_height), 'white')
    draw = ImageDraw.Draw(img)
    
    # Draw title
    draw.text((20, 20), "Color List", fill='black', font=ImageFont.truetype("arial.ttf", 24))
    
    # Draw each color
    for i, color in enumerate(current_colors):
        y = 80 + i * 60
        # Draw color sample
        draw.rectangle([20, y, 70, y + 50], fill=tuple(color['rgb']), outline='black')
        # Draw color number and RGB values
        text = f"Color {i + 1}: RGB({color['rgb'][0]}, {color['rgb'][1]}, {color['rgb'][2]})"
        draw.text((90, y + 15), text, fill='black', font=ImageFont.truetype("arial.ttf", 16))
    
    # Save the color list image
    img.save('static/output/color_list.png')
    return True

def save_gauge_calculation_image():
    """Save the gauge calculation as an image"""
    global current_pattern
    if current_pattern is None:
        return False
    
    # Create a new image with white background
    img_width = 400
    img_height = 300
    img = Image.new('RGB', (img_width, img_height), 'white')
    draw = ImageDraw.Draw(img)
    
    # Draw title
    draw.text((20, 20), "Gauge Calculation", fill='black', font=ImageFont.truetype("arial.ttf", 24))
    
    # Draw gauge information
    y = 80
    draw.text((20, y), "Standard Gauge: 17 × 22", fill='black', font=ImageFont.truetype("arial.ttf", 16))
    
    y += 40
    draw.text((20, y), f"Pattern Size: {current_pattern.shape[1]} × {current_pattern.shape[0]} stitches", 
              fill='black', font=ImageFont.truetype("arial.ttf", 16))
    
    y += 40
    # Calculate physical dimensions
    physical_width = (current_pattern.shape[1] / 17) * 10
    physical_height = (current_pattern.shape[0] / 22) * 10
    draw.text((20, y), f"Estimated Size: {physical_width:.1f} × {physical_height:.1f} cm", 
              fill='black', font=ImageFont.truetype("arial.ttf", 16))
    
    # Save the gauge calculation image
    img.save('static/output/gauge_calculation.png')
    return True

@app.route('/save_pattern', methods=['POST'])
def save_pattern():
    """Save the pattern as an image"""
    try:
        show_numbers = getattr(app, 'show_numbers', True)  # Get current show_numbers state
        if save_pattern_to_file(show_numbers):
            return jsonify({'success': True, 'message': 'Pattern saved successfully'})
        return jsonify({'success': False, 'error': 'No pattern to save'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/save_color_list', methods=['POST'])
def save_color_list():
    """Save the color list as an image"""
    try:
        if save_color_list_image():
            return jsonify({'success': True, 'message': 'Color list saved successfully'})
        return jsonify({'success': False, 'error': 'No colors to save'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/save_gauge', methods=['POST'])
def save_gauge():
    """Save the gauge calculation as an image"""
    try:
        if save_gauge_calculation_image():
            return jsonify({'success': True, 'message': 'Gauge calculation saved successfully'})
        return jsonify({'success': False, 'error': 'No pattern to calculate gauge for'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/save_all', methods=['POST'])
def save_all():
    """Save all images (pattern, color list, and gauge calculation)"""
    try:
        show_numbers = request.json.get('show_numbers', True) if request.json else True
        
        # Try to save all files
        pattern_saved = save_pattern_to_file(show_numbers)
        colors_saved = save_color_list_image()
        gauge_saved = save_gauge_calculation_image()
        
        if not pattern_saved:
            return jsonify({'success': False, 'error': 'No pattern to save'})
            
        return jsonify({
            'success': True,
            'message': 'All files saved successfully',
            'files': {
                'pattern': 'static/output/pattern.png',
                'color_list': 'static/output/color_list.png',
                'gauge': 'static/output/gauge_calculation.png'
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

# Add show_numbers attribute to app
app.show_numbers = True

if __name__ == '__main__':
    # Clean up old files on startup
    cleanup_old_files()
    # Run the app on all network interfaces (0.0.0.0) with port 5000
    app.run(host='0.0.0.0', port=5000, debug=False) 