import collections

from app.model.contract import ContractCategory

"""
Holds a list of all the mappers that apply to a given contract category as well as a decorator to add them
for ex:
@_event_mapper(ERC20)
def my_fun():
  pass
will attach my_fun to the ERC20 mappers.
"""
__event_mappers = collections.defaultdict(list)


def _event_mapper(contract_category: ContractCategory):
    def inner(func):
        __event_mappers[contract_category].append(func)
        return func

    return inner
