import logging

from .agent_state import GraphState

logger = logging.getLogger(__name__)


def reset_state_on_start(state: GraphState) -> dict:
    """
    Resets fields in the state that are marked for reset on start.

    This function inspects the `json_schema_extra` of the `GraphState` model fields
    and identifies fields that are marked with `reset_on_start`. For each such field,
    it resets the field to its default value.

    Args:
        state: The current graph state.

    Returns:
        A dictionary containing the fields to be updated in the state.

    """
    updates = {}
    model_fields = GraphState.model_fields
    for field_name, field_info in model_fields.items():
        if field_info.json_schema_extra and field_info.json_schema_extra.get('reset_on_start'):
            default_value = field_info.get_default()
            logger.debug('Resetting %s to default value: %s', field_name, default_value)
            updates[field_name] = default_value
    return updates
