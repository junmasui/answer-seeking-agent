import logging

import inspect
from typing import Any, Dict, Set, Optional
import pprint as pp


from opentelemetry._logs import get_logger_provider
from opentelemetry.metrics import get_meter_provider
from opentelemetry.trace import get_tracer_provider

logger = logging.getLogger(__name__)

def verify_distro():
    logger_provider = get_logger_provider()
    tree = generate_object_tree(logger_provider)
    logger.info('logger_provider\n%s', pp.pformat(tree, indent=2, width=110, compact=False))

    meter_provider = get_meter_provider()
    tree = generate_object_tree(meter_provider)
    logger.info('meter_provider\n%s', pp.pformat(tree, indent=2, width=110, compact=False))
 
    tracer_provider = get_tracer_provider()
    tree = generate_object_tree(tracer_provider)
    logger.info('tracer_provider\n%s', pp.pformat(tree, indent=2, width=110, compact=False))

    # Verify that the tracer is using a BatchSpanProcessor and that exporters
    # are configured to send to http://otel-collector. This uses guarded
    # introspection so it works across multiple OpenTelemetry SDK versions.
    try:
        span_processors = []

        # Common places where span processors may be stored depending on SDK
        if hasattr(tracer_provider, "_active_span_processor"):
            active = getattr(tracer_provider, "_active_span_processor")
            # MultiSpanProcessor exposes a list of processors on _span_processors
            if hasattr(active, "_span_processors"):
                span_processors = list(getattr(active, "_span_processors"))
            else:
                span_processors = [active]
        elif hasattr(tracer_provider, "_span_processors"):
            span_processors = list(getattr(tracer_provider, "_span_processors"))

        # Best-effort detection of BatchSpanProcessor
        from opentelemetry.sdk.trace.export import BatchSpanProcessor

        has_batch = any(
            isinstance(sp, BatchSpanProcessor)
            or sp.__class__.__name__ == "BatchSpanProcessor"
            for sp in span_processors
        )

        if has_batch:
            logger.info("Tracer is using BatchSpanProcessor")
        else:
            logger.warning(
                "Tracer is NOT using BatchSpanProcessor; processors: %s",
                [sp.__class__.__name__ for sp in span_processors],
            )

        # Inspect exporters attached to span processors and look for endpoint
        endpoints = []
        for sp in span_processors:
            exporter = getattr(sp, "_exporter", None) or getattr(sp, "exporter", None)
            # fallback attribute names
            if exporter is None:
                for attr in ("_span_exporter", "_exporters", "exporter"):
                    if hasattr(sp, attr):
                        exporter = getattr(sp, attr)
                        break
            if exporter is None:
                continue

            exporters = exporter if isinstance(exporter, (list, tuple)) else [exporter]
            for ex in exporters:
                endpoint = None
                # common exporter attributes for endpoint/url
                for a in ("endpoint", "_endpoint", "url", "_url", "connection_string"):
                    if hasattr(ex, a):
                        endpoint = getattr(ex, a)
                        break
                endpoints.append((ex.__class__.__name__, endpoint))

        logger.info("Discovered exporters and endpoints: %r", endpoints)

        if any(ep and "http://otel-collector" in str(ep) for _, ep in endpoints):
            logger.info("Exporters configured to send to http://otel-collector")
        else:
            logger.warning(
                "No exporter found configured to http://otel-collector; endpoints=%r",
                endpoints,
            )
    except Exception:
        logger.exception("failed verifying tracer exporters / processors")



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
        return {"type": type(obj).__name__, "value": "...", "_truncated": "max_depth_reached"}

    # Handle circular references
    obj_id = id(obj)
    if obj_id in visited:
        return {"type": type(obj).__name__, "value": "...", "_truncated": "circular_reference"}

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


