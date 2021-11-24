# General description

inklayers export layers from an SVG file.
It can be used to create slide shows by editing a single SVG file.

By default the exported files are in SVG format too.

If Inkscape is found in the system, an automatic conversion of each single exported layer to Inkscape supported formats (png, pdf, ps, eps) can be done.

A project can be specified using a file format based on JSON, INI, or TOML formats.
The project file allows to specify complex organizations of layers to be combined into "slides".

# Compatibility

The extraction of layers in SVG format should work on any system.

The conversion with Inkscape was tested using Inkscape version 0.91 and 1.1.1 under Ubuntu 20.04.

# Installing

From source:

```
git clone <repository>
```

```
cd <cloned-directory>
```

```
pip install -r requirements.txt
```

```
pip install --user .
```

# Examples

After installing, to test an example:

```
cd examples
```

run

```
inklayers fishes.json
```

The exported layers and their conversions are saved in `output/` under the current directory.

# Reference to layers

Layers can be referenced by label or index (#0, #1, ...).
The first layer has index 0.
Layer's interval is supported. Example format: #1-#9.

Layers can be selected for inclusion or exclusion.
If include/exclude options collide, the latest prevails.

# Project file format

```
{
  "input": {
    "filename": "fishes.svg"
  },
  "output": {
    "type": "pdf",
    "filename": "%b-%n.%e",
    "slides": [
      {"include": ["L0"]},
      {"include": ["L0", "L1"]},
      {"include": ["#0-#2"]},
      {"include": ["#0-#3"]},
      {"include": ["#0-#4"]},
      {"include": ["#0-#5"]},
      {"include": ["#0-#6"], "exclude": ["L5 msg:greetings"]},
      {"include": ["#0-#7"], "exclude": ["L5 msg:greetings"]},
      {"include": ["#0-#8"], "exclude": ["L5 msg:greetings"]},
      {"include": ["#0-#9"], "exclude": ["L5 msg:greetings"]},
      {"include": ["#0-#10"], "exclude": ["L5 msg:greetings"]},
      {"include": ["#0-#11"], "exclude": ["L5 msg:greetings"]},
      {"include": ["#0-#12"], "exclude": ["L5 msg:greetings"]},
      {"include": ["#0-#12"], "exclude": ["L5 msg:greetings", "L12 msg:reply"]}
    ]
  }
}
```
