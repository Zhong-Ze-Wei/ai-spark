#!/usr/bin/env python3
"""Build the public, read-only archive using only the Python standard library."""
from pathlib import Path
from collections import defaultdict
import html
import json
import re

ROOT = Path(__file__).resolve().parents[1]
DATA = json.loads((ROOT / 'content/data.json').read_text())
EDITED = {t['id']: t for t in json.loads((ROOT / 'content/editedTopics.json').read_text())}
ED = json.loads((ROOT / 'content/editorial.json').read_text())
SECTIONS = json.loads((ROOT / 'content/sections.json').read_text())
SOURCES = {s['id']: s for s in DATA['sources']}
TOPICS = {t['id']: t for t in DATA['topics']}
PEOPLE = {p['nick']: p for p in DATA['people']}
DEBATES = {d['id']: d for d in DATA['debates']}
CATEGORIES = {c['id']: c for c in DATA['categories']}
GENERATED = []
SEARCH = []
CURRENT = ''


def e(value):
    return html.escape(str(value), quote=True)


def begin(path):
    global CURRENT
    CURRENT = path


def u(path=''):
    return '../' * CURRENT.count('/') + path


def title(t):
    return ED['topics'][t['id']][0]


def topic_link(tid, text=None):
    return f'<a href="{u("topics/" + tid + "/")}">{e(text or title(TOPICS[tid]))}</a>'


def person_link(nick):
    p = PEOPLE.get(nick)
    return f'<a href="{u("people/" + p["id"] + "/")}">{e(nick)}</a>' if p else e(nick)


def refs(ids):
    return '<span class="refs">' + ''.join(f'<a href="{u("sources/" + sid + "/")}" aria-label="查看 {e(SOURCES[sid]["speaker"])} 的原话">原话 {SOURCES[sid]["number"]}</a>' for sid in dict.fromkeys(ids)) + '</span>'


def rich(text):
    def replace(m):
        sid = m[1]
        assert sid in SOURCES, sid
        s = SOURCES[sid]
        return f'<a class="cite" href="{u("sources/" + sid + "/")}" aria-label="查看 {e(s["speaker"])} 的原话">[{s["number"]}]</a>'
    return re.sub(r'\[\[(s\d+)\]\]', replace, e(text)).replace('\n', '<br>')


def flat(obj):
    if isinstance(obj, str):
        return re.sub(r'\[\[s\d+\]\]', '', obj)
    if isinstance(obj, list):
        return ' '.join(flat(x) for x in obj)
    if isinstance(obj, dict):
        return ' '.join(flat(v) for k, v in obj.items() if k not in ('id', 'refs', 'related', 'topics', 'cat'))
    return ''


def search_record(kind, name, path, obj):
    SEARCH.append({'kind': kind, 'title': name, 'url': path, 'text': flat(obj)})


def intro(name, text='', eyebrow='', meta=''):
    kicker = f'<p class="eyebrow">{e(eyebrow)}</p>' if eyebrow else ''
    lead = f'<p class="lead">{e(text)}</p>' if text else ''
    scope = f'<p class="meta scope">{e(meta)}</p>' if meta else ''
    return f'<header class="intro">{kicker}<h1>{e(name)}</h1>{lead}{scope}</header>'


def crumbs(items):
    return '<nav class="crumbs" aria-label="所在位置">' + '<span aria-hidden="true">/</span>'.join(f'<a href="{u(path)}">{e(label)}</a>' for path, label in items) + '</nav>'


def topic_dates(t):
    dates = sorted({SOURCES[s]['date'][:10] for s in t['refs']})
    return dates[0] if dates[0] == dates[-1] else dates[0] + ' — ' + dates[-1]


def card(t, level=2):
    tid = t['id']
    return f'<article class="topic-card"><span class="eyebrow">{e(CATEGORIES[t["cat"]]["name"])}</span><h{level}>{topic_link(tid)}</h{level}><p>{e(ED["topics"][tid][1])}</p><a class="enter" href="{u("topics/" + tid + "/")}">看看大家怎么说 →</a></article>'


def topic_rows(ids):
    return '<ul class="plain-list">' + ''.join(f'<li><h3>{topic_link(tid)}</h3><p>{e(ED["topics"][tid][1])}</p></li>' for tid in dict.fromkeys(ids)) + '</ul>'


def linked_row(path, name, text='', meta=''):
    return f'<li>{f"<p class=meta>{e(meta)}</p>" if meta else ""}<h2><a href="{u(path)}">{e(name)}</a></h2>{f"<p>{e(text)}</p>" if text else ""}</li>'


def fold(label, body):
    return f'<details class="fold"><summary>{e(label)}</summary><div>{body}</div></details>'


def section(name, body):
    return f'<section class="topic-section"><h2>{e(name)}</h2>{body}</section>'


def all_debate_refs(d):
    return list(dict.fromkeys(s for v in d['voices'] for s in v['refs'])) + [s for s in d['refs'] if s not in {x for v in d['voices'] for x in v['refs']}]


def debate_voices(d):
    return '<div class="voices">' + ''.join(f'<article class="voice"><span class="who">{person_link(v["who"])}</span><p>{e(v["text"])}</p>{refs(v["refs"]) if v["refs"] else "<p class=meta>沿用既有讨论整理，未单列引文。</p>"}</article>' for v in d['voices']) + '</div>'


def quote(s, full=True):
    text = s['text']
    if not full and len(text) > 150:
        text = text[:150] + '…'
    return f'<figure class="source-quote"><figcaption class="source-meta">{person_link(s["speaker"])} · <time>{e(s["date"])}</time></figcaption><blockquote>{e(text)}</blockquote></figure>'


def diagram(tid):
    diagrams = {
        't19': ('<ol class="process"><li><b>需求与交接</b><small>等待与沟通</small></li><li><b class="emphasis">代码生成</b><small>可能加快的环节</small></li><li><b>审查与联调</b><small>仍需检查</small></li><li><b>上线与验收</b><small>最终交付</small></li></ol>', '读图提示：一个环节变快，不等于整条交付链同比变快。示意结构，不表示实际耗时。'),
        't12': ('<ol class="process"><li><b>试做一版</b><small>有边界的任务</small></li><li><b>获得证据</b><small>与目标、基准对照</small></li><li><b>修正方法</b><small>说明改什么、为什么</small></li><li><b>再验证</b><small>确认真的变好</small></li></ol>', '根据讨论整理的工作循环；每次重跑都需要新的证据。'),
        't23': ('<p class="value-equation">业务价值 × 使用概率 × 技术成功率<br>− 开发成本 − 运行成本 − 风险成本</p>', '数读在 7 月 13 日提出的思考公式，不是精确估值模型。'),
        't31': ('<ol class="process"><li><b>获得答案</b><small>知道知识与方法</small></li><li><b>判断情境</b><small>知道何时、怎样用</small></li><li><b>可靠交付</b><small>检查结果并承担责任</small></li></ol>', '整理者对讨论的拆解：这三步不能直接画等号。')
    }
    if tid not in diagrams:
        return ''
    body, caption = diagrams[tid]
    return f'<figure class="diagram">{body}<figcaption>{caption}</figcaption></figure>'


def tools(route):
    return f'<div class="reading-tools"><button type="button" data-save="{e(route)}" aria-pressed="false">收藏这篇</button><button type="button" data-copy-link>复制链接</button><button type="button" data-font="1" aria-label="增大正文字号">字号 ＋</button><button type="button" data-font="-1" aria-label="减小正文字号">字号 −</button></div>'


def page(name, body, nav='资料', description='', narrow=True):
    depth = '../' * CURRENT.count('/')
    navs = [('', '精选补课'), ('topics/', '话题追踪'), ('people/', '人物发言'), ('resources/', '资料')]
    links = ''.join(f'<a href="{u(path)}"{chr(32)+"aria-current=page" if label == nav else ""}>{label}</a>' for path, label in navs)
    qr = f'<div data-qr-current><img src="{u("assets/guanlan-invitation.png")}" width="420" height="672" alt="观澜群邀请卡，微信扫码加入，有效期为 2026 年 10 月 1 日前"></div><p class="notice" data-qr-expired hidden>这张群二维码已过期。请联系邀请你阅读的群友，获取新的入群方式。</p>'
    content = f'''<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="color-scheme" content="light dark"><meta name="robots" content="noindex,nofollow,noarchive"><meta name="description" content="{e(description or name + ' · 观澜群讨论精选')}"><title>{e(name)} · 观澜 / AI Sparks</title><link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 64 64'%3E%3Crect width='64' height='64' rx='12' fill='%23f7f5ef'/%3E%3Ctext x='8' y='46' font-size='44' fill='%2324352c'%3E澜%3C/text%3E%3C/svg%3E"><link rel="stylesheet" href="{u('assets/site/style.css')}"><script>try{{let t=JSON.parse(localStorage.getItem('sparks-v3-theme'));if(['light','dark'].includes(t))document.documentElement.dataset.theme=t;let z=Number(JSON.parse(localStorage.getItem('sparks-v3-font')));if(z>=16&&z<=24)document.documentElement.style.setProperty('--reading-size',z+'px')}}catch(e){{}}</script></head>
<body data-root="{depth or './'}"{' data-legacy-router' if not CURRENT else ''}><a class="skip" href="#main">跳到正文</a><header class="site-header"><a class="brand" href="{u() or './'}" aria-label="观澜首页"><strong>观澜<b>.</b></strong><span>AI SPARKS</span></a><nav class="primary-nav" aria-label="阅读方式">{links}</nav><div class="header-tools"><a href="{u('search/')}">搜索</a><button class="join-trigger" type="button" data-join>加入我们 ↗</button></div></header><main id="main" class="site-main">{'<div class=narrow>' if narrow else ''}{body}{'</div>' if narrow else ''}</main>
<footer class="site-footer"><span>真实问题 · 深入讨论 · 彼此校正 · 共同建设</span><nav><a href="{u('about/')}">关于观澜</a><a href="{u('archive/')}">完整档案</a><a href="{u('saved/')}">我的收藏</a><button type="button" data-theme-toggle>切换深浅色</button></nav><p>收录 2026.07.12—09.15 的讨论。观点与工具体验保留当时语境。<a href="{u('about/#correction')}">纠错与删改</a></p></footer>
<dialog class="join-dialog" id="join-dialog" aria-labelledby="join-title"><div class="dialog-top"><h2 id="join-title">加入观澜</h2><button type="button" data-close>关闭</button></div>{qr}<div class="link-row"><a href="{u('assets/join-qr-original.jpg')}" download>保存微信原图</a><a href="{u('assets/guanlan-invitation.png')}" download>保存邀请卡</a><a href="{u('join/')}">单独打开</a></div><p class="meta">原图注明 10 月 1 日前有效；能否入群以微信提示为准。</p></dialog><script src="{u('assets/site/app.js')}" defer></script></body></html>'''
    path = ROOT / CURRENT / 'index.html'
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)
    GENERATED.append(str(path.relative_to(ROOT)))


def index_pages(folder, records, name, lead, render, size=20, nav='资料'):
    total = (len(records) + size - 1) // size
    for n in range(total):
        path = folder + ('/' if n == 0 else f'/page-{n + 1}/')
        begin(path)
        items = records[n * size:(n + 1) * size]
        body = intro(name, lead, meta=f'共 {len(records)} 条 · 第 {n + 1} / {total} 页')
        body += '<ul class="plain-list">' + ''.join(render(x) for x in items) + '</ul>'
        if total > 1:
            body += '<nav class="pagination" aria-label="分页">'
            for k in range(total):
                target = folder + ('/' if k == 0 else f'/page-{k + 1}/')
                body += f'<span aria-current="page">{k + 1}</span>' if k == n else f'<a href="{u(target)}">{k + 1}</a>'
            body += '</nav>'
        page(name, body, nav)


begin('')
body = '<section class="home-intro home-portal" aria-labelledby="community-name"><header class="intro"><h1 id="community-name">观澜 <span>· AI Sparks</span></h1><p class="community-slogan">AI 时代最好的学习方式，<br>就是跟人聊。</p><p class="community-purpose">借具体变化，看更大的时代走势。</p><p class="community-description">一群对技术好奇、愿意多想一层的人，围绕真实问题交换经验、彼此校正。</p><p class="community-values"><span>真实问题</span><span>深入讨论</span><span>彼此校正</span><span>共同建设</span></p>'
body += f'<a class="text-link" href="{u("about/")}">认识这个群 →</a></header><a class="home-art" href="{u("about/#theme")}" aria-label="查看观澜主题大图"><img src="{u("assets/guanlan-theme.png")}" width="1122" height="1402" alt="观澜水墨主题图：河流与围桌交谈的人们"></a></section>'
body += f'<section aria-labelledby="featured-heading"><div class="section-bar featured-heading"><div><h2 id="featured-heading">把没来得及看的讨论，补回来。</h2><p class="meta">本期精选 · 收录 2026.07.12—09.15 的讨论</p></div><a href="{u("topics/")}">全部话题 →</a></div>'
body += '<div class="cards home-cards">' + ''.join(card(TOPICS[tid], level=3) for tid in ED['featured']) + '</div></section>'
body += '<div class="section-bar"><h2>还有什么值得聊？</h2></div><div class="category-list">'
for c in DATA['categories']:
    body += f'<a class="category-item" href="{u("categories/" + c["id"] + "/")}"><strong>{e(c["name"])}</strong><small>{e(c["desc"])}</small></a>'
body += '</div>'
page('借具体变化，看更大的时代走势', body, '精选补课', description='观澜 · AI Sparks。AI 时代最好的学习方式，就是跟人聊。围绕真实问题交换经验、彼此校正；从群友的讨论里看见更大的时代走势。', narrow=False)

begin('topics/')
body = intro('从你关心的问题开始。', '38 个话题，按问题分类。每篇都有完整分析、相关分歧和原话入口。')
body += '<div class="category-list">'
for c in DATA['categories']:
    n = sum(t['cat'] == c['id'] for t in DATA['topics'])
    body += f'<a class="category-item" href="{u("categories/" + c["id"] + "/")}"><strong>{e(c["name"])}</strong><small>{e(c["desc"])} · {n} 篇</small></a>'
body += '</div><div class="section-bar"><h2>本期较新的讨论</h2></div><div class="cards">'
body += ''.join(card(t) for t in sorted(DATA['topics'], key=lambda t: max(SOURCES[s]['date'] for s in t['refs']), reverse=True)[:6]) + '</div>'
body += f'<div class="link-row"><a href="{u("timeline/")}">按日期回看</a><a href="{u("debates/")}">看不同意见</a><a href="{u("questions/")}">看还没解决的问题</a></div>'
page('话题追踪', body, '话题追踪', narrow=False)

for c in DATA['categories']:
    begin('categories/' + c['id'] + '/')
    body = crumbs([('topics/', '全部分类')]) + intro(c['name'], c['desc'])
    body += '<div class="cards">' + ''.join(card(t) for t in DATA['topics'] if t['cat'] == c['id']) + '</div>'
    page(c['name'], body, '话题追踪', narrow=False)

for t in DATA['topics']:
    tid = t['id']
    primary = DEBATES.get(ED['primaryDebates'].get(tid))
    related_debates = [d for d in DATA['debates'] if tid in d['topics']]
    events = sorted([x for x in DATA['events'] if tid in x['topics']], key=lambda x: x['date'])
    begin('topics/' + tid + '/')
    body = crumbs([('topics/', '话题'), ('categories/' + t['cat'] + '/', CATEGORIES[t['cat']]['name'])])
    body += intro(title(t), eyebrow=CATEGORIES[t['cat']]['name'], meta='相关发言 · ' + topic_dates(t))
    body += '<p class="eyebrow">整理提要</p><p class="answer">' + e(ED['summaries'].get(tid, t['deck'])) + '</p>'
    if primary:
        body += section('大家怎么说', debate_voices(primary))
        body += f'<p class="status">{e(primary["status"])}</p><p>{e(primary["outcome"])}</p><p class="boundary">{e(primary["not_claim"])}</p>'
        body += f'<p class="link-row"><a href="{u("debates/" + primary["id"] + "/")}">展开这场分歧 →</a></p>'
    else:
        picked = []
        for sid in t['refs']:
            s = SOURCES[sid]
            if s['speaker'] not in {x['speaker'] for x in picked}:
                picked.append(s)
            if len(picked) == 2:
                break
        body += section('讨论从这些话开始', '<div class="voices">' + ''.join(f'<article class="voice"><span class="who">{person_link(s["speaker"])}</span><blockquote class="quote-short">{e(s["text"] if len(s["text"]) <= 150 else s["text"][:150] + "…")}</blockquote>{refs([s["id"]])}</article>' for s in picked) + '</div>')
        body += '<p class="boundary">' + e(t['boundary']) + '</p>'
    body += diagram(tid)
    body += f'<div class="actions"><a class="button primary" href="{u("topics/" + tid + "/analysis/")}">为什么这样整理 →</a><a class="button" href="{u("topics/" + tid + "/sources/")}">查看相关原话</a></div>'
    more = [d for d in related_debates if d != primary]
    if more or events:
        tracking = '<ul class="plain-list">'
        for ev in events:
            tracking += linked_row('events/' + ev['id'] + '/', ev['title'], ev['desc'], ev['date'])
        for d in more:
            tracking += linked_row('debates/' + d['id'] + '/', d['title'], d['question'], d['when'] + ' · ' + d['status'])
        tracking += '</ul><p class="meta">按已有记录串联相关讨论，不把跨日期材料写成一场连续对话。</p>'
        body += fold('继续追踪这个问题', tracking)
    body += fold('还有哪些条件没说完？', f'<p>{e(t["boundary"])}</p><p>{e(t["question"])}</p>')
    body += section('接着看', topic_rows(t['related'])) + tools('topic/' + tid)
    page(title(t), body, '话题追踪', ED['topics'][tid][1])
    search_record('话题', title(t), 'topics/' + tid + '/', [t, EDITED[tid]])

    begin('topics/' + tid + '/analysis/')
    body = crumbs([('topics/' + tid + '/', title(t))]) + intro('为什么这样整理', eyebrow=title(t))
    body += '<div class="prose">' + ''.join(f'<section><h2>{e(s["head"])}</h2><p>{rich(s["body"])}</p></section>' for s in EDITED[tid]['sections']) + '</div>'
    body += '<p class="boundary">' + e(t['boundary']) + '</p>'
    body += section('还可以继续问', '<p>' + e(t['question']) + '</p>')
    original = ''.join(f'<section><h3>{e(s["head"])}</h3><p>{rich(s["body"])}</p></section>' for s in t['sections'])
    body += fold('核对早期整理措辞', '<p class="meta">以下保留早期主题稿，供核对表达差异。它同样是整理文字，不是聊天原话。</p><div class="prose">' + original + '</div>')
    body += f'<div class="actions"><a class="button" href="{u("topics/" + tid + "/sources/")}">核对相关原话</a><a class="text-link" href="{u("topics/" + tid + "/")}">回到话题</a></div>' + tools('topic/' + tid)
    page(title(t) + ' · 完整分析', body, '话题追踪')

    begin('topics/' + tid + '/sources/')
    ids = set(t['refs'])
    for s in EDITED[tid]['sections']:
        ids.update(re.findall(r'\[\[(s\d+)\]\]', s['body']))
    if primary:
        ids.update(all_debate_refs(primary))
    body = crumbs([('topics/' + tid + '/', title(t))]) + intro('回到原话', eyebrow=title(t), meta='按发言时间排列 · ' + str(len(ids)) + ' 段')
    for sid in sorted(ids, key=lambda x: SOURCES[x]['date']):
        s = SOURCES[sid]
        body += quote(s) + f'<p class="text-link"><a href="{u("sources/" + sid + "/")}">查看出处与引用位置 →</a></p>'
    page(title(t) + ' · 原话', body, '话题追踪')

for d in DATA['debates']:
    begin('debates/' + d['id'] + '/')
    body = crumbs([('debates/', '全部分歧')]) + intro(d['title'], d['question'], meta=d['when'] + ' · ' + d['status'])
    body += debate_voices(d) + section('讨论走到了哪里', f'<p>{e(d["outcome"])}</p><p class="boundary">{e(d["not_claim"])}</p>{refs(d["refs"])}')
    body += fold('按时间核对原话', ''.join(quote(SOURCES[sid]) + refs([sid]) for sid in sorted(all_debate_refs(d), key=lambda x: SOURCES[x]['date'])))
    body += section('放回话题里看', topic_rows(d['topics'])) + tools('debate/' + d['id'])
    page(d['title'], body, '话题追踪')
    search_record('分歧', d['title'], 'debates/' + d['id'] + '/', d)
index_pages('debates', DATA['debates'], '看见不同意见。', '有的补充条件，有的明确认可，有的仍未解决。', lambda d: linked_row('debates/' + d['id'] + '/', d['title'], d['question'], d['when'] + ' · ' + d['status']), nav='话题追踪')

begin('people/')
body = intro('谁在讨论什么？', '按昵称找观点，按时间看发言。人物页只记录本期材料中的表达与参与。')
body += '<div class="person-grid">'
for p in DATA['people']:
    body += f'<a class="person-card" href="{u("people/" + p["id"] + "/")}"><strong>{e(p["nick"])}</strong><span>{e(p["role"])}</span></a>'
body += '</div>'
page('人物发言', body, '人物发言', narrow=False)
for p in DATA['people']:
    pid = p['id']
    own = sorted([s for s in DATA['sources'] if s['speaker'] == p['nick']], key=lambda x: x['date'], reverse=True)
    tids = [t['id'] for t in DATA['topics'] if any(SOURCES[sid]['speaker'] == p['nick'] for sid in t['refs'])]
    begin('people/' + pid + '/')
    body = crumbs([('people/', '全部人物')]) + intro(p['nick'] + '说过什么？', p['intro'])
    body += fold('本期参与记录', f'<p>{e(p["contribution"])}</p><p>{e(p["question"])}</p>{refs(p["refs"])}')
    body += section('最近收录的发言', '<ul class="plain-list">' + ''.join(linked_row('sources/' + s['id'] + '/', s['text'][:70] + ('…' if len(s['text']) > 70 else ''), '', s['date']) for s in own[:5]) + '</ul>')
    body += f'<p class="link-row"><a href="{u("people/" + pid + "/sources/")}">按时间看全部 {len(own)} 段发言 →</a></p>'
    body += section('相关话题', topic_rows(tids or p['topics'])) + tools('person/' + pid)
    page(p['nick'] + '的发言', body, '人物发言')
    search_record('人物', p['nick'], 'people/' + pid + '/', p)
    index_pages('people/' + pid + '/sources', own, p['nick'] + ' · 发言记录', '从近到远排列；打开一条即可查看完整原话、来源与关联话题。', lambda s: linked_row('sources/' + s['id'] + '/', s['text'][:100] + ('…' if len(s['text']) > 100 else ''), '', s['date']), nav='人物发言')

for s in DATA['sources']:
    sid = s['id']
    begin('sources/' + sid + '/')
    body = crumbs([('sources/', '全部原话')]) + intro(s['speaker'] + '的这段话', meta='原话 ' + str(s['number']))
    body += quote(s)
    note = s['note'].replace(' 称呼按昵称统一。', '').replace('保留该条文字，称呼按昵称统一。', '').strip()
    if note:
        body += '<p class="source-note">' + e(note) + '</p>'
    line = str(s['line']) + ('—' + str(s['end']) if s['end'] != s['line'] else '')
    body += fold('核对来源位置', f'<p class="meta">{e(DATA["meta"]["source_name"])} · 原文件 L{e(line)}。称呼按昵称统一；未公开私人备注映射。</p>')
    tids = [t['id'] for t in DATA['topics'] if sid in t['refs'] or any('[[' + sid + ']]' in x['body'] for x in EDITED[t['id']]['sections'])]
    if tids:
        body += section('这段话出现在哪些话题里', topic_rows(tids))
    ds = [d for d in DATA['debates'] if sid in all_debate_refs(d)]
    if ds:
        body += section('相关分歧', '<ul class="plain-list">' + ''.join(linked_row('debates/' + d['id'] + '/', d['title']) for d in ds) + '</ul>')
    body += tools('source/' + sid)
    page(s['speaker'] + ' · ' + s['date'], body)
    search_record('原话', s['speaker'] + ' · ' + s['date'], 'sources/' + sid + '/', s['text'])
index_pages('sources', sorted(DATA['sources'], key=lambda x: x['date'], reverse=True), '原话与出处', '这里保留全部 177 段已收录引文。它们是群聊中的节选，不是全量聊天备份。', lambda s: linked_row('sources/' + s['id'] + '/', s['text'][:85] + ('…' if len(s['text']) > 85 else ''), '', s['speaker'] + ' · ' + s['date']))

for ev in DATA['events']:
    begin('events/' + ev['id'] + '/')
    body = crumbs([('timeline/', '按时间回看')]) + intro(ev['title'], ev['desc'], meta=ev['date'])
    body += section('为什么留下这段讨论', '<p>' + e(ev['why']) + '</p>') + section('相关话题', topic_rows(ev['topics']))
    body += fold('参与者与原话', '<p>' + ' · '.join(person_link(n) for n in ev['people']) + '</p>' + ''.join(quote(SOURCES[s]) + refs([s]) for s in ev['refs']))
    page(ev['title'], body, '话题追踪')
    search_record('事件', ev['title'], 'events/' + ev['id'] + '/', ev)
index_pages('timeline', sorted(DATA['events'], key=lambda x: x['date'], reverse=True), '按时间回看', '28 条事件记录。主题相近的讨论通过话题页继续连接。', lambda ev: linked_row('events/' + ev['id'] + '/', ev['title'], ev['desc'], ev['date']), size=14, nav='话题追踪')

begin('practice/')
body = intro('把讨论带回自己的工作。', '从具体任务找做法。这里是基于讨论整理的实践建议，使用效果仍需在你的任务中检验。')
body += section('你正在做哪类任务？', '<ul class="plain-list">' + ''.join(linked_row('tasks/' + x['id'] + '/', x['name'], x['input']) for x in DATA['tasks']) + '</ul>')
body += section('想试一种做法？', '<ul class="plain-list">' + ''.join(linked_row('methods/' + x['id'] + '/', x['title'], x['deck']) for x in DATA['methods']) + '</ul>')
page('实践方法', body)
for task in DATA['tasks']:
    begin('tasks/' + task['id'] + '/')
    body = crumbs([('practice/', '实践方法')]) + intro(task['name'])
    body += '<dl class="definition-list">' + ''.join(f'<dt>{label}</dt><dd>{e(task[key])}</dd>' for key, label in [('input','从哪里开始'),('output','最后要交什么'),('bottleneck','容易卡在哪里'),('checks','怎样检查')]) + '</dl>'
    body += '<p class="link-row">' + ' · '.join(person_link(p) for p in task['people']) + '</p>'
    body += section('相关讨论', topic_rows(task['topics'])) + fold('原话依据', ''.join(quote(SOURCES[s]) + refs([s]) for s in task['refs']))
    page(task['name'], body)
    search_record('任务', task['name'], 'tasks/' + task['id'] + '/', task)
for method in DATA['methods']:
    begin('methods/' + method['id'] + '/')
    body = crumbs([('practice/', '实践方法')]) + intro(method['title'], method['deck'], '整理者的实践建议')
    body += '<ol class="prose">' + ''.join('<li>' + e(s) + '</li>' for s in method['steps']) + '</ol>'
    body += section('可以这样开始', '<blockquote class="statement">' + e(method['prompt']) + '</blockquote>')
    body += '<p class="boundary">' + e(method['caution']) + '</p>' + section('来自哪些讨论', topic_rows(method['topics']))
    body += fold('原话依据', ''.join(quote(SOURCES[s]) + refs([s]) for s in method['refs']))
    page(method['title'], body)
    search_record('方法', method['title'], 'methods/' + method['id'] + '/', method)

begin('questions/')
body = intro('还值得继续问。', '这些问题在本期记录里还没有完整答案。带着新案例回来，可以继续补充。')
body += '<ul class="plain-list">' + ''.join(linked_row('questions/' + q['id'] + '/', q['title'], q['body']) for q in DATA['questions']) + '</ul>'
page('开放问题', body, '话题追踪')
for q in DATA['questions']:
    begin('questions/' + q['id'] + '/')
    body = crumbs([('questions/', '全部开放问题')]) + intro(q['title'], q['body'], '待讨论')
    body += section('从这场讨论接着往下问', topic_rows([q['topic']]))
    page(q['title'], body, '话题追踪')
    search_record('开放问题', q['title'], 'questions/' + q['id'] + '/', q)

begin('glossary/')
body = intro('遇到陌生词，随手查。', '解释限于这份档案里的用法。') + '<dl class="definition-list">'
for i, g in enumerate(DATA['glossary']):
    body += f'<dt id="g{i}">{e(g["term"])} · {e(g["cn"])}</dt><dd>{e(g["desc"])}</dd>'
    search_record('术语', g['term'] + ' · ' + g['cn'], 'glossary/#g' + str(i), g)
body += '</dl>'
page('术语', body)


def rewrite_section(source):
    source = re.sub(r'<span[^>]*class="route-anchor"[^>]*></span>', '', source)
    def rewrite(m):
        target = m[1]
        if target.startswith(('http:', 'https:')):
            return m[0]
        if target.startswith('#'):
            route = target[1:]
            direct = {'skills':'skills/','resources':'resources/','welcome':'','read':'topics/','about':'about/','sources':'sources/','questions':'questions/'}
            if route in direct:
                target = direct[route]
            elif re.match(r'^(topic|person|source)/', route):
                kind, ident = route.split('/')
                target = {'topic':'topics','person':'people','source':'sources'}[kind] + '/' + ident + '/'
            else:
                target = 'archive.html#' + route
        return 'href="' + e(u(target)) + '"'
    return re.sub(r'href="([^"]+)"', rewrite, source)


begin('skills/')
page('从思考到工具', rewrite_section(SECTIONS['view-skills']))
search_record('延伸实践', 'temper 与 aptum', 'skills/', '人机协作循环 反馈 验证 表达 读者 上下文 思考 工具')
begin('community/')
page('群公告与共享资源', rewrite_section(SECTIONS['view-resources']))

begin('resources/')
body = intro('需要时，再往深处看。', '完整资料、实践方法、群公告与整理者的延伸作品。')
groups = [
    ('继续读讨论', [('archive/','完整档案与阅读路线'),('debates/','20 场分歧'),('timeline/','28 条事件记录'),('sources/','177 段原话与出处')]),
    ('拿去试一试', [('practice/','9 类任务与 10 张实践卡'),('questions/','12 个开放问题'),('glossary/','25 个术语'),('skills/','从思考到 temper、aptum')]),
    ('延伸阅读', [('materials/distillation-statement.pdf','AI Sparks 蒸馏声明 · PDF'),('materials/when-doing-is-no-longer-scarce.pdf','当「会做事」不再稀缺 · PDF')]),
    ('认识这个群', [('about/','为什么叫观澜'),('community/','群公告与共享资源'),('join/','加入我们'),('about/#correction','内容纠错与删改')])
]
body += '<div class="resource-grid">'
for label, links in groups:
    body += f'<section class="resource-block"><h2>{label}</h2><ul>' + ''.join(f'<li><a href="{u(path)}">{text}</a></li>' for path,text in links) + '</ul></section>'
body += '</div>'
page('资料与实践', body, narrow=False)

begin('archive/')
body = intro('完整内容，都有去处。', '精华放在前面，完整分析和依据继续保留。这里收录的是主要实质讨论，不是全部聊天公开备份。')
body += '<ul class="plain-list">'
for path, name, desc in [('topics/','38 个话题','按七类问题进入；每篇连接完整分析与原话。'),('debates/','20 场分歧','保留不同观点、认可范围和未决之处。'),('people/','26 位参与者','查看各人的相关发言和话题。'),('timeline/','28 条事件记录','回到讨论发生的日期。'),('sources/','177 段原话','保留文本、来源与重要限定。'),('practice/','9 类任务与 10 张实践卡','将讨论中的做法放回具体任务。'),('questions/','12 个开放问题','继续讨论尚未解决的部分。'),('glossary/','25 个术语','补足阅读时需要的背景。')]:
    body += linked_row(path,name,desc)
body += '</ul>'
routes = ''
for route in DATA['routes']:
    routes += f'<h3>{e(route["name"])}</h3><p>{e(route["desc"])}</p>' + topic_rows(route['topics'])
body += fold('沿着一条路线读', routes)
body += fold('七章长文与早期版本', f'<p>早期长文保留七章导读与各版措辞。章节按主题编排，不代表真实发生顺序；其中的综合判断，应结合新版话题页和原话理解。</p><p><a href="{u("archive.html#read")}">打开七章长文存档 →</a></p><p><a href="{u("content/data.json")}" download>下载既有结构化资料</a></p>')
page('完整档案', body)

begin('about/')
body = intro('观澜 · AI Sparks', 'AI 时代最好的学习方式，就是跟人聊。')
body += '<div class="prose"><p>围绕真实的问题，把不同人的经验和判断放在一起碰撞。聊技术背后的原理，聊 AI 能做什么、暂时做不了什么，也聊它正在怎样改变工作、产品、组织和思考方式。</p><p class="statement">借具体变化，看更大的时代走势。</p><p>我们不一定是专家。希望这里聚集的是一群对技术有好奇心、愿意多想一层的人：观察变化、提出问题、交换经验、彼此修正判断，也尽可能亲手参与和建设这个时代。</p></div>'
body += f'<a id="theme" href="{u("assets/guanlan-theme.png")}"><img class="theme-image" src="{u("assets/guanlan-theme.png")}" alt="观澜主题图：水墨河流与围桌交谈的人们" width="1122" height="1402" loading="lazy"></a>'
body += section('这份档案怎样读', '<p>主要服务没时间刷群的朋友：先在首页挑话题，进入后看要点和不同意见，需要时再读完整分析、原话与来源。</p><p>本期材料覆盖 2026 年 7 月 12 日至 9 月 15 日。整理保留 38 个话题和 177 段引文；导出记录中的图片、视频大多只有占位符，没有据此推测内容。</p>')
body += section('怎样决定轻重', '<p>优先呈现一手实践、具体反例、关键分歧和影响判断的条件。日常闲聊与重复表态不进入精选；只有原话明确支持时，才记录观点发生了修正。</p><p>原话、参与者的判断与整理者的推演各有不同作用。资料中存在相近观点，不等于全体群友达成共识；历史工具体验也不是现行产品推荐。</p>')
body += '<section class="topic-section" id="correction"><h2>纠错与删改</h2><p>如发现涉敏内容、引文归属或语境有误，请私聊群主或整理者，并提供页面链接。涉及隐私的原文请私下反馈；普通问题可在 <a href="https://github.com/Zhong-Ze-Wei/ai-spark/issues">GitHub Issues</a> 提出。</p><p>称呼沿用已公开的昵称，不展示私人备注表。昵称本身不一定匿名。</p></section>'
body += f'<div class="actions"><a class="button" href="{u("community/")}">群公告与资源</a><a class="button" href="{u("join/")}">加入我们</a></div>'
page('关于观澜', body)

begin('join/')
body = '<div class="join-page">' + intro('加入观澜', '带着一个真实问题，和一群好奇的人聊一聊。')
body += f'<div data-qr-current><img src="{u("assets/guanlan-invitation.png")}" width="420" height="672" alt="微信扫码加入观澜群，有效期为 2026 年 10 月 1 日前"></div><p class="notice" data-qr-expired hidden>这张群二维码已过期。请联系邀请你阅读的群友，获取新的入群方式。</p>'
body += f'<p class="meta">原图注明 2026 年 10 月 1 日前有效；能否入群以微信提示为准。</p><div class="link-row"><a href="{u("assets/join-qr-original.jpg")}" download>保存微信原图</a><a href="{u("assets/guanlan-invitation.png")}" download>保存邀请卡</a></div><noscript><p class="notice">请先核对当前日期；二维码于 2026 年 10 月 1 日前有效。</p></noscript></div>'
page('加入观澜', body)

begin('saved/')
page('我的收藏', intro('留下想再读的内容。', '收藏只保存在当前浏览器，旧版收藏也可以继续打开。') + '<ul class="plain-list" id="saved-list"></ul><noscript>收藏需要启用 JavaScript。</noscript>')

begin('search/')
body = intro('找一个问题，或一句话。', '搜索全部话题、分歧、人物、原话与实践材料。')
body += '<form class="search-form" id="search-form" method="get"><label for="search-input">关键词或昵称<input id="search-input" type="search" name="q" autocomplete="off" placeholder="例如：返工、专业能力、数读"></label><button type="submit" class="button primary">搜索</button></form><p class="meta" aria-live="polite" id="search-count"></p><ul class="plain-list" id="search-results"></ul><noscript><p>搜索需要 JavaScript；也可以从话题分类和完整档案进入。</p></noscript>'
body += f'<script src="{u("assets/site/search-index.js")}"></script>'
page('搜索', body)
(ROOT / 'assets/site/search-index.js').write_text('window.GUANLAN_SEARCH=' + json.dumps(SEARCH, ensure_ascii=False, separators=(',', ':')).replace('</', '<\\/') + ';\n')
(ROOT / '.nojekyll').touch()
(ROOT / 'content/build-manifest.json').write_text(json.dumps({'pages': GENERATED, 'counts': {k: len(DATA[k]) for k in ['topics','debates','events','people','sources','tasks','methods','questions','glossary','routes']}, 'scope': {'start': DATA['meta']['start'], 'end': DATA['meta']['end']}}, ensure_ascii=False, indent=2) + '\n')
print(f'Built {len(GENERATED)} static pages; {len(SEARCH)} searchable records.')
