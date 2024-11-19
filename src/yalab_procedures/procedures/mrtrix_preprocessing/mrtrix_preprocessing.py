from pathlib import Path

import git
from nipype import logging as nipype_logging
from nipype.interfaces.base import CommandLine, Directory, isdefined, traits

from yalab_procedures.procedures.base.procedure import (
    Procedure,
    ProcedureInputSpec,
    ProcedureOutputSpec,
)
from yalab_procedures.procedures.mrtrix_preprocessing.workflows.mrtrix_preprocessing_wf import (
    init_comis_cortical_wf,
    init_mrtrix_preprocessing_wf,
)

COMIS_CORTICAL_GITHUB = "https://github.com/RonnieKrup/ComisCorticalCode.git"


class MrtrixPreprocessingInputSpec(ProcedureInputSpec):
    """
    Input specification for the MrtrixPreprocessingProcedure
    """

    input_directory = Directory(
        exists=True,
        mandatory=True,
        argstr="-data_path %s",
        desc="BIDS-appropriate input directory.",
    )
    subject_id = traits.Str(mandatory=False, desc="Subject ID")
    session_id = traits.Str(mandatory=False, desc="Session ID")
    comis_cortical_exec = traits.Str(
        exists=True,
        mandatory=False,
        desc="Path to the Comis cortical executable.",
    )
    config_file = traits.File(
        exists=True,
        mandatory=False,
        desc="Configuration file",
    )
    output_directory = Directory(
        exists=False,
        mandatory=True,
        desc="Output directory",
    )
    final_output_directory = Directory(
        exists=False,
        mandatory=False,
        desc="Final output directory",
    )
    work_directory = Directory(
        exists=False,
        mandatory=True,
        desc="Working directory",
    )


class MrtrixPreprocessingOutputSpec(ProcedureOutputSpec):
    """
    Output specification for the MrtrixPreprocessingProcedure
    """

    output_directory = Directory(desc="Output directory")


class MrtrixPreprocessingProcedure(Procedure, CommandLine):
    """
    Procedure to preprocess DWI data using MRtrix3
    """

    comis_cortical_github = COMIS_CORTICAL_GITHUB
    comis_cortical_exec_default_destination = "{repo}/PreProcessing/run_for_sub.py"
    _cmd = "comis_cortical"
    input_spec = MrtrixPreprocessingInputSpec
    output_spec = MrtrixPreprocessingOutputSpec
    _version = "0.0.1"

    def __init__(self, **inputs: dict):
        super().__init__(**inputs)

    def set_missing_inputs(self):
        """
        Set missing inputs for the MRtrix preprocessing procedure
        """
        self.inputs.subject_id = (
            self.infer_subject_id()
            if not isdefined(self.inputs.subject_id)
            else self.inputs.subject_id
        )
        self.inputs.session_id = (
            self.infer_session_id()
            if not isdefined(self.inputs.session_id)
            else self.inputs.session_id
        )

    def run_procedure(self, **kwargs):
        """
        Run the MRtrix preprocessing procedure
        """
        self.logger.info("Starting MRtrix preprocessing procedure...")
        self.logger.info("Validating Comis cortical executable.")
        self.validate_comis_cortical_exec()
        self.logger.info("Inferring additional inputs.")
        self.set_missing_inputs()
        self.logger.info("Initiating workflow for preparing inputs.")
        wf = self.initiate_prepare_inputs_workflow()
        wf.run()
        self.logger.info("Running preprocessing workflow.")
        comis_cortical = init_comis_cortical_wf(wf)
        comis_cortical.run()

    def move_output_directory(self):
        """
        Move the output directory to the final output directory
        """
        if isdefined(self.inputs.final_output_directory):
            self.logger.info("Moving output directory to final output directory.")
            Path(self.inputs.output_directory).rename(
                self.inputs.final_output_directory
            )
            self.outputs.output_directory = self.inputs.final_output_directory
        else:
            self.outputs.output_directory = self.inputs.output_directory

    def initiate_prepare_inputs_workflow(self):
        """
        Initiate the MRtrix preprocessing workflow

        Returns
        -------
        wf : pe.Workflow
            The MRtrix preprocessing workflow
        """
        wf = init_mrtrix_preprocessing_wf(self._gen_wf_name())
        if isdefined(self.inputs.work_directory):
            wf.base_dir = self.inputs.work_directory
        wf.inputs.inputnode.input_directory = self.inputs.input_directory
        wf.inputs.inputnode.subject_id = self.inputs.subject_id
        wf.inputs.inputnode.session_id = self.inputs.session_id
        wf.inputs.inputnode.comis_cortical_exec = self.inputs.comis_cortical_exec
        wf.inputs.inputnode.config_file = self.inputs.config_file
        wf.inputs.inputnode.output_directory = self.inputs.output_directory
        return wf

    def validate_comis_cortical_exec(self):
        """
        Validate the Comis cortical executable
        """
        if not isdefined(self.inputs.comis_cortical_exec):
            self.logger.info("Comis cortical executable not provided.")
            self.inputs.comis_cortical_exec = self._download_comis_cortical_exec()

    def _download_comis_cortical_exec(self):
        """
        Download the Comis cortical executable
        """
        self.logger.info("Downloading Comis cortical executable.")
        comis_cortical_repo = self._clone_comis_cortical_repo()
        self.logger.info("Comis cortical executable downloaded.")
        comis_cortical_exec = self.comis_cortical_exec_default_destination.format(
            repo=comis_cortical_repo
        )
        if not Path(comis_cortical_exec).exists():
            raise FileNotFoundError(
                f"Comis cortical executable not found at {comis_cortical_exec}"
            )
        else:
            self.logger.info(
                f"Comis cortical executable found at {comis_cortical_exec}"
            )
        return comis_cortical_exec

    def _clone_comis_cortical_repo(self):
        """
        Clone the Comis cortical repository
        """
        comis_cortical_repo = Path(self.inputs.work_directory) / "ComisCorticalCode"
        nipype_logging.getLogger("nipype.workflow").info(
            f"Cloning Comis cortical repository to {comis_cortical_repo}"
        )
        comis_cortical_repo = comis_cortical_repo.resolve()
        if not comis_cortical_repo.exists():
            git.Git(comis_cortical_repo.parent).clone(self.comis_cortical_github)
            self.logger.info("Comis cortical repository cloned.")

        return comis_cortical_repo

    def _gen_wf_name(self):
        return f"mrtrix_preprocessing_sub-{self.inputs.subject_id}_ses-{self.inputs.session_id}"

    def infer_session_id(self):
        return Path(self.inputs.input_directory).parts[-1].split("-")[-1]

    def infer_subject_id(self):
        return Path(self.inputs.input_directory).parts[-2].split("-")[-1]
