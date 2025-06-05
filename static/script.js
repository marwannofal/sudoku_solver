// static/script.js

document.addEventListener("DOMContentLoaded", () => {
  const boardContainer = document.getElementById("board");
  const solveBtn = document.getElementById("solveBtn");
  const clearBtn = document.getElementById("clearBtn");
  const statusP = document.getElementById("status");

  // 1) Build a 9×9 grid of <input> elements
  for (let r = 0; r < 9; r++) {
    for (let c = 0; c < 9; c++) {
      const inp = document.createElement("input");
      inp.type = "text";
      inp.maxLength = 1;
      inp.id = `cell-${r}-${c}`;
      inp.autocomplete = "off";
      inp.pattern = "[1-9]";

      // Only allow digits 1–9 on keypress
      inp.addEventListener("keypress", (e) => {
        if (!/[1-9]/.test(e.key)) {
          e.preventDefault();
        }
      });

      // If user pastes invalid content, clear it
      inp.addEventListener("input", (e) => {
        if (!/^[1-9]$/.test(e.target.value)) {
          e.target.value = "";
        }
      });

      boardContainer.appendChild(inp);
    }
  }

  // 2) Clear button: wipe all cells and status
  clearBtn.addEventListener("click", () => {
    for (let r = 0; r < 9; r++) {
      for (let c = 0; c < 9; c++) {
        document.getElementById(`cell-${r}-${c}`).value = "";
      }
    }
    statusP.textContent = "";
  });

  // 3) Solve button: collect puzzle, POST to /solve, fill solution
  solveBtn.addEventListener("click", async () => {
    const puzzle = [];
    let validInput = true;

    // Build a 9×9 nested array of ints
    for (let r = 0; r < 9; r++) {
      const rowArr = [];
      for (let c = 0; c < 9; c++) {
        const val = document.getElementById(`cell-${r}-${c}`).value;
        if (val === "") {
          rowArr.push(0);
        } else {
          const d = parseInt(val, 10);
          if (isNaN(d) || d < 1 || d > 9) validInput = false;
          rowArr.push(d);
        }
      }
      puzzle.push(rowArr);
    }

    if (!validInput) {
      statusP.textContent = "⚠️ Please enter only digits 1–9 or leave blank.";
      return;
    }

    solveBtn.disabled = true;
    clearBtn.disabled = true;
    statusP.textContent = "🕐 Solving… please wait";

    try {
      const resp = await fetch("/solve", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ puzzle }),
      });

      const data = await resp.json();
      if (!resp.ok) {
        throw new Error(data.detail || `Server returned ${resp.status}`);
      }

      // Fill in the solution
      const sol = data.solution;
      for (let r = 0; r < 9; r++) {
        for (let c = 0; c < 9; c++) {
          document.getElementById(`cell-${r}-${c}`).value = sol[r][c];
        }
      }
      statusP.textContent = "✅ Solution loaded!";
    } catch (error) {
      console.error("Error solving Sudoku:", error);
      statusP.textContent = `❌ ${error.message}`;
    } finally {
      solveBtn.disabled = false;
      clearBtn.disabled = false;
    }
  });
});
