import re
import base64
import io
from collections import Counter
from django.db.models import Count, Avg
from django.db.models.functions import Length, TruncDate
from analyzer.models import Message


STOPWORDS = {
    'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at',
    'to', 'for', 'of', 'with', 'is', 'it', 'this', 'that',
    'i', 'you', 'he', 'she', 'we', 'they', 'my', 'your',
    'his', 'her', 'its', 'our', 'their', 'be', 'are', 'was',
    'were', 'been', 'have', 'has', 'had', 'do', 'does', 'did',
    'will', 'would', 'could', 'should', 'may', 'might', 'can',
    'not', 'no', 'so', 'if', 'as', 'by', 'from', 'up', 'out',
    'about', 'into', 'through', 'also', 'just', 'like', 'than',
    'then', 'when', 'what', 'which', 'who', 'how', 'all', 'any',
    'me', 'him', 'us', 'them', 'am', 'get', 'got', 'yes', 'ok',
    'okay', 'hi', 'hello', 'hey', 'bhi', 'hai', 'kar', 'kya',
    'nhi', 'toh', 'bhai', 'aur', 'se', 'ka', 'ki', 'ko', 'ne',
    'na', 'ho', 'hain', 'tha', 'koi', 'mai', 'mein', 'hm',
    'ab', 'bas', 'ek', 'ye', 'wo', 'woh', 'ap', 'aap', 'rha',
    'rhe', 'gya', 'gaye', 'kr', 'kro', 'karna', 'hoga', 'hua',
}

EMOJI_RANGES = [
    (0x1F600, 0x1F64F),
    (0x1F300, 0x1F5FF),
    (0x1F680, 0x1F6FF),
    (0x1F1E0, 0x1F1FF),
    (0x2600,  0x26FF),
    (0x2700,  0x27BF),
    (0x1F900, 0x1F9FF),
    (0x1FA00, 0x1FAFF),
]

def is_emoji(char):
    cp = ord(char)
    return any(start <= cp <= end for start, end in EMOJI_RANGES)


def extract_emojis(text):
    return [c for c in text if is_emoji(c)]


def get_word_frequencies(user_msgs):
    word_counter = Counter()
    for msg in user_msgs:
        words = msg.content.lower().split()
        for word in words:
            word = word.strip('.,!?;:\'"()[]{}«»')
            if (
                len(word) > 2 and
                word not in STOPWORDS and
                not word.startswith('http') and
                word.isalpha()
            ):
                word_counter[word] += 1
    return word_counter


def generate_wordcloud(word_counter):
    """Generate word cloud image and return as base64 string."""
    try:
        from wordcloud import WordCloud
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt

        if not word_counter:
            return None

        wc = WordCloud(
            width=800,
            height=400,
            background_color='#1e293b',
            colormap='Greens',
            max_words=100,
            prefer_horizontal=0.85,
            min_font_size=10,
        ).generate_from_frequencies(dict(word_counter))

        fig, ax = plt.subplots(figsize=(10, 5))
        ax.imshow(wc, interpolation='bilinear')
        ax.axis('off')
        fig.patch.set_facecolor('#1e293b')
        plt.tight_layout(pad=0)

        buf = io.BytesIO()
        plt.savefig(buf, format='png', bbox_inches='tight',
                    facecolor='#1e293b', dpi=150)
        plt.close(fig)
        buf.seek(0)
        img_base64 = base64.b64encode(buf.read()).decode('utf-8')
        return img_base64

    except Exception as e:
        return None


def get_analysis(session) -> dict:
    """
    Master analysis function.
    Returns all stats and chart data needed for the dashboard.
    """
    all_msgs  = Message.objects.filter(session=session)
    real_msgs = all_msgs.filter(is_system=False)
    user_msgs = real_msgs.filter(is_media=False)

    if not real_msgs.exists():
        return {'has_enough_data': False}

    # ── 1. Basic counts ──────────────────────────────────────────
    total_messages = real_msgs.count()
    total_members  = real_msgs.values('sender').distinct().count()
    total_media    = real_msgs.filter(is_media=True).count()
    total_links    = real_msgs.filter(has_link=True).count()
    total_emojis   = sum(m.emoji_count for m in real_msgs)

    # ── 2. Top 10 active members ─────────────────────────────────
    top_members = list(
        real_msgs
        .values('sender')
        .annotate(msg_count=Count('id'), avg_length=Avg(Length('content')))
        .order_by('-msg_count')[:10]
    )

    # ── 3. Messages per day ──────────────────────────────────────
    msgs_per_day = [
        {'date': str(x['date']), 'count': x['count']}
        for x in (
            real_msgs
            .annotate(date=TruncDate('timestamp'))
            .values('date')
            .annotate(count=Count('id'))
            .order_by('date')
        )
    ]

    top_dates = sorted(msgs_per_day, key=lambda x: x['count'], reverse=True)[:10]

    # ── 4. Messages by hour ──────────────────────────────────────
    hour_dict = {
        x['hour']: x['count']
        for x in real_msgs.values('hour').annotate(count=Count('id'))
    }
    msgs_by_hour = [{'hour': h, 'count': hour_dict.get(h, 0)} for h in range(24)]

    # ── 5. Messages by day of week ───────────────────────────────
    day_order = ['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday']
    day_dict  = {x['day']: x['count'] for x in real_msgs.values('day').annotate(count=Count('id'))}
    msgs_by_day = [{'day': d, 'count': day_dict.get(d, 0)} for d in day_order]

    # ── 6. Messages by month ─────────────────────────────────────
    month_order = ['January','February','March','April','May','June',
                   'July','August','September','October','November','December']
    month_dict  = {x['month']: x['count'] for x in real_msgs.values('month').annotate(count=Count('id'))}
    msgs_by_month = [
        {'month': m, 'count': month_dict.get(m, 0)}
        for m in month_order if month_dict.get(m, 0) > 0
    ]

    # ── 7. Top media senders ─────────────────────────────────────
    top_media = list(
        real_msgs.filter(is_media=True)
        .values('sender')
        .annotate(count=Count('id'))
        .order_by('-count')[:10]
    )

    # ── 8. Heatmap data (month x day of week) ────────────────────
    heatmap_months = []
    heatmap_days   = day_order
    heatmap_z      = []

    active_months = [m for m in month_order if month_dict.get(m, 0) > 0]
    raw_heatmap   = {}
    for entry in real_msgs.values('month', 'day').annotate(count=Count('id')):
        raw_heatmap.setdefault(entry['month'], {})[entry['day']] = entry['count']

    for month in active_months:
        row = [raw_heatmap.get(month, {}).get(day, 0) for day in day_order]
        heatmap_months.append(month)
        heatmap_z.append(row)

    # ── 9. Emoji leaderboard ─────────────────────────────────────
    emoji_counter = Counter()
    for msg in user_msgs:
        for e in extract_emojis(msg.content):
            emoji_counter[e] += 1

    top_emojis = [
        {'emoji': e, 'count': c}
        for e, c in emoji_counter.most_common(10)
    ]

    # ── 10. Word frequency ───────────────────────────────────────
    word_counter = get_word_frequencies(user_msgs)
    top_words    = [{'word': w, 'count': c} for w, c in word_counter.most_common(50)]

    # ── 11. Word cloud image ─────────────────────────────────────
    wordcloud_img = generate_wordcloud(word_counter)

    # ── 12. Link extraction ──────────────────────────────────────
    LINK_RE      = re.compile(r'https?://\S+|www\.\S+')
    link_counter = Counter()
    for msg in real_msgs.filter(has_link=True):
        for link in LINK_RE.findall(msg.content):
            link_counter[link.rstrip('.,)')] += 1

    top_links = [{'link': l, 'count': c} for l, c in link_counter.most_common(10)]

    # ── 13. Sentiment ────────────────────────────────────────────
    sentiment = get_sentiment(user_msgs)

    # ── 14. Average message length per member ────────────────────
    avg_length_data = [
        {'sender': m['sender'], 'avg_length': round(m['avg_length'] or 0, 1)}
        for m in top_members
    ]

    return {
        'has_enough_data' : True,
        'total_messages'  : total_messages,
        'total_members'   : total_members,
        'total_media'     : total_media,
        'total_links'     : total_links,
        'total_emojis'    : total_emojis,
        'top_members'     : top_members,
        'avg_length_data' : avg_length_data,
        'msgs_per_day'    : msgs_per_day,
        'top_dates'       : top_dates,
        'msgs_by_hour'    : msgs_by_hour,
        'msgs_by_day'     : msgs_by_day,
        'msgs_by_month'   : msgs_by_month,
        'top_media'       : top_media,
        'heatmap_months'  : heatmap_months,
        'heatmap_days'    : heatmap_days,
        'heatmap_z'       : heatmap_z,
        'top_emojis'      : top_emojis,
        'top_words'       : top_words,
        'wordcloud_img'   : wordcloud_img,
        'top_links'       : top_links,
        'sentiment'       : sentiment,
    }


def get_sentiment(messages) -> dict:
    """VADER sentiment — returns overall + per-member breakdown."""
    try:
        import nltk
        from nltk.sentiment.vader import SentimentIntensityAnalyzer
        try:
            sia = SentimentIntensityAnalyzer()
        except LookupError:
            nltk.download('vader_lexicon', quiet=True)
            sia = SentimentIntensityAnalyzer()

        positive = negative = neutral = 0
        member_sentiment = {}

        for msg in messages:
            if not msg.content.strip():
                continue
            compound = sia.polarity_scores(msg.content)['compound']

            if compound >= 0.05:
                label = 'positive'; positive += 1
            elif compound <= -0.05:
                label = 'negative'; negative += 1
            else:
                label = 'neutral';  neutral += 1

            sender = msg.sender
            if sender not in member_sentiment:
                member_sentiment[sender] = {'positive': 0, 'negative': 0, 'neutral': 0}
            member_sentiment[sender][label] += 1

        # Convert to list for easy JS rendering
        member_sentiment_list = [
            {
                'sender'  : sender,
                'positive': vals['positive'],
                'negative': vals['negative'],
                'neutral' : vals['neutral'],
                'total'   : sum(vals.values()),
            }
            for sender, vals in sorted(
                member_sentiment.items(),
                key=lambda x: sum(x[1].values()),
                reverse=True
            )
        ]

        return {
            'positive'            : positive,
            'negative'            : negative,
            'neutral'             : neutral,
            'member_sentiment'    : member_sentiment,
            'member_sentiment_list': member_sentiment_list,
            'available'           : True,
        }

    except Exception:
        return {
            'positive': 0, 'negative': 0, 'neutral': 0,
            'member_sentiment': {}, 'member_sentiment_list': [],
            'available': False,
        }