# generators/base.py
"""
Shared utilities and data structures for all code generators.

Provides: color conversion, gradient parsing, fill/stroke extraction,
layout info, typography info - framework-agnostic intermediate representations.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Tuple
import math


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

MAX_CHILDREN_LIMIT = 20       # React/Vue/CSS child limit per container
MAX_NATIVE_CHILDREN_LIMIT = 10  # SwiftUI/Kotlin child limit
MAX_DEPTH = 8                  # Max recursive depth

SWIFTUI_WEIGHT_MAP = {
    100: '.ultraLight', 200: '.thin', 300: '.light', 400: '.regular',
    500: '.medium', 600: '.semibold', 700: '.bold', 800: '.heavy', 900: '.black'
}

KOTLIN_WEIGHT_MAP = {
    100: 'FontWeight.Thin', 200: 'FontWeight.ExtraLight', 300: 'FontWeight.Light',
    400: 'FontWeight.Normal', 500: 'FontWeight.Medium', 600: 'FontWeight.SemiBold',
    700: 'FontWeight.Bold', 800: 'FontWeight.ExtraBold', 900: 'FontWeight.Black'
}

TAILWIND_WEIGHT_MAP = {
    100: 'font-thin', 200: 'font-extralight', 300: 'font-light',
    400: 'font-normal', 500: 'font-medium', 600: 'font-semibold',
    700: 'font-bold', 800: 'font-extrabold', 900: 'font-black'
}

TAILWIND_ALIGN_MAP = {
    'LEFT': 'text-left', 'CENTER': 'text-center',
    'RIGHT': 'text-right', 'JUSTIFIED': 'text-justify'
}


# ---------------------------------------------------------------------------
# Data Structures
# ---------------------------------------------------------------------------

@dataclass
class ColorValue:
    """Framework-agnostic color representation."""
    r: float  # 0-1 range (Figma native)
    g: float
    b: float
    a: float = 1.0

    @property
    def hex(self) -> str:
        ri, gi, bi = int(self.r * 255), int(self.g * 255), int(self.b * 255)
        if self.a < 1:
            return f"rgba({ri}, {gi}, {bi}, {self.a:.2f})"
        return f"#{ri:02x}{gi:02x}{bi:02x}"

    @property
    def rgb_ints(self) -> Tuple[int, int, int]:
        return int(self.r * 255), int(self.g * 255), int(self.b * 255)

    @classmethod
    def from_figma(cls, color: Dict[str, float], opacity: float = 1.0) -> 'ColorValue':
        return cls(
            r=color.get('r', 0), g=color.get('g', 0), b=color.get('b', 0),
            a=opacity if opacity < 1 else color.get('a', 1.0)
        )


@dataclass
class GradientStop:
    """Single gradient color stop."""
    color: ColorValue
    position: float  # 0-1


@dataclass
class GradientDef:
    """Framework-agnostic gradient definition."""
    type: str  # LINEAR, RADIAL, ANGULAR, DIAMOND
    stops: List[GradientStop]
    handle_positions: List[Dict[str, float]] = field(default_factory=list)
    opacity: float = 1.0

    @property
    def angle_degrees(self) -> float:
        """Calculate CSS angle from handle positions (for LINEAR)."""
        if len(self.handle_positions) < 2:
            return 180.0
        start = self.handle_positions[0]
        end = self.handle_positions[1]
        dx = end.get('x', 1) - start.get('x', 0)
        dy = end.get('y', 1) - start.get('y', 0)
        angle = math.degrees(math.atan2(dy, dx))
        return (90 - angle) % 360


@dataclass
class FillLayer:
    """Single fill layer. A node can have multiple fills stacked."""
    type: str  # SOLID, GRADIENT_LINEAR, GRADIENT_RADIAL, GRADIENT_ANGULAR, GRADIENT_DIAMOND, IMAGE
    color: Optional[ColorValue] = None
    gradient: Optional[GradientDef] = None
    image_ref: Optional[str] = None
    scale_mode: str = 'FILL'  # FILL, FIT, TILE, STRETCH
    opacity: float = 1.0
    visible: bool = True


@dataclass
class StrokeInfo:
    """Framework-agnostic stroke definition."""
    weight: float
    colors: List[FillLayer]  # Can be solid or gradient
    align: str = 'INSIDE'  # INSIDE, CENTER, OUTSIDE
    cap: str = 'NONE'
    join: str = 'MITER'
    dashes: List[float] = field(default_factory=list)
    individual_weights: Optional[Dict[str, float]] = None  # top, right, bottom, left


@dataclass
class CornerRadii:
    """Corner radius values."""
    top_left: float = 0
    top_right: float = 0
    bottom_right: float = 0
    bottom_left: float = 0

    @property
    def is_uniform(self) -> bool:
        return self.top_left == self.top_right == self.bottom_right == self.bottom_left

    @property
    def uniform_value(self) -> float:
        return self.top_left


@dataclass
class ShadowEffect:
    """Shadow effect."""
    type: str  # DROP_SHADOW, INNER_SHADOW
    color: ColorValue
    offset_x: float = 0
    offset_y: float = 0
    radius: float = 0
    spread: float = 0


@dataclass
class BlurEffect:
    """Blur effect."""
    type: str  # LAYER_BLUR, BACKGROUND_BLUR
    radius: float = 0


@dataclass
class LayoutInfo:
    """Auto-layout information."""
    mode: str  # VERTICAL, HORIZONTAL, NONE
    gap: float = 0
    padding_top: float = 0
    padding_right: float = 0
    padding_bottom: float = 0
    padding_left: float = 0
    primary_align: str = 'MIN'  # MIN, CENTER, MAX, SPACE_BETWEEN
    counter_align: str = 'MIN'  # MIN, CENTER, MAX
    primary_sizing: str = 'AUTO'  # AUTO, FIXED
    counter_sizing: str = 'AUTO'
    wrap: str = 'NO_WRAP'  # NO_WRAP, WRAP


@dataclass
class TextStyle:
    """Typography information."""
    font_family: str = ''
    font_size: float = 16
    font_weight: int = 400
    line_height: Optional[float] = None
    letter_spacing: float = 0
    text_align: str = 'LEFT'
    text_case: str = 'ORIGINAL'  # ORIGINAL, UPPER, LOWER, TITLE
    text_decoration: str = 'NONE'  # NONE, UNDERLINE, STRIKETHROUGH
    color: Optional[ColorValue] = None
    gradient: Optional[GradientDef] = None  # For gradient text fills
    max_lines: Optional[int] = None
    truncation: str = 'DISABLED'


@dataclass
class StyleBundle:
    """Complete style information for a node."""
    fills: List[FillLayer] = field(default_factory=list)
    stroke: Optional[StrokeInfo] = None
    corners: Optional[CornerRadii] = None
    shadows: List[ShadowEffect] = field(default_factory=list)
    blurs: List[BlurEffect] = field(default_factory=list)
    opacity: float = 1.0
    blend_mode: str = 'PASS_THROUGH'
    rotation: float = 0
    layout: Optional[LayoutInfo] = None
    width: float = 0
    height: float = 0
    clips_content: bool = False


# ---------------------------------------------------------------------------
# Color Conversion Helpers
# ---------------------------------------------------------------------------

def rgba_to_hex(color: Dict[str, float]) -> str:
    """Convert Figma color dict (r,g,b,a in 0-1) to hex string."""
    r = int(color.get('r', 0) * 255)
    g = int(color.get('g', 0) * 255)
    b = int(color.get('b', 0) * 255)
    a = color.get('a', 1)
    if a < 1:
        return f"rgba({r}, {g}, {b}, {a:.2f})"
    return f"#{r:02x}{g:02x}{b:02x}"


def hex_to_rgb(hex_color: str) -> Tuple[int, int, int]:
    """Convert hex color string to (R, G, B) tuple (0-255)."""
    hex_color = hex_color.strip()
    if hex_color.startswith('rgba'):
        parts = hex_color.replace('rgba(', '').replace(')', '').split(',')
        return int(parts[0].strip()), int(parts[1].strip()), int(parts[2].strip())
    hex_color = hex_color.lstrip('#')
    if len(hex_color) == 3:
        hex_color = ''.join(c * 2 for c in hex_color)
    if len(hex_color) >= 6:
        return int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)
    return 0, 0, 0


# ---------------------------------------------------------------------------
# Figma Node → Dataclass Parsers
# ---------------------------------------------------------------------------

def parse_fills(node: Dict[str, Any]) -> List[FillLayer]:
    """Parse all fills from a Figma node into FillLayer list."""
    fills = node.get('fills', [])
    result = []
    for fill in fills:
        visible = fill.get('visible', True)
        if not visible:
            continue
        fill_type = fill.get('type', '')
        layer = FillLayer(type=fill_type, visible=visible, opacity=fill.get('opacity', 1.0))

        if fill_type == 'SOLID':
            color_data = fill.get('color', {})
            layer.color = ColorValue.from_figma(color_data, fill.get('opacity', 1.0))

        elif 'GRADIENT' in fill_type:
            stops = []
            for s in fill.get('gradientStops', []):
                c = s.get('color', {})
                stops.append(GradientStop(
                    color=ColorValue(r=c.get('r', 0), g=c.get('g', 0), b=c.get('b', 0), a=c.get('a', 1)),
                    position=s.get('position', 0)
                ))
            gradient_type = fill_type.replace('GRADIENT_', '')
            layer.gradient = GradientDef(
                type=gradient_type,
                stops=stops,
                handle_positions=fill.get('gradientHandlePositions', []),
                opacity=fill.get('opacity', 1.0)
            )

        elif fill_type == 'IMAGE':
            layer.image_ref = fill.get('imageRef', '')
            layer.scale_mode = fill.get('scaleMode', 'FILL')

        result.append(layer)
    return result


def parse_stroke(node: Dict[str, Any]) -> Optional[StrokeInfo]:
    """Parse stroke from a Figma node."""
    strokes = node.get('strokes', [])
    weight = node.get('strokeWeight', 0)
    if not strokes or weight == 0:
        return None

    colors = []
    for s in strokes:
        if not s.get('visible', True):
            continue
        s_type = s.get('type', '')
        layer = FillLayer(type=s_type, visible=True, opacity=s.get('opacity', 1.0))
        if s_type == 'SOLID':
            layer.color = ColorValue.from_figma(s.get('color', {}), s.get('opacity', 1.0))
        elif 'GRADIENT' in s_type:
            stops = []
            for gs in s.get('gradientStops', []):
                c = gs.get('color', {})
                stops.append(GradientStop(
                    color=ColorValue(r=c.get('r', 0), g=c.get('g', 0), b=c.get('b', 0), a=c.get('a', 1)),
                    position=gs.get('position', 0)
                ))
            layer.gradient = GradientDef(
                type=s_type.replace('GRADIENT_', ''),
                stops=stops,
                handle_positions=s.get('gradientHandlePositions', []),
                opacity=s.get('opacity', 1.0)
            )
        colors.append(layer)

    if not colors:
        return None

    dashes = node.get('strokeDashes', [])
    individual = None
    iw = node.get('individualStrokeWeights')
    if iw:
        individual = {'top': iw.get('top', 0), 'right': iw.get('right', 0),
                       'bottom': iw.get('bottom', 0), 'left': iw.get('left', 0)}

    return StrokeInfo(
        weight=weight, colors=colors,
        align=node.get('strokeAlign', 'INSIDE'),
        cap=node.get('strokeCap', 'NONE'),
        join=node.get('strokeJoin', 'MITER'),
        dashes=dashes,
        individual_weights=individual
    )


def parse_corners(node: Dict[str, Any]) -> Optional[CornerRadii]:
    """Parse corner radii from a Figma node."""
    radii = node.get('rectangleCornerRadii')
    if radii and len(radii) == 4:
        return CornerRadii(top_left=radii[0], top_right=radii[1],
                          bottom_right=radii[2], bottom_left=radii[3])
    cr = node.get('cornerRadius', 0)
    if cr > 0:
        return CornerRadii(top_left=cr, top_right=cr, bottom_right=cr, bottom_left=cr)
    return None


def parse_effects(node: Dict[str, Any]) -> Tuple[List[ShadowEffect], List[BlurEffect]]:
    """Parse effects (shadows + blurs) from a Figma node."""
    effects = node.get('effects', [])
    shadows = []
    blurs = []
    for e in effects:
        if not e.get('visible', True):
            continue
        e_type = e.get('type', '')
        if e_type in ('DROP_SHADOW', 'INNER_SHADOW'):
            color = e.get('color', {})
            offset = e.get('offset', {'x': 0, 'y': 0})
            shadows.append(ShadowEffect(
                type=e_type,
                color=ColorValue(r=color.get('r', 0), g=color.get('g', 0),
                                b=color.get('b', 0), a=color.get('a', 0.25)),
                offset_x=offset.get('x', 0), offset_y=offset.get('y', 0),
                radius=e.get('radius', 0), spread=e.get('spread', 0)
            ))
        elif e_type in ('LAYER_BLUR', 'BACKGROUND_BLUR'):
            blurs.append(BlurEffect(type=e_type, radius=e.get('radius', 0)))
    return shadows, blurs


def parse_layout(node: Dict[str, Any]) -> Optional[LayoutInfo]:
    """Parse auto-layout from a Figma node."""
    mode = node.get('layoutMode')
    if not mode or mode == 'NONE':
        return None
    return LayoutInfo(
        mode=mode,
        gap=node.get('itemSpacing', 0),
        padding_top=node.get('paddingTop', 0),
        padding_right=node.get('paddingRight', 0),
        padding_bottom=node.get('paddingBottom', 0),
        padding_left=node.get('paddingLeft', 0),
        primary_align=node.get('primaryAxisAlignItems', 'MIN'),
        counter_align=node.get('counterAxisAlignItems', 'MIN'),
        primary_sizing=node.get('primaryAxisSizingMode', 'AUTO'),
        counter_sizing=node.get('counterAxisSizingMode', 'AUTO'),
        wrap=node.get('layoutWrap', 'NO_WRAP')
    )


def parse_text_style(node: Dict[str, Any]) -> TextStyle:
    """Parse text styling from a TEXT node."""
    style = node.get('style', {})
    fills = node.get('fills', [])

    # Text color: check for solid or gradient
    text_color = None
    text_gradient = None
    for fill in fills:
        if not fill.get('visible', True):
            continue
        if fill.get('type') == 'SOLID':
            text_color = ColorValue.from_figma(fill.get('color', {}), fill.get('opacity', 1.0))
            break
        elif 'GRADIENT' in fill.get('type', ''):
            stops = []
            for s in fill.get('gradientStops', []):
                c = s.get('color', {})
                stops.append(GradientStop(
                    color=ColorValue(r=c.get('r', 0), g=c.get('g', 0), b=c.get('b', 0), a=c.get('a', 1)),
                    position=s.get('position', 0)
                ))
            text_gradient = GradientDef(
                type=fill['type'].replace('GRADIENT_', ''),
                stops=stops,
                handle_positions=fill.get('gradientHandlePositions', []),
                opacity=fill.get('opacity', 1.0)
            )
            break

    return TextStyle(
        font_family=style.get('fontFamily', ''),
        font_size=style.get('fontSize', 16),
        font_weight=style.get('fontWeight', 400),
        line_height=style.get('lineHeightPx'),
        letter_spacing=style.get('letterSpacing', 0),
        text_align=style.get('textAlignHorizontal', 'LEFT'),
        text_case=style.get('textCase', 'ORIGINAL'),
        text_decoration=style.get('textDecoration', 'NONE'),
        color=text_color,
        gradient=text_gradient,
        max_lines=style.get('maxLines'),
        truncation=style.get('textTruncation', 'DISABLED')
    )


def parse_style_bundle(node: Dict[str, Any]) -> StyleBundle:
    """Parse complete style information from a Figma node."""
    bbox = node.get('absoluteBoundingBox', {})
    shadows, blurs = parse_effects(node)

    return StyleBundle(
        fills=parse_fills(node),
        stroke=parse_stroke(node),
        corners=parse_corners(node),
        shadows=shadows,
        blurs=blurs,
        opacity=node.get('opacity', 1.0),
        blend_mode=node.get('blendMode', 'PASS_THROUGH'),
        rotation=node.get('rotation', 0),
        layout=parse_layout(node),
        width=bbox.get('width', 0),
        height=bbox.get('height', 0),
        clips_content=node.get('clipsContent', False)
    )
