
__all__ = ['TAC_Sha3']

class TAC_Sha3:
    __internal_name__ = "SHA3"
    def __init__(self, op1, res):
        self.op1 = op1
        self.res = res

    def parse(self, raw_stmt):
        pass # todo 

    def __str__(self):
        return "{} SHA3 {}".format(self.res,self.op1)