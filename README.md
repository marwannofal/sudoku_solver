# Sudoku Solver Web App

A responsive web‐based Sudoku solver powered by FastAPI, OR-Tools (CP-SAT), and MongoDB for caching.
Enter any valid 9×9 Sudoku puzzle in your browser, click **Solve**, and get an instant solution.
Subsequent solves for the same puzzle load directly from MongoDB cache for maximum performance.

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Installation & Setup](#installation--setup)
3. [Running the App](#running-the-app)
4. [Sample to play](#Sample-to-play)
5. [License](#license)

---

## Prerequisites

1. **Python 3.8+**
2. **MongoDB** (version 4.0+ recommended)
   - Ensure a local MongoDB instance is running on `mongodb://localhost:27017/` (or adjust `MONGO_URI` as needed).
3. **Git** (optional, for cloning the repo)

---

## Installation & Setup

##### 1. Clone the repository** (or download the source):

   git clone https://github.com/marwannofal/sudoku_solver.git
   cd sudoku_solver

2. (Optional) Create and activate a virtual environment (highly recommended):
    python3 -m venv env
    source env/bin/activate     # On Linux/macOS
    env\Scripts\activate        # On Windows (PowerShell)

3. Install Python dependencies:
    pip install -r req.txt

4. Ensure MongoDB is running
##### By default, the app expects MongoDB at mongodb://localhost:27017/. If your setup is different, export the MONGO_URI environment variable:
    export MONGO_URI="mongodb://username:password@hostname:27017/"
##### On Windows PowerShell, use:
    setx MONGO_URI "mongodb://username:password@hostname:27017/"

## Running the App
##### 1. Start the FastAPI server using Uvicorn:
    uvicorn app:app --reload
##### 3. Open your browser at:
    http://127.0.0.1:8000/
3. Use the Sudoku solver

    - Type digits 1–9 into any of the 9×9 cells for your given clues.

    - Leave blank squares empty (interpreted as 0).

    - Click Solve → the board will fill in the computed solution.

    - Click Clear to reset the board at any time.

4. Caching behavior
    - The first time you solve a unique puzzle, OR-Tools CP-SAT will run (may take a few hundred milliseconds).
    - That puzzle + solution pair is stored in MongoDB.
    - Subsequent attempts to solve the same puzzle will return the cached result in just a few milliseconds.

## Sample to play
- There is a sample to play the game look at the you should see it or clik here [sample to play](sample_to_play.txt)

## License
This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.



