import re
from django.core.exceptions import ValidationError

class UpperLowerDigitValidator:
    """
    英小文字・英大文字・数字をそれぞれ１文字以上含める
    """
    def validate(self, password, user=None):
        if not re.search(r"[a-z]", password):
            raise ValidationError("英小文字を１文字以上含めてください。", code="password_no_lower")
        if not re.search(r"[A-Z]", password):
            raise ValidationError("英大文字を１文字以上含めてください。", code="password_no_upper")
        if not re.search(r"\d", password):
            raise ValidationError("数字を１文字以上含めてください。", code="password_no_digit")
    
    def get_help_text(self):
        return "英小文字・英大文字・数字をそれぞれ１文字以上含めてください。"