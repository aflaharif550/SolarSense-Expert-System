# SolarSense — Setup & Deployment Guide (Beginner Friendly)

This guide takes you from the downloaded ZIP to a live public URL you can open during your viva.

---

## PART A — Run SolarSense on your laptop

### Step 1: Install Python (one time)

1. Go to https://www.python.org/downloads/ and download **Python 3.12** (3.10–3.13 also work).
2. Run the installer. **Important (Windows): tick "Add python.exe to PATH"** at the bottom of the first screen, then click *Install Now*.
3. Check it worked: open **Command Prompt** (Windows) or **Terminal** (Mac) and type:
   ```
   python --version
   ```
   You should see something like `Python 3.12.x`. On Mac, use `python3` instead of `python` everywhere in this guide.

### Step 2: Install VS Code (one time)

1. Download from https://code.visualstudio.com/ and install it.
2. Open VS Code → click the **Extensions** icon on the left (four squares) → search **Python** → install the one by **Microsoft**.

### Step 3: Extract the ZIP

1. Find `SolarSense.zip` in your Downloads folder.
2. **Windows:** right-click → **Extract All…** → choose a simple place such as `C:\Projects\` → **Extract**.
   **Mac:** double-click the ZIP.
3. You should now have a folder `SolarSense` containing `app.py`, `requirements.txt` and other folders.
   If you see `SolarSense\SolarSense\app.py` (a folder inside a folder), use the **inner** folder.

### Step 4: Open the project in VS Code

1. Open VS Code → **File → Open Folder…** → select the `SolarSense` folder (the one containing `app.py`) → **Select Folder**.
2. If asked "Do you trust the authors?", click **Yes, I trust the authors**.
3. Open a terminal inside VS Code: menu **Terminal → New Terminal**. It opens at the bottom, already inside your project folder.

### Step 5: Create a virtual environment (recommended)

A virtual environment keeps this project's libraries separate from others.

**Windows:**
```
python -m venv .venv
.venv\Scripts\activate
```
**Mac / Linux:**
```
python3 -m venv .venv
source .venv/bin/activate
```
You will see `(.venv)` at the start of the terminal line. Run the activate command again each time you open a new terminal.

> Windows error "running scripts is disabled on this system"? Run this once, then try activating again:
> `Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned` (answer **Y**).

### Step 6: Install the required libraries

```
pip install -r requirements.txt
```
This installs **streamlit**, **pandas** and **plotly**. It needs internet and takes 1–3 minutes.

### Step 7: (Optional) Run the automated tests

```
python -m unittest discover tests -v
```
All 21 tests should say `ok`, ending with `OK`. One test proves that every one of the 129 rules fires in at least one sample profile.

### Step 8: Run the application

```
streamlit run app.py
```
Your browser opens automatically at **http://localhost:8501**. If it does not, copy that address into your browser.
The first time, Streamlit may ask for an email in the terminal — just press **Enter** to skip.

To stop the app: click the terminal and press **Ctrl + C**.

### Step 9: Test the app locally

1. **Home** → click **Start assessment**.
2. On **Assessment**, choose a sample profile (e.g. *Karachi family home*) → **Load profile**.
3. Look through the five tabs, then click **Run SolarSense analysis**.
4. **Results** opens: check the KPI cards, the four tabs and **Download report**.
5. Open **Diagnosis** (or click **Open full diagnosis** on Results) to see the situation profile and the problems detected, each with its rule ID.
6. Open **Explanation** to see the reasoning chain (each rule that fired, in order).
7. Open **Knowledge Base** to search all 129 rules.
8. Try other profiles. *Gwadar flat* and *Rawalpindi flat* show the "not feasible" path.

### Common local errors and fixes

| Problem | Fix |
|---|---|
| `'python' is not recognized` | Python is not on PATH. Reinstall and tick **Add python.exe to PATH**, or use `py` instead of `python`. |
| `'streamlit' is not recognized` | Activate the virtual environment (Step 5) or run `python -m streamlit run app.py`. |
| `ModuleNotFoundError: No module named 'plotly'` (or pandas/streamlit) | Run `pip install -r requirements.txt` with the virtual environment activated. |
| `ModuleNotFoundError: No module named 'engine'` | You are in the wrong folder. The terminal must be in the folder that contains `app.py` (use `cd path\to\SolarSense`). |
| `FileNotFoundError: data/parameters.json` | Same cause: run the command from the project folder, and don't move files out of `data/`. |
| `Port 8501 is already in use` | Another Streamlit is running. Close it, or run `streamlit run app.py --server.port 8502`. |
| Browser shows a blank page | Refresh (F5). Try Chrome or Edge. |
| pip is very slow or fails | Check internet; try `python -m pip install --upgrade pip` and run the install again. |

---

## PART B — Deploy to the internet (Streamlit Community Cloud, free)

Your instructor needs a public URL that works from any network. Streamlit Community Cloud hosts the app for free directly from GitHub.

### Step 1: Create a GitHub account

1. Go to https://github.com → **Sign up**.
2. Enter email, password and a username (it will appear in your repository link, so keep it professional).
3. Verify your email with the code GitHub sends.

### Step 2: Create a new repository

1. Logged in to GitHub, click **+** (top right) → **New repository**.
2. **Repository name:** `solarsense-expert-system`
3. **Description:** `Rule-based expert system for solar decisions (Streamlit)`
4. Choose **Public** (simplest for Streamlit Cloud).
5. Leave "Add a README" **unticked** (the project already has one).
6. Click **Create repository**.

### Step 3: Upload the project files

**Option 1 — Upload in the browser (easiest)**

1. On the new empty repository page, click the link **uploading an existing file**.
2. Open your `SolarSense` folder in File Explorer / Finder, select **everything inside it**
   (`app.py`, `requirements.txt`, `README.md`, and the folders `engine`, `knowledge_base`, `ui`, `data`, `tests`, `tools`, `docs`, `.streamlit`)
   and **drag them into the browser page**. Do **not** upload the `.venv` folder.
3. Wait until all files are listed, then click **Commit changes**.
4. Check: the repository's main page must show `app.py` and `requirements.txt` **at the top level**, not inside another folder.

> **Hidden `.streamlit` folder:** Windows/Mac may hide folders starting with a dot.
> Windows: File Explorer → **View → Show → Hidden items**. Mac: press **Cmd + Shift + .** in Finder.
> If it still won't upload, it's not critical (it only sets the theme colours). You can create it on GitHub:
> **Add file → Create new file**, name it `.streamlit/config.toml`, paste the contents of your local file, and **Commit**.

**Option 2 — Git commands (if you have Git installed)**

```
git init
git add .
git commit -m "SolarSense expert system"
git branch -M main
git remote add origin https://github.com/YOUR-USERNAME/solarsense-expert-system.git
git push -u origin main
```

### Step 4: Connect GitHub to Streamlit Community Cloud

1. Go to https://share.streamlit.io
2. Click **Continue with GitHub** and sign in.
3. Click **Authorize** so Streamlit can read your repositories.
4. Complete the short profile form if asked.

### Step 5: Deploy the app

1. Click **Create app** (top right).
2. When asked if you already have an app, choose **Yup, I have an app**.
3. Fill in:
   - **Repository:** `YOUR-USERNAME/solarsense-expert-system`
   - **Branch:** `main`
   - **Main file path:** `app.py`
   - **App URL (optional):** type a short name such as `solarsense-pk` → your link becomes `https://solarsense-pk.streamlit.app` (if the name is taken, try another).
4. Click **Advanced settings** → **Python version: 3.12** → **Save**.
5. Click **Deploy**. You'll see a "baking" screen with build logs. The first deployment takes about 2–5 minutes.

### Step 6: Get your public URL

When the build finishes, SolarSense opens in the browser. The address bar shows your public link, for example
`https://solarsense-pk.streamlit.app`. Copy it, put it in your `README.md`, your report and your viva slides.

### Step 7: Verify it works over the internet (WAN)

1. On your phone, **turn off Wi-Fi and use mobile data**, then open the link. If it loads, it is publicly reachable.
2. Open it in a private/incognito window on another computer (you should not need to log in).
3. Run one sample profile end-to-end to confirm the engine works online.

### Step 8: Update the app after changing code

The deployed app redeploys automatically whenever GitHub changes.

- **Browser method:** open the file on GitHub → click the **pencil (Edit)** icon → change → **Commit changes**.
  Or **Add file → Upload files** to replace a file with your updated version.
- **Git method:** `git add .` → `git commit -m "describe change"` → `git push`
- Wait about one minute and refresh the app. If it does not update, open https://share.streamlit.io → click **⋮** next to your app → **Reboot**.
- Changing `data/parameters.json` (prices, export rate) updates the app the same way.

### Deployment troubleshooting

| Problem | Fix |
|---|---|
| "This app has gone to sleep due to inactivity" | Free apps sleep when nobody visits for a while. Click **Yes, get this app back up!** and wait about 30–60 s. **Open your link a few minutes before your viva** to wake it. |
| Error mentioning `ModuleNotFoundError` | `requirements.txt` is missing or not at the top level of the repository. |
| `FileNotFoundError` for `data/parameters.json` | The `data` folder was not uploaded. Upload it with both JSON files inside. |
| "Main module does not exist" | Main file path must be exactly `app.py`, and `app.py` must be at the top level (not in a subfolder). |
| Repository not in the list | Make sure it is **Public**, or re-authorize GitHub at share.streamlit.io. |
| Any other error | On the app page click **Manage app** (bottom right) to read the logs; the last red lines show the cause. |

---

## PART C — Viva-day checklist

- [ ] Open the live link 5–10 minutes before your slot (wakes the app).
- [ ] Rehearse one demo: load *Karachi family home* → Run → Results → Explanation.
- [ ] Keep `docs/Rule_Table.md` handy to answer "show me rule R058".
- [ ] Be ready to show the Knowledge Base page (all 129 rules), and that rules live separately from the engine.
- [ ] Have the app running locally as a backup in case campus Wi-Fi fails.
