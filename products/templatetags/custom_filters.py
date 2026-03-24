from django import template

register = template.Library()

@register.filter
def format_weight(value):
    try:
        kilos = int(value)
        grams = int(round((value - kilos) * 1000))
        result = ""

        if kilos > 0:
            result += f"{kilos} کیلوگرم"
        if grams > 0:
            result += f" و {grams} گرم" if kilos > 0 else f"{grams} گرم"
        if not result:
            result = "۰ گرم"

        return result
    except:
        return value
    