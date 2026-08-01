from pathlib import Path

PACKAGES = [
    "src/f1_platform",
    "src/f1_platform/ingestion",
    "src/f1_platform/storage",
    "src/f1_platform/analysis",
    "src/f1_platform/analysis/telemetry",
    "src/f1_platform/analysis/timing",
    "src/f1_platform/analysis/strategy",
    "src/f1_platform/analysis/championship",
    "src/f1_platform/analysis/historical",
    "src/f1_platform/export",
    "src/f1_platform/utils",
]

PLAIN_DIRS = ["tests", "scripts", "data/cache", "frontend", ".github/workflows"]

for pkg in PACKAGES:
    p = Path(pkg)
    p.mkdir(parents=True, exist_ok=True)
    (p / "__init__.py").touch()

for d in PLAIN_DIRS:
    Path(d).mkdir(parents=True, exist_ok=True)

Path("data/.gitkeep").touch()
print("Scaffolding Python concluído com sucesso!")
