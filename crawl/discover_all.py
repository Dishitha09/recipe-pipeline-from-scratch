from pathlib import Path
import subprocess

SITEMAPS_FILE = Path("data/sitemaps.txt")
OUTPUT_DIR = Path("data/discovered")

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

if not SITEMAPS_FILE.exists():
    raise FileNotFoundError("data/sitemaps.txt not found")

sitemaps = [
    line.strip()
    for line in SITEMAPS_FILE.read_text(encoding="utf-8").splitlines()
    if line.strip()
]

print(f"Found {len(sitemaps)} sitemap(s)\n")

for idx, sitemap in enumerate(sitemaps, start=1):

    domain = sitemap.split("/")[2]
    safe_name = domain.replace(".", "_")

    output_file = OUTPUT_DIR / f"{safe_name}.txt"

    print("=" * 60)
    print(f"[{idx}/{len(sitemaps)}]")
    print("Sitemap :", sitemap)
    print("Output  :", output_file)
    print("=" * 60)

    cmd = [
        "python",
        "-m",
        "crawl.url_discovery",
        "--sitemap",
        sitemap,
        "--allow-domain",
        domain,
        "--output",
        str(output_file)
    ]

    subprocess.run(cmd)

print("\nDISCOVERY COMPLETE")
print("Results saved in data/discovered/")