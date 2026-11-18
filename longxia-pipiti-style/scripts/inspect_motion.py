"""Inspect slide transitions and PowerPoint timing presets in a local PPTX."""

import argparse
from collections import Counter
import json
from pathlib import Path
import posixpath
from urllib.parse import unquote
from xml.etree import ElementTree as ET
from zipfile import ZipFile


NS = {
    "p": "http://schemas.openxmlformats.org/presentationml/2006/main",
    "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
    "mc": "http://schemas.openxmlformats.org/markup-compatibility/2006",
}


def local(name):
    return name.split("}")[-1]


def branches(elem):
    """Yield direct children, keeping Choice before Fallback for inspection."""
    for child in elem:
        if local(child.tag) == "AlternateContent":
            for option in child:
                yield from branches(option)
        else:
            yield child


def transition(node):
    effects = []
    for child in node:
        if local(child.tag) not in {"sndAc", "extLst"}:
            effects.append({"type": local(child.tag), **attrs(child)})
    return {
        **attrs(node),
        "effects": effects,
        "sound": node.find("p:sndAc", NS) is not None,
    }


def attrs(node):
    return {local(key): value for key, value in node.attrib.items()}


def inspect_timing(timing, shapes):
    effects = []
    for node in timing.iterfind(".//p:cTn", NS):
        preset = node.get("presetClass")
        if preset is None:
            continue
        targets = dict.fromkeys(target.get("spid") for target in node.iterfind(".//p:spTgt", NS))
        behaviors = []
        for descendant in node.iter():
            time = descendant.find("p:cBhvr/p:cTn", NS)
            if time is None or local(descendant.tag) == "set":
                continue
            behavior = {"type": local(descendant.tag), "dur_ms": time.get("dur")}
            if descendant.get("filter"):
                behavior["filter"] = descendant.get("filter")
            behaviors.append(behavior)
        effects.append(
            {
                "class": preset,
                "id": node.get("presetID"),
                "subtype": node.get("presetSubtype"),
                "trigger": node.get("nodeType"),
                "start_conditions": [
                    attrs(cond) for cond in node.findall("p:stCondLst/p:cond", NS)
                ],
                "targets": [{"id": obj, "name": shapes.get(obj)} for obj in targets],
                "behaviors": behaviors,
            }
        )
    return effects


def presentation_parts(package):
    root = ET.fromstring(package.read("ppt/presentation.xml"))
    relationships = ET.fromstring(package.read("ppt/_rels/presentation.xml.rels"))
    slide_targets = {
        rel.get("Id"): unquote(rel.get("Target"))
        for rel in relationships
        if rel.get("Type", "").endswith("/slide") and rel.get("TargetMode") != "External"
    }
    parts = []
    for entry in root.findall("p:sldIdLst/p:sldId", NS):
        target = slide_targets[entry.get(f"{{{NS['r']}}}id")]
        parts.append(posixpath.normpath(posixpath.join("ppt", target)).lstrip("/"))
    return root, parts


def shape_names(slide):
    return {
        shape.get("id"): shape.get("name")
        for shape in slide.iterfind(".//p:spTree//p:cNvPr", NS)
    }


def inspect_presentation(filename, include_shapes=False):
    with ZipFile(filename) as package:
        root, parts = presentation_parts(package)
        size = root.find("p:sldSz", NS)
        slides = []
        for page, part in enumerate(parts, start=1):
            slide = ET.fromstring(package.read(part))
            shapes = shape_names(slide)
            transitions = []
            timing = None
            for child in branches(slide):
                if local(child.tag) == "transition":
                    transitions.append(transition(child))
                elif local(child.tag) == "timing" and timing is None:
                    timing = child
            slides.append(
                {
                    "page": page,
                    "hidden": slide.get("show") in {"0", "false"},
                    "transitions": transitions,
                    "has_timing": timing is not None,
                    "effects": inspect_timing(timing, shapes) if timing is not None else [],
                }
            )
            if include_shapes:
                slides[-1]["shapes"] = shapes
    return {
        "file": Path(filename).name,
        "size_emu": attrs(size) if size is not None else {},
        "slide_count": len(slides),
        "timing_pages": sum(slide["has_timing"] for slide in slides),
        "transitions": dict(Counter(transition_name(slide) for slide in slides)),
        "slides": slides,
    }


def transition_name(slide):
    for candidate in slide["transitions"]:
        if candidate["effects"]:
            return candidate["effects"][0]["type"]
    return "none"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("--pages", type=int, nargs="+", help="Inspect selected 1-based slide numbers.")
    parser.add_argument("--summary", action="store_true", help="Show counts without slide details.")
    parser.add_argument("--shapes", action="store_true", help="Include each slide's shape IDs and names.")
    args = parser.parse_args()
    data = inspect_presentation(args.input, include_shapes=args.shapes)
    if args.pages:
        if any(page < 1 or page > data["slide_count"] for page in args.pages):
            parser.error("Each page must be within the slide count.")
        data["slides"] = [data["slides"][page - 1] for page in dict.fromkeys(args.pages)]
    if args.summary:
        del data["slides"]
    print(json.dumps(data, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
