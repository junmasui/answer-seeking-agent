
import pytest
from unittest.mock import MagicMock, patch
import uuid

from core_telemetry_instrumentation.tracing.custom_tracer import CustomMlflowLangchainTracer

@pytest.fixture
def mock_meter_provider():
    with patch('core_telemetry_instrumentation.tracing.custom_tracer.get_meter') as mock_get_meter:
        yield mock_get_meter

def test_custom_tracer_metrics(mock_meter_provider):
    # Setup mocks
    mock_meter = MagicMock()
    mock_meter_provider.return_value = mock_meter
    
    mock_counter = MagicMock()
    mock_histogram = MagicMock()
    
    mock_meter.create_counter.return_value = mock_counter
    mock_meter.create_histogram.return_value = mock_histogram

    # Instantiate tracer
    tracer = CustomMlflowLangchainTracer()
    
    # Verify metrics initialization
    assert mock_meter.create_counter.call_count >= 1
    
    # Simulate on_llm_start
    run_id = uuid.uuid4()
    serialized = {'model_name': 'gpt-4', '_type': 'openai'}
    metadata = {'session_id': 'test-session'}
    
    with patch('mlflow.langchain.langchain_tracer.MlflowLangchainTracer.on_llm_start'):
        tracer.on_llm_start(serialized, ['prompt'], run_id=run_id, metadata=metadata)
    
    # Verify request counter increment
    mock_counter.add.assert_called_with(
        1, attributes={'model': 'gpt-4', 'vendor': 'openai', 'session_id': 'test-session'}
    )
    
