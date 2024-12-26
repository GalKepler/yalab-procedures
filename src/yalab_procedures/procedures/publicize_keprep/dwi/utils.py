from nipype.interfaces.base import File
from nipype.interfaces.mrtrix3.utils import MRTransform, MRTransformInputSpec


class FullMRTransformInputSpec(MRTransformInputSpec):
    warp = File(
        exists=True,
        argstr="-warp %s",
        desc="warp file",
    )


class FullMRTransform(MRTransform):
    input_spec = FullMRTransformInputSpec
