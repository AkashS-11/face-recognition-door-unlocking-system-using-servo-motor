# Face Recognition Door Unlocking System (Servo Motor)

A smart door lock that unlocks only for registered faces. A Python desktop app (Tkinter + OpenCV) recognises people through a webcam and drives a servo motor through an Arduino. Members and the admin PIN are managed from the same GUI.

## Features

- **Face-recognition unlock**: live webcam recognition, with the door opening for registered members only
- **Servo lock control**: the servo turns to 90° (open), then returns to 0° (locked) after 10 seconds
- **LED indicator**: lights for 10 seconds when access is granted
- **Voice feedback**: speaks "Access Granted" or "Access Denied" (pyttsx3)
- **Animated feedback**: on-screen GIFs for success and failure
- **Member management (PIN-protected)**: add, delete and list members
  - Add a member by capturing a photo from the camera or browsing for an image
  - Maximum of 4 registered members
- **PIN protection**: a 4-digit PIN guards adding, deleting and viewing members, and can be changed from the GUI
- **Auto-deny**: if only unknown faces are seen for 5 seconds, access is denied

## How It Works

1. Registered members are stored as photos in the `images/` folder. The file name is the member's name (e.g. `Akash.jpg`).
2. On **Unlock Door**, the app loads the face encodings and starts the webcam.
3. Each frame is brightened, downscaled to 50% and matched against known faces (threshold `0.4`).
4. On a match, the app sends a command to the Arduino over `pyfirmata`: servo to 90°, LED on, then it auto-locks after 10 seconds.
5. If no match is found within 5 seconds, access is denied.

## Hardware Required

- Arduino board (Uno or similar)
- Servo motor (e.g. SG90)
- LED (or the onboard LED on pin 13)
- Webcam
- USB cable and jumper wires

### Wiring

| Component | Arduino Pin |
|---|---|
| Servo signal | D8 |
| Servo VCC / GND | 5V / GND |
| LED | D13 |

Upload the **StandardFirmata** sketch to the Arduino first (Arduino IDE → File → Examples → Firmata → StandardFirmata).

## Software Requirements

- Python 3.9 (the bundled `simple_facerec` module is compiled for CPython 3.9)
- Libraries:

```bash
pip install opencv-python pillow pyfirmata pyttsx3 face_recognition
```

> `face_recognition` depends on `dlib`, which may need CMake and a C++ compiler on Windows.

## Setup and Usage

1. Clone the repository:
   ```bash
   git clone https://github.com/AkashS-11/face-recognition-door-unlocking-system-using-servo-motor.git
   cd face-recognition-door-unlocking-system-using-servo-motor
   ```
2. Connect the Arduino and note its COM port.
3. Open `doorr3.py` and set your port if it isn't COM3:
   ```python
   ARDUINO_PORT = 'COM3'
   ```
4. Run the app:
   ```bash
   python doorr3.py
   ```
5. Click **Add Member** to register at least one face, then click **Unlock Door**.

> If the Arduino isn't connected, the GUI and face recognition still run, but the servo and LED commands will fail with an error message in the console.

## GUI Buttons

| Button | What it does | PIN needed |
|---|---|---|
| Unlock Door | Starts face recognition and unlocks on a match | No |
| Add Member | Registers a new face (camera or file), max 4 | Yes |
| Delete Member | Removes a member by name | Yes |
| Show Members | Lists registered members | Yes |
| Change PIN | Sets a new 4-digit PIN | Current PIN |

## Project Structure

```
├── doorr3.py                      # Main application (GUI, recognition, Arduino control)
├── simple_facerec.cpython-39.pyc  # Face recognition helper module
├── pin.txt                        # Stored PIN
├── background.jpg                 # GUI background
├── lock_open.gif                  # Access-granted animation
├── cross.gif                      # Access-denied animation
└── images/                        # Registered member photos (created automatically)
```

## Security Notes

- A PIN is created on first run (default `1234`). **Change it immediately** from the GUI.
- The PIN is stored in plain text in `pin.txt`. Don't commit a real PIN to a public repository.
- There is no liveness detection, so a photo of a registered person may fool the system. This project is a prototype and is not suitable for protecting anything valuable.

## Tech Stack

Python · OpenCV · face_recognition · Tkinter · Pillow · pyfirmata · pyttsx3 · Arduino

## Future Improvements

- Liveness / anti-spoofing detection (blink or head-movement check)
- Hashed PIN storage
- Activity log with timestamps and captured photos of unknown visitors
- Remove the 4-member limit
- Run speech on a separate thread so the GUI doesn't freeze

## Author

**Akash S**
B.E. Computer Science & Engineering, B.N.M. Institute of Technology, Bengaluru
GitHub: [@AkashS-11](https://github.com/AkashS-11)
