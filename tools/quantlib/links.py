# Extract QuantLib dependency links for the model map.
# Inputs: QuantLib and QuantLib-SWIG source trees (same version as inventory.json).
# Run: python3 tools/quantlib/links.py <QuantLib dir> <QuantLib-SWIG dir>  -> writes links.json next to it.
# For every Python-exposed class: C++ class, base classes, constructor argument types,
# and for engines the instrument they price (from "X::engine" / GenericEngine<X::arguments>).
import json, os, re, sys

ql_dir, swig_dir = sys.argv[1], sys.argv[2]
here = os.path.dirname(os.path.abspath(__file__))
inv = json.load(open(os.path.join(here, 'inventory.json')))

def strip_comments(s):
    s = re.sub(r'/\*.*?\*/', ' ', s, flags=re.S)
    return re.sub(r'//[^\n]*', ' ', s)

def blocks(text):
    """Yield (name, template_params, bases, body) for each class declaration with a body."""
    for m in re.finditer(r'(template\s*<((?:[^<>]|<[^<>]*>)*)>\s*)?class\s+(\w+)\s*(:\s*([^{;]*))?\{', text):
        name, bases = m.group(3), (m.group(5) or '')
        depth, i = 1, m.end()
        while depth and i < len(text):
            depth += {'{': 1, '}': -1}.get(text[i], 0); i += 1
        yield name, m.group(2), bases, text[m.end():i - 1]

TYPE = r'(?:ext::)?shared_ptr<\s*(?:const\s+)?(\w+)\s*>|Handle<\s*(\w+)\s*>|RelinkableHandle<\s*(\w+)\s*>|const\s+(\w+)\s*&'
def ctor_types(name, body):
    out = set()
    for m in re.finditer(r'(?<![\w~])' + name + r'\s*\(([^;{]*)\)', body):
        for t in re.finditer(TYPE, m.group(1)):
            out.add(next(g for g in t.groups() if g))
    return sorted(out)

# 1. SWIG: python name -> cpp name, constructor types
swig = {}       # cpp/swig class name -> {'bases':..., 'ctor':[...]}
templ = {}      # python name -> (cpp template, argument)
typedef = {}
for f in sorted(os.listdir(swig_dir)):
    if not f.endswith('.i'): continue
    t = strip_comments(open(os.path.join(swig_dir, f), encoding='utf-8', errors='ignore').read())
    for name, tp, bases, body in blocks(t):
        swig.setdefault(name, {'bases': bases.strip(), 'ctor': ctor_types(name, body), 'file': f})
    for m in re.finditer(r'%template\((\w+)\)\s*(\w+)\s*<\s*([^;]*?)\s*>\s*;', t):
        templ[m.group(1)] = (m.group(2), m.group(3))
    for m in re.finditer(r'typedef\s+(\w+)\s*<\s*([^;]*?)\s*>\s+(\w+)\s*;', t):
        typedef[m.group(3)] = (m.group(1), m.group(2))
    for m in re.finditer(r'typedef\s+(\w+)\s+(\w+)\s*;', t):
        typedef.setdefault(m.group(2), (m.group(1), ''))

# 2. C++ headers: class -> bases, ctor types
cpp = {}
for root, _, files in os.walk(os.path.join(ql_dir, 'ql')):
    for f in files:
        if not f.endswith('.hpp'): continue
        t = strip_comments(open(os.path.join(root, f), encoding='utf-8', errors='ignore').read())
        for name, tp, bases, body in blocks(t):
            if name not in cpp or len(body) > len(cpp[name]['body']):
                cpp[name] = {'bases': bases.strip(), 'tp': tp or '', 'ctor': ctor_types(name, body), 'body': body,
                             'file': os.path.relpath(os.path.join(root, f), ql_dir)}
    # typedefs in C++ too (e.g. engines defined as typedefs)
for root, _, files in os.walk(os.path.join(ql_dir, 'ql')):
    for f in files:
        if f.endswith('.hpp'):
            t = strip_comments(open(os.path.join(root, f), encoding='utf-8', errors='ignore').read())
            for m in re.finditer(r'typedef\s+(\w+)\s*<\s*([^;]*?)\s*>\s+(\w+)\s*;', t):
                typedef.setdefault(m.group(3), (m.group(1), m.group(2)))

def resolve(py):
    """Python class name -> (cpp class name, template arg)"""
    if py in templ: return templ[py]
    if py in typedef: return typedef[py]
    return (py, '')

INSTRUMENTS = set(inv['Instrument']) | {'ConvertibleBond', 'Instrument'}
def instrument_of(c, arg='', seen=()):
    """Follow C++ bases until X::engine or GenericEngine<X::arguments, ...>.
    When X is a template parameter, take it from the template argument or its default."""
    if c not in cpp or c in seen: return None
    b, tp = cpp[c]['bases'], cpp[c].get('tp', '')
    m = re.search(r'(\w+)::engine\b', b) or re.search(r'GenericEngine<\s*(\w+)::arguments', b) \
        or re.search(r'(\w+)::arguments', b)
    if m:
        x = m.group(1)
        if x in INSTRUMENTS or x in cpp and x not in re.findall(r'class\s+(\w+)', tp): return x
        for a in re.findall(r'\w+', arg):
            if a in INSTRUMENTS: return a
        d = re.search(r'class\s+' + x + r'\s*=\s*(\w+)', tp)
        return d.group(1) if d else x
    for base in re.findall(r'public\s+(?:\w+::)*(\w+)', b):
        r = instrument_of(base, arg, seen + (c,))
        if r: return r
    return None

out = {'version': inv['version'], 'classes': {}}
for group in ['PricingEngine', 'CalibratedModel', 'StochasticProcess', 'Instrument', 'YieldTermStructure',
              'DefaultProbabilityTermStructure', 'BlackVolTermStructure', 'LocalVolTermStructure',
              'SwaptionVolatilityStructure', 'OptionletVolatilityStructure', 'SmileSection']:
    for py in inv[group]:
        c, arg = resolve(py)
        s = swig.get(py) or swig.get(c) or {}
        h = cpp.get(c, {})
        types = sorted(set(s.get('ctor', [])) | set(h.get('ctor', [])))
        rec = {'group': group, 'cpp': c, 'arg': arg, 'file': h.get('file'), 'uses': types}
        if group == 'PricingEngine':
            rec['prices'] = instrument_of(c, arg)
        out['classes'][py] = rec
json.dump(out, open(os.path.join(here, 'links.json'), 'w'), indent=1, sort_keys=True)
miss = [k for k, v in out['classes'].items() if v['group'] == 'PricingEngine' and not v['prices']]
print('classes', len(out['classes']), 'engines without instrument', len(miss), miss)
