import sys, zipfile, pathlib, shutil
root = pathlib.Path(sys.argv[1])
vendor = root / "backend" / "vendor"
vendor.mkdir(parents=True, exist_ok=True)
n = 0
for whl in sorted((root / ".wheels").glob("*.whl")):
    with zipfile.ZipFile(whl) as z:
        for info in z.infolist():
            if info.filename.split("/")[0].endswith(".dist-info"):
                continue
            if info.filename.endswith("/"):
                continue
            target = vendor / info.filename
            target.parent.mkdir(parents=True, exist_ok=True)
            with z.open(info) as src, open(target, "wb") as dst:
                shutil.copyfileobj(src, dst)
    n += 1
print("extracted", n, "wheels ->", vendor)