"""Rebuild dion-security-plus.html from the raw Dion quiz files in Dion-Questions/.

Uses security-plus.html as the quiz engine template.
Usage: python3 scripts/build_dion.py
"""
import glob, html, json, os, re, sys

root = sys.argv[1] if len(sys.argv) > 1 else os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
src_dir = os.path.join(root, 'Dion-Questions')
template = open(os.path.join(root, 'security-plus.html'), encoding='utf-8').read()

def clean(s):
    s = re.sub(r'<[^>]+>', ' ', s or '')
    for _ in range(3):
        s = html.unescape(s)
    s = s.replace(' ', ' ')
    s = re.sub(r'\s*For support or reporting issues.*$', '', s, flags=re.S)
    return re.sub(r'\s+', ' ', s).strip()

def esc(s):
    return s.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')

modules, questions = [], []
for path in sorted(glob.glob(os.path.join(src_dir, '*.html'))):
    text = open(path, encoding='utf-8').read()
    m = re.search(r'const quizData = (\{.*?\});\n', text, re.S)
    data = json.loads(m.group(1))
    num = re.search(r'#(\d+)', data['quiz_title']).group(1)
    name = f'Practice Exam {num}'
    modules.append(name)
    for item in data['questions']:
        p = item['prompt']
        answers = [esc(clean(a)) for a in p['answers']]
        correct = [ord(c) - 97 for c in item['correct_response']]
        expl = clean(p.get('explanation', ''))
        obj = re.match(r'OBJ:?\s*([\d.]+)\s*[-:]?\s*', expl)
        sub = f'Objective {obj.group(1).rstrip(".")}' if obj else ''
        if obj:
            expl = expl[obj.end():]
        expl = esc(expl)
        e = [('Correct. ' + expl) if i in correct else 'Incorrect. See the explanation on the correct answer.'
             for i in range(len(answers))]
        q = {
            'm': name,
            'top': re.sub(r'^[\d.]+\s*-\s*', '', item.get('section', '')),
            'sub': sub,
            'd': 'medium',
            'type': 'multi' if len(correct) > 1 else 'single',
            'q': clean(p['question']),
            'o': [f'{chr(65 + i)}. {a}' for i, a in enumerate(answers)],
            'c': correct if len(correct) > 1 else correct[0],
            'e': e,
        }
        if len(correct) > 1:
            q['need'] = len(correct)
        questions.append(q)

out = template
out = out.replace('<title>CompTIA Security+ Practice Exam</title>', '<title>Dion Security+ Practice Bank</title>')
out = out.replace('--primary: #C8102E;', '--primary: #6b4fbb;').replace('--primary-dark: #9c0c22;', '--primary-dark: #4d3d8d;')
out = out.replace('#fff5f5', '#f4f0ff')
out = out.replace('<div class="brand-badge">S+</div>', '<div class="brand-badge">D</div>')
out = out.replace('<h1>CompTIA Security+ Practice Exam</h1>', '<h1>Dion Security+ Practice Bank</h1>')
out = out.replace('<p>SY0-701 &middot; Select a module to begin a timed practice session</p>',
                  '<p>SY0-701 &middot; Jason Dion Udemy practice exams &middot; Select an exam to begin a timed practice session</p>')

start = out.index('const MODULE_ORDER = [')
end = out.index('const TIME_PER_QUESTION_SECONDS')
desc = {m: f'Full-length Dion SY0-701 practice exam covering all five domains.' for m in modules}
block = (
    'const MODULE_ORDER = ' + json.dumps(modules, indent=2) + ';\n'
    'const MODULE_LABEL = ' + json.dumps({m: 'Dion Udemy course' for m in modules}, indent=2) + ';\n'
    'const MODULE_DESC = ' + json.dumps(desc, indent=2) + ';\n\n'
    '/* Jason Dion SY0-701 practice exams (Udemy), kept separate from the main Security+ bank.\n'
    '   Converted from the raw quiz files in Dion-Questions/. */\n'
    'const questions = [\n' + ',\n'.join(json.dumps(q, ensure_ascii=False).replace('<', '\\u003c') for q in questions) + '\n];\n\n'
)
out = out[:start] + block + out[end:]
old = '<span class="weight">${MODULE_WEIGHT[name]}% of exam</span>'
assert old in out
out = out.replace(old, '<span class="weight">${MODULE_LABEL[name]}</span>')
assert 'MODULE_WEIGHT' not in out

open(os.path.join(root, 'dion-security-plus.html'), 'w', encoding='utf-8').write(out)
print(len(questions), {m: sum(q['m'] == m for q in questions) for m in modules},
      sum(q['type'] == 'multi' for q in questions), sum(not q['sub'] for q in questions))
