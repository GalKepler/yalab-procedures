from nipype.interfaces.base import CommandLine, Directory, isdefined, traits

from yalab_procedures.procedures.base.procedure import (
    Procedure,
    ProcedureInputSpec,
    ProcedureOutputSpec,
)


class MinimalPreprocInputSpec(ProcedureInputSpec):
    input_directory = Directory(
        exists=True,
        mandatory=True,
        desc="BIDS-appropriate input directory.",
    )
    subject_id = traits.Str(mandatory=False, desc="Subject ID")
    session_id = traits.Str(mandatory=False, desc="Session ID")
    config_file = traits.File(
        exists=True,
        mandatory=False,
        desc="Configuration file. Will override configurations provided in the input specification.",
    )
    output_directory = Directory(
        exists=False,
        mandatory=True,
        desc="Output directory",
    )
    work_directory = Directory(
        exists=False,
        mandatory=True,
        desc="Working directory",
    )


class MinimalPreprocOutputSpec(ProcedureOutputSpec):
    output_directory = Directory(desc="Output directory")


class MinimalPreprocProcedure(Procedure, CommandLine):
    """
    Procedure for minimal preprocessing of diffusion MRI data.
    """

    input_spec = MinimalPreprocInputSpec
    output_spec = MinimalPreprocOutputSpec

    def __init__(self, **inputs):
        super(MinimalPreprocProcedure, self).__init__(**inputs)
