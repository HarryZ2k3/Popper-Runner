import sys
import subprocess
import platform
import shutil

# =======================
# ✅ ENSURE TKINTER BEFORE IMPORT
# =======================
def ensure_tkinter_before_import():
    try:
        import tkinter
        print("[OK] Tkinter available.")
    except ImportError:
        os_name = platform.system().lower()
        print("[INFO] Tkinter missing. Attempting to install...")
        try:
            if os_name == "linux":
                subprocess.check_call(["sudo", "apt-get", "update"])
                subprocess.check_call(["sudo", "apt-get", "install", "-y", "python3-tk"])
            elif os_name == "darwin":
                print("[INFO] On macOS, reinstall Python via Homebrew or the official installer to include Tkinter.")
            elif os_name == "windows":
                print("[INFO] On Windows, reinstall Python with Tcl/Tk support enabled.")
        except Exception as e:
            print(f"[ERROR] Tkinter installation failed: {e}")
        # Try importing again after install attempt
        try:
            import tkinter
            print("[OK] Tkinter successfully installed.")
        except ImportError:
            print("[FATAL] Tkinter is still unavailable. Exiting.")
            sys.exit(1)

ensure_tkinter_before_import()

# ✅ Safe to import now
import os
import re
import json
import threading
import webbrowser
from io import BytesIO
from datetime import datetime
from PIL import Image, ImageTk
import matplotlib

import tkinter as tk
from tkinter import scrolledtext, filedialog
import ttkbootstrap as ttk
from ttkbootstrap.constants import *

# ======================
# ✅ FULL LATEX RENDERING
# ======================
matplotlib.use("Agg")
matplotlib.rcParams["text.usetex"] = True
matplotlib.rcParams["font.family"] = "serif"

import matplotlib.pyplot as plt

# =======================
# ✅ CONSTANTS & SETTINGS
# =======================
REQUIRED_PY_LIBS = [
    "ttkbootstrap",
    "clingo",
    "pyswip",
    "bitarray",
    "python-sat[pblib,aiger]",
    "matplotlib",
    "pillow"
]
POPPER_GIT = "https://github.com/logic-and-learning-lab/popper.git"
DEFAULT_POPPER_PATHS = [
    "~/popper/popper.py",
    "~/popper/popper/popper.py",
    "~/popper/popper_ilp/popper.py"
]
LAST_PATHS_FILE = "last_paths.json"
HISTORY_FILE = "history.json"
POPPER_PATH = None
last_error_message = ""

SWI_PROLOG_URL = "https://www.swi-prolog.org/download/stable"
CLINGO_URL = "https://potassco.org/clingo/"

history_store = []  # session + loaded history
render_cache = {}
running = False  # ✅ Prevent multiple threads

# =======================
# ✅ FIXED FIRST-TIME SETUP HELPERS
# =======================
def ensure_pip():
    try:
        import pip
        print("[OK] Pip available.")
    except ImportError:
        print("[INFO] Pip not found. Installing...")
        subprocess.check_call([sys.executable, "-m", "ensurepip", "--upgrade"])
        subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", "pip"])

def install_missing_libs():
    IMPORT_MAPPING = {
        "pillow": "PIL",
        "python-sat": "pysat",
        "ttkbootstrap": "ttkbootstrap",
        "clingo": "clingo",
        "pyswip": "pyswip",
        "bitarray": "bitarray",
        "matplotlib": "matplotlib"
    }

    for pkg in REQUIRED_PY_LIBS:
        base_pkg = pkg.split("[")[0]
        import_name = IMPORT_MAPPING.get(base_pkg, base_pkg.replace("-", "_"))

        try:
            __import__(import_name)
            print(f"[OK] {pkg} already installed.")
        except ImportError:
            print(f"[INFO] Installing missing package: {pkg}")
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", pkg])
                print(f"[DONE] Installed: {pkg}")
            except Exception as e:
                print(f"[ERROR] Failed to install {pkg}: {e}")

def auto_install_dependencies(dep_name):
    os_name = platform.system().lower()
    try:
        if dep_name == "swipl":
            if os_name == "windows":
                webbrowser.open(SWI_PROLOG_URL)
            elif os_name == "linux":
                subprocess.check_call(["sudo", "apt-get", "update"])
                subprocess.check_call(["sudo", "apt-get", "install", "-y", "swi-prolog"])
            elif os_name == "darwin":
                subprocess.check_call(["brew", "install", "swi-prolog"])
        elif dep_name == "clingo":
            if os_name == "windows":
                webbrowser.open(CLINGO_URL)
            elif os_name == "linux":
                subprocess.check_call(["sudo", "apt-get", "install", "-y", "clingo"])
            elif os_name == "darwin":
                subprocess.check_call(["brew", "install", "clingo"])
        elif dep_name == "latex":
            if os_name == "windows":
                webbrowser.open("https://miktex.org/download")
            elif os_name == "linux":
                subprocess.check_call(["sudo", "apt-get", "update"])
                subprocess.check_call([
                    "sudo", "apt-get", "install", "-y",
                    "texlive-latex-base", "texlive-latex-recommended",
                    "texlive-latex-extra", "texlive-fonts-recommended",
                    "texlive-fonts-extra", "texlive-lang-european", "dvipng"
                ])
            elif os_name == "darwin":
                subprocess.check_call(["brew", "install", "--cask", "mactex"])
        elif dep_name == "git":
            if os_name == "linux":
                subprocess.check_call(["sudo", "apt-get", "update"])
                subprocess.check_call(["sudo", "apt-get", "install", "-y", "git"])
            elif os_name == "darwin":
                subprocess.check_call(["brew", "install", "git"])
            elif os_name == "windows":
                webbrowser.open("https://git-scm.com/download/win")
                print("[INFO] Please install Git manually on Windows.")
    except Exception as e:
        print(f"[WARNING] Automatic installation of {dep_name} failed: {e}")

def check_system_dependencies():
    if not shutil.which("swipl"):
        auto_install_dependencies("swipl")
    if not shutil.which("clingo"):
        auto_install_dependencies("clingo")
    if not shutil.which("latex") or not shutil.which("dvipng"):
        print("[WARNING] LaTeX not detected. Falling back to MathText.")
        matplotlib.rcParams["text.usetex"] = False

def check_or_install_popper():
    global POPPER_PATH
    if not shutil.which("git"):
        auto_install_dependencies("git")

    paths_cache = load_last_paths()
    if paths_cache.get("popper_path") and os.path.exists(paths_cache["popper_path"]):
        POPPER_PATH = paths_cache["popper_path"]
        return

    for path in DEFAULT_POPPER_PATHS:
        expanded = os.path.expanduser(path)
        if os.path.exists(expanded):
            POPPER_PATH = expanded
            save_last_paths(popper_path=expanded)
            return

    popper_dir = os.path.expanduser("~/popper")
    if not os.path.exists(popper_dir):
        subprocess.check_call(["git", "clone", "--depth", "1", POPPER_GIT, popper_dir])

    for root, _, files in os.walk(popper_dir):
        if "popper.py" in files:
            POPPER_PATH = os.path.join(root, "popper.py")
            save_last_paths(popper_path=POPPER_PATH)
            return

def save_last_paths(**paths):
    existing = load_last_paths()
    existing.update(paths)
    with open(LAST_PATHS_FILE, "w") as f:
        json.dump(existing, f)

def load_last_paths():
    return json.load(open(LAST_PATHS_FILE)) if os.path.exists(LAST_PATHS_FILE) else {}

def first_time_setup():
    print("\n[SETUP] Running first-time environment setup...")
    ensure_pip()
    install_missing_libs()
    check_system_dependencies()
    check_or_install_popper()
    print("[SETUP] Environment ready!\n")

# ✅ Run setup at the very beginning
first_time_setup()
# =======================
# ✅ HISTORY MANAGEMENT
# =======================
def load_history():
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return []
    return []

def save_history():
    with open(HISTORY_FILE, "w") as f:
        json.dump(history_store, f, indent=2)

def clear_history():
    global history_store
    history_store = []
    save_history()

# =======================
# ✅ LATEX HELPERS
# =======================
def latex_var(var):
    return f"V_{{{var[1:]}}}" if var.lower().startswith("v") and var[1:].isdigit() else var

def safe_parse_predicate(pred):
    pred = pred.strip()
    if "(" not in pred:
        return pred, []
    match = re.match(r"([a-zA-Z0-9_]+)\((.*)\)", pred)
    if not match:
        return pred, []
    name = match.group(1)
    args = [latex_var(a.strip()) for a in match.group(2).split(",") if a.strip()]
    return name, args

def translate_body_literal(literal):
    neg = literal.startswith("\\+")
    literal = literal.replace("\\+", "").strip()
    name, args = safe_parse_predicate(literal)
    ops = {
        ("add", 3): lambda a: f"{a[2]} = {a[0]} + {a[1]}",
        ("sub", 3): lambda a: f"{a[2]} = {a[0]} - {a[1]}",
        ("mult", 3): lambda a: f"{a[2]} = {a[0]} \\times {a[1]}",
        ("succ", 2): lambda a: f"{a[1]} = {a[0]} + 1",
        ("divisible", 2): lambda a: f"{a[0]} \\mod {a[1]} = 0",
        ("greater_than", 2): lambda a: f"{a[0]} > {a[1]}",
        ("less_than", 2): lambda a: f"{a[0]} < {a[1]}",
        ("eq", 2): lambda a: f"{a[0]} = {a[1]}",
        ("neq", 2): lambda a: f"{a[0]} \\neq {a[1]}",
    }
    expr = ops.get((name, len(args)), lambda a: f"{name}({', '.join(a)})" if a else name)(args)
    return f"\\lnot({expr})" if neg else expr

def popper_to_latex(hypothesis):
    latex_lines = []
    for raw in hypothesis.strip().splitlines():
        line = raw.strip().rstrip(".")
        if not line or line.startswith(("tp:", "Precision", "Recall", "Size", "FN:", "FP:", "TN:")):
            continue
        line = re.sub(r"^\d{2}:\d{2}:\d{2}\s+", "", line)
        if ":-" in line:
            head, body = map(str.strip, line.split(":-"))
            head_name, head_args = safe_parse_predicate(head)
            body_literals = [translate_body_literal(b.strip()) for b in body.split(",") if b.strip()]
            vars_set = {v for v in head_args} | {v for lit in body_literals for v in re.findall(r"[A-Z][a-zA-Z0-9_]*", lit)}
            quantifiers = f"\\forall {', '.join(vars_set)}\\ "
            latex_lines.append(f"{quantifiers}({head_name}({', '.join(head_args)}) \\Leftarrow " +
                               " \\land ".join(body_literals) + ")")
        else:
            name, args = safe_parse_predicate(line)
            latex_lines.append(f"{name}({', '.join(args)})")
    return latex_lines

def render_latex_to_image(latex_lines, base_font=14):
    cache_key = (tuple(latex_lines), base_font)
    if cache_key in render_cache:
        return render_cache[cache_key]
    num_lines = max(len(latex_lines), 1)
    font_size = max(8, base_font - (num_lines // 3))
    fig_height = max(2, 0.6 + 0.25 * num_lines)
    fig, ax = plt.subplots(figsize=(6, fig_height))
    ax.axis("off")
    try:
        for i, line in enumerate(latex_lines):
            ax.text(0.05, 1 - 0.12 * i, f"${line}$", fontsize=font_size, ha="left", va="top")
        buf = BytesIO()
        plt.savefig(buf, format="png", bbox_inches="tight", dpi=120)
        plt.close(fig)
        buf.seek(0)
        img = Image.open(buf)
        render_cache[cache_key] = img
        return img
    except Exception as e:
        print(f"[WARNING] LaTeX rendering failed ({e}). Falling back to MathText...")
        matplotlib.rcParams["text.usetex"] = False
        plt.close(fig)
        return render_latex_to_image(latex_lines, base_font)

# =======================
# ✅ POPPER EXECUTION
# =======================
def extract_solutions(stdout):
    solutions, current = [], []
    for line in stdout.splitlines():
        if any(tag in line for tag in ["SOLUTION", "New best hypothesis", "Best program"]):
            if current:
                solutions.append("\n".join(current))
                current = []
        elif line.strip() and (":-" in line or "." in line):
            current.append(line.strip())
    if current:
        solutions.append("\n".join(current))
    return solutions

def run_popper(bk, bias, exs, timeout, console_callback, result_callback, realtime=False, after=None):
    global last_error_message
    last_error_message = ""

    for f in [bk, bias, exs]:
        if not os.path.exists(f):
            console_callback(f"[ERROR] File '{f}' not found!\n", "red")
            return

    work_dir = "popper_tmp"
    os.makedirs(work_dir, exist_ok=True)
    for src, name in zip([bk, bias, exs], ["bk.pl", "bias.pl", "exs.pl"]):
        shutil.copy(src, os.path.join(work_dir, name))

    console_callback("[INFO] Running Popper...\n", "green")
    timeout_sec = int(re.sub(r"\D", "", timeout)) if timeout else None
    cmd = ["python3", "-W", "ignore::UserWarning", POPPER_PATH, work_dir]

    try:
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        stdout_lines, current_stdout = [], []
        for line in process.stdout:
            if not any(ignore in line for ignore in ["pkg_resources", "Clauses of", "discontiguous"]):
                stdout_lines.append(line)
                after(console_callback, line, "white")
                if realtime and (":-" in line or "." in line):
                    current_stdout.append(line.strip())
                    after(result_callback, popper_to_latex("\n".join(current_stdout)))
        process.wait(timeout=timeout_sec)
        if not realtime:
            solutions = extract_solutions("".join(stdout_lines))
            if solutions:
                for sol in solutions:
                    after(result_callback, popper_to_latex(sol))
            else:
                after(console_callback, "[WARNING] No hypothesis generated.\n", "yellow")
    except subprocess.TimeoutExpired:
        after(console_callback, f"[ERROR] Popper timed out after {timeout}\n", "red")
    finally:
        shutil.rmtree(work_dir, ignore_errors=True)
        after(console_callback, f"[INFO] Temporary folder '{work_dir}' deleted.\n", "green")

# =======================
# ✅ GUI
# =======================
def launch_gui():
    global history_store, running
    app = ttk.Window(themename="flatly")
    app.title("Popper ILP Runner")
    app.geometry("1000x900")
    app.minsize(900, 650)

    paths = load_last_paths()
    history_store = load_history()
    realtime_mode = tk.BooleanVar(value=False)

    def after(callback, *args):
        app.after(0, callback, *args)

    def open_file_dialog(entry, key):
        path = filedialog.askopenfilename(filetypes=[("Prolog Files", "*.pl")])
        if path:
            entry.delete(0, tk.END)
            entry.insert(0, path)
            status_bar.config(text=f"File selected: {os.path.basename(path)}")
            paths[key] = path
            save_last_paths(**paths)

    def update_console(text, color="white"):
        console.config(state="normal")
        console.insert(tk.END, text)
        console.see(tk.END)
        console.config(state="disabled")
        status_bar.config(text=f"[Console] {text.strip()[:60]}...")

    def update_results(latex_lines):
        img = render_latex_to_image(latex_lines)
        tk_img = ImageTk.PhotoImage(img)
        result_label.config(image=tk_img)
        result_label.image = tk_img
        if not realtime_mode.get():
            history_store.append({
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "hypotheses": latex_lines
            })
            save_history()
            refresh_history()
            status_bar.config(text=f"✅ Hypothesis Rendered (Total: {len(history_store)})")

    def refresh_history():
        history_box.config(state="normal")
        history_box.delete("1.0", tk.END)
        for i, item in enumerate(history_store, 1):
            history_box.insert(tk.END, f"#{i} - {item['timestamp']}\n" + "\n".join(item["hypotheses"]) + "\n\n")
        history_box.config(state="disabled")

    def run_thread():
        global running
        if running:
            status_bar.config(text="⚠ Already running!")
            return
        running = True
        progress.start()

        def finish():
            progress.stop()
            running = False

        threading.Thread(target=lambda: (run_popper(
            bk_entry.get(), bias_entry.get(), exs_entry.get(),
            timeout_entry.get(), update_console, update_results, realtime_mode.get(), after
        ), finish()), daemon=True).start()

    def clear_console():
        console.config(state="normal")
        console.delete("1.0", tk.END)
        console.config(state="disabled")
        status_bar.config(text="[Console cleared]")

    def clear_all_history():
        clear_history()
        refresh_history()
        status_bar.config(text="[History cleared]")

    def toggle_theme():
        theme = "darkly" if app.style.theme.name == "flatly" else "flatly"
        app.style.theme_use(theme)
        status_bar.config(text=f"Theme changed to: {theme}")

    def make_upload_zone(label, key):
        row = ttk.Frame(file_card)
        row.pack(fill="x", pady=10)
        ttk.Label(row, text=label, width=15).pack(side="left")
        entry = ttk.Entry(row, width=70)
        entry.pack(side="left", padx=5, fill="x", expand=True)
        entry.insert(0, paths.get(key, ""))
        zone = ttk.Label(row, text="Select file", bootstyle="secondary", anchor="center", width=18)
        zone.pack(side="left", padx=5)
        zone.bind("<Button-1>", lambda e: open_file_dialog(entry, key))
        return entry

    file_card = ttk.Labelframe(app, text="📂 File Upload", padding=15)
    file_card.pack(fill="x", padx=15, pady=10)
    bk_entry = make_upload_zone("BK File:", "bk")
    bias_entry = make_upload_zone("Bias File:", "bias")
    exs_entry = make_upload_zone("Examples File:", "exs")

    settings_card = ttk.Labelframe(app, text="⚙ Run Settings", padding=15)
    settings_card.pack(fill="x", padx=15, pady=10)
    setting_frame = ttk.Frame(settings_card)
    setting_frame.pack(fill="x")
    ttk.Label(setting_frame, text="Timeout (e.g., 300s):", width=20).pack(side="left")
    timeout_entry = ttk.Entry(setting_frame, width=10)
    timeout_entry.insert(0, "300s")
    timeout_entry.pack(side="left", padx=5)
    ttk.Checkbutton(setting_frame, text="Real-Time Auto-Refresh", variable=realtime_mode, bootstyle="info-round-toggle").pack(side="left", padx=10)
    ttk.Button(setting_frame, text="Run Popper", bootstyle="success", command=run_thread).pack(side="left", padx=10)
    ttk.Button(setting_frame, text="Clear Console", bootstyle="secondary-outline", command=clear_console).pack(side="left")
    ttk.Button(setting_frame, text="Clear History", bootstyle="danger-outline", command=clear_all_history).pack(side="left", padx=5)
    ttk.Button(setting_frame, text="Toggle Theme", bootstyle="info-outline", command=toggle_theme).pack(side="left", padx=10)

    progress = ttk.Progressbar(setting_frame, bootstyle="info-striped", mode="indeterminate")
    progress.pack(side="left", padx=10)

    tabs = ttk.Notebook(app, bootstyle="primary")
    tabs.pack(fill="both", expand=True, padx=15, pady=10)
    console_tab = ttk.Frame(tabs)
    tabs.add(console_tab, text="🖥 Console Output")
    console = scrolledtext.ScrolledText(console_tab, height=12, state="disabled",
                                        background="#212529", foreground="#f8f9fa")
    console.pack(fill="both", expand=True)

    results_tab = ttk.Frame(tabs)
    tabs.add(results_tab, text="🔬 Learned Hypotheses")
    result_label = ttk.Label(results_tab)
    result_label.pack(fill="both", expand=True)

    history_tab = ttk.Frame(tabs)
    tabs.add(history_tab, text="📜 History")
    history_box = scrolledtext.ScrolledText(history_tab, height=12, state="disabled")
    history_box.pack(fill="both", expand=True)
    refresh_history()

    status_bar = ttk.Label(app, text="Ready", anchor="w", bootstyle="secondary")
    status_bar.pack(fill="x", side="bottom")
    app.mainloop()

# =======================
# ✅ CLI OR GUI
# =======================
if __name__ == "__main__":
    if "--gui" in sys.argv:
        launch_gui()
    else:
        print("Run with --gui for GUI mode!")
