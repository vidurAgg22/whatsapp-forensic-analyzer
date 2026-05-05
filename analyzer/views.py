import json
import os
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse
from django.conf import settings
from django.db.models import Q
from analyzer.models import ChatSession, Message
from analyzer.services import parse_chat, save_chat_to_db, get_analysis
from analyzer.services.forensics import get_forensics


FEATURES = [
    'EDA Dashboard', 'Sentiment Analysis', 'Keyword Detection',
    'Knowledge Graph', 'Word Cloud', 'Link Extraction',
    'Emoji Analysis', 'Activity Heatmap',
]

SAMPLE_CHATS = [
    {
        'id'         : 'college',
        'name'       : '🎓 College Study Group',
        'description': 'Android format · 5 members · Casual Hindi+English · 250+ messages',
        'file'       : 'sample_college_group_android.txt',
        'color'      : 'green',
    },
    {
        'id'         : 'business',
        'name'       : '💼 Business Team',
        'description': 'iPhone format · 5 members · Professional English · Links & docs shared',
        'file'       : 'sample_business_group_iphone.txt',
        'color'      : 'blue',
    },
    {
        'id'         : 'suspicious',
        'name'       : '🚨 Suspicious Group (Forensics Demo)',
        'description': 'Android format · 4 members · Criminal keywords · Best for forensics report',
        'file'       : 'sample_suspicious_group_android.txt',
        'color'      : 'red',
    },
    {
    'id'         : 'coders',
    'name'       : '💻 Coders Group (Real Dataset)',
    'description': 'Android format · 237 members · 11,000+ messages · Used in published research paper',
    'file'       : 'edited_chats.txt',
    'color'      : 'purple',
    },
]


def home(request):
    if request.method == 'POST':
        sample_id = request.POST.get('sample_id')
        if sample_id:
            return load_sample(request, sample_id)

        chat_file = request.FILES.get('chat_file')
        if not chat_file:
            messages.error(request, 'Please select a file to upload.')
            return redirect('home')
        if not chat_file.name.endswith('.txt'):
            messages.error(request, 'Please upload a .txt file exported from WhatsApp.')
            return redirect('home')
        if chat_file.size > 10 * 1024 * 1024:
            messages.error(request, 'File too large. Maximum size is 10MB.')
            return redirect('home')

        try:
            raw_content  = chat_file.read().decode('utf-8', errors='ignore')
            parsed       = parse_chat(raw_content)
            if parsed['total_messages'] == 0:
                messages.error(request, 'No messages found. Make sure this is a valid WhatsApp export.')
                return redirect('home')
            session_name = chat_file.name.replace('.txt', '')
            session      = save_chat_to_db(parsed, session_name)
            return redirect('dashboard', session_id=session.id)
        except Exception:
            messages.error(request, 'Something went wrong processing the file. Please try again.')
            return redirect('home')

    recent_sessions = ChatSession.objects.order_by('-uploaded_at')[:5]
    return render(request, 'analyzer/home.html', {
        'recent_sessions': recent_sessions,
        'features'       : FEATURES,
        'sample_chats'   : SAMPLE_CHATS,
    })


def load_sample(request, sample_id):
    sample = next((s for s in SAMPLE_CHATS if s['id'] == sample_id), None)
    if not sample:
        messages.error(request, 'Sample not found.')
        return redirect('home')
    try:
        sample_path = os.path.join(
            settings.BASE_DIR, 'analyzer', 'sample_chats', sample['file']
        )
        with open(sample_path, 'r', encoding='utf-8') as f:
            raw_content = f.read()
        parsed  = parse_chat(raw_content)
        session = save_chat_to_db(parsed, sample['name'])
        return redirect('dashboard', session_id=session.id)
    except FileNotFoundError:
        messages.error(request, 'Sample file not found on server.')
        return redirect('home')
    except Exception:
        messages.error(request, 'Could not load sample. Please try again.')
        return redirect('home')


def dashboard(request, session_id):
    session  = get_object_or_404(ChatSession, id=session_id)
    analysis = get_analysis(session)

    chart_data = {}
    if analysis.get('has_enough_data'):
        chart_data = {
            'top_members'          : json.dumps(list(analysis['top_members'])),
            'avg_length_data'      : json.dumps(analysis['avg_length_data']),
            'msgs_per_day'         : json.dumps(analysis['msgs_per_day']),
            'msgs_by_hour'         : json.dumps(analysis['msgs_by_hour']),
            'msgs_by_day'          : json.dumps(analysis['msgs_by_day']),
            'msgs_by_month'        : json.dumps(analysis['msgs_by_month']),
            'top_words'            : json.dumps(analysis['top_words']),
            'top_media'            : json.dumps(list(analysis.get('top_media', []))),
            'sentiment'            : json.dumps(analysis.get('sentiment', {})),
            'member_sentiment_list': json.dumps(analysis['sentiment'].get('member_sentiment_list', [])),
            'heatmap_months'       : json.dumps(analysis['heatmap_months']),
            'heatmap_days'         : json.dumps(analysis['heatmap_days']),
            'heatmap_z'            : json.dumps(analysis['heatmap_z']),
            'top_emojis'           : json.dumps(analysis['top_emojis']),
        }

    return render(request, 'analyzer/dashboard.html', {
        'session'   : session,
        'analysis'  : analysis,
        'chart_data': chart_data,
    })


def forensics(request, session_id):
    session        = get_object_or_404(ChatSession, id=session_id)
    forensics_data = get_forensics(session)

    # Get all unique senders for the dropdown
    senders = list(
        Message.objects.filter(session=session, is_system=False)
        .values_list('sender', flat=True)
        .distinct()
        .order_by('sender')
    )

    # Get all unique dates that have messages for the date picker
    from django.db.models.functions import TruncDate
    from django.db.models import Count
    active_dates = list(
        Message.objects.filter(session=session, is_system=False)
        .annotate(date=TruncDate('timestamp'))
        .values_list('date', flat=True)
        .distinct()
        .order_by('date')
    )
    # Format as strings for JS
    active_dates_str = [str(d) for d in active_dates]

    return render(request, 'analyzer/forensics.html', {
        'session'           : session,
        'data'              : forensics_data,
        'senders'           : senders,
        'active_dates'      : json.dumps(active_dates_str),
    })


def search_messages(request, session_id):
    """AJAX endpoint — search messages in a session."""
    session = get_object_or_404(ChatSession, id=session_id)
    query   = request.GET.get('q', '').strip()
    date    = request.GET.get('date', '').strip()
    sender  = request.GET.get('sender', '').strip()

    msgs = Message.objects.filter(
        session=session,
        is_system=False,
        is_media=False,
    ).order_by('timestamp')

    if query:
        msgs = msgs.filter(content__icontains=query)
    if date:
        msgs = msgs.filter(timestamp__date=date)
    if sender:
        msgs = msgs.filter(sender__exact=sender)

    results = []
    for msg in msgs[:100]:
        results.append({
            'sender'   : msg.sender,
            'content'  : msg.content,
            'timestamp': msg.timestamp.strftime('%d %b %Y, %I:%M %p'),
            'date'     : msg.timestamp.strftime('%Y-%m-%d'),
            'hour'     : msg.hour,
        })

    return JsonResponse({'results': results, 'count': len(results)})


def translate_message(request):
    """AJAX endpoint — translate a message using deep-translator."""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)

    try:
        body        = json.loads(request.body)
        text        = body.get('text', '').strip()
        target_lang = body.get('target_lang', 'en')

        if not text:
            return JsonResponse({'error': 'No text provided'}, status=400)

        from deep_translator import GoogleTranslator
        translated = GoogleTranslator(source='auto', target=target_lang).translate(text)
        return JsonResponse({'translated': translated})

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


def delete_session(request, session_id):
    session = get_object_or_404(ChatSession, id=session_id)
    if request.method == 'POST':
        session.delete()
        messages.success(request, 'Session deleted.')
    return redirect('home')


def all_sessions(request):
    sessions = ChatSession.objects.order_by('-uploaded_at')
    return render(request, 'analyzer/sessions.html', {'sessions': sessions})


def debug_analysis(request, session_id):
    session  = get_object_or_404(ChatSession, id=session_id)
    analysis = get_analysis(session)
    debug = {
        'total_messages': analysis.get('total_messages'),
        'total_members' : analysis.get('total_members'),
        'top_members'   : list(analysis.get('top_members', [])),
        'top_emojis'    : analysis.get('top_emojis', []),
        'sentiment'     : analysis.get('sentiment', {}),
    }
    return JsonResponse(debug, safe=False)