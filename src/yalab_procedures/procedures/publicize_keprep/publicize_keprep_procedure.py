import os.path as op
from pathlib import Path
from typing import Any

from nipype.interfaces.base import Directory, isdefined, traits

from yalab_procedures.procedures.base.procedure import (
    Procedure,
    ProcedureInputSpec,
    ProcedureOutputSpec,
)


class PublicizeKePrepInputSpec(ProcedureInputSpec):
    """
    Input specification for the KePrepProcedure
    """

    # Execution configuration
    input_directory = Directory(
        exists=True,
        mandatory=True,
        desc="Input directory containing raw data in BIDS format",
    )
    output_directory = Directory(
        exists=False,
        mandatory=True,
        desc="Path to store outputs of KePrep.",
    )
    participant_label = traits.List(
        traits.Str,
        argstr="--participant_label %s",
        desc="Participant label",
        sep=",",
    )
    work_directory = Directory(
        exists=False,
        mandatory=True,
        argstr="-v %s:/work",
        desc="Path to work directory",
    )
    force = traits.Bool(
        False,
        usedefault=True,
        desc="Whether to force the procedure to run even if the output directory already exists.",
    )


class PublicizeKePrepOutputSpec(ProcedureOutputSpec):
    """
    Output specification for the KePrepProcedure
    """

    output_directory = Directory(desc="KePrep output directory")


class PublicizeKePrepProcedure(Procedure):
    """
    Procedure for running Smriprep
    """

    input_spec = PublicizeKePrepInputSpec
    output_spec = PublicizeKePrepOutputSpec
    _version = "0.1.0"

    def __init__(self, **inputs: Any):
        super().__init__(**inputs)

    def _get_default_value(self, key: str) -> Any:
        """
        Get the default value of an input
        """
        value = getattr(self.inputs, key)
        return value if isdefined(value) else self.inputs.traits().get(key).default

    def run_procedure(self, **kwargs):
        """
        Run the SmriprepProcedure

        Raises
        ------
        CalledProcessError
            If the command fails to run. The error message will be logged.
        """

        self.logger.info("Running KePrepProcedure")
        self.logger.debug(f"Input attributes: {kwargs}")

        # Locate the FreeSurfer license file
        self._locate_fs_license_file()

    # function to avoid rerunning if force is not set
    def _check_output_directory(self):
        """
        Check if the output directory already exists
        """
        if not self.inputs.force:
            self.logger.info(
                f"Attempting to locate outputs from previous run in {self.inputs.output_directory}"
            )
            result = self._list_outputs()
            if all(Path(value).exists() for value in result.values()):
                self.logger.info(
                    f"Outputs already exist in {self.inputs.output_directory}. If you want to run the procedure again, set force=True."
                )
                return

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs["output_directory"] = op.abspath(self.inputs.output_directory)
        return outputs

    @property
    def sessions(self):
        """
        Get the sessions
        """
        return [
            session.name.split("-")[-1]
            for session in Path(self.inputs.input_directory).glob("ses-*")
            if session.is_dir()
        ]
