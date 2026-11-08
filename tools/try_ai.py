"""Measures the precision and speed of the local model on hand-labelled titles.
Usage: python tools/try_ai.py [model]"""
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from pw import ai  # noqa: E402
from pw.rules import split_name  # noqa: E402

RAM, GPU, SSD, CPU = "32 GB ram ddr5 6000 CL30", "RTX 5070 Ti", "SSD 1TB", "Ryzen 9 9900X"
# product searched for, title, right type, same model (None = does not count), values the title really states
CASES = [
    (RAM, "Patriot Viper Venom DDR5 32GB (2 x 16GB) 6000MT/s Kit di Memoria Desktop UDIMM", "product", True, {"CL": None}),
    (RAM, "Corsair Vengeance RGB CMH32GX5M2E6000C36 32 GB DDR5 a 6000 MHz", "product", True, {"CL": 36}),
    (RAM, "Patriot Viper DDR5-6000 CL30 Black", "product", True, {"GB": None, "CL": 30}),
    (RAM, "G.Skill Ripjaws M5 DDR5-6000 32 GB (2x 16 GB Kit), CL30, Schwarz", "product", True, {"CL": 30}),
    (RAM, "Komputer Game X G100 Lite, Core i5-14400F, 32 GB DDR5 6000, RTX 5070, 1 TB SSD", "whole_computer", None, {}),
    (RAM, "Lenovo Legion Pro 5 Gaming Laptop Ryzen 7 32GB DDR5 6000MHz 1TB", "whole_computer", None, {}),
    (RAM, "Raffreddatore per memoria RAM DDR5 con dissipatore in alluminio 32GB", "accessory", None, {}),
    (RAM, "Kingston FURY 32GB DDR5 6000 CL30 usata, come nuova", "used", None, {}),
    (RAM, "Pamięć RAM Kingston Fury Beast DDR5 32 GB 6000 MHz CL30 zestaw 2x16", "product", True, {"CL": 30}),
    (RAM, "삼성 DDR5 32GB 6000 CL30 데스크탑 메모리 패키지", "product", True, {"CL": 30}),
    (RAM, "ASUS TUF Gaming B850-PLUS scheda madre supporta DDR5 6000", "other_product", False, {}),
    (RAM, "Samsung SSD 990 Pro 1 TB NVMe PCIe 4.0", "other_product", False, {}),
    (GPU, "MSI GeForce RTX 5070 Ti 16G Ventus 3X OC", "product", True, {}),
    (GPU, "ASUS Prime RTX5070TI O16G Scheda Grafica NVIDIA", "product", True, {}),
    (GPU, "Gigabyte GeForce RTX 5070 Eagle OC 12G", "product", False, {}),
    (GPU, "MSI GeForce RTX 4070 Ti Super 16G", "product", False, {}),
    (GPU, "Cavo di alimentazione 12VHPWR per RTX 5070 Ti", "accessory", None, {}),
    (GPU, "Staffa di supporto per scheda video RTX 5070 Ti", "accessory", None, {}),
    (GPU, "PC Gamer Ryzen 7 9700X RTX 5070 Ti 32GB 2TB", "whole_computer", None, {}),
    (GPU, "ASUS TUF Gaming A16 portatile RTX 5070 Ti Ryzen 9", "whole_computer", None, {}),
    (GPU, "Karta graficzna MSI RTX 5070 Ti używana", "used", None, {}),
    (GPU, "ゲーミング グラフィックボード RTX 5070 Ti 16GB 中古", "used", None, {}),
    (GPU, "技嘉 RTX 5070 Ti 16G 显卡 全新", "product", True, {}),
    (SSD, "Samsung 990 EVO Plus SSD 1TB NVMe M.2", "product", True, {}),
    (SSD, "WD Blue HDD 1TB disco rigido 3.5", "other_product", False, {}),
    (SSD, "Dissipatore per SSD M.2 NVMe", "accessory", None, {}),
    (SSD, "Box esterno per SSD M.2 USB-C", "accessory", None, {}),
    (CPU, "AMD Ryzen 9 9900X processore 12 core AM5 box", "product", True, {}),
    (CPU, "AMD Ryzen 9 9950X processore 16 core", "product", False, {}),
    (CPU, "AMD 9900X CPU tray", "product", True, {}),
    (CPU, "Dissipatore a liquido per AMD Ryzen 9 9900X", "accessory", None, {}),
    (CPU, "PC Desktop Ryzen 9 9900X 64GB RTX 5080", "whole_computer", None, {}),
]
installed = ai.status(5)
model = sys.argv[1] if len(sys.argv) > 1 else ai.choose_model("", installed["modelli"])
print("modello:", model)
ok_kind = val_ok = val_n = false_alarm = caught = bad_total = 0
times = []
ACTED_ON = ("accessory", "whole_computer", "used")
for name, title, kind, same, values in CASES:
    core, specs = split_name(name)
    res, sec = ai.timed(model, core, specs, title, timeout=120)
    times.append(sec)
    if res is None:
        print(f"  NO ANSWER {title[:60]}")
        continue
    ok_kind += res["kind"] == kind
    flagged = res["kind"] in ACTED_ON
    bad_total += kind in ACTED_ON
    caught += flagged and kind in ACTED_ON
    false_alarm += flagged and kind not in ACTED_ON
    for unit, want in values.items():
        val_n += 1
        val_ok += res["values"].get(unit) == want
    mark = "" if res["kind"] == kind else "  <<<"
    print(f"{sec:5.1f}s {res['kind'][:14]:14} {res['values']} | {title[:62]}{mark}", flush=True)
print(f"\nright type {ok_kind}/{len(CASES)} | values {val_ok}/{val_n}")
print(f"accessories, whole PCs and used items recognized {caught}/{bad_total} | false alarms {false_alarm}")
print(f"seconds: first {times[0]:.1f}, average of the others {sum(times[1:]) / (len(times) - 1):.1f}, maximum {max(times):.1f}")
