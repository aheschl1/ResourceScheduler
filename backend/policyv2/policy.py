import json
import re
from abc import abstractmethod
from typing import Tuple, Any, Dict, List, Union

from backend.requests.requests import Request
from backend.utils.utils import hierarchical_dict_lookup, hierarchical_keys


class Constant:
    """
    Utility class to extract a constant value from a request
    """

    def __init__(self, literal: str, extracted_regulars: Dict[str, str]):
        self._literal = literal.strip()
        self._extracted_regulars = extracted_regulars

    def extract(self, request: Request) -> Any:
        """
        Extract the value from the request, or return the constant
        :param request:
        :return:
        """
        if self._literal[0] == "*":
            raise NotImplementedError("Key lookup does not yet exist (will be wrapped by existential)")
        if self._literal[0] == "$":
            return hierarchical_dict_lookup(request.raw_request, self._literal[1:])
        if self._literal[0] == "^":
            return self._extracted_regulars[self._literal[1:]]
        else:
            return self._literal

    def __str__(self):
        return self._literal


class Policy:
    """
    A policy is a set of sentences of FOL
    Given a request (a model of FOL) returns true iff |Request| is a superset of L(Policy) and Request |= Policy
    """

    @abstractmethod
    def validate(self, request: Request) -> bool: ...

    def __call__(self, request: Request) -> bool:
        return self.validate(request)


class AtomicPolicy(Policy):
    """
    Evaluates atomic policies
    """

    def __init__(self, policy_literal: str, extracted_regulars: Dict[str, str]):
        # TODO assert literal is atomic!
        self._policy_literal = policy_literal
        self._extracted_regulars = extracted_regulars
        self._operation, self._c1, self._c2 = self._parse()

    def _parse(self) -> Tuple[str, Constant, Constant]:
        """
        Parses the literal and generates 2 constant, and one operation.
        TODO validate that literal is valid
        :return:
        """
        current_read = ""
        operation, c1, c2 = None, None, None
        for char in self._policy_literal:
            if char not in ["<", ">", "=", "~"]:
                current_read += char
            else:
                operation = char
                c1 = Constant(current_read, extracted_regulars=self._extracted_regulars)
                current_read = ""
        c2 = Constant(current_read, extracted_regulars=self._extracted_regulars)
        return operation, c1, c2

    def validate(self, request: Request):
        """
        Validates an atomic request
        :param request:
        :return:
        """
        try:
            c1, c2 = str(self._c1.extract(request)), str(self._c2.extract(request))
        except KeyError:
            return False

        if self._operation == "<":
            return c1 < c2
        elif self._operation == ">":
            return c1 > c2
        elif self._operation == "=":
            return c1 == c2
        elif self._operation == "~":
            try:
                match = re.search(c2[1:-1], c1) is not None
            except re.error:
                match = False
            return match

    def __str__(self):
        return self._policy_literal


class AndPolicy(Policy):
    """
    Policy which asserts all policies are True
    """

    def __init__(self, *policies: Policy):
        self._policies = policies

    def validate(self, request: Request):
        result = True
        for atomic_policy in self._policies:
            result = result and atomic_policy(request)
        return result

    def __str__(self):
        result = ""
        for policy in self._policies:
            result += f"({str(policy)})&"
        return result[:-1]


class OrPolicy(Policy):
    """
    Policy which asserts at least one policy is True
    """

    def __init__(self, *policies: Policy):
        self._policies = policies

    def validate(self, request: Request):
        result = False
        for atomic_policy in self._policies:
            result = result or atomic_policy(request)
        return result

    def __str__(self):
        result = ""
        for policy in self._policies:
            result += f"({str(policy)})|"
        return result[:-1]


class NotPolicy(Policy):
    """
    Negate the result of evaluating child policy.
    TODO in the case of a missing key, this will convert False from a KeyError to True
    """

    def __init__(self, policy: Policy):
        self._policy = policy

    def validate(self, request: Request):
        return not self._policy(request)

    def __str__(self):
        return f"!({str(self._policy)})"


class QuantifierPolicy(Policy):
    def __init__(self, literal: str, variable: str, extracted_regulars: Dict, bases: Union[List | None] = None):
        assert len(variable) == 1, "Variable of one length is required"
        self._literal = literal
        self._variable = variable
        self._extracted_regulars = extracted_regulars
        self._bases = bases

    def _replace_variable(self, value: str) -> str:
        permitted_next_to_variable = ["(", ")", ">", "<", "^", "$", "=", "~"]
        i = 0
        replaced = ""
        while i < len(self._literal):
            if self._literal[i] == self._variable:
                # TODO this may have error capacity for index out of bounds
                if self._literal[i + 1] in permitted_next_to_variable and self._literal[i - 1] in permitted_next_to_variable:
                    # the variable is in a context where it can be replaced
                    replaced += value
                    i += 1
                    continue
            replaced += self._literal[i]
            i += 1
        return replaced

    def _get_keys_for_check(self, request: Request) -> List[str]:
        """
        Given a list of keys, returns all recursive keys to check in the request.
        If a key does not end in *, then we do not go recursively.

        Example, data.a stays as data.a. data.a.* gives us data.a, as well as all children!
        :param request:
        :return:
        """
        all_keys = hierarchical_keys(request.raw_request) if self._bases is None else []
        if self._bases is None:
            return all_keys
        for key in self._bases:
            # TODO chance for index out of bounds
            if key[-1] == "*" and key[-2] == ".":
                key = key[:-2]
                all_keys.extend(hierarchical_keys(hierarchical_dict_lookup(request.raw_request, key), parent_key=key))
            else:
                all_keys.append(key)
        return all_keys


    @abstractmethod
    def validate(self, request: Request):
        ...


class ExistentialPolicy(QuantifierPolicy):
    """
    If a literal appears as ExA the literal given will be A.
    We iterate through all KEYS at ALL DEPTHS if x = *v.
    We iterate through all VALUES at ALL DEPTHS if x = $v.

    If in A we encounter x, we replace with the key.
    If in A we encounter $x, we will then be replacing with the value at key in the request
    """

    def validate(self, request: Request):
        all_keys = self._get_keys_for_check(request)
        for key in all_keys:
            literal_attempt = self._replace_variable(key)
            policy = PolicyFactory.get_policy_from_literal(literal_attempt, **self._extracted_regulars)
            if policy(request):
                return True
        return False


class UniversalPolicy(QuantifierPolicy):
    """
    If a literal appears as AxA the literal given will be A.
    We iterate through all KEYS at ALL DEPTHS if x = *v.
    We iterate through all VALUES at ALL DEPTHS if x = $v.

    If in A we encounter x, we replace with the key.
    If in A we encounter $x, we will then be replacing with the value at key in the request
    """

    def validate(self, request: Request):
        all_keys = self._get_keys_for_check(request)
        result = True
        for key in all_keys:
            literal_attempt = self._replace_variable(key)
            policy = PolicyFactory.get_policy_from_literal(literal_attempt, **self._extracted_regulars)
            result = result and policy(request)
        return result


class PolicyFactory:

    @staticmethod
    def _get_matching_bracket_index(literal: str, start_idx: int):
        """
        Given the index of an opening bracket, finds the clossing bracket
        :param literal:
        :param start_idx:
        :return:
        """
        assert literal[start_idx] == "(", f"_get_matching_bracket_index misused with {literal}"
        level = 0
        i = start_idx
        while i < len(literal):
            char = literal[i]
            if char == "(":
                level += 1
            elif char == ")":
                level -= 1
                if level == 0:
                    return i
            i += 1
        return -1

    @staticmethod
    def isAtomic(literal: str):
        return not ("(" in literal or "[" in literal or "{" in literal)

    @staticmethod
    def _extract_regulars(literal: str, extracted_regulars: Dict):
        """
        Given a literal with regular expressions surrounded in "", replaced the regular expresison with a ^key
        Also returns the mapping
        :param literal:
        :param extracted_regulars: Current list of regulars extracted to add to
        :return:
        """
        keys = sorted(list(extracted_regulars.keys()))
        while literal.find('"') != -1:
            starting = literal.find('"')
            closing = literal.find('"', literal.find('"') + 1)
            key = "0" if len(keys) == 0 else keys[-1] + "0"
            keys.append(key)
            extracted_regulars[key] = literal[starting + 1:closing]
            literal = f"{literal[0:starting]}^{key}{literal[closing + 1:]}"
        return literal, extracted_regulars

    @staticmethod
    def get_policy_from_literal(literal: str, **extracted_regulars) -> Policy:
        """
        Recursively build a Policy object from a sentence literal string.
        Sentences must be surrounded by either {, ( or [.
        For example, A & B is invalid! [A]&[B] is invalid! [[A]&[B]] is valid.

        MUST BE IN PRENEX FORM

        A negation !, can sit directly before a sentence, and be evaluated

        Since we handle regex, we treat portions in " " as regular expressions, and regular expressions MUST
        be surrounded to work.
        :param literal:
        :return:
        """
        # Extract the regular expressions into a dictionary to keep safety!
        # This will simplify future steps
        # ($a~"+{a}")->($a~^0)
        literal, extracted_regulars = PolicyFactory._extract_regulars(literal, extracted_regulars)
        # clean the literal (remove spaces and replace brackets to ( and  ))
        literal = (literal.strip().replace(" ", "")
                   .replace("{", "(")
                   .replace("}", ")")
                   .replace("[", "(")
                   .replace("]", ")"))

        apply_negation = 0
        while literal[0] != "(":
            # we have the unary connective "not".
            # after the ! we expect to have a proper sentence
            # remember to apply a not, remove it, and move forward
            # If the first character is E, then there is an existential request.
            # Export the remaining literal with the variable to an existential policy
            bases = None
            if literal[0] in ["A", "E"]:
                quantifier_policy = ExistentialPolicy if literal[0] == "E" else UniversalPolicy
                if literal[2] == "@":
                    assert literal[3] == "(", "With @ you must specify a list of keys or key families"
                    # extract list version of bases
                    bases = eval(literal[3:literal.find(")", 2)+1].replace("(", "[").replace(")", "]"))
                variable = literal[1]
                assert variable != "(", "Variable needed on universal policy"
                if bases is None:
                    new_literal = literal[2:]
                else:
                    new_literal = literal[3 + len(str(bases).replace(" ", "")):]
                quantifier_policy = quantifier_policy(new_literal, variable, extracted_regulars, bases)
                return quantifier_policy if apply_negation % 2 == 0 else NotPolicy(quantifier_policy)

            apply_negation += 1
            literal = literal[1:]

        # we are expeccting that a well formatted sentence always starts with a bracket
        literal = literal[1:PolicyFactory._get_matching_bracket_index(literal, 0)]
        # we need to be careful not to consume regex!
        if PolicyFactory.isAtomic(literal):
            # this is a unit literal because there is no other sentence
            policy = AtomicPolicy(literal, extracted_regulars)
            return policy if apply_negation % 2 == 0 else NotPolicy(policy)
        # now, we have guaranteed that there is some BINARY CONNECTIVE
        # [A] & [B] for example
        # literal at 0 is an opening brace, the character after the matching closing is the binary connective
        # everything after is the second literal

        # when getting the first literal, we need to be careful. We allow ! to sit on a bracket without being surrounded
        # start_idx = 0 if literal[0] == "(" else 1
        first_literal_end = PolicyFactory._get_matching_bracket_index(literal, literal.find("("))
        # include ! if it is there
        first_literal = literal[0:first_literal_end + 1]
        connective = literal[first_literal_end + 1]
        second_literal = literal[first_literal_end + 2:]
        first_policy = PolicyFactory.get_policy_from_literal(first_literal, **extracted_regulars)
        second_policy = PolicyFactory.get_policy_from_literal(second_literal, **extracted_regulars)
        if connective == "&":
            policy = AndPolicy(first_policy, second_policy)
        elif connective == "|":
            policy = OrPolicy(first_policy, second_policy)
        else:
            raise ValueError("Invalid connective")
        return policy if not apply_negation else NotPolicy(policy)


if __name__ == "__main__":
    isoregex = r'^(-?(?:[1-9][0-9]*)?[0-9]{4})-(1[0-2]|0[1-9])-(3[01]|0[1-9]|[12][0-9])T(2[0-3]|[01][0-9]):([0-5][0-9]):([0-5][0-9])(\.[0-9]+)?(Z|[+-](?:2[0-3]|[01][0-9]):[0-5][0-9])?$'
    tests = {
        f"[(($a~\"{isoregex}\") & ($b~\"{isoregex}\")) & ($b>$a)]": True,
        f"[(($a~\"{isoregex}\") & ($b~\"{isoregex}\")) & ($b<$a)]": False,
        "($entity=a)": True,
        "!($entity=a)": False,
        f"[!($entity=a) | [(($a~\"{isoregex}\") & ($b~\"{isoregex}\")) & ($b>$a)]]": True,
        f"[!($entity=a) & [(($a~\"{isoregex}\") & ($b~\"{isoregex}\")) & ($b>$a)]]": False,
        f"[(($data.a~\"{isoregex}\") & ($data.b~\"{isoregex}\")) & ($data.b>$data.a)]": True,
        f"[(($data.a~\"{isoregex}\") & ($data.b~\"{isoregex}\")) & ($data.b<$data.a)]": False,
        f"[!($entity=a) | [(($data.a~\"{isoregex}\") & ($data.b~\"{isoregex}\")) & ($data.b>$data.a)]]": True,
        f"[!!!($entity=a) & [(($data.a~\"{isoregex}\") & ($data.b~\"{isoregex}\")) & ($data.b>$data.a)]]": False,
        f"[$c=d]": False,
        f"![$c=d]": True,
        "[$float>$int]": True,
        "[$float<$int]": False,
        "Ex($x=2.2)": True,
        "ExEt[($x=2.2)&($t=exact)]": True,
        "!ExEt[($x=2.2)&($t=exact)]": False,
        "Ex!Et[($x=2.2)&($t=exacto)]": True,
        "!Ex!Et[($x=2.2)&($t=exacto)]": False,
        "AxEt[($t>$x)|(t=x)]": True,
        "!AxEt[($t>$x)|(t=x)]": False,
        "Ax(x>-1)": True,
        "Ax($x>3)": False,
        f"Ax@['data']($x~\"{isoregex})\")": False,
        f"Ax@['data.*']($x~\"{isoregex})\")": True,
        f"Ax@['data.*', 'data']($x~\"{isoregex})\")": False,
        f"Ax@['data.*']Ey@['a', 'b']([[$x~\"{isoregex})\"]&[$y~\"{isoregex})\"]]&($y>$x))": True
    }

    # the value a must be iso, and the value b must be iso, and b must be greater than a
    request2 = {
        "entity": "a",
        "a": "2024-12-13T12:12:12.000Z",
        "b": "2024-12-13T12:12:12.002Z",
        "float": 2.2,
        "int": 2,
        "exeact": "exact",
        "data": {
            "a": "2024-12-13T12:12:12.000Z",
            "b": "2024-12-13T12:12:12.001Z"
        }
    }
    request2 = Request(json.dumps(request2).encode())
    for literal2, expected in tests.items():
        policy2 = PolicyFactory.get_policy_from_literal(literal2)
        result2 = policy2.validate(request2)
        print(result2 == expected)
