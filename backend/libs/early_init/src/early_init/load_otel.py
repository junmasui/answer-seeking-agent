from importlib.metadata import entry_points
import logging
# from opentelemetry.distro import BaseDistro
# from opentelemetry.instrumentation.distro import BaseConfigurator

logger = logging.getLogger(__name__)

def load_custom_distro_by_entry_point(distro_name: str):
    """Load custom distro using importlib.metadata entry points"""
    logger.info('loading %s', distro_name)

    try:
        # Get all opentelemetry_distro entry points
        distro_entry_points = entry_points(group='opentelemetry_distro')
        
        for entry_point in distro_entry_points:
            if entry_point.name == distro_name:
                distro_class = entry_point.load()
                distro_instance = distro_class()
                distro_instance.configure()
                logger.info('loaded %s', distro_name)
                return distro_instance
        
        logging.warning('Distro \'%s\' not found in entry points', distro_name)
        return None
        
    except Exception as e:
        logging.warning('Failed to load distro: %s', distro_name, exc_info=e)
        return None

def load_custom_configurator_by_entry_point(configurator_name: str, **config_kwargs):
    """Load custom configurator using importlib.metadata entry points"""
    logger.info('loading %s', configurator_name)

    try:
        # Get all opentelemetry_configurator entry points
        configurator_entry_points = entry_points(group='opentelemetry_configurator')
        
        for entry_point in configurator_entry_points:
            if entry_point.name == configurator_name:
                configurator_class = entry_point.load()
                configurator_instance = configurator_class()
                configurator_instance.configure(**config_kwargs)
                logger.info(f'loaded %s', configurator_name)
                return configurator_instance
                
        logger.warning('Configurator \'%s\' not found in entry points', configurator_name)
        return None
        
    except Exception as e:
        logging.warning('Failed to load configurator: %s', configurator_name, exc_info=e)
        return None

# # Usage
# if __name__ == "__main__":
#     # Load and configure custom distro
#     distro = load_custom_distro_by_entry_point("my_custom_distro")
    
#     # Load and configure custom configurator with options
#     configurator = load_custom_configurator_by_entry_point(
#         "my_custom_configurator",
#         service_name="my-app",
#         environment="staging",
#         endpoint="http://jaeger:14268/api/traces"
#     )
