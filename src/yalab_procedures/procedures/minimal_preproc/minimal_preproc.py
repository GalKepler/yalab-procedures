import json

from nipype.interfaces.base import Directory, isdefined, traits

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
        desc="Configuration file.",
    )
    overwrite_configurations = traits.Bool(
        True,
        usedefault=True,
        desc="Whether to overwrite existing configurations with the new ones provided by the config file.",
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
    # BIDS filters should either be a json file or a dictionary

    bids_filters = traits.Either(
        traits.Dict,
        traits.File(exists=True),
        desc="BIDS filters",
    )
    do_smriprep = traits.Bool(
        False,
        usedefault=True,
        desc="Whether to run sMRIPrep on the anatomical data.",
    )


class MinimalPreprocOutputSpec(ProcedureOutputSpec):
    output_directory = Directory(desc="Output directory")


class MinimalPreprocProcedure(Procedure):
    """
    Procedure for minimal preprocessing of diffusion MRI data.
    """

    input_spec = MinimalPreprocInputSpec
    output_spec = MinimalPreprocOutputSpec

    def __init__(self, **inputs):
        super(MinimalPreprocProcedure, self).__init__(**inputs)

    def _process_inputs(self):
        """
        Process inputs to the procedure.
        """
        if isdefined(self.inputs.config_file):
            self.load_inputs_from_json(
                json_file=self.inputs.config_file,
                overwrite=self.inputs.overwrite_configurations,
            )
        self._read_bids_filters()

    def _read_bids_filters(self):
        """
        Read BIDS filters.
        """
        if isdefined(self.inputs.bids_filters):
            with open(self.inputs.bids_filters, "r") as f:
                self.inputs.bids_filters = json.load(f)

    def _collect_subject_data(self):
        """
        Collect subject data.
        """
