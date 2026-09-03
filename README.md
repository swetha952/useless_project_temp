<img width="1280" height="640" alt="git (1)" src="https://github.com/user-attachments/assets/8920b256-2ba8-4988-b824-5351134eb4bd" />



# Hello Chayae,Kadi Evide???🎯


## Basic Details
### Team Name: Useless.exe


### Team Members
- Member 1: Swetha C R - Muthoot Institute of Technology and Science
- Member 2: Arathi S- Muthoot Institute of Technology and Science

### Project Description
Hello Chayae, Kadi Undo??? is a computer-vision-based biscuit dunking analyzer that uses a webcam to detect and track a biscuit and cup, monitor its immersion, angle, movement and dunk duration. It then calculates a Biscuit Stability Index, Breakage Risk, Dunking Score and real-time Stability Graph to determine whether your dunk was a masterpiece or a biscuit disaster.

### The Problem (that doesn't exist)
The Problem (that doesn't exist)

Nobody has ever asked:

"How scientifically dangerous is my biscuit dunk?"

People have been dunking biscuits irresponsibly for years without knowing the exact moment their biscuit is about to surrender to the tea.

Our project solves this completely unnecessary but extremely important problem.

### The Solution (that nobody asked for)
We use OpenCV-based computer vision and mathematical analysis to monitor the biscuit during a dunk.

The system:

Detects and tracks the biscuit using OpenCV
Identifies the beverage surface
Measures biscuit immersion depth
Measures dunk duration
Estimates biscuit orientation/angle
Tracks biscuit movement
Calculates biscuit stability
Predicts breakage probability
Generates a dunk score out of 100
Assigns a hilarious dunk rating
Generates a stability graph
Displays the final dunk analysis
Overall Pipeline

Webcam → OpenCV Detection/Tracking → Immersion + Angle + Movement → Stability → Break Risk → Dunk Score → Final Analysis

## Technical Details
### Technologies/Components Used
For Software:
Python — Main programming language
HTML — Web interface structure
CSS — UI styling
JavaScript — Web interface interactions and result display
OpenCV — Camera access, object tracking, image processing and computer vision
NumPy — Numerical and array operations
Math — Mathematical calculations for angle, movement and breakage probability
VS Code — Development environment
GitHub Copilot — Development assistance

Computer Vision Techniques Used
OpenCV contour detection
Thresholding and image preprocessing
Morphological operations
minAreaRect() for biscuit orientation
CSRT Tracker for real-time biscuit tracking
ROI-based image analysis
Webcam frame processing

For Hardware:
-Laptop/PC
-Built-in or USB webcam
-Biscuit
-Cup
-Tea/coffee/beverage

### Implementation
For Software:
# Installation
Install Python dependencies:

pip install opencv-python numpy

If your OpenCV version does not provide the CSRT tracker through the normal cv2 package, install the contrib package:

pip uninstall opencv-python
pip install opencv-contrib-python

Important: Don't install both opencv-python and opencv-contrib-python at the same time, because that can cause OpenCV module conflicts.

# Run
From the project directory:

python main.py

or on Windows:

py main.py

The application opens the web interface, where the user can select OPEN CAMERA and begin the biscuit dunk analysis.

### Project Documentation
For Software:

# Screenshots
Website Interface
<img width="1600" height="770" alt="img1" src="https://github.com/user-attachments/assets/f0b0c3a7-3969-45c1-9d86-735f53c69b37" />
The landing page of the Biscuit Dunk AI website, providing access to the biscuit dunk analysis system and introducing the project’s AI-powered computer vision functionality.

Real-Time Biscuit Dunk Detection
<img width="1600" height="756" alt="img2" src="https://github.com/user-attachments/assets/6e816dc3-9586-4f41-b61e-6a6e48511322" />
The system uses the webcam and OpenCV to detect and track the biscuit during the dunking process, while monitoring its position and interaction with the beverage.

Biscuit Dunk Analysis Results
<img width="1600" height="759" alt="img3" src="https://github.com/user-attachments/assets/ed27af82-b7e2-4590-9423-ddfb2d9f2d85" />
he final analysis screen presents the measured dunk parameters, including immersion, dunk time, angle, stability, breakage risk, and overall dunk score, along with a stability graph showing the dunk performance over time.

# Diagrams
![Workflow](Add your workflow/architecture diagram here)
*Add caption explaining your workflow*

For Hardware:

# Schematic & Circuit
![Circuit](Add your circuit diagram here)
*Add caption explaining connections*

![Schematic](Add your schematic diagram here)
*Add caption explaining the schematic*

# Build Photos
![Components](Add photo of your components here)
*List out all components shown*

![Build](Add photos of build process here)
*Explain the build steps*

![Final](Add photo of final product here)
*Explain the final build*

### Project Demo
# Video
[Add your demo video link here]
*Explain what the video demonstrates*

# Additional Demos
[Add any extra demo materials/links]

## Team Contributions
- Swetha C R: Developed the OpenCV-based computer vision system, including real-time biscuit detection and tracking, beverage-surface calibration, immersion        measurement, dunk-time calculation, biscuit angle detection, and movement tracking. Also integrated the analysis modules into the main Python application.
- Arathi S: Developed the website UI and result interface, including the landing page, camera interaction, final results display, stability graph, dunk score, stability calculation, and breakage-risk analysis. Also handled the integration between the frontend interface and the Python/OpenCV backend.


---
Made with ❤️ at TinkerHub Useless Projects 

![Static Badge](https://img.shields.io/badge/TinkerHub-24?color=%23000000&link=https%3A%2F%2Fwww.tinkerhub.org%2F)
![Static Badge](https://img.shields.io/badge/UselessProjects--26-26?link=https%3A%2F%2Ftinkerhub.org%2Fevents%2F1M8ORET9A1%2Fuseless-projects-3.0)



