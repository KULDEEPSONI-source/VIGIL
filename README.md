# Real-Time Driver Monitoring System (DMS)

A complete, production-ready Driver Monitoring System (DMS) built in Python using **OpenCV**, **Ultralytics YOLOv8**, and **MediaPipe Face Mesh**.

The system monitors the driver in real-time through a webcam feed to identify distractions, drowsiness, and dangerous driver behaviors, escalating critical incidents to emergency contacts via Twilio SMS.

---

## 🌟 Key Features

| Feature | Detection Method | Alert Criteria |
| :--- | :--- | :--- |
| **Distracted Driver Behaviors** | Fine-tuned YOLOv8n (`phone`, `cigarette`, `drink`) | Confidence > 0.60 for **3+ consecutive frames** |
| **Drowsiness Monitoring** | MediaPipe Face Mesh Eye Aspect Ratio (EAR) | Average EAR < 0.25 for **20 consecutive frames** (~1s) |
| **Gaze & Head Distraction** | MediaPipe Iris & Eye Landmark tracking | Gaze away from center for **> 2.0 seconds** |
| **Emergency Escalation** | Twilio SMS API + SQLite Contacts Database | Any critical event persisting **> 5.0 seconds** |
| **Live HUD Overlay** | OpenCV UI | Real-time EAR, Gaze, Active Alerts, FPS, Hotkeys |

---

## 📁 Project Architecture & File Tree

```text
project-model-train/
│
├── config.yaml               # Central configuration for all thresholds, paths, and camera
├── requirements.txt          # Python project dependencies
├── main.py                   # Main entry point (OpenCV feed, HUD overlay, event loop)
├── detection.py              # YOLOv8 object detector with consecutive-frame filtering
├── eye_tracking.py           # MediaPipe FaceMesh EAR calculation and iris gaze tracker
├── alerts.py                 # Twilio SMS dispatcher, logging to events.log, audio alerts
├── contacts.py               # SQLite emergency contacts manager & standalone CLI tool
├── train_yolo.py             # Script to fine-tune YOLOv8n (epochs=100, imgsz=640, batch=16)
│
├── dataset/                  # Template directory for YOLO format dataset
│   ├── data.yaml             # YOLOv8 dataset configuration
│   ├── README.md             # Dataset formatting instructions
│   ├── images/
│   │   ├── train/            # Training images (.jpg/.png)
│   │   └── val/              # Validation images (.jpg/.png)
│   └── labels/
│       ├── train/            # YOLO format annotations (.txt)
│       └── val/              # YOLO format annotations (.txt)
│
├── snapshots/                # Directory where snapshots are saved (press 's')
├── events.log                # Persistent log file of all warnings, alerts, and SMS actions
└── contacts.db               # SQLite database storing emergency contacts
```

---

## ⚙️ Installation & Setup

### 1. Clone or Open Project
```bash
cd "c:/Users/sahde/OneDrive/Desktop/project model train"
```

### 2. Create and Activate a Virtual Environment (Recommended)
```bash
python -m venv venv
# On Windows:
.\venv\Scripts\activate
# On Linux/macOS:
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

---

## 📦 Dataset Preparation & Restructuring Guide

To fine-tune YOLOv8 on the 3 custom classes (`phone`, `cigarette`, `drink`), you need annotated images in standard YOLO format.

### Recommended Public Datasets

1. **Roboflow Universe (Easiest & Pre-formatted)**:
   - **Driver Drowsiness & Distraction / Smoking / Phone**:
     - [Roboflow Driver Distraction Datasets](https://universe.roboflow.com/search?q=driver+distraction)
     - [Roboflow Driver Smoking & Phone Detection](https://universe.roboflow.com/search?q=smoking+cell+phone)
   - *Advantage*: Direct export in **YOLOv8** format. When exporting from Roboflow, choose **YOLOv8** format, download the `.zip`, and extract directly into `dataset/`.

2. **Kaggle State Farm Distracted Driver Detection**:
   - [Kaggle State Farm Competition](https://www.kaggle.com/c/state-farm-distracted-driver-detection/data)
   - Contains 10 driver posture classes:
     - `c0`: safe driving
     - `c1`: texting - right
     - `c2`: talking on the phone - right
     - `c3`: texting - left
     - `c4`: talking on the phone - left
     - `c5`: operating the radio
     - `c6`: drinking
     - `c7`: reaching behind
     - `c8`: hair and makeup
     - `c9`: talking to passenger
   - *How to restructure into YOLO format*:
     1. Map `c1`, `c2`, `c3`, `c4` images to class `0` (`phone`).
     2. Map `c6` images to class `2` (`drink`).
     3. For object detection bounding boxes, use auto-annotation tools (e.g., [LabelImg](https://github.com/HumanSignal/labelImg), [CVAT](https://www.cvat.ai/), or Roboflow) to label the phone, cup/bottle, and cigarette bounding boxes.

### Target YOLO Annotation Format

Place your files in:
```text
dataset/
  images/train/img_001.jpg
  labels/train/img_001.txt
  images/val/img_002.jpg
  labels/val/img_002.txt
```

Each `.txt` file contains one row per detected object:
```text
<class_id> <x_center> <y_center> <width> <height>
```
Normalized between `0.0` and `1.0`.

Class mapping in `dataset/data.yaml`:
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

## 🚀 Model Training (Feature 1)

Fine-tune YOLOv8n with the exact required parameters:
- `epochs = 100`
- `imgsz = 640`
- `batch = 16`
- Pretrained weights: `yolov8n.pt`
- Target weights output: `runs/detect/train/weights/best.pt`

Run the training script:
```bash
python train_yolo.py --data dataset/data.yaml --epochs 100 --batch 16 --imgsz 640
```

To verify dataset health without starting training:
```bash
python train_yolo.py --check-only
```

Once training completes, the best weights will automatically be saved to `runs/detect/train/weights/best.pt`.

---

## 🏃 Running the Driver Monitoring System

Launch the real-time DMS application:
```bash
python main.py
```

### Demonstration Mode (COCO Fallback)
If you run `python main.py` before training custom weights, the system automatically detects that `best.pt` is missing and:
1. Prints a clear error advising you to run `python train_yolo.py`.
2. Seamlessly falls back to pre-trained `yolov8n.pt` COCO weights (`cell phone` $\rightarrow$ `phone`, `bottle`/`cup` $\rightarrow$ `drink`) so you can test the system, camera, HUD, MediaPipe EAR, and Twilio alerts immediately!

---

## 🎮 Interactive Controls & UI

| Key | Action | Description |
| :---: | :---: | :--- |
| **`q`** or **`ESC`** | **Quit** | Gracefully releases camera and terminates the system. |
| **`s`** | **Save Snapshot** | Captures the current frame with timestamp into `snapshots/`. |
| **`c`** | **Add Contact** | Opens an interactive terminal prompt to add an emergency contact into `contacts.db`. |

### On-Screen HUD Overlay Details:
- **Telemetry Box**: Shows Face Detection status, Eye Aspect Ratio (EAR), Gaze Direction, YOLO Object Detection counters, and Active Alerts.
- **Top Center Warning Banner**: Flashing alert banner whenever drowsiness, distraction, or behavior alerts fire.
- **Critical Alert Escalation**: If an alert persists for **> 5.0 seconds**, the banner flashes bright red and an emergency SMS is dispatched.

---

## 📞 Managing Emergency Contacts (Feature 3)

Emergency contacts are stored in a local SQLite database (`contacts.db`). You can manage them anytime using `contacts.py`:

### Add a Contact
```bash
python contacts.py --add "Jane Doe" "+14155552671"
```

### List All Contacts
```bash
python contacts.py --list
```

### Delete a Contact by ID
```bash
python contacts.py --delete 1
```

### Interactive Menu
```bash
python contacts.py --interactive
```

---

## 📲 Configuring Twilio SMS Alerts

When any critical incident persists for **> 5.0 seconds** (e.g. eyes closed > 5s, looking away > 5s, continuous phone usage > 5s), the system sends an SMS to all registered emergency contacts.

Set your Twilio credentials as environment variables:

### Windows (PowerShell):
```powershell
$env:TWILIO_ACCOUNT_SID="your_account_sid_here"
$env:TWILIO_AUTH_TOKEN="your_auth_token_here"
$env:TWILIO_PHONE_NUMBER="+1xxxxxxxxxx"
```

### Windows (Command Prompt):
```cmd
set TWILIO_ACCOUNT_SID=your_account_sid_here
set TWILIO_AUTH_TOKEN=your_auth_token_here
set TWILIO_PHONE_NUMBER=+1xxxxxxxxxx
```

### Linux / macOS:
```bash
export TWILIO_ACCOUNT_SID="your_account_sid_here"
export TWILIO_AUTH_TOKEN="your_auth_token_here"
export TWILIO_PHONE_NUMBER="+1xxxxxxxxxx"
```

> **Note on Fallback**: If Twilio credentials are not set, the system gracefully logs `[SIMULATED SMS]` to `events.log` and console without interrupting monitoring or crashing.

---

## 🛡️ Edge Cases Handled

1. **No Face Detected**:
   - MediaPipe skips EAR and gaze calculations gracefully.
   - Resets drowsiness and gaze counters so phantom alerts are not triggered.
   - Displays `Face: NO FACE DETECTED` on the HUD.
2. **Missing YOLO Model File**:
   - Displays a prominent error banner directing the user to `python train_yolo.py`.
   - Offers automatic fallback to base COCO weights if enabled in `config.yaml`.
3. **Camera Unavailable**:
   - Checks camera status and prints clear instructions on verifying USB connection, permissions, or changing `device_index` in `config.yaml`.
4. **Flicker-Free Object Detection**:
   - Requires detection above confidence 0.60 for **3+ consecutive frames** before triggering an alert.
5. **SMS Flood Protection**:
   - Built-in cooldown timer (`sms_cooldown_seconds: 60.0`) prevents spamming contacts during sustained emergencies.
#   V I G I L  
 