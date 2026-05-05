from analyzer.models import ChatSession, Message


def save_chat_to_db(parsed_data: dict, session_name: str) -> ChatSession:
    """
    Takes output from parse_chat() and saves everything to the database.
    Returns the ChatSession object so the view can redirect to it.
    """
    # Create the session first
    session = ChatSession.objects.create(
        session_name=session_name,
        total_messages=parsed_data['total_messages'],
        total_members=parsed_data['total_members'],
        device_type=parsed_data['device'],
    )

    # Bulk create all messages — much faster than saving one by one
    message_objects = []
    for m in parsed_data['messages']:
        message_objects.append(Message(
            session=session,
            timestamp=m['timestamp'],
            sender=m['sender'],
            content=m['content'],
            is_media=m['is_media'],
            is_system=m['is_system'],
            emoji_count=m['emoji_count'],
            has_link=m['has_link'],
            day=m['day'],
            month=m['month'],
            year=m['year'],
            hour=m['hour'],
        ))

    Message.objects.bulk_create(message_objects)
    return session