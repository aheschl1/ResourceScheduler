import os.path
from typing import Tuple, List, Union, Dict

from backend.fol_policies.policy import FolPolicyFactory
from backend.json_policies.difference_policies.policies import GreaterThanPolicy, GreaterThanEQPolicy, LesserThanPolicy, LesserThanEQPolicy
from backend.json_policies.equality_policies.policies import EqualityPolicy, MatchPolicy, RegularExpressionPolicy
from backend.json_policies.policy import Policy
from backend.json_policies.request_control_policies.policies import RequiredHeaderPolicy, ArgumentFormatPolicy
import json

from backend.requests.requests import Request

"""
A policy is an object that validates a request.
A policy is a collection of behaviors.

We can define policy P as:

P = {b1, b2, b3, b4, .... bn}
Where bi is some behavior that defines a type of validation.

A behavior may be one of these:
1. Match(key, [v1, v2, v3, ...., vn]) where vi is an allowable value for a key DONE
2. Lesser_Than(key1, val) is key1 < val DONE
3. Greater_Than(key1, val) is key1 > val DONE
4. Lesser_ThanEQ(key1, val) is key1 <= val DONE
5. Greater_ThanEQ(key1, val) is key1 >= val DONE
2. Lesser_ThanK(key1, key2) is key1 < key2 
3. Greater_ThanK(key1, key2) is key1 > key2 
4. Lesser_ThanEQK(key1, key2) is key1 <= key2 
5. Greater_ThanEQK(key1, key2) is key1 >= key2 
6. Equal(key1, key2, ... keyn) is key1 == key2 == ... == keyn DONE
7. Format(ke1, f) where f is a format type element of Formats DONE
8. and(b1, b2, ....) where all behaviors bi apply DONE
9. Or(b1, b2, ....) where at least one behavior bi applies DONE
10. Required_Headers(h1, h2, .... hn) where hn is a required header DONE

Formats:
1. iso8601
"""


class LogicalPolicy(Policy):
    def __init__(self, cascaded_policies: Union[Dict, List[Union[str, Policy, List, Dict]]]):
        super().__init__(False)
        policies = []
        if not isinstance(cascaded_policies, dict):
            for p in cascaded_policies:
                if isinstance(p, Policy):
                    policies.append(p)
                else:
                    policies.append(PolicyFactory.get_policy_from_argument(p))
        else:
            policies = PolicyFactory.get_policy_from_dict(cascaded_policies, return_policy_list=True)
        self.cascaded_policies = policies

    def validate(self, request: Request) -> Tuple[bool]:
        raise NotImplementedError("Server error. CascadePolicy is to be treated as abstract.")


class AndPolicy(LogicalPolicy):
    def validate(self, request: Request) -> Tuple[bool, str]:
        """
        Validated request against a list of cascaded json_policies
        :param request:
        :return:
        """
        result, reasons = True, []
        for policy in self.cascaded_policies:
            p_result, reason = policy.validate(request)
            reason = json.decoder.JSONDecoder().decode(reason)
            reasons.append({f"{str(policy)}": reason})
            if not p_result:
                result = False
        return result, json.dumps(reasons, indent=4)


class OrPolicy(LogicalPolicy):
    def validate(self, request: Request) -> Tuple[bool, str]:
        """
        Validated request against a list of json_policies.
        Only one policy must accept
        :param request:
        :return:
        """
        result, reasons = False, []
        for policy in self.cascaded_policies:
            p_result, reason = policy.validate(request)
            reason = json.decoder.JSONDecoder().decode(reason)
            reasons.append({f"{str(policy)}": reason})
            if p_result:
                result = True
                break

        return result, json.dumps(reasons, indent=4)


class PolicyFactory:
    @staticmethod
    def create_full_approval_policy() -> Policy:
        return Policy(full_approval=True)

    @staticmethod
    def get_cascade_policy_from_list(arg: List) -> Policy:
        return AndPolicy(arg)

    @staticmethod
    def get_policy_from_dict(arg: Dict, return_policy_list: bool = False) -> Union[LogicalPolicy | List[Policy]]:
        """
        :param arg:
        :param return_policy_list: If we should return the list of json_policies instead of the wrapped version.
        :return:
        """
        policy_lookup = {
            "required_headers": RequiredHeaderPolicy,
            "or": OrPolicy,
            "and": AndPolicy,
            "formatted_arguments": ArgumentFormatPolicy,
            "equality": EqualityPolicy,
            "greater_than": GreaterThanPolicy,
            "greater_than_eq": GreaterThanEQPolicy,
            "lesser_than": LesserThanPolicy,
            "lesser_than_eq": LesserThanEQPolicy,
            "match": MatchPolicy,
            "regex": RegularExpressionPolicy,
            "fol": FolPolicyFactory.get_policy_from_literal
        }

        policies = []
        for key, value in arg.items():
            policies.append(policy_lookup[key](value))
        return AndPolicy(policies) if not return_policy_list else policies

    @staticmethod
    def get_policy_from_argument(arg: Union[str, Dict, List], org_name=None) -> Policy:
        if isinstance(arg, str) and org_name is not None:
            """
            If entity name is not none, and we received a string, try a lookup in the policy database
            """
            from backend.database_endpoints.data_management import PolicyManagement
            lookup_policy = PolicyManagement.lookup_policy_from_org_name(org_name, arg)
            if lookup_policy is not None:
                return lookup_policy
        if isinstance(arg, str):
            return PolicyFactory.get_policy_from_name(arg)
        if isinstance(arg, list):
            return PolicyFactory.get_cascade_policy_from_list(arg)
        if isinstance(arg, dict):
            return PolicyFactory.get_policy_from_dict(arg)
        raise NotImplementedError(f"Policy is invalid: Could not recognize datatype/requested policy file.")

    @staticmethod
    def get_policy_from_name(name: str) -> Policy:
        from backend.json_policies.highlevel_policies.policies import TimeslotPolicy, TicketedPolicy
        mapping = {
            "FullApproval": PolicyFactory.create_full_approval_policy(),
            "BasicTimeslot": TimeslotPolicy(),
            "TicketedPolicy": TicketedPolicy()
        }
        if name not in mapping:
            raise NotImplementedError(f"Policy is invalid: {name} is not a pre-made policy.")

        return mapping[name]


if __name__ == "__main__":
    import json

    policy_test = {
        "formatted_arguments": {
            "data.date": "iso8601",
            "data.date2": "iso8601"
        },
        "equality": ["data.date", "data.date2"],
        "lesser_than_eq": {
            "data.date": "2024-01-12T12:30:16.001Z"
        },
        "or": [
            {"match": {
                "hello": ["worlds", "world"]
            }},
            {"match": {
                "hello": ["wor2ld", "world"]
            }}
        ]
    }
    policy2 = PolicyFactory.get_policy_from_argument(policy_test)
    request_sample = {
        "header": "hi",
        "request": "uofc.hi",
        "data": {
            "date": "2024-01-12T12:30:16.001Z",
            "date2": "2024-01-12T12:30:16.001Z"
        },
        "hello": "wor2ld"
    }
    encoded_data = json.dumps(request_sample, indent=4).encode('utf-8')
    request2 = Request(encoded_data)
    result2, reason2 = policy2(request2)
    print(reason2)
    print(result2)
