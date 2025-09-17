import inspect
import io
from typing import Any, Dict, Optional, Set


def generate_object_tree(obj: Any, max_depth: int = 25, visited: Optional[Set[int]] = None,
                        current_depth: int = 0) -> Dict[str, Any]:
    """
    Generate an object tree representation of a live Python object.

    This function creates a nested dictionary structure representing the object's
    type hierarchy and immediate children (instance attributes and fields).
    It utilizes Python's inspect module where appropriate for introspection.

    The resulting structure is optimized for use with pprint.pprint() to display
    a readable tree representation of the object.

    Args:
        obj: The live object to introspect
        max_depth: Maximum recursion depth to prevent infinite loops (default: 5)
        visited: Set of object IDs to track circular references (internal use)
        current_depth: Current recursion depth (internal use)

    Returns:
        Dictionary containing the object tree structure with the following keys:
        - 'type': The object's type name (__class__.__name__)
        - 'module': The module where the type is defined (if not builtin)
        - 'value': For primitive types, the actual repr() value
        - 'children': Dictionary of child attributes and their recursive trees
        - 'elements': For collections, indexed or named elements
        - 'items': For dictionaries, key-value pairs
        - 'length': For collections, the number of items
        - Additional metadata keys prefixed with '_' for internal information

    Examples:
        >>> class Person:
        ...     def __init__(self, name, age):
        ...         self.name = name
        ...         self.age = age
        ...
        >>> person = Person("Alice", 30)
        >>> tree = generate_object_tree(person)
        >>> pprint(tree)
        {'children': {'age': {'type': 'int', 'value': '30'},
                      'name': {'type': 'str', 'value': "'Alice'"}},
         'module': '__main__',
         'type': 'Person'}

        >>> # Works with __slots__ classes too
        >>> class Point:
        ...     __slots__ = ['x', 'y']
        ...     def __init__(self, x, y):
        ...         self.x, self.y = x, y
        ...
        >>> point = Point(1, 2)
        >>> pprint(generate_object_tree(point))
        {'children': {'x': {'type': 'int', 'value': '1'},
                      'y': {'type': 'int', 'value': '2'}},
         'module': '__main__',
         'type': 'Point'}

    Notes:
        - Handles circular references by tracking visited objects
        - Respects max_depth to prevent infinite recursion
        - Filters out methods, functions, and dunder attributes for cleaner output
        - Uses inspect.getmembers() as fallback for objects without __dict__ or __slots__
        - Gracefully handles inspection errors and inaccessible attributes
    """
    if visited is None:
        visited = set()

    # Prevent infinite recursion
    if current_depth >= max_depth:
        try:
            # Try to get a simple representation
            representation = repr(obj)
            if len(representation) > 60:
                representation = f"{obj.__class__.__name__} at {hex(obj_id)}"
        except Exception:
            representation = f"<{type(obj).__name__} object>"
        return {"type": type(obj).__name__, "value": representation, "_truncated": "max_depth_reached"}

    # Handle circular references
    obj_id = id(obj)
    if obj_id in visited:
        try:
            # Try to get a simple representation
            representation = repr(obj)
            if len(representation) > 60:
                representation = f"{obj.__class__.__name__} at {hex(obj_id)}"
        except Exception:
            representation = f"<{type(obj).__name__} object>"
        return {"type": type(obj).__name__, "value": representation, "_truncated": "circular_reference"}

    visited.add(obj_id)

    try:
        # Start building the tree node
        tree_node = {"type": type(obj).__name__}

        # Add module info for non-builtin types
        obj_module = getattr(type(obj), "__module__", None)
        if obj_module and obj_module not in ("builtins", "__builtin__"):
            tree_node["module"] = obj_module

        # Handle None separately
        if obj is None:
            tree_node["value"] = "None"
            return tree_node

        # Treat logging.Logger instances as simple terminal nodes
        try:
            import logging as _logging
            if isinstance(obj, _logging.Logger):
                tree_node["value"] = repr(obj)
                tree_node["_note"] = "logging.Logger (simple)"
                return tree_node
        except Exception:
            pass

        # Handle primitive types
        if isinstance(obj, (int, float, str, bool)):
            tree_node["value"] = repr(obj)
            return tree_node

        # Handle bytes and bytearray
        if isinstance(obj, (bytes, bytearray)):
            if len(obj) <= 20:
                tree_node["value"] = repr(obj)
            else:
                tree_node["value"] = f"<{type(obj).__name__} of length {len(obj)}>"
            return tree_node

        # Handle sequence types (list, tuple, etc.)
        if isinstance(obj, (list, tuple)):
            tree_node["length"] = len(obj)
            if len(obj) == 0:
                tree_node["value"] = "empty"
            elif len(obj) <= 5:  # Show details for small collections
                tree_node["elements"] = {}
                for i, item in enumerate(obj):
                    tree_node["elements"][f"[{i}]"] = generate_object_tree(
                        item, max_depth, visited.copy(), current_depth + 1
                    )
            else:
                tree_node["_preview"] = f"showing first 3 of {len(obj)} items"
                tree_node["elements"] = {}
                for i in range(3):
                    tree_node["elements"][f"[{i}]"] = generate_object_tree(
                        obj[i], max_depth, visited.copy(), current_depth + 1
                    )
            return tree_node

        # Handle sets and frozensets
        if isinstance(obj, (set, frozenset)):
            tree_node["length"] = len(obj)
            if len(obj) == 0:
                tree_node["value"] = "empty"
            elif len(obj) <= 5:
                tree_node["elements"] = {}
                for i, item in enumerate(obj):
                    tree_node["elements"][f"item_{i}"] = generate_object_tree(
                        item, max_depth, visited.copy(), current_depth + 1
                    )
            else:
                tree_node["_preview"] = f"showing 3 of {len(obj)} items"
                tree_node["elements"] = {}
                for i, item in enumerate(list(obj)[:3]):
                    tree_node["elements"][f"item_{i}"] = generate_object_tree(
                        item, max_depth, visited.copy(), current_depth + 1
                    )
            return tree_node

        # Handle dictionaries
        if isinstance(obj, dict):
            tree_node["length"] = len(obj)
            if len(obj) == 0:
                tree_node["value"] = "empty"
            else:
                items_to_show = min(5, len(obj))
                if len(obj) > 5:
                    tree_node["_preview"] = f"showing first {items_to_show} of {len(obj)} items"

                tree_node["items"] = {}
                for i, (key, value) in enumerate(obj.items()):
                    if i >= items_to_show:
                        break
                    # Handle non-string keys safely
                    safe_key = str(key) if isinstance(key, (str, int, float)) else f"<{type(key).__name__}>"
                    tree_node["items"][safe_key] = generate_object_tree(
                        value, max_depth, visited.copy(), current_depth + 1
                    )
            return tree_node

        # For custom objects, introspect their attributes
        tree_node["children"] = {}

        # Strategy 1: Try using object's __dict__ (most common case)
        if hasattr(obj, '__dict__') and obj.__dict__:
            for name, value in obj.__dict__.items():
                if not name.startswith('__'):  # Skip dunder attributes for cleaner output
                    tree_node["children"][name] = generate_object_tree(
                        value, max_depth, visited.copy(), current_depth + 1
                    )

        # Strategy 2: Handle __slots__ objects
        elif hasattr(type(obj), '__slots__'):
            for slot_name in type(obj).__slots__:
                if hasattr(obj, slot_name):
                    try:
                        value = getattr(obj, slot_name)
                        tree_node["children"][slot_name] = generate_object_tree(
                            value, max_depth, visited.copy(), current_depth + 1
                        )
                    except (AttributeError, Exception):
                        # Skip slots that can't be accessed
                        continue

        # Strategy 3: Fallback to inspect.getmembers with careful filtering
        else:
            try:
                members = inspect.getmembers(obj)
                for name, value in members:
                    # Only include data attributes, skip methods, functions, and built-ins
                    if (not name.startswith('_') and
                        not callable(value) and
                        not inspect.isclass(value) and
                        not inspect.ismodule(value)):
                        tree_node["children"][name] = generate_object_tree(
                            value, max_depth, visited.copy(), current_depth + 1
                        )
            except Exception as e:
                tree_node["_inspection_error"] = f"Could not inspect: {str(e)}"

        # Add metadata if no children found
        if not tree_node["children"]:
            tree_node["_note"] = "no_instance_attributes"

    except Exception as e:
        tree_node["_error"] = f"Error during introspection: {str(e)}"
    finally:
        visited.discard(obj_id)

    return tree_node


def _iter_container_items(obj):
    """Yield (label, item, is_last) for supported container types.

    Labels are human-friendly strings used when printing the tree.
    """
    # dict: yield key repr and value
    if isinstance(obj, dict):
        items = list(obj.items())
        for i, (k, v) in enumerate(items):
            label = repr(k) if isinstance(k, (str, int, float)) else f"<{type(k).__name__}>"
            yield label, v, i == len(items) - 1
        return

    # ordered sequences: list, tuple
    if isinstance(obj, (list, tuple)):
        for i, item in enumerate(obj):
            yield f"[{i}]", item, i == len(obj) - 1
        return

    # unordered sequences: set, frozenset
    if isinstance(obj, (set, frozenset)):
        items = list(obj)
        for i, item in enumerate(items):
            yield f"item_{i}", item, i == len(items) - 1
        return


def print_object_tree(obj, indent='', max_depth=8, _visited=None, _buffer=None, show_callables: bool = False):
    """
    Recursively prints a tree-like structure for a Python object.

    :param obj: The object to inspect.
    :param indent: The string used for indentation (managed by recursion).
    :param max_depth: The maximum depth to traverse.
    :param _visited: A set to store IDs of visited objects to prevent infinite loops.
    """
    if _buffer is None:
        _buffer = io.StringIO()

    if _visited is None:
        _visited = set()
        _buffer.write(f"Inspecting object: {obj.__class__.__name__}\n")

    obj_id = id(obj)
    if obj_id in _visited or max_depth <= 0:
        # Avoid recursion for already visited objects or if max depth is reached
        try:
            # Try to get a simple representation
            representation = repr(obj)
            if len(representation) > 110:
                representation = f"{obj.__class__.__name__} at {hex(obj_id)}"
        except Exception:
            representation = f"<{type(obj).__name__} object>"
        _buffer.write(f"{indent}└─> {representation} [Recursion limit reached]\n")
        return _buffer

    _visited.add(obj_id)
    # Special-case common container types so we recurse into their elements/values
    # Treat logging.Logger instances as simple
    try:
        import logging as _logging
        if isinstance(obj, _logging.Logger):
            _buffer.write(f"{indent}└─> {repr(obj)}\n")
            return _buffer
    except Exception:
        pass
    if isinstance(obj, (dict, list, tuple, set, frozenset)):
        # empty container
        try:
            if len(obj) == 0:
                _buffer.write(f"{indent}└─> {repr(obj)}\n")
                return _buffer
        except Exception:
            pass

        for name, member, is_last in _iter_container_items(obj):
            connector = '└─ ' if is_last else '├─ '
            _buffer.write(f"{indent}{connector}{name}: ")
            if max_depth <= 1:
                try:
                    _buffer.write(f"{repr(member)}\n")
                except Exception:
                    _buffer.write("<Unrepresentable>\n")
            else:
                _buffer.write(f"({member.__class__.__name__})\n")
                new_indent = indent + ('    ' if is_last else '│   ')
                print_object_tree(member, indent=new_indent, max_depth=max_depth - 1, _visited=_visited, _buffer=_buffer, show_callables=show_callables)
        return _buffer

    # Use inspect.getmembers to find all attributes
    try:
        members = inspect.getmembers(obj)
    except Exception:
        members = []

    # Filter out some built-in methods for cleaner output
    # Optionally hide callable members (functions, methods, bound methods)
    members_to_show = [
        m for m in members if not (
            m[0].startswith('__') and m[0].endswith('__')
        ) and not inspect.isbuiltin(m[1]) and (show_callables or not callable(m[1]))
    ]

    if not members_to_show:
        try:
            _buffer.write(f"{indent}└─> {repr(obj)}\n")
        except Exception:
            _buffer.write(f"{indent}└─> <Unrepresentable object>\n")
        return _buffer


    for i, (name, member) in enumerate(members_to_show):
        is_last = i == len(members_to_show) - 1
        connector = '└─ ' if is_last else '├─ '

        # Determine if the member is a "leaf" (simple type) or a "branch" (complex object)
        is_complex = hasattr(member, '__dict__') or isinstance(member, (list, dict, set, tuple))

        _buffer.write(f"{indent}{connector}{name}:  ")

        if not is_complex or max_depth <= 1:
            try:
                # Print a summary for simple types or at max depth
                representation = repr(member)
                if len(representation) > 110:
                   representation = f"{member.__class__.__name__} at {hex(id(member))}"
                _buffer.write(f'{representation}\n')
            except Exception:
                _buffer.write("<Unrepresentable>")
        else:
            _buffer.write(f"({member.__class__.__name__})\n")
            new_indent = indent + ('    ' if is_last else '│   ')
            # Recurse into the complex member
            print_object_tree(member, indent=new_indent, max_depth=max_depth - 1, _visited=_visited, _buffer=_buffer, show_callables=show_callables)

    return _buffer