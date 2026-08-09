from __future__ import annotations

import html
import re

from .config import TemplateMode, validate_template_mode


def render_inline(text: str) -> str:
    s = html.escape(text)
    s = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', s)
    s = re.sub(
        r'\[([^\]]+)\]\((https?://[^\s)]+)\)',
        r"<a href='\2' style='color:#2563eb'>\1</a>",
        s,
    )
    return s


def md_to_html(md: str, template_mode: str | TemplateMode = TemplateMode.WEEKLY_FULL) -> str:
    resolved_template_mode = validate_template_mode(template_mode)
    lines = md.splitlines()
    out: list[str] = []
    in_ul = False
    for line in lines:
        if not line.strip():
            if in_ul:
                out.append('</ul>')
                in_ul = False
            continue
        if line.startswith('# '):
            if in_ul:
                out.append('</ul>')
                in_ul = False
            out.append(f"<h1 style='font-size:24px;margin:20px 0 10px;color:#1f2937'>{html.escape(line[2:])}</h1>")
        elif line.startswith('## '):
            if in_ul:
                out.append('</ul>')
                in_ul = False
            out.append(f"<h2 style='font-size:20px;margin:22px 0 8px;color:#374151;border-top:1px solid #e5e7eb;padding-top:14px'>{html.escape(line[3:])}</h2>")
        elif line.startswith('### '):
            if in_ul:
                out.append('</ul>')
                in_ul = False
            out.append(f"<h3 style='font-size:17px;margin:16px 0 6px;color:#374151'>{html.escape(line[4:])}</h3>")
        elif line.startswith('- '):
            if not in_ul:
                out.append("<ul style='margin:8px 0 14px 24px;padding:0'>")
                in_ul = True
            s = render_inline(line[2:])
            out.append(f"<li style='margin:6px 0;line-height:1.45'>{s}</li>")
        else:
            if in_ul:
                out.append('</ul>')
                in_ul = False
            s = render_inline(line).replace('  ', '&nbsp; ')
            out.append(f"<p style='line-height:1.5;margin:8px 0'>{s}</p>")
    if in_ul:
        out.append('</ul>')
    if resolved_template_mode == TemplateMode.WEEKLY_FULL:
        body_open = "<html><body style='font-family:-apple-system,BlinkMacSystemFont,Segoe UI,Arial,sans-serif;color:#111827;max-width:820px'>"
    else:
        mode_attr = html.escape(resolved_template_mode.value, quote=True)
        body_open = f"<html><body data-template-mode='{mode_attr}' style='font-family:-apple-system,BlinkMacSystemFont,Segoe UI,Arial,sans-serif;color:#111827;max-width:820px'>"
    return body_open + "\n".join(out) + "</body></html>"
