import os
from radon.cli import Config
from radon.cli.harvest import CCHarvester, RawHarvester, MIHarvester
from radon.complexity import SCORE
import json

work_dir = os.getcwd()
excludes = ["tests", "dist", "external_libraries", "setup", "ui"]
excludes = [os.path.join(work_dir, e, r"*") for e in excludes]
excludes = ",".join(excludes)
print(excludes)

config = Config(
    exclude=excludes,
    ignore="",
    order=SCORE,
    no_assert=False,
    show_closures=False,
    show_complexity=True,
    total_average=True,
    min='A',
    max='F',
    multi=2,
    summary=True
)

cc = CCHarvester([os.getcwd()], config)
raw = RawHarvester([os.getcwd()], config)
mi = MIHarvester([os.getcwd()], config)

for key, value in json.loads(cc.as_json()).items():
    print(f"File: {os.path.basename(key)}")
    print(f"{' ' * 4}{'name':32} |{'type':10} |{'rank'} |{'complexity'}")
    print("-" * 100)
    for val in value:

        
        if val['type'] == "method":
            pass
        else:
            print(f"{' ' * 4}{val['name']:32} |{val['type']:10} |{val['rank']:4} "
                  f"|{val['complexity']}/100")

        if val['type'] == "class":
            val["methods"].sort(key=lambda x: x["complexity"], reverse=True)
            for v in val["methods"]:
                print(f"{' ' * 8}{v['name']:28} |{v['type']:10} |{v['rank']:4} "
                      f"|{v['complexity']}/100")
    #print(value)
    print("_" * 170)
    #print(os.path.basename(line[0]))


for key, value in json.loads(mi.as_json()).items():
    print(f"File: {os.path.basename(key)}")
    print(value)

for key, value in json.loads(raw.as_json()).items():
    print(f"File: {os.path.basename(key)}")
    print(value)