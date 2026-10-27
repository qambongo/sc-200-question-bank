"""Build the Security+ "by topic" pages: the CompTIA bank (security-plus-topics.html)
and the Dion bank (dion-security-plus-topics.html), each grouped by SY0-701 exam
objective and split into small sets. The banks are kept on separate pages.

Reads the question arrays from security-plus.html and dion-security-plus.html
(run scripts/build_dion.py first if the Dion files changed), and the page shell
from scripts/topics_template.html.
Usage: python3 scripts/build_topics.py
"""
import hashlib, json, math, os, re, sys

root = sys.argv[1] if len(sys.argv) > 1 else os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SET_SIZE = 15

DOMAINS = [
    {'n': 1, 'name': 'General Security Concepts', 'weight': 12},
    {'n': 2, 'name': 'Threats, Vulnerabilities, and Mitigations', 'weight': 22},
    {'n': 3, 'name': 'Security Architecture', 'weight': 18},
    {'n': 4, 'name': 'Security Operations', 'weight': 28},
    {'n': 5, 'name': 'Security Program Management and Oversight', 'weight': 20},
]
OBJECTIVES = {
    '1.1': ('Security Controls', 'Compare and contrast various types of security controls.'),
    '1.2': ('Fundamental Security Concepts', 'Summarize fundamental security concepts.'),
    '1.3': ('Change Management', 'Explain the importance of change management processes and the impact to security.'),
    '1.4': ('Cryptographic Solutions', 'Explain the importance of using appropriate cryptographic solutions.'),
    '2.1': ('Threat Actors and Motivations', 'Compare and contrast common threat actors and motivations.'),
    '2.2': ('Threat Vectors and Attack Surfaces', 'Explain common threat vectors and attack surfaces.'),
    '2.3': ('Vulnerability Types', 'Explain various types of vulnerabilities.'),
    '2.4': ('Indicators of Malicious Activity', 'Given a scenario, analyze indicators of malicious activity.'),
    '2.5': ('Mitigation Techniques', 'Explain the purpose of mitigation techniques used to secure the enterprise.'),
    '3.1': ('Architecture Models', 'Compare and contrast security implications of different architecture models.'),
    '3.2': ('Secure Enterprise Infrastructure', 'Given a scenario, apply security principles to secure enterprise infrastructure.'),
    '3.3': ('Data Protection', 'Compare and contrast concepts and strategies to protect data.'),
    '3.4': ('Resilience and Recovery', 'Explain the importance of resilience and recovery in security architecture.'),
    '4.1': ('Securing Computing Resources', 'Given a scenario, apply common security techniques to computing resources.'),
    '4.2': ('Asset Management', 'Explain the security implications of proper hardware, software, and data asset management.'),
    '4.3': ('Vulnerability Management', 'Explain various activities associated with vulnerability management.'),
    '4.4': ('Alerting and Monitoring', 'Explain security alerting and monitoring concepts and tools.'),
    '4.5': ('Enhancing Enterprise Security', 'Given a scenario, modify enterprise capabilities to enhance security.'),
    '4.6': ('Identity and Access Management', 'Given a scenario, implement and maintain identity and access management.'),
    '4.7': ('Automation and Orchestration', 'Explain the importance of automation and orchestration related to secure operations.'),
    '4.8': ('Incident Response', 'Explain appropriate incident response activities.'),
    '4.9': ('Data Sources for Investigations', 'Given a scenario, use data sources to support an investigation.'),
    '5.1': ('Security Governance', 'Summarize elements of effective security governance.'),
    '5.2': ('Risk Management', 'Explain elements of the risk management process.'),
    '5.3': ('Third-Party Risk', 'Explain the processes associated with third-party risk assessment and management.'),
    '5.4': ('Security Compliance', 'Summarize elements of effective security compliance.'),
    '5.5': ('Audits and Assessments', 'Explain types and purposes of audits and assessments.'),
    '5.6': ('Security Awareness', 'Given a scenario, implement security awareness practices.'),
}

# CompTIA bank topics ("top") -> objective. Keys are (domain module, topic) since some
# topic names appear under more than one domain.
COMPTIA_MAP = {
    ('General Security Concepts', 'Security Controls'): '1.1',
    ('General Security Concepts', 'Fundamental Security Concepts'): '1.2',
    ('General Security Concepts', 'Change Management'): '1.3',
    ('General Security Concepts', 'Cryptographic Solutions'): '1.4',
    ('General Security Concepts', 'Data Protection'): '3.3',
    ('Threats, Vulnerabilities, and Mitigations', 'Threat Actors'): '2.1',
    ('Threats, Vulnerabilities, and Mitigations', 'Social Engineering'): '2.2',
    ('Threats, Vulnerabilities, and Mitigations', 'Threat Vectors and Attack Surfaces'): '2.2',
    ('Threats, Vulnerabilities, and Mitigations', 'Supply Chain Risk'): '2.2',
    ('Threats, Vulnerabilities, and Mitigations', 'Vulnerability Types'): '2.3',
    ('Threats, Vulnerabilities, and Mitigations', 'Vulnerabilities and Attacks'): '2.3',
    ('Threats, Vulnerabilities, and Mitigations', 'Application Vulnerabilities'): '2.3',
    ('Threats, Vulnerabilities, and Mitigations', 'Indicators of Malicious Activity'): '2.4',
    ('Threats, Vulnerabilities, and Mitigations', 'Malware'): '2.4',
    ('Threats, Vulnerabilities, and Mitigations', 'Malicious Activity'): '2.4',
    ('Threats, Vulnerabilities, and Mitigations', 'Indicators of Compromise'): '2.4',
    ('Threats, Vulnerabilities, and Mitigations', 'Physical Security'): '1.2',
    ('Threats, Vulnerabilities, and Mitigations', 'Mitigation Techniques'): '2.5',
    ('Threats, Vulnerabilities, and Mitigations', 'Hardening'): '2.5',
    ('Threats, Vulnerabilities, and Mitigations', 'Risk Concepts'): '5.2',
    ('Security Architecture', 'Architecture Models'): '3.1',
    ('Security Architecture', 'Security Architecture'): '3.1',
    ('Security Architecture', 'Security Infrastructure'): '3.2',
    ('Security Architecture', 'Enterprise Infrastructure Security'): '3.2',
    ('Security Architecture', 'Enterprise Infrastructure'): '3.2',
    ('Security Architecture', 'Network Security'): '3.2',
    ('Security Architecture', 'Data Protection'): '3.3',
    ('Security Architecture', 'Resilience and Recovery'): '3.4',
    ('Security Architecture', 'Cyber Resilience and Redundancy'): '3.4',
    ('Security Architecture', 'Identity and Access Management'): '4.6',
    ('Security Operations', 'Security Techniques'): '4.1',
    ('Security Operations', 'Securing Computing Resources'): '4.1',
    ('Security Operations', 'Asset Management'): '4.2',
    ('Security Operations', 'Vulnerability Management'): '4.3',
    ('Security Operations', 'Alerting and Monitoring'): '4.4',
    ('Security Operations', 'Security Alerting and Monitoring'): '4.4',
    ('Security Operations', 'Security Monitoring'): '4.4',
    ('Security Operations', 'Enhancing Enterprise Security'): '4.5',
    ('Security Operations', 'Identity and Access Management'): '4.6',
    ('Security Operations', 'Automation and Orchestration'): '4.7',
    ('Security Operations', 'Incident Response'): '4.8',
    ('Security Operations', 'Digital Forensics'): '4.8',
    ('Security Operations', 'Investigating an Incident'): '4.9',
    ('Security Operations', 'Data Sources for Investigation'): '4.9',
    ('Security Program Management and Oversight', 'Security Governance'): '5.1',
    ('Security Program Management and Oversight', 'Governance and Compliance'): '5.1',
    ('Security Program Management and Oversight', 'Governance'): '5.1',
    ('Security Program Management and Oversight', 'Risk Management'): '5.2',
    ('Security Program Management and Oversight', 'Business Continuity and Disaster Recovery'): '3.4',
    ('Security Program Management and Oversight', 'Third-party Vendor Risks'): '5.3',
    ('Security Program Management and Oversight', 'Third-Party Risk Management'): '5.3',
    ('Security Program Management and Oversight', 'Security Compliance'): '5.4',
    ('Security Program Management and Oversight', 'Compliance'): '5.4',
    ('Security Program Management and Oversight', 'Audits and Assessments'): '5.5',
    ('Security Program Management and Oversight', 'Security Awareness'): '5.6',
    ('Security Program Management and Oversight', 'Security Awareness Practices'): '5.6',
}
CHANGE_WORDS = re.compile(r'change|backout|maintenance window|dependency|allow list', re.I)


def load_questions(filename):
    text = open(os.path.join(root, filename), encoding='utf-8').read()
    start = text.index('const questions = [') + len('const questions = ')
    end = text.index('\n];', start) + 2
    return json.loads(text[start:end])


def comptia_objective(q):
    if (q['m'], q['top']) == ('General Security Concepts', 'Asset and Change Management'):
        return '1.3' if CHANGE_WORDS.search(q['sub']) else '4.2'
    return COMPTIA_MAP[(q['m'], q['top'])]


def dion_objective(q):
    m = re.match(r'Objective (\d\.\d)', q['sub'])
    if m:
        return m.group(1)
    m = re.search(r'OBJ:?\s*(\d\.\d)', ' '.join(q['e']))
    return m.group(1)


merged = []  # both banks, tagged with 'src'; split into one page per bank below
for src, filename, objective_of in (('CompTIA', 'security-plus.html', comptia_objective),
                                     ('Dion', 'dion-security-plus.html', dion_objective)):
    for q in load_questions(filename):
        obj = objective_of(q)
        assert obj in OBJECTIVES, (src, obj, q['q'][:60])
        q = dict(q)
        q['obj'] = obj
        q['src'] = src
        if src == 'Dion':
            q['top'] = OBJECTIVES[obj][0]
            q['sub'] = ''
        q.pop('m', None)
        merged.append(q)

# Stable per-question ids so saved progress survives rebuilds.
seen = set()
for q in merged:
    base = hashlib.sha1((q['src'] + '\n' + q['q'] + '\n' + '|'.join(q.get('o', []))).encode()).hexdigest()
    qid = base[:10]
    n = 0
    while qid in seen:
        n += 1
        qid = hashlib.sha1((base + str(n)).encode()).hexdigest()[:10]
    seen.add(qid)
    q['id'] = qid

PAGES = [
    {'src': 'CompTIA', 'file': 'security-plus-topics.html', 'title': 'Security+ by Topic', 'badge': 'S+',
     'theme': 'theme-comptia', 'crumb': 'CompTIA bank &middot; By topic',
     'subtitle': 'CompTIA question bank &middot; 864 questions grouped by SY0-701 objective. Pick a short set to practice.'},
    {'src': 'Dion', 'file': 'dion-security-plus-topics.html', 'title': 'Dion Security+ by Topic', 'badge': 'D',
     'theme': 'theme-dion', 'crumb': 'Dion bank &middot; By topic',
     'subtitle': 'Jason Dion question bank &middot; 540 questions grouped by SY0-701 objective. Pick a short set to practice.'},
]

template = open(os.path.join(root, 'scripts', 'topics_template.html'), encoding='utf-8').read()
banks = {}  # question ids per bank, used by the hub to show progress

for page in PAGES:
    bank = [q for q in merged if q['src'] == page['src']]
    objectives = []
    for key, (short, full) in OBJECTIVES.items():
        qs = sorted((q for q in bank if q['obj'] == key), key=lambda q: q['id'])
        if not qs:
            continue
        n_sets = math.ceil(len(qs) / SET_SIZE)
        sets = [[q['id'] for q in qs[i * len(qs) // n_sets:(i + 1) * len(qs) // n_sets]] for i in range(n_sets)]
        objectives.append({'id': key, 'domain': int(key[0]), 'short': short, 'full': full, 'sets': sets})

    order = {qid: i for i, qid in enumerate(qid for o in objectives for s in o['sets'] for qid in s)}
    bank.sort(key=lambda q: order[q['id']])

    data = (
        'const DOMAINS = ' + json.dumps(DOMAINS) + ';\n'
        'const OBJECTIVES = ' + json.dumps(objectives, indent=1) + ';\n'
        'const questions = [\n' + ',\n'.join(json.dumps(q, ensure_ascii=False).replace('<', '\\u003c') for q in bank) + '\n];\n'
    )
    out = template
    for k in ('title', 'badge', 'subtitle', 'theme', 'crumb'):
        out = out.replace(f'__{k.upper()}__', page[k])
    out = out.replace('/*__DATA__*/', data)
    open(os.path.join(root, page['file']), 'w', encoding='utf-8').write(out)

    banks[page['src']] = [q['id'] for q in bank]
    print(page['file'], len(bank), 'questions in', sum(len(o['sets']) for o in objectives), 'sets')
    for o in objectives:
        print(f"  {o['id']} {o['short']:<34} {sum(map(len, o['sets'])):>3} q, {len(o['sets'])} sets")

with open(os.path.join(root, 'assets', 'banks.json'), 'w', encoding='utf-8') as f:
    json.dump(banks, f, separators=(',', ':'))
