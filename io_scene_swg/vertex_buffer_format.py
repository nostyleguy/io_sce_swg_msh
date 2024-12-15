# MIT License
#
# Copyright (c) 2022 Nick Rafalski
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

# Bit-shift and mask constants for texture coordinate sets and blend settings
TextureCoordinateSetCountShift = 8  # Shift for texture coordinate set count
TextureCoordinateSetCountMask = 0b1111  # Mask to extract 4 bits for texture set count (15 in decimal)

TextureCoordinateSetDimensionBaseShift = 12  # Base shift for texture coordinate set dimensions
TextureCoordinateSetDimensionPerSetShift = 2  # Shift per texture set
TextureCoordinateSetDimensionAdjustment = 1  # Adjustment for texture dimension
TextureCoordinateSetDimensionMask = 0b11  # Mask to extract 2 bits for texture set dimension (3 in decimal)

BlendCountShift = 24  # Shift for blend count
BlendMask = 0b111  # Mask to extract 3 bits for blend count (7 in decimal)

# Bit flag constants for different vertex attributes
F_none = 0b00000000000000000000000000000000  # No attributes
F_position = 0b00000000000000000000000000000001  # Position flag
F_transformed = 0b00000000000000000000000000000010  # Transformed flag
F_normal = 0b00000000000000000000000000000100  # Normal flag
F_color0 = 0b00000000000000000000000000001000  # Color0 flag
F_color1 = 0b00000000000000000000000000010000  # Color1 flag
F_pointSize = 0b00000000000000000000000000010000  # Point size flag

# Texture coordinate set count flags (0-8 sets)
F_textureCoordinateCount0 = 0b00000000000000000000000000000000  # 0 texture coordinate sets
F_textureCoordinateCount1 = 0b00000000000000000000000100000000  # 1 texture coordinate set
F_textureCoordinateCount2 = 0b00000000000000000000001000000000  # 2 texture coordinate sets
F_textureCoordinateCount3 = 0b00000000000000000000001100000000  # 3 texture coordinate sets
F_textureCoordinateCount4 = 0b00000000000000000000010000000000  # 4 texture coordinate sets
F_textureCoordinateCount5 = 0b00000000000000000000010100000000  # 5 texture coordinate sets
F_textureCoordinateCount6 = 0b00000000000000000000011000000000  # 6 texture coordinate sets
F_textureCoordinateCount7 = 0b00000000000000000000011100000000  # 7 texture coordinate sets
F_textureCoordinateCount8 = 0b00000000000000000000100000000000  # 8 texture coordinate sets

# Texture coordinate set dimensions (1D, 2D, 3D, 4D) for various sets
F_textureCoordinateSet0_1d = 0b00000000000000000000000000000000  # Set 0, 1D
F_textureCoordinateSet0_2d = 0b00000000000000000001000000000000  # Set 0, 2D
F_textureCoordinateSet0_3d = 0b00000000000000000010000000000000  # Set 0, 3D
F_textureCoordinateSet0_4d = 0b00000000000000000011000000000000  # Set 0, 4D
F_textureCoordinateSet1_1d = 0b00000000000000000000000000000000  # Set 1, 1D
F_textureCoordinateSet1_2d = 0b00000000000000000100000000000000  # Set 1, 2D
F_textureCoordinateSet1_3d = 0b00000000000000001000000000000000  # Set 1, 3D
F_textureCoordinateSet1_4d = 0b00000000000000001100000000000000  # Set 1, 4D

# Further texture sets can be defined similarly for higher indices (Set 2-7)

# Blend flags for blending operations
F_blend0 = 0b00000000000000000000000000000000  # Blend 0 (no blending)
F_blend1 = 0b00010000000000000000000000000000  # Blend 1
F_blend2 = 0b00100000000000000000000000000000  # Blend 2
F_blend3 = 0b00110000000000000000000000000000  # Blend 3
F_blend4 = 0b01000000000000000000000000000000  # Blend 4
F_blend5 = 0b01010000000000000000000000000000  # Blend 5

# Functions to check the presence of certain attributes
def hasPosition(flags):
    """Check if the position flag is set."""
    return (flags & F_position) != 0

def isTransformed(flags):
    """Check if the transformed flag is set."""
    return (flags & F_transformed) != 0

def hasNormal(flags):
    """Check if the normal flag is set."""
    return (flags & F_normal) != 0

def hasPointSize(flags):
    """Check if the point size flag is set."""
    return (flags & F_pointSize) != 0

def hasColor0(flags):
    """Check if the Color0 flag is set."""
    return (flags & F_color0) != 0

def hasColor1(flags):
    """Check if the Color1 flag is set."""
    return (flags & F_color1) != 0

# Function to get the number of texture coordinate sets
def getNumberOfTextureCoordinateSets(flags):
    """Extract the number of texture coordinate sets from the flags."""
    return (flags >> TextureCoordinateSetCountShift) & TextureCoordinateSetCountMask

# Function to get the dimension of a specific texture coordinate set
def getTextureCoordinateSetDimension(flags, textureCoordinateSet):
    """Extract the dimension of a given texture coordinate set."""
    shift = TextureCoordinateSetDimensionBaseShift + (textureCoordinateSet * TextureCoordinateSetDimensionPerSetShift)
    dimension = (flags >> shift) & TextureCoordinateSetDimensionMask
    return dimension + TextureCoordinateSetDimensionAdjustment

# Functions to enable or disable attributes
def setPosition(flags, enabled):
    """Enable or disable the position attribute."""
    if enabled:
        flags |= F_position
    else:
        flags &= ~F_position
    return flags

def setTransformed(flags, enabled):
    """Enable or disable the transformed attribute."""
    if enabled:
        flags |= F_transformed
    else:
        flags &= ~F_transformed
    return flags

def setNormal(flags, enabled):
    """Enable or disable the normal attribute."""
    if enabled:
        flags |= F_normal
    else:
        flags &= ~F_normal
    return flags

def setPointSize(flags, enabled):
    """Enable or disable the point size attribute."""
    if enabled:
        flags |= F_pointSize
    else:
        flags &= ~F_pointSize
    return flags

def setColor0(flags, enabled):
    """Enable or disable the Color0 attribute."""
    if enabled:
        flags |= F_color0
    else:
        flags &= ~F_color0
    return flags

def setColor1(flags, enabled):
    """Enable or disable the Color1 attribute."""
    if enabled:
        flags |= F_color1
    else:
        flags &= ~F_color1
    return flags

# Functions to set texture coordinate properties
def setNumberOfTextureCoordinateSets(flags, numberOfTextureCoordinateSets):
    """Set the number of texture coordinate sets."""
    flags = (flags & ~(TextureCoordinateSetCountMask << TextureCoordinateSetCountShift)) | \
            (numberOfTextureCoordinateSets << TextureCoordinateSetCountShift)
    return flags

def setTextureCoordinateSetDimension(flags, textureCoordinateSet, dimension):
    """Set the dimension for a specific texture coordinate set."""
    shift = TextureCoordinateSetDimensionBaseShift + (textureCoordinateSet * TextureCoordinateSetDimensionPerSetShift)
    flags = (flags & ~(TextureCoordinateSetDimensionMask << shift)) | \
            ((dimension - TextureCoordinateSetDimensionAdjustment) << shift)
    return flags

