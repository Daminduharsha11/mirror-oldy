# Mirror-Oldy

Mirror-Oldy is primarily designed and tested for older Android versions (roughly Android 5.0 Lollipop up to Android 9 Pie). 

It leverages basic ADB shell commands for screen capture and input events which may have limited or no support on newer Android releases or certain device OEM customizations.

Works best on devices where adb shell screencap and adb shell input commands function reliably.

May not work correctly on the latest Android versions (Android 10+), due to security enhancements and changed APIs.

A PyQt5-based desktop application for real-time control and interaction with Android devices via ADB.  

Mirror your device screen, send taps, swipes, scrolls, and rotate the view — all from your PC.

---

## Features

- **Live screen mirroring** of your connected Android device.
- **Touch interaction support:** Tap, swipe, and scroll gestures on mirrored screen.
- **Device screen rotation:** Rotate the mirrored screen by 90° increments.
- **Keyboard shortcuts:**  
  - Press **R** to refresh screenshot manually.  
  - Press **S** to toggle continuous streaming mode.  
  - Press **L** to rotate the device view clockwise.
- **Minimal dependencies:** Uses PyQt5 and Pillow for GUI and image handling.
- **ADB-powered:** Requires `adb` tool configured and device connected via USB or TCP.

---

## Installation

1. Clone this repository:

   ```bash
   git clone https://github.com/Daminduharsha11/mirror-oldy.git
   cd mirror-oldy

2. (Optional but recommended) Create and activate a Python virtual environment:

   '''bash
   python -m venv venv
   source venv/bin/activate   # Linux/macOS
   venv\Scripts\activate      # Windows

4. Install required packages

   '''bash
   pip install -r requirements.txt

6. Ensure ADB
 is installed and your Android device is connected with USB debugging enabled.

##Usage

Run the application:

   '''bash
   python main.py


Interact with your device through the mirrored window. Use mouse for taps and swipes. Use keyboard shortcuts to refresh, stream, or rotate.
