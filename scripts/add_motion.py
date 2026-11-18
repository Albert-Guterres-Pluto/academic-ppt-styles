"""Add click-to-fade entrances and slide transitions to a static PPTX copy."""

import argparse
from collections import Counter
from copy import copy
from itertools import count
import json
from pathlib import Path
from shutil import copyfileobj
from tempfile import TemporaryFile
from xml.etree import ElementTree as ET
from xml.parsers import expat
from zipfile import BadZipFile, ZipFile

from inspect_motion import NS, branches, local, presentation_parts, shape_names

P14 = "http://schemas.microsoft.com/office/powerpoint/2010/main"
P159 = "http://schemas.microsoft.com/office/powerpoint/2015/09/main"
ANIMATABLE = {"sp", "pic", "grpSp", "graphicFrame", "cxnSp"}


def p(parent, tag, **attrs):
    return ET.SubElement(parent, f"p:{tag}", {key: str(value) for key, value in attrs.items()})


def bounded_ms(value):
    if type(value) is not int or not 1 <= value <= 60000:
        raise ValueError("duration_ms and fade_ms must be integers from 1 to 60000")
    return value


def transition_xml(spec, current_names, previous_names):
    if not isinstance(spec, dict) or set(spec) - {"type", "duration_ms", "direction"}:
        raise ValueError("invalid transition fields")
    effect = spec.get("type")
    if not isinstance(effect, str) or effect not in {"fade", "push", "morph"}:
        raise ValueError("transition type must be fade, push, or morph")
    duration = bounded_ms(spec.get("duration_ms", 1500 if effect == "morph" else 700))
    direction = spec.get("direction", "l")
    if "direction" in spec and (effect != "push" or direction not in ("l", "r", "u", "d")):
        raise ValueError("direction applies to push and must be l, r, u, or d")

    if effect == "morph":
        current = Counter(current_names.values())
        previous = Counter(previous_names.values())
        if not any(name.startswith("!!") and current[name] == previous[name] == 1
                   for name in current if name):
            raise ValueError("morph needs a shared, unique name beginning with !! on adjacent slides")

    root = ET.Element("mc:AlternateContent", {
        "xmlns:mc": NS["mc"], "xmlns:p": NS["p"], "xmlns:p14": P14, "xmlns:p159": P159,
    })
    choice = ET.SubElement(root, "mc:Choice", Requires="p159" if effect == "morph" else "p14")
    speed = "slow" if duration >= 1000 else "med"
    main = p(choice, "transition", spd=speed, **{"p14:dur": duration})
    alternate = p(ET.SubElement(root, "mc:Fallback"), "transition", spd=speed)
    if effect == "morph":
        ET.SubElement(main, "p159:morph", option="byObject")
        p(alternate, "fade")
    else:
        options = {"dir": direction} if effect == "push" else {}
        p(main, effect, **options)
        p(alternate, effect, **options)
    return root


def timing_xml(groups, duration):
    ids = count(1)

    def time(parent, **attrs):
        return p(parent, "cTn", id=next(ids), **attrs)

    def delay(node, ms):
        p(p(node, "stCondLst"), "cond", delay=ms)

    def target(parent, shape):
        p(p(parent, "tgtEl"), "spTgt", spid=shape)

    root = ET.Element("p:timing", {"xmlns:p": NS["p"]})
    outer = time(p(p(root, "tnLst"), "par"), dur="indefinite", restart="never", nodeType="tmRoot")
    sequence = p(p(outer, "childTnLst"), "seq", concurrent=1, nextAc="seek")
    main = time(sequence, dur="indefinite", nodeType="mainSeq")
    steps = p(main, "childTnLst")

    for group in groups:
        wait = time(p(steps, "par"), fill="hold")
        delay(wait, "indefinite")
        start = time(p(p(wait, "childTnLst"), "par"), fill="hold")
        delay(start, 0)
        peers = p(start, "childTnLst")
        for i, (shape_id, shape_kind) in enumerate(group):
            effect = time(
                p(peers, "par"), presetID=10, presetClass="entr", presetSubtype=0,
                fill="hold", grpId=0, nodeType="clickEffect" if i == 0 else "withEffect",
            )
            delay(effect, 0)
            effects = p(effect, "childTnLst")
            show = p(effects, "set")
            show_behavior = p(show, "cBhvr")
            delay(time(show_behavior, dur=1, fill="hold"), 0)
            target(show_behavior, shape_id)
            p(p(show_behavior, "attrNameLst"), "attrName").text = "style.visibility"
            p(p(show, "to"), "strVal", val="visible")
            fade = p(effects, "animEffect", transition="in", filter="fade")
            fade_behavior = p(fade, "cBhvr")
            time(fade_behavior, dur=duration)
            target(fade_behavior, shape_id)

    for tag, event in (("prevCondLst", "onPrev"), ("nextCondLst", "onNext")):
        cond = p(p(sequence, tag), "cond", evt=event, delay=0)
        p(p(cond, "tgtEl"), "sldTgt")
    text_shapes = [pair for group in groups for pair in group if pair[1] == "sp"]
    if text_shapes:
        build = p(root, "bldLst")
        for shape_id, _ in text_shapes:
            p(build, "bldP", spid=shape_id, grpId=0, animBg=1)
    return root


def click_groups(slide, names):
    if not isinstance(names, list) or not names:
        raise ValueError("fade_clicks must contain at least one group")
    available = {}
    for shape in slide.findall("p:cSld/p:spTree/*", NS):
        kind = local(shape.tag)
        if kind not in ANIMATABLE:
            continue
        props = shape.find("*/p:cNvPr", NS)
        if props is not None and (props.get("id") or "").isdecimal():
            available.setdefault(props.get("name"), []).append((props.get("id"), kind))

    groups = []
    seen = set()
    for group in names:
        if not isinstance(group, list) or not group:
            raise ValueError("each click group must be a nonempty list of shape names")
        targets = []
        for name in group:
            if not isinstance(name, str) or len(available.get(name, [])) != 1:
                raise ValueError(f"target must name one top-level shape: {name!r}")
            target = available[name][0]
            if target[0] in seen:
                raise ValueError(f"shape listed more than once: {name!r}")
            targets.append(target)
            seen.add(target[0])
        groups.append(targets)
    return groups


def insert_parts(raw, fragments):
    """Insert at the slide-child boundary without rewriting existing XML."""
    depth = 0
    insert_at = None
    parser = expat.ParserCreate(namespace_separator=" ")

    def start(tag, attrs):
        nonlocal depth, insert_at
        if depth == 1 and tag == f"{NS['p']} extLst":
            insert_at = parser.CurrentByteIndex
        depth += 1

    def end(tag):
        nonlocal depth, insert_at
        depth -= 1
        if depth == 0 and insert_at is None:
            insert_at = parser.CurrentByteIndex

    def declaration(version, encoding, standalone):
        if encoding is not None and encoding.lower() not in {"utf-8", "utf8"}:
            raise ValueError("slide XML must be encoded as UTF-8")

    parser.StartElementHandler = start
    parser.EndElementHandler = end
    parser.XmlDeclHandler = declaration
    if b"\x00" in raw:
        raise ValueError("slide XML must be encoded as UTF-8")
    parser.Parse(raw, True)
    payload = b"".join(ET.tostring(node, encoding="utf-8") for node in fragments)
    return raw[:insert_at] + payload + raw[insert_at:]


def changed_slide(raw, spec, previous):
    if not isinstance(spec, dict) or set(spec) - {"transition", "fade_clicks", "fade_ms"}:
        raise ValueError("invalid slide fields")
    slide = ET.fromstring(raw)
    if slide.tag != f"{{{NS['p']}}}sld":
        raise ValueError("expected a standard transitional PPTX slide")
    if any(local(child.tag) in {"transition", "timing"} for child in branches(slide)):
        raise ValueError("slide already has animation or a transition")
    fragments = []
    if "transition" in spec:
        fragments.append(transition_xml(spec["transition"], shape_names(slide), previous))
    if "fade_clicks" in spec:
        groups = click_groups(slide, spec["fade_clicks"])
        fragments.append(timing_xml(groups, bounded_ms(spec.get("fade_ms", 500))))
    elif "fade_ms" in spec:
        raise ValueError("fade_ms requires fade_clicks")
    if not fragments:
        raise ValueError("slide plan has no actions")
    return insert_parts(raw, fragments)


def apply_motion(source, output, plan):
    if source.suffix.lower() != ".pptx" or output.suffix.lower() != ".pptx":
        raise ValueError("provide .pptx input and output paths")
    if not isinstance(plan, dict) or set(plan) != {"slides"}:
        raise ValueError("expected a JSON object with a nonempty slides map")
    slides = plan["slides"]
    if not isinstance(slides, dict) or not slides:
        raise ValueError("expected a JSON object with a nonempty slides map")

    with ZipFile(source) as package, TemporaryFile() as staged:
        if any(name.startswith("_xmlsignatures/") for name in package.namelist()):
            raise ValueError("the input is digitally signed")
        _, parts = presentation_parts(package)
        changes = {}
        for number, spec in slides.items():
            if not number.isascii() or not number.isdecimal() or number.startswith("0"):
                raise ValueError(f"invalid slide number: {number!r}")
            index = int(number) - 1
            if not 0 <= index < len(parts):
                raise ValueError(f"slide {number} is outside the presentation")
            previous = shape_names(ET.fromstring(package.read(parts[index - 1]))) if index > 0 else {}
            try:
                changes[parts[index]] = changed_slide(package.read(parts[index]), spec, previous)
            except ValueError as error:
                raise ValueError(f"slide {number}: {error}") from error

        with ZipFile(staged, "w") as result:
            result.comment = package.comment
            for item in package.infolist():
                if item.filename in changes:
                    result.writestr(copy(item), changes[item.filename])
                else:
                    with package.open(item) as original, result.open(copy(item), "w") as new:
                        copyfileobj(original, new)
        staged.seek(0)
        created = False
        try:
            with output.open("xb") as final:
                created = True
                copyfileobj(staged, final)
        except BaseException:
            if created:
                output.unlink()
            raise
    return len(changes)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("plan", type=Path, help="JSON animation plan indexed by 1-based slide number.")
    parser.add_argument("output", type=Path, help="Path to a new .pptx file.")
    args = parser.parse_args()
    try:
        plan = json.loads(args.plan.read_text(encoding="utf-8-sig"))
        edited = apply_motion(args.input, args.output, plan)
    except (OSError, ValueError, KeyError, BadZipFile, ET.ParseError, expat.ExpatError) as error:
        parser.exit(2, f"Error: {error}\n")
    print(f"Wrote {args.output} ({edited} slide(s) updated).")


if __name__ == "__main__":
    main()
