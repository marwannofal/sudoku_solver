from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List
from ortools.sat.python import cp_model
from pymongo import MongoClient
import uvicorn
import os

app = FastAPI()

"""Serve index.html at GET "/" """
@app.get("/", response_class=FileResponse)
def read_index():
    return FileResponse(os.path.join("static", "index.html"))

app.mount("/static", StaticFiles(directory="static"), name="static")

"""Pydantic models for request/response"""

class PuzzleIn(BaseModel):
    puzzle: List[List[int]]  # Expect 9×9 nested list of ints (0–9).


class SolutionOut(BaseModel):
    solution: List[List[int]]  # 9×9 nested list of ints (1–9)

"""MongoDB Setup"""
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
client = MongoClient(MONGO_URI)
db = client["sudoku_db"]
coll = db["puzzles"]

coll.create_index("puzzle", unique=True)

"""Helpers: Convert board ↔ string key"""
def puzzle_to_key(board: List[List[int]]) -> str:
    """
    Flatten a 9×9 board into an 81-character string, row-major.
    E.g. [[5,3,0,...], ...] → "530070000600195000..."
    """
    return "".join(str(cell) for row in board for cell in row)


def key_to_board(key: str) -> List[List[int]]:
    """
    Convert an 81-character string back into a 9×9 list of ints.
    """
    flat = [int(ch) for ch in key]
    return [flat[i * 9 : (i + 1) * 9] for i in range(9)]


"""Helper: Validate initial board has shape 9×9 and no duplicates"""
def is_valid_placement(board: list[list[int]], r: int, c: int, num: int) -> bool:
    # Check the row and column
    for k in range(9):
        if board[r][k] == num or board[k][c] == num:
            return False
    # Check the 3×3 block
    br = (r // 3) * 3
    bc = (c // 3) * 3
    for i in range(br, br + 3):
        for j in range(bc, bc + 3):
            if board[i][j] == num:
                return False
    return True


def is_initial_board_valid(board: list[list[int]]) -> bool:
    """
    1) Check that `board` is 9 rows of length 9, each entry int in 0..9
    2) For each nonzero entry, temporarily clear it and make sure re-placing is valid.
    """
    # 1) Check shape and range
    if len(board) != 9:
        return False
    for row in board:
        if not isinstance(row, list) or len(row) != 9:
            return False
        for val in row:
            if not isinstance(val, int) or val < 0 or val > 9:
                return False

    # 2) Check duplicates among nonzero givens
    for r in range(9):
        for c in range(9):
            val = board[r][c]
            if val == 0:
                continue
            board[r][c] = 0
            if not is_valid_placement(board, r, c, val):
                board[r][c] = val
                return False
            board[r][c] = val

    return True


"""Internal: Solve with OR-Tools CP-SAT"""
def solve_with_ortools(puzzle: list[list[int]]) -> list[list[int]] | None:
    model = cp_model.CpModel()
    cell = {}

    # Create 9×9 IntVars in [1..9]
    for r in range(9):
        for c in range(9):
            cell[(r, c)] = model.NewIntVar(1, 9, f"cell_{r}_{c}")

    # Fix the given clues
    for r in range(9):
        for c in range(9):
            if puzzle[r][c] != 0:
                model.Add(cell[(r, c)] == puzzle[r][c])

    # AllDifferent for each row
    for r in range(9):
        model.AddAllDifferent([cell[(r, c)] for c in range(9)])

    # AllDifferent for each column
    for c in range(9):
        model.AddAllDifferent([cell[(r, c)] for r in range(9)])

    # AllDifferent for each 3×3 block
    for br in range(3):
        for bc in range(3):
            block_vars = []
            for dr in range(3):
                for dc in range(3):
                    rr = br * 3 + dr
                    cc = bc * 3 + dc
                    block_vars.append(cell[(rr, cc)])
            model.AddAllDifferent(block_vars)

    # Solve with a time limit
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = 10.0
    solver.parameters.num_search_workers = 8
    status = solver.Solve(model)

    if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        solution = [[0] * 9 for _ in range(9)]
        for r in range(9):
            for c in range(9):
                solution[r][c] = int(solver.Value(cell[(r, c)]))
        return solution

    return None


"""POST /solve endpoint"""
@app.post("/solve", response_model=SolutionOut)
@app.post("/solve", response_model=SolutionOut)
def solve_endpoint(payload: PuzzleIn):
    puzzle = payload.puzzle

    # (A) Validate shape and no duplicate givens
    board_copy = [row[:] for row in puzzle]
    if not is_initial_board_valid(board_copy):
        raise HTTPException(status_code=400, detail="Invalid puzzle: ensure 9×9 and no duplicates.")

    # (B) Compute cache key (flattened row-major string)
    puzzle_key = puzzle_to_key(puzzle)

    # (C) Check MongoDB for existing solution
    doc = coll.find_one({"puzzle": puzzle_key})
    if doc:
        # Return cached solution
        sol_key = doc["solution"]
        solution = key_to_board(sol_key)
        return {"solution": solution}

    # (D) Not in cache → solve with OR-Tools
    solution = solve_with_ortools(puzzle)
    if solution is None:
        raise HTTPException(status_code=400, detail="No solution exists for the given puzzle.")

    # (E) Store new puzzle→solution pair
    sol_key = puzzle_to_key(solution)
    new_doc = {"puzzle": puzzle_key, "solution": sol_key}
    try:
        coll.insert_one(new_doc)
    except Exception as e:
        # In case of a race‐condition (another process inserted simultaneously),
        # ignore the duplicate‐key error (104) and continue.
        # Otherwise, re‐raise.
        if hasattr(e, "code") and e.code == 11000:
            pass
        else:
            raise

    # (F) Return the computed solution
    return {"solution": solution}

"""Run with: uvicorn app:app --reload"""
if __name__ == "__main__":
    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=True)
