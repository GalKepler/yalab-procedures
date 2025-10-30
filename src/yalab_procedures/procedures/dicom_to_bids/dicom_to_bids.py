# src/yalab_procedures/procedures/dicom_to_bids.py

import shlex
from pathlib import Path
from subprocess import CalledProcessError, run

from nipype.interfaces.base import (
    CommandLine,
    CommandLineInputSpec,
    Directory,
    File,
    isdefined,
    traits,
)

from yalab_procedures.procedures.base.procedure import (
    Procedure,
    ProcedureInputSpec,
    ProcedureOutputSpec,
)
from yalab_procedures.procedures.dicom_to_bids.templates.post_heudiconv import (
    create_pa_epi_workflow,
)

DEFAULT_HEURISTIC = Path(__file__).parent / "templates" / "heuristic.py"


class DicomToBidsInputSpec(ProcedureInputSpec, CommandLineInputSpec):
    """
    Input specification for the DicomToBidsProcedure
    """

    subject_id = traits.Str(argstr="-s %s", mandatory=True, desc="Subject ID")
    session_id = traits.Str(argstr="-ss %s", desc="Session ID")
    heuristic_file = File(
        DEFAULT_HEURISTIC,
        exists=True,
        mandatory=False,
        argstr="-f %s",
        desc="Heuristic file",
        usedefault=True,
    )
    input_directory = Directory(
        exists=True,
        mandatory=True,
        argstr="--files '%s'/*/*.dcm",
        desc="Input directory containing DICOM files",
    )
    output_directory = Directory(
        exists=True,
        mandatory=True,
        argstr="-o %s",
        desc="Directory to store BIDS output",
    )
    converter = traits.Enum(
        "dcm2niix",
        default="dcm2niix",
        usedefault=True,
        argstr="-c %s",
        desc="DICOM converter to use",
    )
    grouping = traits.Enum(
        "all",
        "studyUID",
        "accession_number",
        "custom",
        usedefault=True,
        argstr="-g %s",
        desc="Grouping strategy for DICOM files",
    )
    overwrite = traits.Bool(
        True, usedefault=True, argstr="--overwrite", desc="Overwrite existing files"
    )
    bids = traits.Enum(
        "notop",
        default="notop",
        usedefault=True,
        argstr="--bids %s",
        desc="Organize output in BIDS format",
    )
    infer_session_id = traits.Bool(
        True,
        usedefault=True,
        desc="Infer session ID from DICOM directory name",
    )


class DicomToBidsOutputSpec(ProcedureOutputSpec):
    """
    Output specification for the DicomToBidsProcedure
    """

    bids_directory = Directory(desc="Output BIDS directory")


class DicomToBidsProcedure(Procedure, CommandLine):
    """
    Convert DICOM files to BIDS format using `HeuDiConv. <https://heudiconv.readthedocs.io/en/latest/>`_

    Examples
    --------
    >>> from yalab_procedures.procedures.dicom_to_bids import DicomToBidsProcedure
    >>> dcm2bids = DicomToBidsProcedure()
    >>> dcm2bids.inputs.subject_id = '01'
    >>> dcm2bids.inputs.input_directory = '/path/to/dicom'
    >>> dcm2bids.inputs.output_directory = '/path/to/bids'
    >>> dcm2bids.inputs.session_id = '01'
    >>> dcm2bids.inputs.heuristic_file = '/path/to/heuristic.py'
    >>> dcm2bids.inputs.cmdline
    'heudiconv -s 01 -ss 01 -f /path/to/heuristic.py --files /path/to/dicom/*/*.dcm -o /path/to/bids -c dcm2niix --overwrite --bids'
    >>> res = dcmtobids.run() # doctest: +SKIP

    """

    _cmd = "heudiconv"
    input_spec = DicomToBidsInputSpec
    output_spec = DicomToBidsOutputSpec
    _version = "0.0.1"

    def __init__(self, **inputs):
        super(DicomToBidsProcedure, self).__init__(**inputs)

    def run_procedure(self, **kwargs):
        """
        Run the DicomToBidsProcedure

        Raises
        ------
        CalledProcessError
            If the command fails to run. The error message will be logged.
        """

        self.logger.info("Running DicomToBidsProcedure")
        self.infer_session_id()
        # self.standardize_input_directory()
        self.logger.debug(f"Input attributes: {kwargs}")

        # Run the heudiconv command
        command = self.build_commandline()
        result = run(
            command,
            shell=True,
            check=False,
            capture_output=True,
            text=True,
        )
        self.post_heudiconv_fieldmap_correction()
        self.logger.info(result.stdout)
        if (
            result.stderr
            and "TypeError: 'NoneType' object is not iterable" not in result.stderr
        ):
            self.logger.error(result.stderr)
            raise CalledProcessError(
                result.returncode, command, output=result.stdout, stderr=result.stderr
            )
        self.logger.info("Finished running DicomToBidsProcedure")

    def post_heudiconv_fieldmap_correction(self):
        """
        Post-process fieldmap correction if needed
        """
        wf = create_pa_epi_workflow(
            name="post_heudiconv_fieldmap_correction",
            bids_dir=str(self.inputs.output_directory),
            subject_id=self.inputs.subject_id,
            session_id=(
                self.inputs.session_id if isdefined(self.inputs.session_id) else ""
            ),
        )
        wf.run()

    def infer_session_id(self):
        """
        Infer the session ID from the input directory name.
        This is useful for DICOM directories provided by TAU's MRI facility.
        """
        if not isdefined(self.inputs.session_id) and self.inputs.infer_session_id:
            session_id = Path(self.inputs.input_directory).name.split("_")[-2:]
            session_id = "".join(session_id)
            self.inputs.session_id = session_id

    def standardize_input_directory(self):
        """
        Standardize the input directory path
        """
        self.inputs.input_directory = shlex.quote(str(self.inputs.input_directory))

    def build_commandline(self) -> str:
        """
        Build the command line arguments for the heudiconv command

        Returns
        -------
        str
            The command line arguments as a string
        """
        # Build the command line arguments
        cmd_args = self._parse_inputs()
        cmd = [self._cmd] + cmd_args
        self.logger.debug(f"Command line: {' '.join(cmd)}")
        # Run the command
        return " ".join(cmd)

    def _list_outputs(self):
        """
        List the outputs of the DicomToBidsProcedure

        Returns
        -------
        dict
            The outputs of the procedure
        """
        outputs = self._outputs().get()
        outputs["bids_directory"] = str(self.inputs.output_directory)
        return outputs
