from datetime import datetime


from pydantic import BaseModel, field_validator, Field, AliasPath


def get_current_date():
    return datetime.now().strftime("%d.%m.%Y %H:%M:%S")


class LeadCreationData(BaseModel):
    comment: str = Field(validation_alias=AliasPath("call_result_comment"), default="")


class ContactCreationData(BaseModel):
    phone: str = Field(validation_alias=AliasPath("lead_phones"), default="")

    @field_validator("phone")
    def phone_validator(cls, value):
        remove_symbols = "+_-() "
        for symbol in remove_symbols:
            value = value.replace(symbol, "")
        if value[0] == 8:
            value[0] = 7
        return value


def flatten_data(y):
    out = {}

    def flatten(x, name=''):
        if type(x) is dict:
            for a in x:
                flatten(x[a], name + a + '_')
        elif type(x) is list:
            i = 0
            for a in x:
                flatten(a, name + str(i) + '_')
                i += 1
        else:
            out[name[:-1]] = x

    flatten(y)
    return out