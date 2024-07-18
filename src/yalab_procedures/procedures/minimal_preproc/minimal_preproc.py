import json

from nipype.interfaces.base import Directory, isdefined, traits
from niworkflows.utils.bids import collect_data

from yalab_procedures.procedures.base.procedure import (
    Procedure,
    ProcedureInputSpec,
    ProcedureOutputSpec,
)
from yalab_procedures.procedures.minimal_preproc.workflows.base import (
    init_minimal_preproc_wf,
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
            if isinstance(self.inputs.bids_filters, str):
                with open(self.inputs.bids_filters, "r") as f:
                    return json.load(f)
            elif isinstance(self.inputs.bids_filters, dict):
                return self.inputs.bids_filters
            else:
                raise ValueError(
                    "BIDS filters should be either a dictionary or a json file."
                )
        return None

    def _collect_subject_data(self) -> tuple:
        """
        Collect subject data.

        Returns
        -------
        tuple
            subject_data : dict
                Subject data.
            layout : BIDSLayout
                BIDS layout.
        """
        subject_data, layout = collect_data(
            self.inputs.input_directory,
            participant_label=self.inputs.subject_id,
            session_id=self.inputs.session_id,
            bids_filters=self._read_bids_filters(),
        )
        return subject_data, layout

    def init_workflow(self):
        """
        Initialize the workflow for the procedure.
        """
        subject_data, _ = self._collect_subject_data()
        wf = init_minimal_preproc_wf(
            subject_id=self.inputs.subject_id,
            subject_data=subject_data,
            name=self._gen_wf_name(),
        )
        wf.base_dir = (
            self.inputs.work_directory
            if isdefined(self.inputs.work_directory)
            else self.inputs.output_directory
        )
        wf.write_graph(graph2use="colored", format="png", simple_form=True)
        return wf

    def _gen_wf_name(self):
        """
        Generate a name for the workflow.

        Returns
        -------
        str
            Name for the workflow.
        """
        return f"minimal_preproc_{self.inputs.subject_id}_{self.inputs.session_id}"
