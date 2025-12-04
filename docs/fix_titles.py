import os

SRC = "source"

def titleize(filename):
    """Gera um título baseado no nome do arquivo."""
    name = os.path.splitext(os.path.basename(filename))[0]
    title = name.replace("_", " ").replace("-", " ").title()
    return title

for root, dirs, files in os.walk(SRC):
    for f in files:
        if f.endswith(".rst"):
            path = os.path.join(root, f)
            with open(path, "r") as file:
                content = file.read()

            # se já houver título no início, ignore
            if content.lstrip().startswith("=") or "\n=" in content.splitlines()[1:2]:
                continue

            title = titleize(f)
            header = f"{title}\n{'=' * len(title)}\n\n"

            with open(path, "w") as file:
                file.write(header + content)

            print(f"[OK] Título adicionado a: {path}")
