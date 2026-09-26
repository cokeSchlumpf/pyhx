import htpy as y

from pyhx.core.primitives.icon_name import IconName


def icon(icon_name: IconName) -> y.Node:
    return y.i(data_feather=icon_name)
