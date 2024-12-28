from sqlmodel import MetaData, SQLModel


class Base(SQLModel):
    # set schema. not required because isolating apps+environments via database
    # but may as well specify to avoid ambiguity
    metadata = MetaData(schema="fcm")


"""
# Trying out a different way to build these models, copied from a tutorial that seems to have a better grasp on this
# than I did when working on manman
# So, rather than having one model for everything, going to create multiple classes that work together
# unsure of benefits or drawbacks as of writing

# one benefit appears to be easier separation between what is required for api/function consumers
# any create action doesn't have (and usually cannot have) an ID, but it should always return one
# this is possible to communicate through different models with a shared hierarchy

# IMPLEMENTATION MODEL:
class MyClassBase:
    ...

class MyClass(MyClassBase, table=True):
    id: int = Field(default=None, nullable=False, primary_key=True)

class MyClassCreate(MyClassBase):
    pass
"""
