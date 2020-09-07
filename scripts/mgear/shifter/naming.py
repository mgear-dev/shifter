import string
import re
import pymel.core as pm

# default fields/tokens
NAMING_RULE_TOKENS = ["component",
                      "side",
                      "index",
                      "description",
                      "extension"]
DEFAULT_NAMING_RULE = r"{component}_{side}{index}_{description}_{extension}"
DEFAULT_SIDE_L_NAME = "L"
DEFAULT_SIDE_R_NAME = "R"
DEFAULT_SIDE_C_NAME = "C"
DEFAULT_CTL_EXT_NAME = "ctl"
DEFAULT_JOINT_EXT_NAME = "jnt"


def normalize_name_rule(text):
    """Normalize naming rule templates removing
    invalid characters

    :param text string: A text to normalize.
    :return text: Normalized text

    """
    text = str(text)

    if re.match("^[0-9]", text):
        text = "_" + text

    return re.sub("[^A-Za-z0-9_{}]", "", str(text))


def name_rule_validator(rule, valid_tokens, log=True):
    invalid_tokens = []
    for token in string.Formatter().parse(rule):

        if token[1] and token[1] in valid_tokens:
            continue
        # compare to None to avoid errors with empty token
        elif token[1] is None and token[0]:
            continue
        else:
            invalid_tokens.append(token[1])

    if invalid_tokens:
        if log:
            pm.displayWarning(
                "{} not valid token".format(invalid_tokens))
            pm.displayInfo("Valid tokens are: {}".format(NAMING_RULE_TOKENS))
        return
    else:
        return True


def name_solve(rule, values, validate=True):
    included_val = dict()
    if validate and not name_rule_validator(rule, NAMING_RULE_TOKENS):
        return
    for token in string.Formatter().parse(rule):
        if token[1]:
            included_val[token[1]] = values[token[1]]
        elif token[0]:
            continue
        else:
            return

    return rule.format(**included_val)
