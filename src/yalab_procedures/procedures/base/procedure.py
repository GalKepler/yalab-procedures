import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

from nipype.interfaces.base import (
    BaseInterface,
    BaseInterfaceInputSpec,
    Directory,
    TraitedSpec,
    isdefined,
    traits,
)


class ProcedureInputSpec(BaseInterfaceInputSpec):
    input_directory = Directory(exists=True, mandatory=True, desc="Input directory")
    output_directory = Directory(mandatory=True, desc="Output directory")
    logging_directory = Directory(desc="Logging directory")
    logging_level = traits.Enum(
        "DEBUG",
        "INFO",
        "WARNING",
        "ERROR",
        "CRITICAL",
        desc="Logging level",
        usedefault=True,
        default="INFO",
    )


class ProcedureOutputSpec(TraitedSpec):
    output_directory = Directory(desc="Output directory")
    log_file = traits.File(desc="Log file")


class Procedure(BaseInterface):
    input_spec = ProcedureInputSpec
    output_spec = ProcedureOutputSpec

    def __init__(self, **inputs: Any):
        super().__init__(**inputs)
        self.logger = None
        self.log_file_path = None

        # Validate directories and set up logging
        if not isdefined(self.inputs.logging_directory):
            self.inputs.logging_directory = self.inputs.output_directory

        self.setup_logging()

        self.logger.info(
            f"Running procedure with input directory: {self.inputs.input_directory}"
        )

    def _run_interface(self, runtime) -> Any:
        """
        Executes the interface, setting up logging and calling the procedure.
        """

        # Run the custom procedure
        self.run_procedure(**self.inputs.__dict__)

        return runtime

    def _list_outputs(self) -> Dict[str, str]:
        """
        Lists the outputs of the procedure.
        """
        outputs = self._outputs().get()
        outputs["output_directory"] = str(self.inputs.output_directory)
        outputs["log_file"] = self.log_file_path
        return outputs

    def _gen_log_filename(self) -> str:
        """
        Generates a log filename based on the procedure name and the current timestamp.
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"{self.__class__.__name__}_{timestamp}.log"

    def setup_logging(self):
        """
        Sets up logging configuration.
        """
        # Reset logging configuration
        for handler in logging.root.handlers[:]:
            logging.root.removeHandler(handler)

        # Set up logging configuration
        logging_dir = Path(self.inputs.logging_directory)
        if not logging_dir.exists():
            logging_dir.mkdir(parents=True, exist_ok=True)

        log_file_path = logging_dir / self._gen_log_filename()
        self.log_file_path = log_file_path
        logging.basicConfig(
            filename=log_file_path,
            level=getattr(logging, self.inputs.logging_level),
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        )
        self.logger = logging.getLogger(self.__class__.__name__)

        self.logger.debug(f"Logging setup complete. Log file: {log_file_path}")

    def run_procedure(self, **kwargs):
        """
        This method should be implemented by subclasses to define the specific steps of the procedure.
        """
        raise NotImplementedError("Subclasses should implement this method")
