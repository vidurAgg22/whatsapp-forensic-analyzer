import re
from datetime import datetime

# ── Android pattern ──────────────────────────────────────────────
# Real format: 02/06/25, 7:03 pm - Sender Name: message text
ANDROID_MSG = re.compile(
    r'^(\d{1,2}/\d{1,2}/\d{2,4}),\s'           # date: 02/06/25,
    r'(\d{1,2}:\d{2}\s?[aApP][mM])'             # time: 7:03 pm
    r'\s-\s'                                      # separator: -
    r'([^:]+):\s'                                 # sender: Name:
    r'(.*)'                                       # message content
)

# Android system messages have no sender — just text after the dash
# e.g: 02/06/25, 7:03 pm - Messages and calls are end-to-end encrypted.
ANDROID_SYS = re.compile(
    r'^(\d{1,2}/\d{1,2}/\d{2,4}),\s'
    r'(\d{1,2}:\d{2}\s?[aApP][mM])'
    r'\s-\s'
    r'(?![^:]+:\s)'                               # negative lookahead — no sender:
    r'(.+)$'
)

# ── iPhone pattern ───────────────────────────────────────────────
# Real format: [15/01/24, 6:14:59 PM] Sender Name: message text
IPHONE_MSG = re.compile(
    r'^\[(\d{1,2}/\d{1,2}/\d{2,4}),\s'          # date
    r'(\d{1,2}:\d{2}:\d{2}\s?[aApP][mM])\]'     # time with seconds
    r'\s([^:]+):\s'                               # sender
    r'(.*)'                                       # message
)

# iPhone has no true system-only pattern — system messages still have
# a sender field. We detect them by content instead (see is_system_message)
IPHONE_SYS = re.compile(
    r'^\[(\d{1,2}/\d{1,2}/\d{2,4}),\s'
    r'(\d{1,2}:\d{2}:\d{2}\s?[aApP][mM])\]'
    r'\s(?![^:]+:\s)'                             # no sender: pattern
    r'(.+)$'
)

LINK_PATTERN = re.compile(r'https?://\S+|www\.\S+')

MEDIA_KEYWORDS = [
    '<media omitted>',
    'image omitted',
    'video omitted',
    'audio omitted',
    'document omitted',
    'gif omitted',
    'sticker omitted',
]

# These phrases identify system messages by content
# Works for iPhone where system msgs still have a sender field
SYSTEM_PHRASES = [
    'messages and calls are end-to-end encrypted',
    'created group',
    'added you',
    'you were added',
    'left',
    'removed',
    ' added ',
    'changed the subject',
    'changed this group',
    'pinned a message',
    "you're now an admin",
    'changed their phone number',
    'deleted this message',
    'you deleted this message',
    'this message was deleted',
    'missed voice call',
    'missed video call',
    'security code changed',
    'turned on disappearing messages',
    'turned off disappearing messages',
    'created this group',
]

# Invisible unicode characters WhatsApp injects
INVISIBLE_CHARS = re.compile(
    r'[\u200e\u200f\u202a-\u202e\u2066-\u2069\ufeff]'
)

# iPhone mention format: @⁨Name⁩
MENTION_PATTERN = re.compile(r'@\u2048([^\u2049]+)\u2049')


def clean_text(text: str) -> str:
    """Remove invisible unicode chars and normalize mentions"""
    text = INVISIBLE_CHARS.sub('', text)
    text = MENTION_PATTERN.sub(r'@\1', text)
    return text.strip()


def detect_device(content: str) -> str:
    """
    Read first 30 lines to detect format.
    iPhone lines start with [
    Android lines start with a digit
    """
    for line in content.splitlines()[:30]:
        line = clean_text(line)
        if not line:
            continue
        if line.startswith('['):
            return 'iphone'
        if re.match(r'\d{1,2}/\d{1,2}/\d{2,4},', line):
            return 'android'
    return 'android'


def parse_datetime(date_str: str, time_str: str) -> datetime:
    """
    Try every WhatsApp date/time format combination.
    Normalizes to uppercase so am/pm/AM/PM all work.
    Never crashes — returns fallback date if all formats fail.
    """
    combined = f"{date_str} {time_str.strip().upper()}"
    # Replace narrow no-break space some iPhones insert
    combined = combined.replace('\u202f', ' ').replace('  ', ' ')

    formats = [
        '%d/%m/%y %I:%M %p',        # 02/06/25 7:03 PM
        '%d/%m/%y %I:%M:%S %p',     # 02/06/25 7:03:45 PM
        '%d/%m/%Y %I:%M %p',        # 02/06/2025 7:03 PM
        '%d/%m/%Y %I:%M:%S %p',     # 02/06/2025 7:03:45 PM
        '%m/%d/%y %I:%M %p',        # US format
        '%m/%d/%y %I:%M:%S %p',
        '%m/%d/%Y %I:%M %p',
        '%m/%d/%Y %I:%M:%S %p',
        '%d/%m/%y %H:%M',           # 24-hour variants
        '%d/%m/%y %H:%M:%S',
        '%d/%m/%Y %H:%M',
        '%d/%m/%Y %H:%M:%S',
        '%m/%d/%y %H:%M',
        '%m/%d/%Y %H:%M',
    ]

    for fmt in formats:
        try:
            return datetime.strptime(combined, fmt)
        except ValueError:
            continue

    # Fallback — never crash over one bad timestamp
    return datetime(2000, 1, 1, 0, 0, 0)


def count_emojis(text: str) -> int:
    """Count emojis using Unicode codepoint ranges. No external library needed."""
    count = 0
    for char in text:
        cp = ord(char)
        if (
            0x1F600 <= cp <= 0x1F64F or   # emoticons
            0x1F300 <= cp <= 0x1F5FF or   # misc symbols & pictographs
            0x1F680 <= cp <= 0x1F6FF or   # transport & map
            0x1F1E0 <= cp <= 0x1F1FF or   # flags
            0x2600  <= cp <= 0x26FF  or   # misc symbols
            0x2700  <= cp <= 0x27BF  or   # dingbats
            0x1F900 <= cp <= 0x1F9FF or   # supplemental symbols
            0x1FA00 <= cp <= 0x1FAFF      # extended symbols
        ):
            count += 1
    return count


def is_media_message(content: str) -> bool:
    return any(kw in content.lower() for kw in MEDIA_KEYWORDS)


def is_system_message(content: str) -> bool:
    """
    Detect system messages by checking content against known phrases.
    This is the KEY fix for iPhone — where system messages still have
    a sender field so regex alone cannot distinguish them.
    """
    content_lower = content.lower()
    return any(phrase in content_lower for phrase in SYSTEM_PHRASES)


def build_message_dict(timestamp, sender, content, override_system=False):
    """
    Build a standard message dictionary.
    Calls is_system_message on content so iPhone system msgs are caught.
    """
    content = clean_text(content)
    is_sys = override_system or is_system_message(content)

    return {
        'timestamp'  : timestamp,
        'sender'     : sender.strip(),
        'content'    : content,
        'is_media'   : is_media_message(content),
        'is_system'  : is_sys,
        'emoji_count': 0 if is_sys else count_emojis(content),
        'has_link'   : False if is_sys else bool(LINK_PATTERN.search(content)),
        'day'        : timestamp.strftime('%A'),
        'month'      : timestamp.strftime('%B'),
        'year'       : timestamp.year,
        'hour'       : timestamp.hour,
    }


def parse_chat(file_content: str) -> dict:
    """
    Master parser function.

    Takes raw WhatsApp export text (Android or iPhone).
    Returns a clean structured dictionary ready for Django views.
    Works correctly on both short and long chats.
    """
    device = detect_device(file_content)

    if device == 'iphone':
        msg_pattern = IPHONE_MSG
        sys_pattern = IPHONE_SYS
    else:
        msg_pattern = ANDROID_MSG
        sys_pattern = ANDROID_SYS

    messages = []
    current = None

    for raw_line in file_content.splitlines():
        line = clean_text(raw_line)

        # Blank line — could be part of a multiline message
        if not line:
            if current:
                current['content'] += '\n'
            continue

        msg_match = msg_pattern.match(line)
        sys_match = sys_pattern.match(line)

        if msg_match:
            # Save previous message first
            if current:
                current['content'] = current['content'].strip()
                messages.append(current)

            date_str, time_str, sender, content = msg_match.groups()
            timestamp = parse_datetime(date_str, time_str)

            # ── KEY FIX ──────────────────────────────────────────
            # Call build_message_dict which internally calls
            # is_system_message() on the content.
            # This catches iPhone system messages that have a sender.
            # ─────────────────────────────────────────────────────
            current = build_message_dict(timestamp, sender, content)

        elif sys_match:
            # Android-style system message (no sender at all)
            if current:
                current['content'] = current['content'].strip()
                messages.append(current)
                current = None

            date_str, time_str, sys_text = sys_match.groups()
            timestamp = parse_datetime(date_str, time_str)

            # Force is_system=True since there's no sender
            messages.append(
                build_message_dict(timestamp, 'System', sys_text, override_system=True)
            )

        else:
            # Continuation of previous multiline message
            if current:
                current['content'] += ' ' + line

    # Save the very last message
    if current:
        current['content'] = current['content'].strip()
        messages.append(current)

    # Separate real messages from system messages
    real_messages = [m for m in messages if not m['is_system']]
    members = list(set(m['sender'] for m in real_messages))

    return {
        'device'         : device,
        'messages'       : messages,        # all including system
        'real_messages'  : real_messages,   # only user messages
        'total_messages' : len(real_messages),
        'total_members'  : len(members),
        'members'        : members,
        'has_enough_data': len(real_messages) >= 5,
    }