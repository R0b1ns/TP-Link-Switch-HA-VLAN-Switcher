import json
import re


def extract_js_object_field(html: str, object_name: str, field: str = None):
    """
    Extracts a field or the whole JS object from HTML containing a JS variable.

    :param html: The HTML content as string
    :param object_name: The JS object variable name (e.g., "info_ds")
    :param field: Optional: specific field to extract (e.g., "hardwareStr")
    :return: dict of the object or value of the field
    """
    # Finde das JS-Objekt
    match = re.search(rf"var {object_name} = (\{{.*?\}});", html, re.DOTALL)
    if not match:
        return None

    js_obj_str = match.group(1)

    # Konvertiere JS-Listen in JSON-Listen
    js_obj_str = re.sub(r'(\w+)?:\s*\[\s*"(.*?)"\s*\]', r'"\1": ["\2"]', js_obj_str)

    # Lade als Python dict
    obj = json.loads(js_obj_str)

    # Transform
    transformed_obj = {k: v[0] for k, v in obj.items()}

    if field:
        return transformed_obj.get(field)
    return transformed_obj