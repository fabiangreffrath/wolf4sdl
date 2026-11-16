#!/usr/bin/env python3
"""Generate layouts_gen.h and verify it against the original headers.

Usage: gen_layouts.py SRCDIR OUTDIR

SRCDIR holds wl_def.h, gfxv_*.h and audio*.h. The six Debian build
configurations are compiled with gcc to obtain the ground-truth values,
then logical enums plus per-version maps are written to OUTDIR and
checked by compiling a generated test program against them.
"""
import os
import re
import subprocess
import sys
import tempfile

CONFIGS = [  # (name, defines), taken from debian/rules
    ("wl6",   ["CARMACIZED", "GOODTIMES"]),
    ("wl6a",  ["CARMACIZED"]),
    ("wl6a1", ["CARMACIZED", "APOGEE_1_1"]),
    ("wl1",   ["CARMACIZED", "UPLOAD"]),
    ("sod",   ["CARMACIZED", "SPEAR", "GOODTIMES"]),
    ("sdm",   ["CARMACIZED", "SPEAR", "SPEARDEMO"]),
]
CONST_MACROS = ["STRUCTPIC", "NUMFONT", "NUMFONTM", "NUMPICM", "NUMSPRITES", "NUMTILE8",
                "NUMTILE8M", "NUMTILE16", "NUMTILE16M", "NUMTILE32", "NUMTILE32M"]
ALIAS_MACROS = ["STARTPICM", "STARTSPRITES", "STARTTILE16", "STARTTILE16M", "STARTTILE32",
                "STARTTILE32M"]
GFX_MACROS = ["NUMCHUNKS", "NUMPICS", "STARTFONT", "STARTFONTM", "STARTPICS", "STARTTILE8",
              "STARTTILE8M", "STARTEXTERNS"] + CONST_MACROS + ALIAS_MACROS
DATA_EXT = {"wl6": "wl6", "wl6a": "wl6", "wl6a1": "wl6", "wl1": "wl1", "sod": "sod", "sdm": "sdm"}
VERSION_FLAGS = ["SPEAR", "SPEARDEMO", "UPLOAD", "GOODTIMES", "APOGEE_1_1"]
LUMPS = ["BACKDROP", "CONTROL", "CONTROLS", "OPTIONS", "SOUND", "NEWGAME", "LOADSAVE",
         "HIGHSCORES", "LEVELEND", "LATCHPICS"]
AUD_MACROS = ["LASTSOUND", "LASTMUSIC", "STARTPCSOUNDS", "STARTADLIBSOUNDS",
              "STARTDIGISOUNDS", "STARTMUSIC", "NUMSNDCHUNKS"]
TYPED_ENUM = re.compile(r"typedef\s+enum\s*\{(.*?)\}\s*(\w+)\s*;", re.S)
PLAIN_ENUM = re.compile(r"enum\s*\{(.*?)\}\s*;", re.S)


def read_blocks(src):
    """Return the header-selection block and the sprite enum from wl_def.h."""
    lines = open(os.path.join(src, "wl_def.h")).read().split("\n")
    first = next(i for i, l in enumerate(lines) if '#include "audiowl6.h"' in l) - 1
    last = next(i for i, l in enumerate(lines) if l.startswith("typedef uint8_t byte;"))
    select = [l for l in lines[first:last] if "f_spear.h" not in l]
    start = next(i for i, l in enumerate(lines)
                 if l.strip() == "enum" and "SPR_DEMO" in lines[i + 2])
    end = next(i for i in range(start, len(lines)) if lines[i].startswith("};"))
    return "\n".join(select), "\n".join(lines[start:end + 1])


def cpp(text, src, flags):
    res = subprocess.run(["gcc", "-E", "-P", "-x", "c", "-I", src]
                         + ["-D" + f for f in flags] + ["-"],
                         input=text, capture_output=True, text=True, check=True)
    return res.stdout


def idents(body):
    return [re.match(r"\w+", s.strip()).group(0) for s in body.split(",") if s.strip()]


def evaluate(text, src, flags, names):
    """Compile TEXT plus a main() printing every name; return {name: int}."""
    prog = text + "\n#include <stdio.h>\nint main(void)\n{\n"
    prog += "".join('    printf("%%s %%d\\n", "%s", (int)(%s));\n' % (n, n) for n in names)
    prog += "    return 0;\n}\n"
    with tempfile.TemporaryDirectory() as tmp:
        c, exe = os.path.join(tmp, "e.c"), os.path.join(tmp, "e")
        open(c, "w").write(prog)
        subprocess.run(["gcc", "-w", "-I", src] + ["-D" + f for f in flags]
                       + [c, "-o", exe], check=True)
        out = subprocess.run([exe], capture_output=True, text=True, check=True).stdout
    return {k: int(v) for k, v in (l.split() for l in out.splitlines())}


def lump_values(text, src, flags):
    """Return {lump: (start, end)} of the original macros, (-1, -1) if undefined."""
    prog = text + "\n#include <stdio.h>\nint main(void)\n{\n"
    for n in LUMPS:
        prog += ('#ifdef %s_LUMP_START\n    printf("%s %%d %%d\\n", (int)(%s_LUMP_START), (int)(%s_LUMP_END));\n'
                 '#else\n    printf("%s -1 -1\\n");\n#endif\n' % (n, n, n, n, n))
    prog += "    return 0;\n}\n"
    with tempfile.TemporaryDirectory() as tmp:
        c, exe = os.path.join(tmp, "l.c"), os.path.join(tmp, "l")
        open(c, "w").write(prog)
        subprocess.run(["gcc", "-w", "-I", src] + ["-D" + f for f in flags] + [c, "-o", exe], check=True)
        out = subprocess.run([exe], capture_output=True, text=True, check=True).stdout
    return {l.split()[0]: (int(l.split()[1]), int(l.split()[2])) for l in out.splitlines()}


def unwrap_spear(text):
    """Keep both branches of the SPEAR conditionals in a header."""
    out, stack = [], []
    for line in text.split("\n"):
        m = re.match(r"\s*#\s*(ifdef|ifndef|else|endif)\b\s*(\w*)", line)
        if m:
            k = m.group(1)
            if k in ("ifdef", "ifndef"):
                stack.append(m.group(2) == "SPEAR")
                if stack[-1]:
                    continue
            elif k == "else":
                if stack[-1]:
                    continue
            else:
                if stack.pop():
                    continue
        out.append(line)
    return "\n".join(out)


def legacy_states(src):
    """Return (logical, wolf, spear) state names, the old builds' numbering is the position."""
    text = open(os.path.join(src, "states.h"), newline="").read().replace("\r\n", "\n")

    def names(t, flags):
        pre = cpp(t, src, flags)
        m = next(x for x in TYPED_ENUM.finditer(pre) if x.group(2) == "statenum_t")
        return [n for n in idents(m.group(1)) if n != "numstates"]
    logical = names(unwrap_spear(text), [])
    wolf, spear = names(text, []), names(text, ["SPEAR"])
    assert set(wolf) <= set(logical) and set(spear) <= set(logical)
    return logical, wolf, spear


def gather(src):
    select, sprites = read_blocks(src)
    data = {}
    for name, flags in CONFIGS:
        enums = {m.group(2): idents(m.group(1)) for m in TYPED_ENUM.finditer(cpp(select, src, flags))}
        gn = [n for n in enums["graphicnums"] if n != "ENUMEND"]
        sn = [n for n in enums["soundnames"] if n != "LASTSOUND"]
        mn = [n for n in enums["musicnames"] if n != "LASTMUSIC"]
        vals = evaluate(select, src, flags, gn + sn + mn + GFX_MACROS + AUD_MACROS + ["ENUMEND"])
        gfx = {n: vals[n] for n in gn}
        gfx.setdefault("TILE8", vals["STARTTILE8"])  # wl6 has no TILE8 enumerator
        spr_names = idents(PLAIN_ENUM.search(cpp(sprites, src, flags)).group(1))
        spr = evaluate(sprites, src, flags, spr_names)
        data[name] = dict(
            gfx=gfx, gm={k: vals[k] for k in GFX_MACROS + ["ENUMEND"]},
            snd={n: vals[n] for n in sn}, mus={n: vals[n] for n in mn},
            am={k: vals[k] for k in AUD_MACROS}, lump=lump_values(select, src, flags),
            spr={n: spr[n] for n in spr_names})
    return data


def merge(lists):
    """Union of ordered name lists; new names go right after their predecessor."""
    out = []
    for lst in lists:
        prev = None
        for n in lst:
            if n not in out:
                out.insert(out.index(prev) + 1 if prev is not None else 0, n)
            prev = n
    return out


def uniq(data, key):
    """Return ({config: layout key}, {layout key: dict}) with equal layouts shared."""
    seen, owner = {}, {}
    for name, _ in CONFIGS:
        d = data[name][key]
        for k, v in seen.items():
            if v == d:
                owner[name] = k
                break
        else:
            seen[name] = d
            owner[name] = name
    return owner, seen


def gfx_group(phys, m):
    if phys == m["STARTTILE8"]:
        return "tile8"
    return "ext" if phys >= m["STARTEXTERNS"] else "pic"


def breaks(items, logical):
    """Pairs adjacent in one layout but not adjacent in the logical enum."""
    res = []
    ordered = sorted(items.items(), key=lambda kv: kv[1])
    for (a, pa), (b, pb) in zip(ordered, ordered[1:]):
        if pb == pa + 1 and logical[b] != logical[a] + 1:
            res.append((a, b))
    return res


def arr(name, values, per=10):
    rows = []
    for i in range(0, len(values), per):
        rows.append("    " + ", ".join(str(v) for v in values[i:i + per]) + ",")
    return "static const short %s[%d] = {\n%s\n};\n" % (name, len(values), "\n".join(rows))


def enum_text(head, names, first, tail=None):
    items = ["%s=%d" % (n, first) if i == 0 else n for i, n in enumerate(names)]
    if tail:
        items.append(tail)
    rows = ["    " + ", ".join(items[i:i + 6]) + "," for i in range(0, len(items), 6)]
    return "%s{\n%s\n}" % (head, "\n".join(rows))


def build(data, states):
    for k in ("STARTFONT", "STARTFONTM", "STARTPICS") + tuple(CONST_MACROS):
        assert len({d["gm"][k] for d in data.values()}) == 1, k
    for d in data.values():
        m, g = d["gm"], d["gfx"]
        assert m["STARTTILE8M"] == m["STARTEXTERNS"] == g["ORDERSCREEN"]
        assert m["STARTPICM"] == m["STARTSPRITES"] == g["TILE8"]
        assert all(m[k] == g["ORDERSCREEN"] for k in ALIAS_MACROS[2:])
        assert m["NUMPICS"] == g["TILE8"] - m["STARTPICS"]
        assert (d["am"]["STARTPCSOUNDS"], d["am"]["STARTADLIBSOUNDS"],
                d["am"]["STARTDIGISOUNDS"], d["am"]["STARTMUSIC"]) == \
            (0, d["am"]["LASTSOUND"], 2 * d["am"]["LASTSOUND"], 3 * d["am"]["LASTSOUND"])

    # graphics: pictures, then TILE8, then externs, merged across layouts
    gown, glay = uniq(data, "gfx")
    grp = {}
    for cfg, d in data.items():
        for n, p in d["gfx"].items():
            g = gfx_group(p, d["gm"])
            assert grp.setdefault(n, g) == g, n
    order = []
    for g in ("pic", "tile8", "ext"):
        order += merge([[n for n in data[c]["gfx"] if grp[n] == g] for c in glay])
    glog = {n: 3 + i for i, n in enumerate(order)}
    gend = 3 + len(order)

    sown, slay = uniq(data, "snd")
    snd_order = merge([list(data[c]["snd"]) for c in slay])
    mus_order = merge([list(data[c]["mus"]) for c in slay])
    slog = {n: i for i, n in enumerate(snd_order)}
    mlog = {n: i for i, n in enumerate(mus_order)}
    pown, play = uniq(data, "spr")
    spr_order = merge([list(data[c]["spr"]) for c in play])
    plog = {n: i for i, n in enumerate(spr_order)}

    def table(logical, items, size, ident=0):
        t = [-1] * size
        t[:ident] = range(ident)
        for n, p in items.items():
            t[logical[n]] = p
        return t

    # lumps: physical ranges become logical ranges between the same names
    lumps = {}
    for c, d in data.items():
        inv = {p: n for n, p in d["gfx"].items()}
        lumps[c] = {}
        for l, (a, b) in d["lump"].items():
            lumps[c][l] = (-1, -1) if a < 0 else (inv[a], inv[b])

    lump_ids = {c: {l: [glog[n] for n, p in sorted(data[c]["gfx"].items(), key=lambda kv: kv[1])
                        if data[c]["lump"][l][0] <= p <= data[c]["lump"][l][1]]
                    if data[c]["lump"][l][0] >= 0 else None for l in LUMPS} for c in data}
    inexact_lumps = set()
    for c in data:
        for l in LUMPS:
            if lump_ids[c][l] is not None:
                lo, hi = glog[lumps[c][l][0]], glog[lumps[c][l][1]]
                if [i for i in range(lo, hi + 1) if i in set(glog[n] for n in data[c]["gfx"])] != lump_ids[c][l]:
                    inexact_lumps.add(l)

    # a lump range only stays exact if each layout keeps its physical order
    violations = []
    for kind, layouts, logical in (("gfx", glay, glog), ("spr", play, plog)):
        for k, d in layouts.items():
            seq = [logical[n] for n, _ in sorted(d.items(), key=lambda kv: kv[1])]
            violations += ["%s %s" % (kind, k) for a, b in zip(seq, seq[1:]) if b <= a]
    for kind, key, logical in (("snd", "snd", slog), ("mus", "mus", mlog)):
        for k in slay:
            seq = [logical[n] for n, _ in sorted(data[k][key].items(), key=lambda kv: kv[1])]
            violations += ["%s %s" % (kind, k) for a, b in zip(seq, seq[1:]) if b <= a]

    pics = [n for n in order if grp[n] == "pic"]
    exts = [n for n in order if grp[n] == "ext"]
    hdr = ["// Generated by gen_layouts.py, do not edit.",
           "// Logical ids are shared by all game versions, the maps give the physical position.",
           "#ifndef LAYOUTS_GEN_H", "#define LAYOUTS_GEN_H", "",
           enum_text("typedef enum\n", pics + ["TILE8"] + exts, 3, "ENUMEND") + " graphicnums;\n"]
    hdr.append("#define NUMCHUNKS    ENUMEND\n#define NUMPICS      (TILE8 - STARTPICS)\n"
               "#define STARTFONT    1\n#define STARTFONTM   3\n#define STARTPICS    3\n"
               "#define STARTPICM    TILE8\n#define STARTSPRITES TILE8\n#define STARTTILE8   TILE8\n"
               "#define STARTTILE8M  ORDERSCREEN\n#define STARTTILE16  ORDERSCREEN\n"
               "#define STARTTILE16M ORDERSCREEN\n#define STARTTILE32  ORDERSCREEN\n"
               "#define STARTTILE32M ORDERSCREEN\n#define STARTEXTERNS ORDERSCREEN\n")
    first = next(iter(data.values()))["gm"]
    hdr.append("".join("#define %-12s %d\n" % (k, first[k]) for k in CONST_MACROS))
    hdr.append(enum_text("typedef enum\n", snd_order, 0, "LASTSOUND") + " soundnames;\n")
    hdr.append(enum_text("typedef enum\n", mus_order, 0, "LASTMUSIC") + " musicnames;\n")
    hdr.append("#define NUMSOUNDS        LASTSOUND\n#define STARTPCSOUNDS    0\n"
               "#define STARTADLIBSOUNDS LASTSOUND\n#define STARTDIGISOUNDS (2*LASTSOUND)\n"
               "#define STARTMUSIC       (3*LASTSOUND)\n#define NUMSNDCHUNKS     (STARTMUSIC + LASTMUSIC)\n")
    hdr.append(enum_text("enum\n", spr_order, 0) + ";\n")
    hdr.append("#define NUMSPRITES_LOGICAL %d\n" % len(spr_order))
    hdr.append("enum\n{\n" + "".join("    LUMP_%s,\n" % l for l in LUMPS) + "    NUMLUMPS\n};\n")
    hdr.append("enum\n{\n" + "".join("    LAYOUT_%s,\n" % c.upper() for c, _ in CONFIGS) + "    NUMLAYOUTS\n};\n")
    hdr.append("typedef struct\n{\n    const char *name;\n    const char *ext;\n    bool spear, spear_demo, upload, goodtimes, apogee_1_1;\n    int numchunks;\n    int lastsound, lastmusic;\n"
               "    const short *gfxmap, *soundmap, *musicmap, *sprmap;\n    const short *lumps[NUMLUMPS];\n    short lumprange[NUMLUMPS][2];\n"
               "    const short *statemap, *stateinv, *sprinv;   // numbers of the former separate builds, used by savegames\n"
               "    int numlegacystates, numphysprites;\n"
               "} gamelayout_t;\n")
    hdr.append("extern const gamelayout_t gamelayouts[NUMLAYOUTS];\nextern const gamelayout_t *gamelayout;\n")
    hdr.append("// Lumps are -1 terminated chunk lists, NULL if the version has none.\n"
               "// Exact lumps also have a range, inexact ones must be used through the list.\n")
    for l in LUMPS:
        if l not in inexact_lumps:
            hdr.append("#define %s_LUMP_START (gamelayout->lumprange[LUMP_%s][0])\n"
                       "#define %s_LUMP_END   (gamelayout->lumprange[LUMP_%s][1])\n" % (l, l, l, l))
    hdr.append("#endif")

    logical_states, wolf_states, spear_states = states
    tag_of = lambda c: "spear" if "SPEAR" in dict(CONFIGS)[c] else "wolf"
    lidx = {n: i for i, n in enumerate(logical_states)}
    state_tables = {}
    for tag, legacy in (("wolf", wolf_states), ("spear", spear_states)):
        pos = {n: i for i, n in enumerate(legacy)}
        state_tables[tag] = ([pos.get(n, -1) for n in logical_states], [lidx[n] for n in legacy])
    spr_inv = {}
    for k, d in play.items():
        inv = [-1] * (max(d.values()) + 1)
        for n, p in d.items():
            inv[p] = plog[n]
        spr_inv[k] = inv

    cpp_out = ['// Generated by gen_layouts.py, do not edit.', '#include <stddef.h>', '#include "layouts_gen.h"', ""]
    for k, d in glay.items():
        cpp_out.append(arr("gfxmap_" + k, table(glog, d, gend, 3)))
    for k, d in slay.items():
        cpp_out.append(arr("soundmap_" + k, table(slog, data[k]["snd"], len(snd_order))))
        cpp_out.append(arr("musicmap_" + k, table(mlog, data[k]["mus"], len(mus_order))))
    for k, d in play.items():
        cpp_out.append(arr("sprmap_" + k, table(plog, d, len(spr_order))))
        cpp_out.append(arr("sprinv_" + k, spr_inv[k]))
    for tag, (fwd, inv) in state_tables.items():
        cpp_out.append(arr("statemap_" + tag, fwd))
        cpp_out.append(arr("stateinv_" + tag, inv))
    for c, _ in CONFIGS:
        for l in LUMPS:
            if lump_ids[c][l] is not None:
                cpp_out.append(arr("lump_%s_%s" % (c, l), lump_ids[c][l] + [-1]))
    rows = []
    for c, _ in CONFIGS:
        lp = ", ".join("lump_%s_%s" % (c, l) if lump_ids[c][l] is not None else "NULL" for l in LUMPS)
        rg = ", ".join("{%d, %d}" % ((-1, -1) if lumps[c][l][0] == -1 or l in inexact_lumps
                                     else (glog[lumps[c][l][0]], glog[lumps[c][l][1]])) for l in LUMPS)
        fl = ", ".join("1" if f in dict(CONFIGS)[c] else "0" for f in VERSION_FLAGS)
        rows.append('    { "%s", "%s", %s, %d, %d, %d, gfxmap_%s, soundmap_%s, musicmap_%s, sprmap_%s,\n'
                    '      { %s },\n      { %s },\n      statemap_%s, stateinv_%s, sprinv_%s, %d, %d },'
                    % (c, DATA_EXT[c], fl, data[c]["gm"]["ENUMEND"], data[c]["am"]["LASTSOUND"], data[c]["am"]["LASTMUSIC"],
                       gown[c], sown[c], sown[c], pown[c], lp, rg, tag_of(c), tag_of(c), pown[c],
                       len(spear_states if tag_of(c) == "spear" else wolf_states), len(spr_inv[pown[c]])))
    cpp_out.append("const gamelayout_t gamelayouts[NUMLAYOUTS] = {\n" + "\n".join(rows) + "\n};\n")

    chk = ['#include <stddef.h>', '#include <stdio.h>', '#include "layouts_gen.h"', '#include "states_logical.h"', "", "const gamelayout_t *gamelayout;", "",
           "static int failures;", "",
           "// Records a mismatch between a table entry and the original header value.",
           "static void expect(const char *what, int got, int want)", "{",
           "    if (got != want)", "    {",
           '        printf("MISMATCH %s: got %d, want %d\\n", what, got, want);',
           "        failures++;", "    }", "}", "",
           "// Compares a -1 terminated list with the expected one.",
           "static void expect_list(const char *what, const short *got, const short *want)", "{",
           "    int i = 0;", "    while (want[i] != -1 && got[i] == want[i])", "        i++;",
           "    expect(what, got[i], want[i]);", "}", "",
           "// Counts the entries that are present in a map.",
           "static int present(const short *map, int count)", "{", "    int n = 0;",
           "    for (int i = 0; i < count; i++)", "        n += map[i] != -1;",
           "    return n;", "}", "", "int main(void)", "{"]
    for c, _ in CONFIGS:
        d = data[c]
        chk += ["    {", "        const gamelayout_t *const l = &gamelayouts[LAYOUT_%s];" % c.upper(),
                "        gamelayout = l;",
                *['        expect("%s %s", l->%s, %d);' % (c, f, f.lower() if f != "SPEARDEMO" else "spear_demo",
                                                         f in dict(CONFIGS)[c]) for f in VERSION_FLAGS],
                '        expect("%s numchunks", l->numchunks, %d);' % (c, d["gm"]["ENUMEND"]),
                '        expect("%s numpics", l->gfxmap[TILE8] - STARTPICS, %d);' % (c, d["gm"]["NUMPICS"]),
                '        expect("%s lastsound", l->lastsound, %d);' % (c, d["am"]["LASTSOUND"]),
                '        expect("%s lastmusic", l->lastmusic, %d);' % (c, d["am"]["LASTMUSIC"])]
        for l in LUMPS:
            if lump_ids[c][l] is None:
                chk.append('        expect("%s lump %s null", l->lumps[LUMP_%s] == NULL, 1);' % (c, l, l))
                continue
            names = [n for n, p in sorted(d["gfx"].items(), key=lambda kv: kv[1])
                     if d["lump"][l][0] <= p <= d["lump"][l][1]]
            chk.append('        { const short want[] = { %s, -1 }; expect_list("%s lump %s", l->lumps[LUMP_%s], want); }'
                       % (", ".join(names), c, l, l))
            if l not in inexact_lumps:
                chk.append('        expect("%s lump %s start", %s_LUMP_START, %s);' % (c, l, l, lumps[c][l][0]))
                chk.append('        expect("%s lump %s end", %s_LUMP_END, %s);' % (c, l, l, lumps[c][l][1]))
        for key, field, size in (("gfx", "gfxmap", "ENUMEND"), ("snd", "soundmap", "LASTSOUND"),
                                 ("mus", "musicmap", "LASTMUSIC"), ("spr", "sprmap", "NUMSPRITES_LOGICAL")):
            for n, p in d[key].items():
                chk.append('        expect("%s %s", l->%s[%s], %d);' % (c, n, field, n, p))
            lo = 3 if key == "gfx" else 0
            chk.append('        expect("%s %s count", present(l->%s + %d, %s - %d), %d);'
                       % (c, key, field, lo, size, lo, len(d[key])))
        legacy = spear_states if tag_of(c) == "spear" else wolf_states
        chk.append('        expect("%s numlegacystates", l->numlegacystates, %d);' % (c, len(legacy)))
        for i, n in enumerate(legacy):
            chk.append('        expect("%s state %s", l->statemap[%s], %d);' % (c, n, n, i))
            chk.append('        expect("%s stateinv %s", l->stateinv[%d], %s);' % (c, n, i, n))
        chk.append('        expect("%s state count", present(l->statemap, numstates), %d);' % (c, len(legacy)))
        for n in d["spr"]:
            chk.append('        expect("%s sprinv %s", l->sprinv[l->sprmap[%s]], %s);' % (c, n, n, n))
        chk.append("    }")
    chk += ['    printf("%d mismatches\\n", failures);', "    return failures != 0;", "}"]

    report = ["graphics layouts: %s -> %d logical chunks" % (", ".join(glay), gend),
              "audio layouts: %s -> %d sounds, %d musics" % (", ".join(slay), len(snd_order), len(mus_order)),
              "sprite layouts: %s -> %d logical sprites" % (", ".join(play), len(spr_order)),
              "layouts whose physical order is not preserved: %s" % (violations or "none")]
    wanted = ["FACE1APIC:FACE8APIC", "GODMODEFACE1PIC:GODMODEFACE3PIC", "KNIFEPIC:GATLINGGUNPIC",
              "L_NUM0PIC:L_NUM9PIC", "C_DISKLOADING1PIC:C_DISKLOADING2PIC", "C_EPISODE1PIC:C_EPISODE6PIC",
              "BJWAITING1PIC:BJWAITING2PIC"]
    for w in wanted:
        a, b = w.split(":")
        for k, d in glay.items():
            if a in d and b in d and not (glog[b] - glog[a] == d[b] - d[a] == len(
                    [n for n in d if d[a] <= d[n] <= d[b]]) - 1):
                report.append("RUN BROKEN in gfx %s: %s..%s" % (k, a, b))
    report.append("arithmetic runs from the grep checked: %d" % len(wanted))
    report.append("lumps used as lists only (inexact as ranges): %s" % sorted(inexact_lumps))
    inexact = []
    for c in data:
        g = data[c]["gfx"]
        for l in LUMPS:
            a, b = data[c]["lump"][l]
            if a < 0:
                continue
            lo, hi = glog[lumps[c][l][0]], glog[lumps[c][l][1]]
            in_range = {n for n in g if lo <= glog[n] <= hi}
            want = {n for n, p in g.items() if a <= p <= b}
            if in_range != want:
                inexact.append("%s %s: extra %s missing %s" % (c, l, sorted(in_range - want), sorted(want - in_range)))
    report.append("lumps that are not exact as logical ranges: %s" % (inexact or "none"))
    for k in ("sod",):
        seq = sorted(data[k]["gfx"].items(), key=lambda kv: kv[1])
        bad = [(a, b) for (a, _), (b, _) in zip(seq, seq[1:]) if glog[b] <= glog[a]]
        report.append("gfx %s order violations: %s" % (k, bad))
    states_header = "typedef enum\n{\n" + "".join("    %s,\n" % n for n in logical_states) + "    numstates\n} statenum_t;\n"
    return "\n".join(hdr) + "\n", "\n".join(cpp_out) + "\n", "\n".join(chk) + "\n", "\n".join(report), states_header


def main():
    src, outdir = sys.argv[1:3]
    header, tables, check, report, states_header = build(gather(src), legacy_states(src))
    os.makedirs(outdir, exist_ok=True)
    open(os.path.join(outdir, "layouts_gen.h"), "w").write(header)
    open(os.path.join(outdir, "layouts_gen.cpp"), "w").write(tables)
    print(report)
    with tempfile.TemporaryDirectory() as tmp:
        for name, text in (("layouts_gen.h", header), ("layouts_gen.cpp", tables), ("check.cpp", check),
                           ("states_logical.h", states_header)):
            open(os.path.join(tmp, name), "w").write(text)
        exe = os.path.join(tmp, "check")
        subprocess.run(["g++", "-Wall", "-Werror", "-I", tmp, os.path.join(tmp, "check.cpp"),
                        os.path.join(tmp, "layouts_gen.cpp"), "-o", exe], check=True)
        res = subprocess.run([exe], capture_output=True, text=True)
        print(res.stdout.strip())
        sys.exit(res.returncode)


if __name__ == "__main__":
    main()
