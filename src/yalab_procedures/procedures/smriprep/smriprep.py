import os
from pathlib import Path
from subprocess import CalledProcessError, run
from typing import Any, Dict

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
from yalab_procedures.procedures.smriprep.templates.outputs import SMRIPREP_OUTPUTS


class SmriprepInputSpec(ProcedureInputSpec, CommandLineInputSpec):
    """
    Input specification for the SmriprepProcedure
    """

    input_directory = Directory(
        exists=True,
        mandatory=True,
        argstr="-v %s:/data:ro",
        desc="Input directory containing preprocessed data",
    )
    output_directory = Directory(
        exists=False,
        mandatory=True,
        argstr="-v %s:/out",
        desc="Directory to store Smriprep's output",
    )
    analysis_level = traits.Str(
        mandatory=False,
        desc="Analysis level",
        default_value="participant",
        argstr="%s",
        position=0,
    )
    fs_license_file = File(
        exists=True,
        mandatory=False,
        argstr="-v %s:/fslicense.txt",
        desc="Path to FreeSurfer license file",
    )
    work_directory = Directory(
        exists=False,
        mandatory=True,
        argstr="-v %s:/work",
        desc="Path to work directory",
    )
    smriprep_version = traits.Str(
        mandatory=False,
        desc="Smriprep version",
        default_value="0.15.0",
        argstr="%s",
    )
    participant_label = traits.Str(
        argstr="--participant_label %s",
        desc="Participant label",
    )
    output_spaces = traits.List(
        traits.Str,
        argstr="--output-spaces %s",
        desc="Output spaces",
        sep=",",
    )
    longitudinal = traits.Bool(
        True,
        argstr="--longitudinal",
        desc="Longitudinal processing. May increase runtime.",
    )
    bids_filters = traits.File(
        exists=True,
        argstr="-v %s:/bids_filters.json",
        desc="BIDS filter file",
    )
    force = traits.Bool(
        False,
        usedefault=True,
        desc="Whether to force the procedure to run even if the output directory already exists.",
    )


class SmriprepOutputSpec(ProcedureOutputSpec):
    """
    Output specification for the SmriprepProcedure
    """

    # T1w-related files
    preprocessed_T1w = File(desc="Preprocessed T1w image")
    brain_mask = File(desc="Brain mask")
    MNI_preprocessed_T1w = File(desc="MNI preprocessed T1w image")
    MNI_brain_mask = File(desc="MNI brain mask")
    # Transformations
    mni_to_native_transform = File(desc="MNI to native transform")
    native_to_mni_transform = File(desc="Native to MNI transform")
    fsnative_to_native_transform = File(desc="Freesurfer native to native transform")
    native_to_fsnative_transform = File(desc="Native to freesurfer native transform")
    # Segmentation
    segmentation = File(desc="Segmentation")
    probseg_gm = File(desc="Probabilistic segmentation of gray matter")
    probseg_wm = File(desc="Probabilistic segmentation of white matter")
    probseg_csf = File(desc="Probabilistic segmentation of cerebrospinal fluid")
    # FreeSurfer
    fs_fsaverage = File(desc="fsaverage")
    fs_T1w = File(desc="T1w")
    fs_brainmask = File(desc="Brain mask")
    fs_brain = File(desc="Dilated brain mask")
    fs_wm = File(desc="White matter")
    fs_lh_pial = File(desc="Left hemisphere pial surface")
    fs_rh_pial = File(desc="Right hemisphere pial surface")


class SmriprepProcedure(Procedure, CommandLine):
    """
    Procedure for running Smriprep
    """

    _cmd_prefix = "docker run --rm"
    _cmd = "nipreps/smriprep"
    input_spec = SmriprepInputSpec
    output_spec = SmriprepOutputSpec
    _version = "0.0.1"

    def __init__(self, **inputs: Any):
        super().__init__(**inputs)

    def _parse_mounted_inputs(self):
        """
        Parse mounted inputs
        """
        return [inp for inp in self._parse_inputs() if inp.startswith("-v")]

    def _parse_cmd_inputs(self):
        """
        Parse command inputs
        """
        all_args = []
        metadata = dict(argstr=lambda t: t is not None)
        for name, spec in sorted(self.inputs.traits(**metadata).items()):
            argstr = spec.argstr
            if "-v" in argstr:
                continue
            value = getattr(self.inputs, name)
            if not isdefined(value):
                continue
            arg = self._format_arg(name, spec, value)
            all_args += [arg]
        return all_args

    def _get_default_value(self, key: str) -> Any:
        """
        Get the default value of an input
        """
        value = getattr(self.inputs, key)
        return value if isdefined(value) else self.inputs.traits().get(key).default

    def _add_mounts_to_command(
        self,
        mounts: dict = {
            "fs_license_file": "--fs-license-file",
            "work_directory": "--work-dir",
            "bids_filters": "--bids-filter-file",
        },
    ):
        """
        Add mounts to the command
        """
        args = []
        for key, argstr in mounts.items():
            value = getattr(self.inputs, key)
            if isdefined(value):
                mounted_destination = (
                    self.inputs.traits().get(key).argstr.split(":")[-1]
                )
                args += [f"{argstr} {mounted_destination}"]
        return args

    def run_procedure(self, **kwargs):
        """
        Run the SmriprepProcedure

        Raises
        ------
        CalledProcessError
            If the command fails to run. The error message will be logged.
        """

        self.logger.info("Running SmriprepProcedure")
        self.logger.debug(f"Input attributes: {kwargs}")

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

        # Locate the FreeSurfer license file
        self._locate_fs_license_file()
        # Prepare inputs
        temp_input_directory = self._prepare_inputs()
        # Run the smriprep command
        command = self.cmdline
        # Log the command
        self.logger.info(f"Running command: {command}")
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
        self.logger.info("Finished running SmriprepProcedure")
        # Clean up
        run(f"rm -rf {temp_input_directory}", shell=True, check=True)

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

    def _prepare_inputs(self):
        """
        Prepare inputs for the SmriprepProcedure
        """
        work_directory = Path(self.inputs.work_directory)
        input_directory = Path(self.inputs.input_directory)
        temp_bids = work_directory / self.log_file_path.stem / "bids"
        temp_bids.mkdir(parents=True, exist_ok=True)
        # rsync input directory to work directory
        run(
            f"rsync -azPL {input_directory}/sub-{self.inputs.participant_label} {temp_bids}",
            shell=True,
            check=True,
        )
        for fname in [
            "dataset_description.json",
            "participants.tsv",
            "participants.json",
            "README",
        ]:
            run(
                f"rsync -azPL {input_directory / fname} {temp_bids}",
                shell=True,
                check=True,
            )
        self.inputs.input_directory = temp_bids
        return temp_bids

    @property
    def cmdline(self):
        """`command` plus any arguments (args)
        validates arguments and generates command line"""
        self._check_mandatory_inputs()
        allargs = (
            [self._cmd_prefix]
            + self._parse_mounted_inputs()
            + [f"{self._cmd}:{self._get_default_value('smriprep_version')} /data /out"]
            + [self._get_default_value("analysis_level")]
            + self._parse_cmd_inputs()
            + self._add_mounts_to_command()
        )
        return " ".join(allargs)

    def _list_outputs(
        self, smriprep_outputs: dict = SMRIPREP_OUTPUTS
    ) -> Dict[str, str]:
        """
        List the outputs of the SmriprepProcedure
        """
        outputs_level = "session" if len(self.sessions) == 1 else "subject"
        output_directory = Path(self.inputs.output_directory)
        outputs = self._outputs().get()
        outputs["output_directory"] = str(output_directory)
        for (
            output_source,
            output_formats,
        ) in smriprep_outputs.items():
            search_destination = output_directory / output_source
            for output, desc in output_formats.items():
                key = output if output_source != "freesurfer" else f"fs_{output}"
                template = desc.get(outputs_level) if isinstance(desc, dict) else desc
                if outputs_level == "session":
                    value = template.format(
                        subject=self.inputs.participant_label,
                        session=self.sessions[0],
                    )
                else:
                    value = template.format(subject=self.inputs.participant_label)
                outputs[key] = str(search_destination / value)
        if hasattr(self, "log_file_path"):
            outputs["log_file"] = str(self.log_file_path)
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
