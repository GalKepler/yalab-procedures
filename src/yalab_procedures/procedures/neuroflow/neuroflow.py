# src/yalab_procedures/procedures/dicom_to_bids.py

from pathlib import Path
from subprocess import CalledProcessError, run

from nipype.interfaces.base import (
    CommandLine,
    CommandLineInputSpec,
    Directory,
    File,
    traits,
)

from yalab_procedures.procedures.base.procedure import (
    Procedure,
    ProcedureInputSpec,
    ProcedureOutputSpec,
)

NEUROFLOW_STEPS = [
    "smriprep",
    "atlases",
    "dipy_tensors",
    "mrtrix3_tensors",
    "covariates",
    "connectome_recon",
]


class NeuroflowInputSpec(ProcedureInputSpec, CommandLineInputSpec):
    """
    Input specification for the NeuroflowProcedure
    """

    input_directory = Directory(
        exists=True,
        mandatory=True,
        argstr="%s",
        position=0,
        desc="Input directory containing preprocessed data",
    )
    output_directory = Directory(
        exists=False,
        mandatory=True,
        argstr="%s",
        position=1,
        desc="Directory to store Neuroflow's output",
    )
    google_credentials = File(
        exists=True,
        mandatory=True,
        argstr="%s",
        position=2,
        desc="Path to Google credentials JSON file",
    )
    patterns_file = File(
        exists=True,
        mandatory=False,
        argstr="--paterns_file %s",
        desc="Path to patterns file containing mapping of required inputs",
    )
    atlases = traits.List(
        traits.Str,
        mandatory=False,
        argstr="--atlases %s",
        desc="List of atlases to use",
        sep=",",
    )
    crop_to_gm = traits.Bool(
        mandatory=False,
        argstr="--crop_to_gm",
        desc="Crop the atlases to the gray matter",
        default_value=True,
        usedefault=True,
    )
    use_smriprep = traits.Bool(
        mandatory=False,
        argstr="--use_smriprep",
        desc="Use sMRIPrep for registration of atlases and preprocessing of structural data",
        default_value=True,
        usedefault=True,
    )
    fs_license_file = File(
        exists=True,
        mandatory=False,
        argstr="--fs_license_file %s",
        desc="Path to FreeSurfer license file",
    )
    max_bval = traits.Int(
        mandatory=False,
        argstr="--max_bval %d",
        desc="Maximum b-value to use for DTI",
        default_value=1000,
        usedefault=True,
    )
    ignore_steps = traits.List(
        traits.Str,
        mandatory=False,
        argstr="--ignore_steps %s",
        desc="List of steps to ignore. Available steps are: "
        + ", ".join(NEUROFLOW_STEPS),
        sep=",",
    )
    steps = traits.List(
        traits.Str,
        mandatory=False,
        argstr="--steps %s",
        desc="List of steps to run. Available steps are: " + ", ".join(NEUROFLOW_STEPS),
        sep=",",
    )
    force = traits.Bool(
        mandatory=False,
        argstr="--force",
        desc="Force re-running of all steps even if the output already exists",
        default_value=False,
        usedefault=True,
    )


class NeuroflowOutputSpec(ProcedureOutputSpec):
    """
    Output specification for the DicomToBidsProcedure
    """

    output_directory = Directory(desc="Output directory containing Neuroflow's output")


class NeuroflowProcedure(Procedure, CommandLine):
    """
    Apply further processing of dMRI and structural data using `neuroflow. <https://neuroflow.readthedocs.io/en/latest/>`_

    Examples
    --------
    >>> from yalab_procedures.procedures.neuroflow import NeuroflowProcedure
    >>> neuroflow = NeuroflowProcedure()
    >>> neuroflow = NeuroflowProcedure()
    >>> neuroflow.inputs.input_directory = "/path/to/preprocessed/data"
    >>> neuroflow.inputs.output_directory = "/path/to/neuroflow/output"
    >>> neuroflow.inputs.google_credentials = "/path/to/google_credentials.json"
    >>> neuroflow.inputs.atlases = ["fan2016","huang2022"]
    >>> neuroflow.inputs.cmdline
    'neuroflow process /path/to/preprocessed/data /path/to/neuroflow/output /path/to/google_credentials.json --atlases fan2016,huang2022 --crop_to_gm --max_bval 1000 --use_smriprep'
    >>> res = neuroflow.run() # doctest: +SKIP

    """

    _cmd = "neuroflow process"
    input_spec = NeuroflowInputSpec
    output_spec = NeuroflowOutputSpec
    _version = "0.0.1"

    def __init__(self, **inputs):
        super(NeuroflowProcedure, self).__init__(**inputs)

    def run_procedure(self, **kwargs):
        """
        Run the DicomToBidsProcedure

        Raises
        ------
        CalledProcessError
            If the command fails to run. The error message will be logged.
        """

        self.logger.info("Running NeuroflowProcedure")
        self.logger.debug(f"Input attributes: {kwargs}")

        # Run the heudiconv command
        command = self.cmdline
        result = run(
            command,
            shell=True,
            check=False,
            capture_output=True,
            text=True,
        )
        self.logger.info(result.stdout)
        if result.stderr:
            self.logger.error(result.stderr)
            raise CalledProcessError(
                result.returncode, command, output=result.stdout, stderr=result.stderr
            )
        self.logger.info("Finished running NeuroflowProcedure")

    def infer_subject_id(self):
        """
        Infer the subject ID from the input directory

        Returns
        -------
        str
            The subject ID
        """
        return Path(self.inputs.input_directory).parent.name

    def infer_session_id(self):
        """
        Infer the session ID from the input directory

        Returns
        -------
        str
            The session ID
        """
        return Path(self.inputs.input_directory).name

    def _list_outputs(self):
        """
        List the outputs of the DicomToBidsProcedure

        Returns
        -------
        dict
            The outputs of the procedure
        """
        outputs = self._outputs().get()
        outputs["output_directory"] = str(self.inputs.output_directory)
        return outputs
