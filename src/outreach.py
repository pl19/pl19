"""Draft outreach emails to brokers and listing contacts. Drafts only; nothing is sent."""


def _sign(profile):
    o = profile.get("outreach", {})
    lines = [o.get("buyer_name") or "[Your name]"]
    for k in ("buyer_phone", "buyer_email"):
        if o.get(k):
            lines.append(o[k])
    return "\n".join(lines)


def listing_email(row, profile):
    pitch = profile.get("outreach", {}).get("pitch", "")
    subject = f"Inquiry: {row['name']}"
    body = (
        f"Hello,\n\n"
        f"I came across your listing for \"{row['name']}\""
        f"{' in ' + row['location'] if row.get('location') else ''} and would like to learn more. "
        f"{pitch}\n\n"
        f"I'm happy to sign an NDA. Could you send the CIM or teaser, and let me know the best time for a call?\n\n"
        f"Thank you,\n{_sign(profile)}\n"
    )
    return subject, body


def broker_email(broker, sectors, profile):
    contact = (broker.get("Key contact(s)") or "").split(";")[0].strip()
    first = contact.split()[0] if contact else "there"
    pitch = profile.get("outreach", {}).get("pitch", "")
    subject = "Buyer for manufacturing businesses, $4M+ revenue"
    body = (
        f"Hi {first},\n\n"
        f"{pitch} I'm focused on {', '.join(sectors)}, which overlaps with {broker.get('Firm', 'your firm')}'s coverage.\n\n"
        f"Could you add me to your buyer list and send anything current or upcoming that fits? "
        f"I'm happy to share proof of funds and sign NDAs.\n\n"
        f"Best regards,\n{_sign(profile)}\n"
    )
    return subject, body


def render(subject, body, to=""):
    return f"To: {to}\nSubject: {subject}\n\n{body}"
