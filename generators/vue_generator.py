"""
Vue Code Generator - Recursive template rendering with full property support.

Generates Vue SFC (Single File Component) code (with or without Tailwind CSS)
from Figma node trees.
Supports: fills (solid, gradient, image), strokes, corner radius, shadows,
blur, opacity, blend modes, rotation, padding, auto-layout, text styling,
hyperlinks, line clamping, and paragraph spacing.
"""

from typing import Dict, Any, List

# Import shared constants from base module
from generators.base import (
    TAILWIND_WEIGHT_MAP,
    TAILWIND_ALIGN_MAP,
    MAX_CHILDREN_LIMIT,
)

# Import helper functions from the main figma_mcp module.
# These will be migrated to generators.base in a future task.
from figma_mcp import (
    _get_background_css,
    _extract_stroke_data,
    _corner_radii_to_css,
    _transform_to_css,
    _blend_mode_to_css,
    _rgba_to_hex,
    _text_case_to_css,
    _text_decoration_to_css,
)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def generate_vue_code(node: Dict[str, Any], component_name: str, use_tailwind: bool = True) -> str:
    """Generate detailed Vue component code from Figma node with all nested children."""
    inner_template = recursive_node_to_vue_template(node, indent=4, use_tailwind=use_tailwind)

    if use_tailwind:
        code = f'''<script setup lang="ts">
defineProps<{{
  class?: string;
}}>();
</script>

<template>
{inner_template}
</template>
'''
    else:
        # Generate CSS for all nodes
        css_rules = generate_recursive_css(node, [])
        css_code = '\n'.join(css_rules)

        code = f'''<script setup lang="ts">
defineProps<{{
  class?: string;
}}>();
</script>

<template>
{inner_template}
</template>

<style scoped>
{css_code}
</style>
'''
    return code


def recursive_node_to_vue_template(node: Dict[str, Any], indent: int = 4, use_tailwind: bool = True) -> str:
    """Recursively generate Vue template code for nested children with enhanced styles."""
    lines = []
    prefix = ' ' * indent
    node_type = node.get('type', '')
    name = node.get('name', 'Unknown')

    bbox = node.get('absoluteBoundingBox', {})
    width = int(bbox.get('width', 0))
    height = int(bbox.get('height', 0))

    # Fills (with gradient support)
    fills = node.get('fills', [])
    bg_value, bg_type = _get_background_css(node)

    # Strokes
    stroke_data = _extract_stroke_data(node)
    stroke_color = ''
    stroke_weight = stroke_data['weight'] if stroke_data else 0
    if stroke_data and stroke_data['colors']:
        first_stroke = stroke_data['colors'][0]
        if first_stroke.get('type') == 'SOLID':
            stroke_color = first_stroke.get('color', '')

    # Corner radius (with individual corners)
    corner_radius_css = _corner_radii_to_css(node)

    # Transform
    transform_css = _transform_to_css(node)

    # Blend mode and opacity
    blend_mode = node.get('blendMode', 'PASS_THROUGH')
    blend_mode_css = _blend_mode_to_css(blend_mode)
    opacity = node.get('opacity', 1)

    # Layout
    layout_mode = node.get('layoutMode')
    gap = node.get('itemSpacing', 0)
    padding_top = node.get('paddingTop', 0)
    padding_right = node.get('paddingRight', 0)
    padding_bottom = node.get('paddingBottom', 0)
    padding_left = node.get('paddingLeft', 0)

    if node_type == 'TEXT':
        text = node.get('characters', name)
        style = node.get('style', {})
        font_size = style.get('fontSize', 16)
        font_weight = style.get('fontWeight', 400)
        text_case = style.get('textCase', 'ORIGINAL')
        text_decoration = style.get('textDecoration', 'NONE')
        line_height = style.get('lineHeightPx')
        letter_spacing = style.get('letterSpacing', 0)
        text_align = style.get('textAlignHorizontal', 'LEFT').lower()

        # Get hyperlink if present
        hyperlink = node.get('hyperlink')
        hyperlink_url = None
        if hyperlink and hyperlink.get('type') == 'URL':
            hyperlink_url = hyperlink.get('url', '')

        text_color = ''
        if fills and fills[0].get('type') == 'SOLID' and fills[0].get('visible', True):
            text_color = _rgba_to_hex(fills[0].get('color', {}))

        # Convert text case and decoration to CSS
        text_transform = _text_case_to_css(text_case)
        text_dec_value = _text_decoration_to_css(text_decoration)

        # Get maxLines and textTruncation for line-clamp
        max_lines = style.get('maxLines')
        text_truncation = style.get('textTruncation', 'DISABLED')

        if use_tailwind:
            weight_class = TAILWIND_WEIGHT_MAP.get(font_weight, 'font-normal')
            align_class = TAILWIND_ALIGN_MAP.get(text_align.upper(), '')

            # Tailwind text-transform classes
            transform_map = {'uppercase': 'uppercase', 'lowercase': 'lowercase', 'capitalize': 'capitalize'}
            transform_class = transform_map.get(text_transform, '') if text_transform else ''

            # Tailwind text-decoration classes
            decoration_map = {'underline': 'underline', 'line-through': 'line-through'}
            decoration_class = decoration_map.get(text_dec_value, '') if text_dec_value else ''

            classes = [f'text-[{int(font_size)}px]', weight_class]
            if text_color:
                classes.append(f'text-[{text_color}]')
            if line_height:
                classes.append(f'leading-[{int(line_height)}px]')
            if letter_spacing:
                classes.append(f'tracking-[{letter_spacing:.2f}px]')
            if align_class:
                classes.append(align_class)
            if transform_class:
                classes.append(transform_class)
            if decoration_class:
                classes.append(decoration_class)

            # Tailwind line-clamp for maxLines
            if max_lines and max_lines > 0:
                classes.append(f'line-clamp-{max_lines}')
                if text_truncation == 'ENDING':
                    classes.append('text-ellipsis')

            # Paragraph spacing (margin-bottom)
            paragraph_spacing = style.get('paragraphSpacing', 0)
            if paragraph_spacing and paragraph_spacing > 0:
                classes.append(f'mb-[{int(paragraph_spacing)}px]')

            class_str = ' '.join(filter(None, classes))
            # Wrap in anchor tag if hyperlink present
            if hyperlink_url:
                lines.append(f'{prefix}<a href="{hyperlink_url}" class="{class_str}" target="_blank" rel="noopener noreferrer">{text}</a>')
            else:
                lines.append(f'{prefix}<span class="{class_str}">{text}</span>')
        else:
            # Wrap in anchor tag if hyperlink present
            if hyperlink_url:
                lines.append(f'{prefix}<a href="{hyperlink_url}" class="text-{name.lower().replace(" ", "-")}" target="_blank" rel="noopener noreferrer">{text}</a>')
            else:
                lines.append(f'{prefix}<span class="text-{name.lower().replace(" ", "-")}">{text}</span>')
    else:
        if use_tailwind:
            classes = []
            inline_styles = []

            if width:
                classes.append(f'w-[{width}px]')
            if height:
                classes.append(f'h-[{height}px]')

            # Background
            if bg_value and bg_type:
                if bg_type == 'color':
                    classes.append(f'bg-[{bg_value}]')
                elif bg_type in ('gradient', 'image', 'layered'):
                    # Gradients, images, and layered backgrounds need inline style
                    inline_styles.append(f"background: {bg_value}")

            # Corner radius
            if corner_radius_css:
                classes.append(f'rounded-[{corner_radius_css}]')

            # Strokes
            if stroke_color and stroke_weight:
                classes.append(f'border-[{stroke_weight}px]')
                classes.append(f'border-[{stroke_color}]')

            # Transform
            if transform_css:
                inline_styles.append(f"transform: {transform_css}")

            # Blend mode
            if blend_mode_css:
                classes.append(f'mix-blend-{blend_mode_css}')

            # Opacity
            if opacity < 1:
                classes.append(f'opacity-[{opacity}]')

            # Layout
            if layout_mode:
                classes.append('flex')
                classes.append('flex-col' if layout_mode == 'VERTICAL' else 'flex-row')
                if gap:
                    classes.append(f'gap-[{gap}px]')

            # Padding
            if padding_top:
                classes.append(f'pt-[{padding_top}px]')
            if padding_right:
                classes.append(f'pr-[{padding_right}px]')
            if padding_bottom:
                classes.append(f'pb-[{padding_bottom}px]')
            if padding_left:
                classes.append(f'pl-[{padding_left}px]')

            # Flex child properties (layoutGrow, layoutPositioning, layoutAlign)
            layout_grow = node.get('layoutGrow', 0)
            layout_positioning = node.get('layoutPositioning')
            layout_align = node.get('layoutAlign')

            if layout_grow and layout_grow > 0:
                classes.append('grow')  # Tailwind: flex-grow: 1
            if layout_positioning == 'ABSOLUTE':
                classes.append('absolute')
            if layout_align == 'STRETCH':
                classes.append('self-stretch')
            elif layout_align == 'INHERIT':
                classes.append('self-auto')

            class_str = ' '.join(filter(None, classes))

            if inline_styles:
                style_str = '; '.join(inline_styles)
                lines.append(f'{prefix}<div class="{class_str}" style="{style_str}">')
            else:
                lines.append(f'{prefix}<div class="{class_str}">')
        else:
            class_name = name.lower().replace(' ', '-').replace('/', '-')
            lines.append(f'{prefix}<div class="{class_name}">')

        children = node.get('children', [])
        for child in children[:MAX_CHILDREN_LIMIT]:
            child_template = recursive_node_to_vue_template(child, indent + 2, use_tailwind)
            if child_template:
                lines.append(child_template)

        lines.append(f'{prefix}</div>')

    return '\n'.join(lines)


def generate_recursive_css(node: Dict[str, Any], rules: List[str], parent_name: str = '') -> List[str]:
    """Generate CSS rules for all nodes recursively."""
    node_type = node.get('type', '')
    name = node.get('name', 'Unknown')
    class_name = name.lower().replace(' ', '-').replace('/', '-')

    bbox = node.get('absoluteBoundingBox', {})
    width = int(bbox.get('width', 0))
    height = int(bbox.get('height', 0))

    fills = node.get('fills', [])
    bg_color = ''
    if fills and fills[0].get('type') == 'SOLID' and fills[0].get('visible', True):
        bg_color = _rgba_to_hex(fills[0].get('color', {}))

    strokes = node.get('strokes', [])
    stroke_css = ''
    if strokes and strokes[0].get('type') == 'SOLID' and strokes[0].get('visible', True):
        stroke_color = _rgba_to_hex(strokes[0].get('color', {}))
        stroke_weight = node.get('strokeWeight', 1)
        stroke_css = f"border: {stroke_weight}px solid {stroke_color};"

    corner_radius = node.get('cornerRadius', 0)
    layout_mode = node.get('layoutMode')
    gap = node.get('itemSpacing', 0)
    padding_top = node.get('paddingTop', 0)
    padding_right = node.get('paddingRight', 0)
    padding_bottom = node.get('paddingBottom', 0)
    padding_left = node.get('paddingLeft', 0)

    css_props = []
    if width:
        css_props.append(f"width: {width}px;")
    if height:
        css_props.append(f"height: {height}px;")
    if bg_color:
        css_props.append(f"background-color: {bg_color};")
    if corner_radius:
        css_props.append(f"border-radius: {corner_radius}px;")
    if stroke_css:
        css_props.append(stroke_css)
    if layout_mode:
        css_props.append("display: flex;")
        css_props.append(f"flex-direction: {'column' if layout_mode == 'VERTICAL' else 'row'};")
        if gap:
            css_props.append(f"gap: {gap}px;")
    if padding_top or padding_right or padding_bottom or padding_left:
        css_props.append(f"padding: {padding_top}px {padding_right}px {padding_bottom}px {padding_left}px;")

    if node_type == 'TEXT':
        style = node.get('style', {})
        font_size = style.get('fontSize', 16)
        font_weight = style.get('fontWeight', 400)
        text_case = style.get('textCase', 'ORIGINAL')
        text_decoration = style.get('textDecoration', 'NONE')
        line_height = style.get('lineHeightPx')
        letter_spacing = style.get('letterSpacing', 0)
        text_align = style.get('textAlignHorizontal', 'LEFT').lower()
        font_family = style.get('fontFamily', '')
        text_color = ''
        if fills and fills[0].get('type') == 'SOLID':
            text_color = _rgba_to_hex(fills[0].get('color', {}))

        css_props = [f"font-size: {int(font_size)}px;", f"font-weight: {font_weight};"]
        if text_color:
            css_props.append(f"color: {text_color};")
        if font_family:
            css_props.append(f"font-family: '{font_family}', sans-serif;")
        if line_height:
            css_props.append(f"line-height: {line_height}px;")
        if letter_spacing:
            css_props.append(f"letter-spacing: {letter_spacing}px;")
        if text_align != 'left':
            css_props.append(f"text-align: {text_align};")

        # Text transform (textCase)
        text_transform = _text_case_to_css(text_case)
        if text_transform:
            css_props.append(f"text-transform: {text_transform};")

        # Text decoration
        text_dec_value = _text_decoration_to_css(text_decoration)
        if text_dec_value:
            css_props.append(f"text-decoration: {text_dec_value};")

    if css_props:
        rule = f".{class_name} {{\n  " + "\n  ".join(css_props) + "\n}"
        rules.append(rule)

    for child in node.get('children', [])[:20]:
        generate_recursive_css(child, rules, class_name)

    return rules


# ---------------------------------------------------------------------------
# Backward-compatible aliases (match the original underscore-prefixed names)
# ---------------------------------------------------------------------------

_generate_vue_code = generate_vue_code
_recursive_node_to_vue_template = recursive_node_to_vue_template
_generate_recursive_css = generate_recursive_css
