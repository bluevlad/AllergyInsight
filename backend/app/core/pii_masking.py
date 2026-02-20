"""PII 마스킹 유틸리티"""


def mask_phone(phone: str) -> str:
    """전화번호 마스킹: 010-9999-8888 -> 010-****-8888"""
    if not phone:
        return phone
    # Remove non-digit characters for processing
    digits = phone.replace("-", "").replace(" ", "")
    if len(digits) == 11:
        return f"{digits[:3]}-****-{digits[7:]}"
    elif len(digits) == 10:
        return f"{digits[:3]}-***-{digits[6:]}"
    return phone[:3] + "*" * (len(phone) - 6) + phone[-3:] if len(phone) > 6 else phone


def mask_name(name: str) -> str:
    """이름 마스킹: 김철수 -> 김*수, 이가나다 -> 이**다"""
    if not name or len(name) < 2:
        return name
    if len(name) == 2:
        return name[0] + "*"
    return name[0] + "*" * (len(name) - 2) + name[-1]
