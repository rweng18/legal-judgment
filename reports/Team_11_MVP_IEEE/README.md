# Build the IEEE report

Read the [MVP report PDF](Team11_MVP_report.pdf) or edit [the LaTeX source](main.tex). The saved checkpoint PDF has resolved table, figure and citation references.

From this directory, run:

```powershell
latexmk -pdf -interaction=nonstopmode -halt-on-error main.tex
```

This updates `main.pdf` and automatically repeats LaTeX until cross-references stabilize. A single `pdflatex` pass from a clean folder can produce `Table ??`, `Figure ??`, and unresolved citations even though a PDF is written. If using `pdflatex` directly, repeat it until the log has no undefined-reference or rerun warnings.

After checking a new build, copy `main.pdf` to `Team11_MVP_report.pdf` to refresh the versioned checkpoint PDF. Auxiliary build files are ignored by Git.

Expected numbering is Tables I–V (splits, lengths, model results, random-removal controls, bootstrap intervals) and Figure 1 (confusion matrices). IEEE style uses Roman numerals for tables and Arabic numerals for figures.

Keep `main.tex`, all four `*_table.tex` files and the `images` folder together. The editor preview and the saved PDF are separate outputs; this command refreshes the PDF on disk.
