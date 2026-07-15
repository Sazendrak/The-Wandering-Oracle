import os
import re
import html
import urllib.parse
from pathlib import Path

def get_valid_paths(base_dir):
    valid_paths = set()
    for root, dirs, files in os.walk(base_dir):
        for file in files:
            full_path = os.path.join(root, file)
            rel_path = os.path.relpath(full_path, base_dir).replace('\\', '/')
            valid_paths.add(rel_path)
    return valid_paths

def normalize_target(target):
    target = urllib.parse.unquote(target)
    target = target.replace('\\', '/')
    return target.strip('/')

def check_site():
    base_dir = "docs_site"
    valid_paths_lower = {p.lower() for p in valid_paths}
    html_files = [p for p in valid_paths if p.endswith('.html')]

    broken_links = []
    misclassified = []

    link_regex = re.compile(r'(?:href|src)=[\'"]([^\'"]+)[\'"]')

    for f in html_files:
        filepath = os.path.join(base_dir, f)
        with open(filepath, 'r', encoding='utf-8') as file:
            content = file.read()

        main_match = re.search(r'<article[^>]*>(.*?)</article>', content, re.DOTALL | re.IGNORECASE)
        if main_match:
            text = main_match.group(1).lower()
        else:
            text = content.lower()

        is_core = '/core/' in f
        is_homebrew = '/homebrew/' in f

        if is_core and '[approved homebrew]' in text:
            misclassified.append((f, "Contains [Approved Homebrew] tag in Core/SRD page"))
        if is_homebrew and '[official srd content]' in text:
            misclassified.append((f, "Contains [Official SRD Content] tag in Homebrew page"))

        for match in link_regex.finditer(content):
            raw_url = match.group(1)
            url = html.unescape(raw_url)

            if url.startswith(('http://', 'https://', 'mailto:', 'data:', '#')):
                continue

            url_no_frag = url.split('#')[0]
            if not url_no_frag:
                continue

            if url_no_frag.startswith('/The-Wandering-Oracle/'):
                target_path = url_no_frag[len('/The-Wandering-Oracle/'):]
            elif url_no_frag.startswith('/'):
                target_path = url_no_frag[1:]
            else:
                curr_dir = os.path.dirname(f)
                target_path = os.path.normpath(os.path.join(curr_dir, url_no_frag))

            target_stripped = normalize_target(target_path)

            if target_stripped == '' or target_stripped == '.':
                if 'index.html' not in valid_paths:
                    broken_links.append((f, raw_url, "Root index.html missing"))
                continue

            possible = [
                target_stripped,
                target_stripped + '/index.html',
                target_stripped + '.html',
            ]

            found = False
            for p in possible:
                if p in valid_paths:
                    found = True
                    break
                if p.lower() in valid_paths_lower:
                    found = True
                    break

                p_alt1 = p.replace('-', ' ')
                p_alt2 = p.replace(' ', '-')
                p_alt3 = p.replace('_', '-')

                for alt in [p_alt1, p_alt2, p_alt3]:
                    if alt in valid_paths or alt.lower() in valid_paths_lower:
                        found = True
                        break
                if found:
                    break

            if not found:
                broken_links.append((f, raw_url, "Target not found"))

    return broken_links, misclassified

def check_data():
    base_dir = Path("data")
    srd_dir = base_dir / "srd"
    hb_avrae = base_dir / "avrae"
    hb_handbook = base_dir / "handbooks"

    misclassified = []

    if not srd_dir.exists():
        return misclassified

    for f in srd_dir.glob("*.json"):
        try:
            with open(f, 'r', encoding='utf-8') as file:
                content = file.read().lower()
                if 'homebrew' in content:
                    misclassified.append((str(f), "Found 'homebrew' string in SRD JSON"))
        except Exception as e:
            print(f"Error reading {f}: {e}")

    for d in [hb_avrae, hb_handbook]:
        if not d.exists():
            continue
        for f in d.glob("*.json"):
            try:
                with open(f, 'r', encoding='utf-8') as file:
                    content = file.read().lower()
                    if 'official srd' in content or 'srd content' in content:
                        misclassified.append((str(f), "Found 'official srd' string in Homebrew JSON"))
            except Exception as e:
                print(f"Error reading {f}: {e}")

    return misclassified

def generate_report():
    bl, mc_site = check_site()
    mc_data = check_data()

    mc = set(mc_site) | set(mc_data)

    with open('error_index.md', 'w', encoding='utf-8') as out:
        out.write("# Comprehensive Error Index\n\n")
        out.write(f"## Broken Links ({len(set(bl))})\n")
        for src, url, target in sorted(set(bl)):
            out.write(f"- Source: `{src}` -> Link: `{url}` (Reason: `{target}`)\n")

        out.write(f"\n## Misclassified Content ({len(mc)})\n")
        for src, reason in sorted(set(mc)):
            out.write(f"- File: `{src}` -> {reason}\n")

    print(f"Generated report with {len(set(bl))} broken links and {len(mc)} misclassifications.")

if __name__ == '__main__':
    generate_report()
