"""
Fine-tuning script for YOLOv8n on distracted driver objects:
- phone
- cigarette
- drink (bottle/cup)
- mask (face mask / face covering)

Saves best trained weights to: runs/detect/train/weights/best.pt
"""

import os
import sys
import argparse
from pathlib import Path
import yaml
from ultralytics import YOLO


def check_dataset_health(data_yaml_path: str) -> bool:
    """Validate that data.yaml exists and contains valid references."""
    yaml_file = Path(data_yaml_path)
    if not yaml_file.exists():
        print(f"\n[ERROR] Dataset config file not found: {data_yaml_path}")
        print("Please ensure your dataset is prepared and data.yaml exists.")
        return False

    try:
        with open(yaml_file, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        print("[DATASET HEALTH CHECK]")
        print(f"  Configuration file: {yaml_file.resolve()}")
        print(f"  Classes ({data.get('nc', len(data.get('names', {})))}): {data.get('names')}")

        base_path = Path(data.get("path", yaml_file.parent))
        train_path = base_path / data.get("train", "images/train")
        val_path = base_path / data.get("val", "images/val")

        print(f"  Train images directory: {train_path.resolve()}")
        print(f"  Val images directory:   {val_path.resolve()}")

        train_imgs = (
            list(train_path.glob("*.jpg"))
            + list(train_path.glob("*.png"))
            + list(train_path.glob("*.jpeg"))
            if train_path.exists()
            else []
        )
        val_imgs = (
            list(val_path.glob("*.jpg"))
            + list(val_path.glob("*.png"))
            + list(val_path.glob("*.jpeg"))
            if val_path.exists()
            else []
        )

        print(f"  Found {len(train_imgs)} training images and {len(val_imgs)} validation images.")

        if len(train_imgs) == 0:
            print("\n[WARNING] No training images found in the specified train folder!")
            print("To train a custom model, place your labeled images into:")
            print(f"  - Images: {train_path.resolve()}")
            print("  - Labels: " + str((base_path / "labels/train").resolve()))
            print("\nRefer to README.md for instructions on downloading public datasets from")
            print("Kaggle or Roboflow and converting them to YOLO format.\n")
            return False

        return True
    except Exception as e:
        print(f"[ERROR] Failed to parse {data_yaml_path}: {e}")
        return False


def train(
    data: str = "dataset/data.yaml",
    epochs: int = 100,
    imgsz: int = 640,
    batch: int = 16,
    weights: str = "yolov8n.pt",
    device: str = "",
    project: str = "runs/detect",
    name: str = "train",
    workers: int = 4,
) -> Path:
    """
    Train YOLOv8n model with parameters requested:
    epochs=100, imgsz=640, batch=16, pretrained weights yolov8n.pt,
    saving to runs/detect/train/weights/best.pt.
    """
    print("\n" + "=" * 65)
    print("      YOLOv8n DRIVER MONITORING FINE-TUNING PIPELINE")
    print("=" * 65)
    print(f"  Base weights: {weights}")
    print(f"  Dataset config: {data}")
    print(f"  Epochs: {epochs}")
    print(f"  Image size: {imgsz}")
    print(f"  Batch size: {batch}")
    print(f"  Output directory: {project}/{name}")
    print("=" * 65 + "\n")

    # Load pretrained model
    print(f"[INFO] Loading pretrained YOLO model: {weights}...")
    model = YOLO(weights)

    # Train
    print("[INFO] Starting training session...")
    results = model.train(
        data=data,
        epochs=epochs,
        imgsz=imgsz,
        batch=batch,
        project=project,
        name=name,
        exist_ok=True,  # Keeps output strictly in runs/detect/train
        device=device if device else None,
        workers=workers,
        save=True,
        plots=True,
    )

    best_weights_path = Path(project) / name / "weights" / "best.pt"
    if best_weights_path.exists():
        print("\n" + "=" * 65)
        print(" [SUCCESS] Training completed successfully!")
        print(f" Best weights saved to: {best_weights_path.resolve()}")
        print("=" * 65)
        print("\nYou can now start the Driver Monitoring System by running:")
        print("   python main.py\n")
    else:
        print(f"\n[WARNING] Training completed, but weights not found at expected path: {best_weights_path}")

    return best_weights_path


def main():
    parser = argparse.ArgumentParser(
        description="Fine-tune YOLOv8n for Driver Distraction Object Detection"
    )
    parser.add_argument(
        "--data",
        type=str,
        default="dataset/data.yaml",
        help="Path to dataset data.yaml file (default: dataset/data.yaml)",
    )
    parser.add_argument(
        "--epochs",
        type=int,
        default=100,
        help="Number of training epochs (default: 100)",
    )
    parser.add_argument(
        "--imgsz",
        type=int,
        default=640,
        help="Image size for training (default: 640)",
    )
    parser.add_argument(
        "--batch",
        type=int,
        default=16,
        help="Batch size (default: 16)",
    )
    parser.add_argument(
        "--weights",
        type=str,
        default="yolov8n.pt",
        help="Pretrained weights to initialize from (default: yolov8n.pt)",
    )
    parser.add_argument(
        "--device",
        type=str,
        default="",
        help="Device to use, e.g. 0 or 0,1,2,3 or cpu (default: auto)",
    )
    parser.add_argument(
        "--check-only",
        action="store_true",
        help="Validate dataset structure without starting training",
    )

    args = parser.parse_args()

    is_healthy = check_dataset_health(args.data)
    if args.check_only:
        sys.exit(0 if is_healthy else 1)

    if not is_healthy:
        print("\n[NOTICE] To proceed with actual training, please add dataset images.")
        print("If you wish to test DMS immediately without training custom weights,")
        print("python main.py is pre-configured with COCO fallback mode.\n")
        response = input("Do you still wish to attempt launching YOLO training? (y/N): ").strip().lower()
        if response != "y":
            print("Training aborted.")
            sys.exit(1)

    train(
        data=args.data,
        epochs=args.epochs,
        imgsz=args.imgsz,
        batch=args.batch,
        weights=args.weights,
        device=args.device,
    )


if __name__ == "__main__":
    main()
