from .base_pass import Pass
from .type_res_pass import TypeResolutionPass


# TODO: implement TypeInferencePass
# This pass checks for TypeVars and infers them from the context
class TypeInferencePass(Pass):
    def __init__(self, previous_pass: TypeResolutionPass):
        super().__init__(previous_pass=previous_pass)

    def run(self) -> None:
        # TODO: implement
        raise NotImplementedError("TypeInferencePass not implemented")
