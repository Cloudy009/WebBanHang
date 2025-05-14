from django import template

register = template.Library()

@register.filter
def format_currency(value):
    """
    Định dạng số với dấu phân cách hàng nghìn là dấu chấm.
    """
    try:
        return f"{int(value):,}".replace(",", ".")
    except (ValueError, TypeError):
        return value  # Trả về giá trị gốc nếu có lỗi

@register.filter
def length_is(value, arg):
    try:
        return len(value) == int(arg)
    except:
        return False