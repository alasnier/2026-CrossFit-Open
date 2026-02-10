# scripts/apply_diffs.py
import json
import os

if os.path.exists("diffs.json"):
    diffs = json.load(open("diffs.json", encoding="utf-8"))
    for d in diffs:
        p = d["path"]
        if os.path.dirname(p):
            os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "w", encoding="utf-8") as f:
            f.write(d["content_after"])
    print(f"[apply_diffs] {len(diffs)} fichier(s) appliqué(s)")
else:
    print("[apply_diffs] Aucun diffs.json trouvé")
