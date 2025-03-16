
from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel

class CamelModel(BaseModel):
    """
    See https://medium.com/@drewscatterday/convert-fastapi-snake-case-json-response-to-camel-case-d94c20e92b52
    and https://stackoverflow.com/questions/67995510/how-to-inflect-from-snake-case-to-camel-case-post-the-pydantic-schema-validation/77424889#77424889
    """
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        from_attributes=True,
    )

