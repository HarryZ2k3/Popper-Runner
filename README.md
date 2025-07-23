---

# **Popper ILP GUI Runner**

A Python-based **Graphical Interface (GUI)** for running [Popper (Inductive Logic Programming)](https://github.com/logic-and-learning-lab/popper) with **real-time hypothesis rendering**, **LaTeX visualization**, and **auto-environment setup**.

---

## ✅ **Features**

* Auto-checks & installs required Python libraries and system dependencies (Popper, SWI-Prolog, Clingo, LaTeX).
* GUI built with **Tkinter** + **TTKBootstrap**.
* Real-time or batch hypothesis visualization with **LaTeX-style rendering**.
* Automatic caching of last used paths and history.
* Cross-platform (Linux, Windows, macOS; best tested on Ubuntu/WSL).

---

## 🗂 **Project Structure**

```
calculator_popper/
│
├── ruleset/               # Stores last used paths & history
│   ├── history.json
│   └── last_paths.json
│
├── run.py                  # Main entry point (GUI & CLI)
├── popper/                 # Cloned Popper repository (auto-cloned if missing)
├── Problem bank/           # (Optional) Your custom .pl files or datasets
├── LICENSE
└── README.md
```

---

## ⚙ **Requirements**

* **Python 3.8+**
* **Git** (auto-installed if missing)
* **SWI-Prolog** (auto-installed on Linux, manual on Windows/macOS)
* **Clingo** (auto-installed on Linux, manual on Windows/macOS)
* **LaTeX** (optional – fallback to MathText if unavailable)

---

## 🚀 **First-Time Setup**

Just run:

```bash
python3 run.py --gui
```

The script will:

1. **Check pip** → upgrade if missing.
2. **Install required Python libraries** (`ttkbootstrap`, `pyswip`, `clingo`, `bitarray`, `matplotlib`, `pillow`, `python-sat`).
3. **Install system dependencies** (SWI-Prolog, Clingo, LaTeX if available).
4. **Clone Popper automatically** if not found.

If something fails, follow the **manual installation** below.

---

### **Manual Installation (Optional)**

If automatic installation fails:

#### 1. Install Python libraries

```bash
pip install ttkbootstrap pyswip clingo bitarray "python-sat[pblib,aiger]" matplotlib pillow
```

#### 2. Install system dependencies

**Ubuntu / WSL (recommended)**:

```bash
sudo apt-get update
sudo apt-get install -y swi-prolog clingo \
    texlive-latex-base texlive-latex-recommended texlive-latex-extra \
    texlive-fonts-recommended texlive-fonts-extra texlive-lang-european dvipng
```

**Windows**:

* [Install SWI-Prolog](https://www.swi-prolog.org/download/stable)
* [Install Clingo](https://potassco.org/clingo/)
* [Install MiKTeX (optional)](https://miktex.org/download)

**macOS**:

```bash
brew install swi-prolog clingo --cask mactex
```

---

## 🖥 **Usage**

### **Run GUI Mode**

```bash
python3 run.py --gui
```

* **Upload** your `bk.pl`, `bias.pl`, and `exs.pl` files.
* **Set timeout** (e.g., `300s`).
* **Toggle real-time refresh** for live hypothesis updates.
* Results will be **rendered as LaTeX images**.

### **Run CLI Mode**

```bash
python3 run.py
```

*(Currently only displays a message; full CLI mode may be extended later.)*

---

## 📝 **Ruleset & History**

* **`last_paths.json`** → remembers your last used file paths.
* **`history.json`** → stores past hypotheses (can be cleared via GUI).

---

## ❗ **Troubleshooting**

* **Tkinter Missing**:
  On Ubuntu/WSL: `sudo apt-get install -y python3-tk`
  On Windows: reinstall Python with Tcl/Tk enabled.

* **Popper Not Found**: The script auto-clones it to `~/popper/`. Check if `popper.py` exists.

* **LaTeX Rendering Fails**: Falls back to MathText automatically.

* **Permission Errors (WSL/Linux)**: Run with `sudo` if installation fails.

---

## 📌 **Next Steps / Roadmap**

* ✅ Add CLI full support.
* ✅ Add drag-and-drop .pl upload.
* ✅ Export hypotheses as PDF.

---

## 👨‍💻 **Author**

Developed by **\[Your Name]**
For academic and research use.

---
