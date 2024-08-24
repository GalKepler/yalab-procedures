import os
import os.path as op
from pathlib import Path
from typing import Any

import kepost
from kepost import config, data
from kepost.data.quality_assurance.reports import build_boilerplate, run_reports
from kepost.workflows.base import init_kepost_wf
from nipype.interfaces.base import Directory, File, isdefined, traits
from niworkflows.engine.workflows import LiterateWorkflow as Workflow

from yalab_procedures.procedures.base.procedure import (
    Procedure,
    ProcedureInputSpec,
    ProcedureOutputSpec,
)
from yalab_procedures.procedures.kepost_procedure.templates.inputs import INPUTS_MAPPING


class KePostInputSpec(ProcedureInputSpec):
    """
    Input specification for the KePrepProcedure
    """

    # Execution configuration
    input_directory = Directory(
        exists=True,
        mandatory=True,
        desc="Input directory containing preprocessed data (by KePrep)",
    )
    output_directory = Directory(
        exists=False,
        mandatory=True,
        desc="Path to store outputs of KePost.",
    )
    keprep_database_dir = Directory(
        exists=False,
        mandatory=False,
        desc="Directory containing SQLite database indices for the input KePrep dataset.",
    )
    reset_database = traits.Bool(
        True,
        usedefault=True,
        desc="Whether to reset the database",
    )
    fs_license_file = File(
        exists=True,
        mandatory=False,
        desc="Path to FreeSurfer license file",
    )
    fs_subjects_dir = Directory(
        exists=False,
        mandatory=False,
        desc="Path to FreeSurfer subjects directory",
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
    # Workflow configuration
    anat_only = traits.Bool(
        False,
        usedefault=True,
        desc="Whether to run anatomical processing only",
    )
    five_tissue_type_algorithm = traits.Enum(
        "hsvs",
        "fsl",
        usedefault=True,
        desc="Algorithm to use for five tissue-type segmentation",
    )
    gm_probseg_threshold = traits.Float(
        0.0001,
        usedefault=True,
        desc="Threshold for gray matter segmentation",
    )
    atlases = traits.List(
        traits.Str,
        usedefault=True,
        desc="List of atlases to use for registration",
    )
    tensor_max_bval = traits.Int(
        1000,
        usedefault=True,
        desc="Maximum b-value for tensor estimation",
    )
    dipy_reconstruction_method = traits.Enum(
        "NLLS",
        "RESTORE",
        usedefault=True,
        desc="Method to use for dipy reconstruction",
    )
    dipy_reconstruction_sigma = traits.Float(
        desc="Sigma for dipy reconstruction",
        mandatory=False,
    )
    parcellate_gm = traits.Bool(
        True,
        usedefault=True,
        desc="Whether to parcellate gray matter",
    )
    response_algorithm = traits.Enum(
        "dhollander",
        "manual",
        "msmt_5tt",
        "tax",
        "tournier",
        usedefault=True,
        desc="Algorithm to use for response estimation",
    )
    fod_algorithm = traits.Enum(
        "msmt_csd",
        "csd",
        usedefault=True,
        desc="Algorithm to use for FOD estimation",
    )
    n_raw_tracts = traits.Int(
        1000000,
        usedefault=True,
        desc="Number of streamlines to generate in the tractography.",
    )
    n_tracts = traits.Int(
        100000,
        usedefault=True,
        desc="Number of streamlines to keep after SIFT filtering.",
    )
    det_tracking_algorithm = traits.Enum(
        "SD_Stream",
        usedefault=True,
        desc="Algorithm to use for deterministic tracking",
    )
    prob_tracking_algorithm = traits.Enum(
        "iFOD2",
        usedefault=True,
        desc="Algorithm to use for probabilistic tracking",
    )
    tracking_max_angle = traits.Float(
        45,
        usedefault=True,
        desc="Maximum angle between steps in tractography.",
    )
    tracking_lenscale_min = traits.Float(
        30,
        usedefault=True,
        desc="Minimum length scale for tractography.",
    )
    tracking_lenscale_max = traits.Float(
        500,
        usedefault=True,
        desc="Maximum length scale for tractography.",
    )
    tracking_stepscale = traits.Float(
        0.2,
        usedefault=True,
        desc="Step scale for tractography.",
    )
    fs_scale_gm = traits.Bool(
        True,
        usedefault=True,
        desc="Heuristically downsize the fibre density estimates based on the presence of GM in the voxel",
    )
    debug_sift = traits.Bool(
        False,
        usedefault=True,
        desc="Whether to run SIFT in debug mode",
    )
    # Nipype configuration
    crashfile_format = traits.Enum(
        "txt",
        "txt.gz",
        "no",
        usedefault=True,
        desc="Crashfile format",
    )
    nprocs = traits.Int(
        os.cpu_count(),
        usedefault=True,
        desc="Number of processes (compute tasks) that can be run in parallel (multiprocessing only).",
    )
    omp_nthreads = traits.Int(
        1,
        usedefault=True,
        desc="Number of CPUs a single process can access for multithreaded execution.",
    )
    stop_on_first_crash = traits.Bool(
        False,
        usedefault=True,
        desc="Whether to stop on first crash",
    )
    write_graph = traits.Bool(
        False, usedefault=True, desc="Whether to write the workflow's graph"
    )
    force = traits.Bool(
        False,
        usedefault=True,
        desc="Whether to force the procedure to run even if the output directory already exists.",
    )


class KePostOutputSpec(ProcedureOutputSpec):
    """
    Output specification for the KePostProcedure
    """

    output_directory = Directory(desc="KePost output directory")


class KePostProcedure(Procedure):
    """
    Procedure for running KePost
    """

    input_spec = KePostInputSpec
    output_spec = KePostOutputSpec
    _version = kepost.__version__

    def __init__(self, **inputs: Any):
        super().__init__(**inputs)

    def _setup_config_toml(self):
        """
        Set up the configuration file
        """
        inputs_dict = self.inputs.get()
        configuration_dict = {}
        for key, value in inputs_dict.items():
            if key in INPUTS_MAPPING:
                target_key = INPUTS_MAPPING.get(key)
                if not isdefined(value):
                    default_value = self._get_default_value(key)
                    if isdefined(default_value):
                        configuration_dict[target_key] = default_value
                    else:
                        raise ValueError(f"Value for {key} not provided.")
                else:
                    configuration_dict[target_key] = value
            else:
                if isdefined(value):
                    configuration_dict[key] = value
        return configuration_dict

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

        self.logger.info("Running KePostProcedure")
        self.logger.debug(f"Input attributes: {kwargs}")

        # Locate the FreeSurfer license file
        self._locate_fs_license_file()
        # Prepare inputs
        configuration_dict = self._setup_config_toml()
        config.from_dict(configuration_dict)

        # Run the workflow
        workflow = init_kepost_wf()
        workflow.run()
        self._generate_reports(workflow=workflow, configuration_dict=configuration_dict)

    def _generate_reports(self, workflow: Workflow, configuration_dict: dict):
        # Generate reports
        build_boilerplate(config_file=configuration_dict, workflow=workflow)
        bootstrap_file = data.load("quality_assurance/templates/reports-spec.yml")
        run_uuid = config.execution.run_uuid
        for participant_label in self.inputs.participant_label:
            err = run_reports(
                config.execution.output_dir,
                participant_label,
                run_uuid,
                bootstrap_file=bootstrap_file,
                out_filename="report.html",
                reportlets_dir=config.execution.output_dir,
                errorname=f"report-{run_uuid}-{participant_label}.err",
                subject=participant_label,
            )
            if err:
                self.logger.warn(
                    f"Failed to generate report for subject {participant_label}"
                )

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

    def _locate_fs_license_file(self):
        """
        Locate the FreeSurfer license file
        """
        if not isdefined(self.inputs.fs_license_file):
            fs_home = os.getenv("FREESURFER_HOME")
            if fs_home is None:
                raise ValueError(
                    "FREESURFER_HOME environment variable is not set and fs_license_file is not provided."
                )
            fs_license_file = Path(fs_home) / "license.txt"
            if not fs_license_file.exists():
                raise ValueError(
                    f"FreeSurfer license file not found at {fs_license_file}"
                )
            self.inputs.fs_license_file = str(Path(fs_home) / "license.txt")

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


if __name__ == "__main__":
    task = KePostProcedure()
    task.inputs.input_directory = "/media/storage/yalab-dev/derivatives/keprep"
    task.inputs.output_directory = "/media/storage/yalab-dev/derivatives/kepost"
    task.inputs.atlases = ["fan2016"]
    task.inputs.participant_label = ["CLMC10"]
    task.inputs.work_directory = "/media/storage/yalab-dev/work"
    res = task.run()
