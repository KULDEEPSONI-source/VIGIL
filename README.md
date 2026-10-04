# 🚗 Real-Time Driver Monitoring System (DMS)

A real-time Driver Monitoring System built in Python using **OpenCV**, **Ultralytics YOLOv8**, and **MediaPipe Face Mesh**. It watches the driver through a webcam, detects drowsiness, gaze distraction, and risky behaviors (phone, cigarette, drink), and escalates critical incidents to emergency contacts via **Twilio SMS**.

![Python](https://img.shields.io/badge/Python-3.9%2B-blue)
![OpenCV](https://img.shields.io/badge/OpenCV-4.x-green)
![YOLOv8](https://img.shields.io/badge/YOLOv8-Ultralytics-orange)
![MediaPipe](https://img.shields.io/badge/MediaPipe-FaceMesh-purple)
![License](https://img.shields.io/badge/License-MIT-lightgrey)

---

## 📑 Table of Contents

- [Features](#-features)
- [How It Works](#-how-it-works)
- [Project Structure](#-project-structure)
- [Installation](#-installation)
- [Dataset Preparation](#-dataset-preparation)
- [Model Training](#-model-training)
- [Running the System](#-running-the-system)
- [Controls and HUD](#-controls-and-hud)
- [Emergency Contacts](#-emergency-contacts)
- [Twilio SMS Setup](#-twilio-sms-setup)
- [Edge Cases Handled](#-edge-cases-handled)
- [Configuration](#-configuration)
- [Roadmap](#-roadmap)
- [License](#-license)

---

## 🌟 Features

| Feature | Detection Method | Alert Criteria |
| :--- | :--- | :--- |
| **Distracted driver behaviors** | Fine-tuned YOLOv8n (`phone`, `cigarette`, `drink`) | Confidence > 0.60 for **3+ consecutive frames** |
| **Drowsiness monitoring** | MediaPipe Face Mesh Eye Aspect Ratio (EAR) | Average EAR < 0.25 for **20 consecutive frames** (~1 s) |
| **Gaze and head distraction** | MediaPipe iris and eye landmark tracking | Gaze away from center for **> 2.0 seconds** |
| **Emergency escalation** | Twilio SMS API + SQLite contacts database | Any critical event lasting **> 5.0 seconds** |
| **Live HUD overlay** | OpenCV UI | Real-time EAR, gaze, active alerts, FPS, hotkeys |

---

## 🧠 How It Works

```text
Webcam Frame
     │
     ├──► YOLOv8n Detector ──► phone / cigarette / drink ──┐
     │                                                      │
     └──► MediaPipe Face Mesh ──► EAR + Iris Gaze ─────────┤
                                                            ▼
                                              Alert Manager (alerts.py)
                                                            │
                          ┌─────────────────────────────────┼────────────────────┐
                          ▼                                 ▼                    ▼
                    HUD Banner + Sound               events.log        Twilio SMS (> 5 s)
```

---

## 📁 Project Structure

```text
project-model-train/
│
├── config.yaml          # Central config: thresholds, paths, camera
├── requirements.txt     # Python dependencies
├── main.py              # Entry point: camera feed, HUD, event loop
├── detection.py         # YOLOv8 detector with consecutive-frame filtering
├── eye_tracking.py      # MediaPipe EAR calculation and iris gaze tracker
├── alerts.py            # Twilio SMS, logging to events.log, audio alerts
├── contacts.py          # SQLite emergency contacts manager and CLI
├── train_yolo.py        # Fine-tunes YOLOv8n (epochs=100, imgsz=640, batch=16)
│
├── dataset/             # YOLO-format dataset template
│   ├── data.yaml
│   ├── README.md
│   ├── images/{train,val}/
│   └── labels/{train,val}/
│
├── snapshots/           # Saved frames (press 's')
├── events.log           # Log of warnings, alerts, and SMS actions
└── contacts.db          # SQLite database of emergency contacts
```

---

## ⚙️ Installation

### 1. Clone the repository
```bash
git clone https://github.com/<your-username>/<your-repo-name>.git
cd <your-repo-name>
```

### 2. Create a virtual environment (recommended)
```bash
python -m venv venv

# Windows
.\venv\Scripts\activate

# Linux / macOS
source venv/bin/activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

> **Tip:** If you get `AttributeError: module 'mediapipe' has no attribute 'solutions'`, make sure none of your files is named `mediapipe.py`, and reinstall with `pip install --upgrade --force-reinstall mediapipe`.

---

## 📦 Dataset Preparation

To fine-tune YOLOv8 on the 3 custom classes (`phone`, `cigarette`, `drink`), you need annotated images in YOLO format.

### Recommended datasets

**1. Roboflow Universe (easiest, pre-formatted)**
- [Driver distraction datasets](https://universe.roboflow.com/search?q=driver+distraction)
- [Smoking and phone detection datasets](https://universe.roboflow.com/search?q=smoking+cell+phone)
- Export in **YOLOv8** format, download the `.zip`, and extract it into `dataset/`.

**2. Kaggle State Farm Distracted Driver Detection**
- [Competition data](https://www.kaggle.com/c/state-farm-distracted-driver-detection/data)
- Contains 10 posture classes (`c0` safe driving to `c9` talking to passenger).
- To convert for this project:
  1. Map `c1`, `c2`, `c3`, `c4` (texting / phone) to class `0` (`phone`).
  2. Map `c6` (drinking) to class `2` (`drink`).
  3. Draw bounding boxes using [LabelImg](https://github.com/HumanSignal/labelImg), [CVAT](https://www.cvat.ai/), or Roboflow.

### YOLO annotation format

```text
dataset/
  images/train/img_001.jpg
  labels/train/img_001.txt
  images/val/img_002.jpg
  labels/val/img_002.txt
```

Each `.txt` file has one row per object, normalized between `0.0` and `1.0`:

```text
<class_id> <x_center> <y_center> <width> <height>
```

`dataset/data.yaml`:

```yaml
path: dataset
train: images/train
val: images/val
nc: 3
names:
  0: phone
  1: cigarette
  2: drink
```

---

## 🚀 Model Training

Fine-tunes YOLOv8n with:

- `epochs = 100`
- `imgsz = 640`
- `batch = 16`
- Pretrained weights: `yolov8n.pt`
- Output weights: `runs/detect/train/weights/best.pt`

```bash
python train_yolo.py --data dataset/data.yaml --epochs 100 --batch 16 --imgsz 640
```

Check dataset health without training:

```bash
python train_yolo.py --check-only
```

---

## 🏃 Running the System

```bash
python main.py
```

### Demo mode (COCO fallback)

If `best.pt` is missing, the system:

1. Prints an error telling you to run `python train_yolo.py`.
2. Falls back to pretrained `yolov8n.pt` COCO weights (`cell phone` → `phone`, `bottle` / `cup` → `drink`), so you can test the camera, HUD, EAR tracking, and SMS alerts right away.

---

## 🎮 Controls and HUD

| Key | Action | Description |
| :---: | :--- | :--- |
| `q` / `ESC` | Quit | Releases the camera and exits cleanly. |
| `s` | Save snapshot | Saves the current frame with a timestamp into `snapshots/`. |
| `c` | Add contact | Opens a terminal prompt to add an emergency contact. |

**HUD overlay**
- **Telemetry box:** face status, EAR, gaze direction, YOLO counters, active alerts.
- **Top warning banner:** flashes on drowsiness, distraction, or behavior alerts.
- **Critical escalation:** if an alert lasts **> 5 seconds**, the banner turns bright red and an emergency SMS is sent.

---

## 📞 Emergency Contacts

Contacts are stored in a local SQLite database (`contacts.db`) and managed with `contacts.py`.

```bash
# Add a contact
python contacts.py --add "Jane Doe" "+14155552671"

# List all contacts
python contacts.py --list

# Delete a contact by ID
python contacts.py --delete 1

# Interactive menu
python contacts.py --interactive
```

---

## 📲 Twilio SMS Setup

When a critical incident lasts **> 5 seconds** (eyes closed, looking away, continuous phone use), an SMS goes out to all registered contacts.

Set your credentials as environment variables:

**Windows (PowerShell)**
```powershell
$env:TWILIO_ACCOUNT_SID="your_account_sid_here"
$env:TWILIO_AUTH_TOKEN="your_auth_token_here"
$env:TWILIO_PHONE_NUMBER="+1xxxxxxxxxx"
```

**Windows (Command Prompt)**
```cmd
set TWILIO_ACCOUNT_SID=your_account_sid_here
set TWILIO_AUTH_TOKEN=your_auth_token_here
set TWILIO_PHONE_NUMBER=+1xxxxxxxxxx
```

**Linux / macOS**
```bash
export TWILIO_ACCOUNT_SID="your_account_sid_here"
export TWILIO_AUTH_TOKEN="your_auth_token_here"
export TWILIO_PHONE_NUMBER="+1xxxxxxxxxx"
```

> **Fallback:** If credentials are not set, the system logs `[SIMULATED SMS]` to `events.log` and the console, and keeps running without crashing.

> ⚠️ **Never commit your Twilio credentials to GitHub.** Keep them in environment variables and add any `.env` file to `.gitignore`.

---

## 🛡️ Edge Cases Handled

| Case | Behavior |
| :--- | :--- |
| **No face detected** | Skips EAR and gaze, resets counters to avoid false alerts, shows `Face: NO FACE DETECTED`. |
| **Missing YOLO model** | Shows an error banner pointing to `train_yolo.py` and optionally falls back to COCO weights (set in `config.yaml`). |
| **Camera unavailable** | Prints steps to check USB connection, permissions, or `device_index` in `config.yaml`. |
| **Detection flicker** | Requires confidence > 0.60 for 3+ consecutive frames before alerting. |
| **SMS flooding** | 60-second cooldown (`sms_cooldown_seconds: 60.0`) between messages. |

---

## 🔧 Configuration

All thresholds live in `config.yaml`: EAR threshold, consecutive-frame counts, gaze duration, YOLO confidence, camera index, SMS cooldown, and fallback behavior. Adjust them to suit your camera and lighting.

---

## 🗺️ Roadmap

- [ ] Head-pose estimation (yawning and nodding detection)
- [ ] Night / IR camera support
- [ ] Seatbelt detection
- [ ] Lightweight deployment on Raspberry Pi / Jetson Nano

---

## 📄 License

This project is licensed under the MIT License. See the `LICENSE` file for details.

---

## 🙌 Acknowledgements

- [Ultralytics YOLOv8](https://github.com/ultralytics/ultralytics)
- [MediaPipe](https://github.com/google/mediapipe)
- [OpenCV](https://opencv.org/)
- [Twilio](https://www.twilio.com/)
