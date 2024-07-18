from nipype.interfaces.base import (
    BaseInterface,
    BaseInterfaceInputSpec,
    CommandLine,
    CommandLineInputSpec,
    TraitedSpec,
    traits,
)


class SmriprepInputSpec(BaseInterfaceInputSpec, CommandLineInputSpec):
    """
    Input specification for the SmriprepInterface
    """

    bids_directory = traits.Directory(
        exists=True,
        mandatory=True,
        argstr="-v %s",
        position=0,
        desc="BIDS-appropriate input directory.",
    )
    output_directory = traits.Directory(
        exists=False,
        mandatory=True,
        argstr="-v %s",
        position=1,
        desc="Output directory",
    )
    analysis_level = traits.Str(
        default_value="participant",
        mandatory=False,
        argstr="%s",
        position=2,
        desc="Analysis level",
        usedefault=True,
    )
    work_directory = traits.Directory(
        exists=False,
        mandatory=False,
        argstr="--work-dir %s",
        desc="Working directory",
    )
    freesurfer_license_file = traits.File(
        exists=True,
        mandatory=True,
        argstr="--fs-license-file %s",
        desc="Path to the FreeSurfer license file.",
    )
    freesurfer_subjects_directory = traits.Directory(
        exists=False,
        mandatory=False,
        argstr="--fs-subjects-dir %s",
        desc="Path to the FreeSurfer subjects directory.",
    )
    bids_filter_file = traits.File(
        exists=False,
        mandatory=False,
        argstr="--bids-filter-file %s",
        desc="Path to the BIDS filter file.",
    )
    n_cpus = traits.Int(
        mandatory=False,
        argstr="--n_cpus %d",
        desc="Number of CPUs to use.",
    )
    mem_gb = traits.Int(
        mandatory=False,
        argstr="--mem_gb %d",
        desc="Amount of memory to use in GB.",
    )
    omp_threads = traits.Int(
        mandatory=False,
        argstr="--omp-nthreads %d",
        desc="Number of threads to use.",
    )


class SmriprepOutputSpec(TraitedSpec):
    """
    Output specification for the SmriprepInterface
    """

    output_directory = traits.Directory(desc="Output directory")


class SmriprepInterface(BaseInterface, CommandLine):
    """
    Interface to run sMRIPrep
    """

    input_spec = SmriprepInputSpec
    output_spec = SmriprepOutputSpec
    _cmd = "docker run -ti --rm"

    def __init__(self, **inputs: dict):
        super().__init__(**inputs)

    def _format_arg(self, name, spec, value):
        return super()._format_arg(name, spec, value)

    def _run_interface(self, runtime):
        self.set_missing_inputs()
        return super()._run_interface(runtime)
