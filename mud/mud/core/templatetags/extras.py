import textwrap

from django.template.defaultfilters import stringfilter
from django import template


@stringfilter
def break_filter(lines):
    nlines = []
    for line in lines.split('\n'):
        a = textwrap.wrap(line, 80)
        if len(a):
            nlines += a
        else:
            nlines += ['']
    return '\n'.join(nlines)

register = template.Library()
register.filter('break', break_filter)


DIRECTIONS={
    'n': ('north', 's'),
    's': ('south', 'n'),
    'e': ('east', 'w'),
    'w': ('west', 'e'),
    }

@register.simple_tag
def long_direction(direction):
    return DIRECTIONS[direction][0]

@register.simple_tag
def opposite_long_direction(direction):
    return DIRECTIONS[DIRECTIONS[direction][1]][0]
