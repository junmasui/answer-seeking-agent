from enum import Enum
from typing import Any, Dict, Generic, Set, Type, TypeVar, Union

from pydantic import BaseModel, Field

# Generic type for constants
T = TypeVar('T', bound=Union[str, int, float])


class DynamicConstants(Generic[T]):
    """
    Base class for creating dynamic constant registries.

    Supports both static constants defined as class attributes and
    dynamic runtime additions. Works with any hashable type (str, int, float, etc.).
    """

    # Dynamic registry for runtime additions
    _dynamic_registry: Dict[Any, str] = {}  # value -> description

    def __new__(cls, value: T):
        """Create instance, validating it exists."""
        if not cls.is_valid(value):
            raise ValueError(f"'{value}' is not a registered {cls.__name__}")
        # Create instance of the appropriate base type
        base_type = cls._get_base_type()
        return base_type.__new__(cls, value)

    def __init_subclass__(cls, **kwargs):
        """Initialize subclass with its own registry."""
        super().__init_subclass__(**kwargs)
        # Each subclass gets its own registry
        cls._dynamic_registry = {}

    @classmethod
    def _get_base_type(cls) -> Type:
        """Get the base type for this constants class from MRO."""
        for base in cls.__mro__[1:]:  # Skip self
            if base in (str, int, float):
                return base
        return str  # Default fallback

    @classmethod
    def is_valid(cls, value: T) -> bool:
        """Check if value is a valid constant (static or dynamic)."""
        # Check static constants
        for attr in dir(cls):
            if not attr.startswith('_') and not callable(getattr(cls, attr)) and getattr(cls, attr) == value:
                return True
        # Check dynamic registry
        return value in cls._dynamic_registry

    @classmethod
    def by_name(cls, name: str) -> 'DynamicConstants[T]':
        """
        Look up a constant by its attribute name (like old Enum['NAME'] behavior).

        Args:
            name: The attribute name (e.g., 'GENERATE_ANSWER')

        Returns:
            Instance for the constant

        Raises:
            ValueError: If the name doesn't exist
        """
        # Check static constants by attribute name
        if hasattr(cls, name):
            attr_value = getattr(cls, name)
            if not name.startswith('_') and not callable(attr_value) and isinstance(attr_value, cls._get_base_type()):
                return cls(attr_value)

        raise ValueError(f"'{name}' is not a valid {cls.__name__} constant name")

    @classmethod
    def register(cls, value: T, description: str = None) -> 'DynamicConstants[T]':
        """
        Register a new constant value dynamically.

        Args:
            value: The constant value to register
            description: Optional description for documentation

        Returns:
            Instance for the new constant
        """
        if cls.is_valid(value):
            raise ValueError(f"Constant '{value}' already exists in {cls.__name__}")

        cls._dynamic_registry[value] = description or ''
        return cls(value)

    @classmethod
    def unregister(cls, value: T) -> bool:
        """
        Remove a dynamically registered constant.

        Args:
            value: The constant value to remove

        Returns:
            True if removed, False if not found or is static
        """
        if value in cls._dynamic_registry:
            del cls._dynamic_registry[value]
            return True
        return False

    @classmethod
    def list_all(cls) -> Dict[T, str]:
        """List all available constants with their descriptions."""
        result = {}

        # Add static constants
        for attr_name in dir(cls):
            if not attr_name.startswith('_') and not callable(getattr(cls, attr_name)):
                value = getattr(cls, attr_name)
                # Only include values of the correct type
                base_type = cls._get_base_type()
                if isinstance(value, base_type):
                    result[value] = f'Static: {attr_name}'

        # Add dynamic constants
        for value, desc in cls._dynamic_registry.items():
            result[value] = f'Dynamic: {desc or "No description"}'

        return result

    @classmethod
    def get_static_values(cls) -> Set[T]:
        """Get all static constant values."""
        values = set()
        base_type = cls._get_base_type()
        for attr_name in dir(cls):
            if not attr_name.startswith('_') and not callable(getattr(cls, attr_name)):
                value = getattr(cls, attr_name)
                if isinstance(value, base_type):
                    values.add(value)
        return values

    @classmethod
    def get_dynamic_values(cls) -> Set[T]:
        """Get all dynamically registered constant values."""
        return set(cls._dynamic_registry.keys())

    @classmethod
    def clear_dynamic(cls) -> None:
        """Clear all dynamically registered constants."""
        cls._dynamic_registry.clear()

    @property
    def value(self):
        """Return the value (for compatibility with Enum)."""
        base_type = self._get_base_type()
        return base_type(self)

    def __repr__(self):
        is_dynamic = self.value in self._dynamic_registry
        source = 'Dynamic' if is_dynamic else 'Static'
        return f'<{self.__class__.__name__}({source}): {self.value!r}>'


class AgentPrompt(DynamicConstants[str], str):
    """
    Enumeration of available agent prompt templates for different AI operations.

    Supports both static constants and dynamic runtime additions.
    """

    # Static constants for core prompts (maintainable)
    GENERATE_ANSWER = 'Generate Answer'
    REWRITE_QUERY = 'Rewrite Query'
    GRADE_RETRIEVED_DOCUMENTS = 'Grade Retrieved Documents'
    GRADE_ANSWER = 'Grade Answer'
    GRADE_HALLUCINATION = 'Grade Hallucination'


class GradeDocuments(BaseModel):
    """Binary score for relevance check on retrieved documents."""

    binary_score: str = Field(description='Documents are relevant to the question, "yes" or "no"')


class GradeHallucinations(BaseModel):
    """Binary score for hallucination present in generation answer."""

    binary_score: str = Field(description='Answer is grounded in the facts, "yes" or "no"')


class GradeAnswer(BaseModel):
    """Binary score to assess answer addresses question."""

    binary_score: str = Field(description='Answer addresses the question, "yes" or "no"')
