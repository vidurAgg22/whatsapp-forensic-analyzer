from analyzer.services.parser import parse_chat


android_sample = """02/06/25, 7:03 pm - Messages and calls are end-to-end encrypted. Only people in this chat can read, listen to, or share them. *Learn more*
23/03/25, 5:55 pm - Group creator created group "Nukkad"
23/03/25, 5:55 pm - You were added
01/06/25, 10:32 am - SARTHAK JAIN Vips New: Bhai subha bhejta toh aap pdhte nhi
01/06/25, 10:32 am - SARTHAK JAIN Vips New: Bawal ho jata
01/06/25, 10:32 am - SARTHAK JAIN Vips New: Mai sbka bhala sochta hu pehle
01/06/25, 11:58 am - Mudit Vashistha Vips: Waiting for this message"""

iphone_sample = "[15/01/24, 6:14:59 PM] Maaticrafts X HUBAKO: \u200eMessages and calls are end-to-end encrypted.\n[15/01/24, 6:14:59 PM] Bhavesh Agarwal: \u200eBhavesh Agarwal created group \"Maaticrafts X HUBAKO\"\n[15/01/24, 6:14:59 PM] Maaticrafts X HUBAKO: \u200eBhavesh Agarwal added you\n[23/01/24, 10:44:57 AM] Hubako Media: Hello @\u2048Jayashree Maaticrafts\u2049 ,\nGood Morning!\n[23/01/24, 11:00:00 AM] Jayashree Maaticrafts: Good morning! How are you?\n[23/01/24, 11:01:00 AM] Hubako Media: Doing well thanks"
for i, line in enumerate(iphone_sample.splitlines()[:4]):
    print(f"Line {i}: {repr(line)}")
print("=" * 50)
print("ANDROID TEST")
print("=" * 50)
r = parse_chat(android_sample)
print(f"Device         : {r['device']}")
print(f"Total messages : {r['total_messages']}")
print(f"Total members  : {r['total_members']}")
print(f"Members        : {r['members']}")
print(f"Has enough data: {r['has_enough_data']}")
print("\nReal messages:")
for m in r['real_messages']:
    print(f"  {m['sender']}: {m['content']}")

print("\n" + "=" * 50)
print("IPHONE TEST")
print("=" * 50)
r2 = parse_chat(iphone_sample)
print(f"Device         : {r2['device']}")
print(f"Total messages : {r2['total_messages']}")
print(f"Total members  : {r2['total_members']}")
print(f"Members        : {r2['members']}")
print("\nReal messages:")
for m in r2['real_messages']:
    print(f"  {m['sender']}: {m['content']}")