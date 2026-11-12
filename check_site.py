from html.parser import HTMLParser
from pathlib import Path
import re
import sys


class PrivacyHeading(HTMLParser):
    def __init__(self):
        super().__init__()
        self.in_vi = False
        self.in_heading = False
        self.heading = ''

    def handle_starttag(self, tag, attrs):
        if tag == 'section' and dict(attrs).get('id') == 'vi':
            self.in_vi = True
        elif self.in_vi and tag == 'h2' and not self.heading:
            self.in_heading = True

    def handle_endtag(self, tag):
        if tag == 'h2':
            self.in_heading = False
        elif tag == 'section' and self.in_vi:
            self.in_vi = False

    def handle_data(self, data):
        if self.in_heading:
            self.heading += data


root = Path(__file__).resolve().parent
errors = []
checked = 0
for path in sorted(root.rglob('*')):
    if not path.is_file() or any(part in {'.git', '.agents', '.codex'} for part in path.relative_to(root).parts):
        continue
    if path.suffix.lower() not in {'.html', '.md'} and path.name != 'LICENSE':
        continue
    checked += 1
    try:
        content = path.read_text(encoding='utf-8')
    except UnicodeDecodeError as exc:
        errors.append(f'{path.relative_to(root)}: invalid UTF-8: {exc}')
        continue
    for match in re.finditer(r'[^\W\d_]\?[^\W\d_]', content, re.UNICODE):
        errors.append(f'{path.relative_to(root)}: suspicious sequence {match.group()!r} at character {match.start()}')

try:
    parser = PrivacyHeading()
    parser.feed((root / 'privacy.html').read_text(encoding='utf-8'))
    if not parser.heading.strip():
        errors.append('privacy.html: Vietnamese heading not found')
    else:
        print(f'Vietnamese privacy heading: {parser.heading.strip()}')
except UnicodeDecodeError:
    pass  # Already reported above.

for error in errors:
    print(error, file=sys.stderr)
if errors:
    sys.exit(1)
print(f'PASS: {checked} files are valid UTF-8; no letter-question-mark-letter sequences found.')
