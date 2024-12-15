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

class Vector3D:
    __slots__ = ('x', 'y', 'z')  # Memory optimization by restricting instance attributes

    def __init__(self, x: float, y: float, z: float) -> None:
        """
        Initialize a 3D vector with coordinates (x, y, z).
        """
        self.x = x
        self.y = y
        self.z = z

    def __neg__(self) -> 'Vector3D':
        """
        Return the negation of the vector (i.e., the vector pointing in the opposite direction).
        """
        return Vector3D(-self.x, -self.y, -self.z)

    def __add__(self, other: 'Vector3D') -> 'Vector3D':
        """
        Add two vectors component-wise.
        """
        return Vector3D(self.x + other.x, self.y + other.y, self.z + other.z)

    def __sub__(self, other: 'Vector3D') -> 'Vector3D':
        """
        Subtract two vectors component-wise.
        """
        return Vector3D(self.x - other.x, self.y - other.y, self.z - other.z)

    @staticmethod
    def dot(first: 'Vector3D', second: 'Vector3D') -> float:
        """
        Compute the dot product of two vectors.
        Dot product formula: x1 * x2 + y1 * y2 + z1 * z2
        """
        return first.x * second.x + first.y * second.y + first.z * second.z

    @staticmethod
    def cross(first: 'Vector3D', second: 'Vector3D') -> 'Vector3D':
        """
        Compute the cross product of two vectors.
        Cross product formula:
        x = (y1 * z2) - (z1 * y2)
        y = (z1 * x2) - (x1 * z2)
        z = (x1 * y2) - (y1 * x2)
        """
        return Vector3D(
            first.y * second.z - first.z * second.y,
            first.z * second.x - first.x * second.z,
            first.x * second.y - first.y * second.x
        )

    def length(self) -> float:
        """
        Compute the magnitude (length) of the vector.
        Length formula: sqrt(x^2 + y^2 + z^2)
        """
        return (self.x ** 2 + self.y ** 2 + self.z ** 2) ** 0.5

    def normalize(self) -> 'Vector3D':
        """
        Normalize the vector (make its length 1 while preserving direction).
        """
        magnitude = self.length()
        if magnitude > 0:
            return Vector3D(self.x / magnitude, self.y / magnitude, self.z / magnitude)
        return self  # Return zero vector if magnitude is zero

    def __str__(self) -> str:
        """
        Return the string representation of the vector in (x, y, z) format.
        """
        return f'({self.x}, {self.y}, {self.z})'


def _calcSurfaceNormal(verts: list[Vector3D]) -> Vector3D:
    """
    Calculate the surface normal for a polygon defined by a list of vertices in 3D space.

    The normal is computed using a method based on Newell's algorithm for polygons.
    It assumes the vertices are ordered in a counter-clockwise direction.

    Args:
        verts (list[Vector3D]): A list of 3D vectors representing the vertices of the polygon.

    Returns:
        Vector3D: The normalized surface normal of the polygon.
    """
    if len(verts) < 3:
        raise ValueError("At least 3 vertices are required to compute a surface normal.")

    result_normal = Vector3D(0.0, 0.0, 0.0)
    n = len(verts)

    # Loop over each vertex and accumulate the normal vector components
    for i in range(n):
        current = verts[i]
        next_vert = verts[(i + 1) % n]  # Next vertex, wrap around with modulo

        # Using Newell's method to accumulate the components of the normal vector
        result_normal.x += (current.y - next_vert.y) * (current.z + next_vert.z)
        result_normal.y += (current.z - next_vert.z) * (current.x + next_vert.x)
        result_normal.z += (current.x - next_vert.x) * (current.y + next_vert.y)

    # Normalize the resulting vector to ensure it's a unit vector
    return result_normal.normalize()
