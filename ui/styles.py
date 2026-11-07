"""Custom CSS and small HTML building blocks for the SolarSense interface."""

import html

AMBER = "#F5A623"
NAVY = "#1B2A41"
TEAL = "#2A9D8F"
CORAL = "#E76F51"
SKY = "#4C8BF5"

CSS = f"""
<style>
.block-container {{ padding-top: 2rem; padding-bottom: 3rem; max-width: 1200px; }}

.ss-hero {{
    background: linear-gradient(120deg, {NAVY} 0%, #24406b 55%, #c9821a 100%);
    border-radius: 18px; padding: 2.2rem 2.4rem; color: #ffffff; margin-bottom: 1.4rem;
}}
.ss-hero h1 {{ color: #ffffff; font-size: 2.4rem; margin: 0 0 .4rem 0; padding: 0; }}
.ss-hero p {{ color: #f3f4f6; font-size: 1.08rem; margin: 0; max-width: 760px; line-height: 1.55; }}
.ss-hero .ss-tag {{
    display: inline-block; background: rgba(245,166,35,.22); color: #FFD27A;
    border: 1px solid rgba(245,166,35,.55); border-radius: 999px;
    padding: .2rem .8rem; font-size: .8rem; font-weight: 600; margin-bottom: .9rem; letter-spacing: .03em;
}}

.ss-card {{
    background: #ffffff; border: 1px solid #ece6d8; border-radius: 14px;
    padding: 1.1rem 1.2rem; height: 100%; box-shadow: 0 1px 3px rgba(27,42,65,.06);
}}
.ss-card h4 {{ margin: .2rem 0 .4rem 0; color: {NAVY}; font-size: 1.02rem; }}
.ss-card p {{ margin: 0; color: #4b5563; font-size: .92rem; line-height: 1.5; }}
.ss-card .ss-icon {{ font-size: 1.6rem; }}

.ss-kpi {{
    background: #ffffff; border: 1px solid #ece6d8; border-left: 5px solid {AMBER};
    border-radius: 12px; padding: .85rem 1rem; height: 100%;
}}
.ss-kpi .lbl {{ font-size: .78rem; color: #6b7280; text-transform: uppercase; letter-spacing: .05em; }}
.ss-kpi .val {{ font-size: 1.55rem; font-weight: 700; color: {NAVY}; line-height: 1.25; margin-top: .15rem; }}
.ss-kpi .sub {{ font-size: .8rem; color: #6b7280; margin-top: .1rem; }}

.ss-verdict {{
    background: #FFF8E7; border: 1px solid #F5D58C; border-radius: 14px;
    padding: 1.2rem 1.4rem; margin-bottom: 1rem;
}}
.ss-verdict.bad {{ background: #FDECEA; border-color: #F3B4A6; }}
.ss-verdict h3 {{ margin: 0 0 .35rem 0; color: {NAVY}; font-size: 1.15rem; }}
.ss-verdict p {{ margin: 0; color: #1f2937; font-size: 1.02rem; line-height: 1.55; }}

.ss-badge {{
    display: inline-block; border-radius: 999px; padding: .15rem .65rem; font-size: .78rem;
    font-weight: 600; margin: .45rem .35rem 0 0; background: #eef2f7; color: {NAVY};
}}
.ss-badge.good {{ background: #E3F4F1; color: #1d7064; }}
.ss-badge.warn {{ background: #FFF1D6; color: #9a6206; }}
.ss-badge.bad  {{ background: #FDECEA; color: #a3402a; }}

.ss-rule {{
    display: inline-block; font-family: monospace; font-size: .75rem; font-weight: 700;
    background: {NAVY}; color: #ffffff; border-radius: 6px; padding: .05rem .4rem; margin-right: .45rem;
}}
.ss-item {{
    border-radius: 10px; padding: .65rem .9rem; margin-bottom: .5rem; font-size: .95rem; line-height: 1.5;
}}
.ss-item.warning {{ background: #FDECEA; border-left: 4px solid {CORAL}; }}
.ss-item.recommendation {{ background: #E3F4F1; border-left: 4px solid {TEAL}; }}
.ss-item.note {{ background: #EEF3FB; border-left: 4px solid {SKY}; }}

.ss-step {{ text-align: center; padding: .6rem; }}
.ss-step .num {{
    display: inline-block; width: 2.1rem; height: 2.1rem; line-height: 2.1rem; border-radius: 50%;
    background: {AMBER}; color: {NAVY}; font-weight: 800; margin-bottom: .4rem;
}}
.ss-step h5 {{ margin: .1rem 0 .25rem 0; color: {NAVY}; font-size: .98rem; }}
.ss-step p {{ margin: 0; font-size: .85rem; color: #4b5563; }}

.ss-section-title {{ color: {NAVY}; font-weight: 700; font-size: 1.25rem; margin: 1.2rem 0 .6rem 0; }}
.ss-footer {{ text-align: center; color: #9ca3af; font-size: .8rem; margin-top: 2.5rem; }}
</style>
"""


def esc(text):
    return html.escape(str(text))


def hero(title, subtitle, tag):
    return (f'<div class="ss-hero"><span class="ss-tag">{esc(tag)}</span>'
            f'<h1>{esc(title)}</h1><p>{esc(subtitle)}</p></div>')


def card(icon, title, text):
    return (f'<div class="ss-card"><div class="ss-icon">{icon}</div>'
            f'<h4>{esc(title)}</h4><p>{esc(text)}</p></div>')


def kpi(label, value, sub=""):
    return (f'<div class="ss-kpi"><div class="lbl">{esc(label)}</div>'
            f'<div class="val">{esc(value)}</div><div class="sub">{esc(sub)}</div></div>')


def step(num, title, text):
    return (f'<div class="ss-step"><div class="num">{num}</div>'
            f'<h5>{esc(title)}</h5><p>{esc(text)}</p></div>')


def badge(text, kind=""):
    return f'<span class="ss-badge {kind}">{esc(text)}</span>'


def verdict(title, text, badges_html="", bad=False):
    cls = "ss-verdict bad" if bad else "ss-verdict"
    return f'<div class="{cls}"><h3>{esc(title)}</h3><p>{esc(text)}</p>{badges_html}</div>'


def advice_item(kind, rule_id, text):
    return f'<div class="ss-item {kind}"><span class="ss-rule">{esc(rule_id)}</span>{esc(text)}</div>'


def section_title(text):
    return f'<div class="ss-section-title">{esc(text)}</div>'
