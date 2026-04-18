ACTION_TYPES = {}


def action_type(name):
    """Decorateur : enregistre une classe action sous un nom JSON (champ "type")."""
    def decorator(cls):
        ACTION_TYPES[name] = cls
        return cls
    return decorator