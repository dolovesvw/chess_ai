# ♟️ Project SYNTHESIS

**Project SYNTHESIS** is a creative extension of the Eve VTuber chess AI module. Its purpose is to enable **Eve**, a modular AI entertainer, to **generate, test, refine, and ultimately master her own original chess openings**—both for White and Black sides. These openings are not static; they evolve over time based on data, results, and creative heuristics.

> “Why play by the rules... when I can evolve my own path?”

---

## 🎯 Goal

To give Eve a *signature style* of chess play by allowing her to:
- Analyze opening patterns from her own games using already practical and well designed openings.
- Synthesize original opening lines that reflect her personality and strategic tendencies.
- Name and narrate her own openings.
- Continuously adapt her opening repertoire through learning.

### **TLDR**
- Play normally using popular openings.
- Learn from them and adapt the playstyle.
- Name and update her own opening.
- Experiment and adapt

---

## 🧠 Core Concepts

- **Synthetic Opening Creation**  
  Eve generates openings using a blend of clustering, evaluation metrics, and novelty detection.

- **Style-Conscious Moves**  
  Each move is evaluated not just for strength, but for style consistency (aggressive, tactical, solid, etc.).

- **Evolving Repertoire**  
  Eve’s openings evolve over time based on win rates, viewer reactions(if a viewer gives a good suggestion), and internal evaluation feedback.

---

## 🗂️ Project Structure

```yaml
project-synthesis/
├── data/ # PGN/FEN history, training samples
├── generator/ # Opening generation algorithms
│ ├── synthesizer.py # Core logic for line creation
│ └── eval.py # Position evaluation + novelty scoring
├── openings/ # Saved custom openings
│ ├── white_opening.pgn # She can create versions and chnage the name (so like Eve_OpeningV1.0.5)
│ └── black_opening.pgn
├── integration/ # Hooks for Eve’s main logic
├── config.yaml # Style & tuning config
└── README.md
```

---
