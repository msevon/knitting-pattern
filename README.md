# Knitting Pattern Generator

A web application that converts images into knitting patterns by reducing colors and creating a grid-based pattern suitable for knitting projects. Made for my girlfriend :).

## Features

- **Image to Pattern Conversion**: Upload any image and convert it into a knitting pattern
- **Customizable Grid Size**: Adjust the width and height of the pattern in stitches (10-200)
- **Color Management**:
  - Choose number of colors (2-20)
  - Click on color samples to modify colors using a color picker
  - View RGB values for each color
- **Pattern Display**:
  - Clear grid layout with color numbers
  - Toggle color numbers visibility
  - Y-axis numbers on the right
  - X-axis numbers at the bottom
- **Gauge and Dimensions**:
  - Input custom gauge measurements (stitches and rows per 10cm)
  - Real-time calculation of physical dimensions
  - Default gauge: 17 stitches × 22 rows = 10cm × 10cm
- **Responsive Interface**:
  - Clean, modern design
  - Loading indicators for operations
  - Error handling and feedback
  - File name display after selection

## Technologies Used

### Frontend
- HTML5
- CSS3
- JavaScript (ES6+)
- Fetch API for HTTP requests

### Backend
- Python 3
- Flask web framework
- OpenCV for image processing
- scikit-learn for color clustering
- PIL (Python Imaging Library) for image manipulation

## Requirements

```
flask==3.0.2
numpy==1.26.4
pillow==10.2.0
opencv-python==4.9.0.80
scikit-learn==1.4.0
```

## Setup

1. Clone the repository:
```bash
git clone [repository-url]
cd knitting-pattern
```

2. Create and activate a virtual environment (optional but recommended):
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Run the application:
```bash
python app.py
```

5. Open your browser and navigate to:
```
http://localhost:5000
```

## Usage

1. **Select an Image**:
   - Click "Choose Image" to upload your source image
   - Supported formats: PNG, JPG, JPEG, etc.

2. **Configure Pattern Settings**:
   - Set the width in stitches (10-200)
   - Set the height in stitches (10-200)
   - Choose the number of colors (2-20)
   - Adjust gauge settings if needed:
     - Gauge X: stitches per 10cm (default: 17)
     - Gauge Y: rows per 10cm (default: 22)
   - View estimated physical dimensions based on gauge

3. **Generate Pattern**:
   - Click "Generate Pattern" to create your knitting pattern
   - Wait for processing to complete

4. **Customize Colors** (optional):
   - Click on any color sample to open the color picker
   - Select a new color to update the pattern
   - Changes are applied automatically

5. **Toggle Numbers**:
   - Use the "Hide/Show Numbers" button to toggle color numbers visibility
   - Numbers help identify which color to use in each stitch

6. **Clear Pattern**:
   - Click "Clear" to reset everything and start over

## Notes

- Larger images and patterns may take longer to process
- The application automatically reduces colors using K-means clustering
- Color numbers are displayed in both the pattern grid and color list
- The pattern maintains aspect ratio while fitting to the specified grid size

## Error Handling

The application handles various error cases:
- Invalid image files
- Processing failures
- Network issues
- Invalid color updates

Error messages are displayed clearly to the user when issues occur.

## Contributing

Feel free to submit issues, fork the repository, and create pull requests for any improvements.

## License

MIT license
