from backend.policies.behaviors.behavior import Behavior


def get_behavior_from_id(behavior_id) -> Behavior:
    """
    TODO This should look up the behavior in a database maybe?
    :param behavior_id: the requested behavior id
    :return: behavior object
    """
    behaviors = {
        0: Behavior(behavior_id)
    }

    return behaviors[behavior_id]
