# OpenLLMetry Migration Implementation Plan

## Executive Summary

This document outlines the migration from Langfuse to OpenLLMetry (OpenTelemetry for LLM applications) targeting Prometheus and Jaeger as telemetry backends. The plan provides infrastructure simplification while maintaining observability capabilities.

## Current State Analysis

### Existing Langfuse Integration
- **Location**: `src/core/agent/agent.py`
- **Usage**: LangChain callback handler for LangGraph tracing
- **Features Used**: Session tracking, user tracking, sampling
- **Status**: Partially disabled (commented out)

### Dependencies
- `langfuse>=2.58.2` in pyproject.toml
- `prometheus-client>=0.21.1` (already present)
- `prometheus-fastapi-instrumentator>=7.0.2` (already present)

## Implementation Plan

### Phase 1: Infrastructure Setup (Week 1-2)

#### 1.1 Add OpenTelemetry Dependencies
```toml
# Add to pyproject.toml
"opentelemetry-api>=1.21.0",
"opentelemetry-sdk>=1.21.0", 
"opentelemetry-instrumentation-langchain>=0.1.0",
"opentelemetry-exporter-prometheus>=1.12.0",
"opentelemetry-exporter-jaeger>=1.21.0",
"opentelemetry-instrumentation-celery>=0.46b0",
"opentelemetry-instrumentation-fastapi>=0.46b0",
```

#### 1.2 Docker Compose Updates
- Add Jaeger service for distributed tracing
- Add Prometheus service for metrics (if not already present)
- Configure OTLP endpoints

#### 1.3 Configuration Updates
- Add OpenTelemetry configuration to `lib_config.py`
- Environment variables for telemetry backends
- Service name and resource attributes

### Phase 2: Core Telemetry Infrastructure (Week 2-3)

#### 2.1 Telemetry Initialization
- Create `src/core/telemetry/` module
- Initialize OpenTelemetry SDK
- Configure exporters (Prometheus + Jaeger)
- Resource detection and service naming

#### 2.2 Custom LLM Metrics
- Define LLM-specific metrics (token counts, latency, costs)
- Create semantic conventions for LLM operations
- Implement metric collection utilities

### Phase 3: Agent Instrumentation (Week 3-4)

#### 3.1 LangChain Callback Handler
- Implement custom OpenTelemetry callback handler
- Replace Langfuse CallbackHandler
- Maintain session and user tracking
- Add LLM-specific spans and metrics

#### 3.2 LangGraph Integration
- Instrument graph execution
- Track node transitions and timing
- Capture graph state and decisions
- Error tracking and retry logic

### Phase 4: Ingestion Pipeline Instrumentation (Week 4-5)

#### 4.1 Document Processing Metrics
- Track document ingestion rates
- Monitor processing times per document type
- S3 operation metrics
- Vector store operation metrics

#### 4.2 Celery Task Instrumentation
- Automatic Celery task tracing
- Queue depth and processing time metrics
- Error rates and retry patterns

### Phase 5: Testing and Validation (Week 5-6)

#### 5.1 Parallel Operation
- Run both Langfuse and OpenLLMetry in parallel
- Compare telemetry data for consistency
- Performance impact assessment

#### 5.2 Dashboard Creation
- Grafana dashboards for LLM metrics
- Jaeger trace analysis
- Alert rules for critical metrics

### Phase 6: Migration and Cleanup (Week 6-7)

#### 6.1 Production Migration
- Gradual rollout with feature flags
- Monitor system performance
- Rollback procedures

#### 6.2 Cleanup
- Remove Langfuse dependencies
- Clean up configuration
- Documentation updates

## Technical Architecture

### Telemetry Stack
```
Application Layer
├── LangChain/LangGraph (Auto-instrumentation)
├── FastAPI (Auto-instrumentation) 
├── Celery (Auto-instrumentation)
└── Custom LLM Metrics

OpenTelemetry SDK
├── Traces → Jaeger
├── Metrics → Prometheus
└── Logs → File/Console

Storage & Visualization
├── Jaeger (Distributed Tracing)
├── Prometheus (Metrics Storage)
└── Grafana (Visualization)
```

### Key Components

#### 1. Telemetry Initializer
```python
# src/core/telemetry/init.py
def initialize_telemetry():
    """Initialize OpenTelemetry with multiple exporters"""
    # Resource configuration
    # Tracer provider setup
    # Meter provider setup
    # Exporter configuration
```

#### 2. LLM Callback Handler
```python
# src/core/telemetry/langchain_handler.py
class OpenTelemetryCallbackHandler(BaseCallbackHandler):
    """OpenTelemetry-based replacement for Langfuse CallbackHandler"""
    # Session tracking
    # User tracking
    # LLM operation metrics
    # Error handling
```

#### 3. Custom Metrics
```python
# src/core/telemetry/metrics.py
class LLMMetrics:
    """LLM-specific metrics collection"""
    # Token usage metrics
    # Response time metrics
    # Quality metrics
    # Cost tracking
```

## Migration Benefits

### Infrastructure Simplification
- ✅ Eliminate ClickHouse dependency
- ✅ Use standard observability tools
- ✅ Reduce operational complexity

### Cost Optimization
- ✅ Open-source telemetry stack
- ✅ Lower infrastructure costs
- ✅ Flexible storage backends

### Standards Compliance
- ✅ OpenTelemetry standard compliance
- ✅ Vendor-neutral approach
- ✅ Future-proof architecture

## Risk Mitigation

### Data Loss Prevention
- Parallel operation during migration
- Comprehensive testing phase
- Rollback procedures

### Performance Impact
- Sampling strategies
- Async exporters
- Resource limits

### Feature Gaps
- Custom dashboards for missing features
- Enhanced logging for debugging
- Documentation of differences

## Success Metrics

### Technical Metrics
- 99.9% trace export success rate
- <50ms latency overhead
- Zero data loss during migration

### Operational Metrics
- 50% reduction in infrastructure costs
- Improved deployment simplicity
- Reduced maintenance overhead

## Timeline Summary

| Phase | Duration | Key Deliverables |
|-------|----------|------------------|
| Phase 1 | Week 1-2 | Infrastructure setup |
| Phase 2 | Week 2-3 | Core telemetry framework |
| Phase 3 | Week 3-4 | Agent instrumentation |
| Phase 4 | Week 4-5 | Ingestion instrumentation |
| Phase 5 | Week 5-6 | Testing and validation |
| Phase 6 | Week 6-7 | Migration and cleanup |

**Total Duration**: 6-7 weeks

## Next Steps

1. **Approval**: Get stakeholder approval for the migration plan
2. **Team Allocation**: Assign dedicated team members
3. **Environment Setup**: Prepare development environment
4. **Proof of Concept**: Begin with the PoC implementation
5. **Detailed Design**: Create detailed technical specifications

---

*This plan provides a structured approach to migrating from Langfuse to OpenLLMetry while ensuring minimal disruption and maximum observability value.*
