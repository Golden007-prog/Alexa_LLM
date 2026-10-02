"""Copy the en-IN interaction model to every other locale in skill.json.

The skill speaks the same English in en-IN, en-US and en-GB, so one model
is edited (en-IN, the primary locale) and copied. tests/test_flows.py fails
if the copies drift.

    python scripts/sync_locales.py
"""
import json
import os
import shutil

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODELS = os.path.join(ROOT, "skill-package", "interactionModels", "custom")


def main():
    with open(os.path.join(ROOT, "skill-package", "skill.json"),
              encoding="utf-8") as fh:
        locales = json.load(fh)["manifest"]["publishingInformation"]["locales"]
    source = os.path.join(MODELS, "en-IN.json")
    with open(source, encoding="utf-8") as fh:
        json.load(fh)  # refuse to copy a broken file
    for locale in sorted(locales):
        if locale != "en-IN":
            shutil.copyfile(source, os.path.join(MODELS, locale + ".json"))
            print("synced", locale)


if __name__ == "__main__":
    main()
