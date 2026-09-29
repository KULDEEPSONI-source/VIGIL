# YOLO Dataset Format Guide for DMS

This directory holds the training and validation data for fine-tuning YOLOv8n on:
1. `phone` (class 0)
2. `cigarette` (class 1)
3. `drink` (class 2)

## Directory Structure:
```text
dataset/
├── data.yaml
├── images/
│   ├── train/     # e.g., frame001.jpg, frame002.jpg
│   └── val/       # e.g., val001.jpg, val002.jpg
└── labels/
    ├── train/     # e.g., frame001.txt, frame002.txt
    └── val/       # e.g., val001.txt, val002.txt
```

## Annotation Format:
Each `.txt` label file must have the same name as its corresponding `.jpg`/`.png` image.
Format per line:
`<class_id> <x_center> <y_center> <width> <height>`
(Coordinates normalized to 0.0 - 1.0)

Example `labels/train/img_01.txt`:
```
0 0.512 0.623 0.180 0.240
2 0.820 0.450 0.110 0.320
```
Class IDs:
- `0`: phone
- `1`: cigarette
- `2`: drink
