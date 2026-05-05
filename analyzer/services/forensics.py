from collections import Counter
import re
from analyzer.models import Message

CRIMINAL_KEYWORDS = [
    'kill', 'murder', 'bomb', 'explosion', 'attack', 'weapon',
    'gun', 'shoot', 'hack', 'scam', 'fraud', 'threat', 'blackmail',
    'ransom', 'poison', 'drug', 'cocaine', 'heroin', 'trafficking',
    'smuggle', 'steal', 'robbery', 'terror', 'jihad', 'extremist',
    'illegal', 'counterfeit', 'bribe', 'corrupt', 'launder',
    'execute', 'kidnap', 'hostage', 'riot', 'arson', 'rape',
    'abuse', 'exploit', 'infiltrate', 'spy', 'surveillance',
    'detonate', 'explosive', 'ammunition', 'firearm', 'knife',
    'stab', 'strangle', 'torture', 'assassin', 'hitman',
]

LINK_RE = re.compile(r'https?://\S+|www\.\S+')

TRANSLATE_LANGUAGES = [
    ('en', 'English'),
    ('hi', 'Hindi'),
    ('fr', 'French'),
    ('de', 'German'),
    ('es', 'Spanish'),
    ('ar', 'Arabic'),
    ('zh-CN', 'Chinese'),
    ('ja', 'Japanese'),
    ('ru', 'Russian'),
    ('pt', 'Portuguese'),
    ('it', 'Italian'),
    ('ko', 'Korean'),
    ('tr', 'Turkish'),
    ('nl', 'Dutch'),
    ('pl', 'Polish'),
]


def get_forensics(session) -> dict:
    real_msgs = Message.objects.filter(
        session=session,
        is_system=False,
        is_media=False,
    ).order_by('timestamp')

    all_msgs_list = list(real_msgs)

    # ── 1. Keyword extraction with context ───────────────────────
    flagged_messages = []
    for idx, msg in enumerate(all_msgs_list):
        content_lower = msg.content.lower()
        found_keywords = [
            kw for kw in CRIMINAL_KEYWORDS
            if re.search(r'\b' + kw + r'\b', content_lower)
        ]
        if found_keywords:
            # Get 2 messages before and after for context
            context_before = []
            context_after  = []
            for i in range(max(0, idx - 2), idx):
                m = all_msgs_list[i]
                context_before.append({
                    'sender'   : m.sender,
                    'content'  : m.content,
                    'timestamp': m.timestamp.strftime('%I:%M %p'),
                })
            for i in range(idx + 1, min(len(all_msgs_list), idx + 3)):
                m = all_msgs_list[i]
                context_after.append({
                    'sender'   : m.sender,
                    'content'  : m.content,
                    'timestamp': m.timestamp.strftime('%I:%M %p'),
                })

            flagged_messages.append({
                'id'            : msg.id,
                'sender'        : msg.sender,
                'content'       : msg.content,
                'keywords'      : found_keywords,
                'timestamp'     : msg.timestamp.strftime('%d %b %Y, %I:%M %p'),
                'date'          : msg.timestamp.strftime('%Y-%m-%d'),
                'context_before': context_before,
                'context_after' : context_after,
            })

    # ── 2. Link extraction with full sender attribution ──────────
    link_data   = {}   # link -> {count, senders: [{sender, timestamp}]}
    all_links   = []

    msgs_with_links = Message.objects.filter(
        session=session,
        has_link=True,
        is_system=False,
    ).order_by('timestamp')

    for msg in msgs_with_links:
        found = LINK_RE.findall(msg.content)
        for link in found:
            link = link.rstrip('.,)')
            all_links.append({
                'sender'   : msg.sender,
                'link'     : link,
                'timestamp': msg.timestamp.strftime('%d %b %Y, %I:%M %p'),
            })
            if link not in link_data:
                link_data[link] = {'count': 0, 'senders': []}
            link_data[link]['count'] += 1
            link_data[link]['senders'].append({
                'sender'   : msg.sender,
                'timestamp': msg.timestamp.strftime('%d %b %Y, %I:%M %p'),
            })

    top_links = sorted(
        [
            {
                'link'   : link,
                'count'  : data['count'],
                'senders': data['senders'],
            }
            for link, data in link_data.items()
        ],
        key=lambda x: x['count'],
        reverse=True
    )[:10]

    # ── 3. Knowledge graph ───────────────────────────────────────
    graph_data = get_knowledge_graph(all_msgs_list)

    return {
        'flagged_messages' : flagged_messages,
        'flagged_count'    : len(flagged_messages),
        'all_links'        : all_links,
        'top_links'        : top_links,
        'graph_data'       : graph_data,
        'translate_languages': TRANSLATE_LANGUAGES,
        'session_id'       : session.id,
    }


def get_knowledge_graph(messages_list) -> dict:
    edge_counter = Counter()

    for i in range(1, len(messages_list)):
        prev_sender = messages_list[i - 1].sender
        curr_sender = messages_list[i].sender
        if prev_sender != curr_sender:
            edge_counter[(prev_sender, curr_sender)] += 1

    sender_count = Counter(m.sender for m in messages_list)
    top_10       = [s for s, _ in sender_count.most_common(10)]

    nodes = [{'id': s} for s in top_10]
    edges = [
        {'source': src, 'target': tgt, 'weight': count}
        for (src, tgt), count in edge_counter.items()
        if src in top_10 and tgt in top_10
    ]

    return {'nodes': nodes, 'edges': edges}