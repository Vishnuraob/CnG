-Physical Development
What It Includes:
--Growth in height and weight
--Head size (for brain growth)
--Motor skills (like holding up the head, crawling, walking)
Motor Milestones:
--Lifts head (around 2 months)
--Rolls over (around 4–6 months)
--Sits without support (around 6–8 months)
--Crawls, stands, walks (by 12–15 months)


The system processes a live camera stream or a prerecorded video and overlays detected actions on-screen in real time.

---

Project Structure

- `main.py` – Core script for loading video and detecting movements
- `models/` – (Optional) Pretrained models if needed in future
- `videos/` – Sample or output videos
- `requirements.txt` – Python dependencies

---

## ⚙️ How It Works

This project uses [MediaPipe Pose](https://google.github.io/mediapipe/solutions/pose) to identify body landmarks and applies rule-based logic for each movement type:

- **Rolling Over:** Monitored by shoulder orientation and hip rotation
- **Head Turning:** Detected using relative distance between eyes and ears
- **Sitting Without Support:** Based on hip-knee-foot alignment and torso angle
- **Walking:** Detected by analyzing foot and hip movements across frames

---

## ▶️ How to Run

1. Clone this repository:
   ```bash
   git clone https://github.com/yourusername/baby-movement-detector.git
   cd baby-movement-detector
