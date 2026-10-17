import logging 
from qiskit.transpiler.preset_passmanagers import generate_preset_pass_manager

from app.config import get_settings
from app.errors import HardwareUnavailableError

logger = logging.getLogger(__name__)

_TERMINAL = {"DONE","ERROR","CANCELLED"}

class IBMRuntimeClient:
    _service = None

    @classmethod
    def service(cls):
        settings = get_settings()
        if not settings.ibm_hardware_enabled:
            raise HardwareUnavailableError("IBM hardware is not enabled.")
        if not settings.ibm_quantum_api_key:
            raise HardwareUnavailableError("IBM Quantum API key is not configured.")


        if cls._service is None:
            from qiskit_ibm_runtime import  QiskitRuntimeService

            cls._service = QiskitRuntimeService(
                channel="ibm_quantum_platform",
                token=settings.ibm_quantum_api_key,
                instance=settings.ibm_quantum_instance or None,
            )

        return cls._service

    @classmethod
    def select_backend(cls,required_qubits:int):
        service = cls.service()
        backends = service.backends(operational=True,simulator=False)
        candidates = [b for b in backends if b.num_qubits >= required_qubits]
        if not candidates:
            raise HardwareUnavailableError(f"No available IBM backend with at least {required_qubits} qubits.")
        return min(candidates,key=lambda backend: backend.status().pending_jobs)


    @classmethod
    def submit_job(cls,experiment_id:str,shots:int) -> tuple[str,str,str]:
        from qiskit_ibm_runtime import SamplerV2 as Sampler

        from app.quantum.circuits import build_circuit

        circuit = build_circuit(experiment_id)
        backend = cls.select_backend(circuit.num_qubits)
        pass_manager = generate_preset_pass_manager(backend=backend, optimization_level=1)
        isa_circuit = pass_manager.run(circuit)

        sampler = Sampler(mode=backend)
        job = sampler.run([isa_circuit], shots=shots)
        logger.info("Submitted IBM job", extra={"provider_job_id": job.job_id()})
        return job.job_id(), backend.name, isa_circuit.name

    @classmethod
    def get_status_and_counts(cls, provider_job_id: str) -> tuple[str, dict[str, int] | None, str | None]:
        service = cls.service()
        try:
            job = service.job(provider_job_id)
            raw_status = job.status()
            status = str(raw_status).upper()

            if status == "DONE":
                result = job.result()
                pub_result = result[0]
                register = next(iter(pub_result.data.__dict__.values()))
                counts = dict(register.get_counts())
                return "completed", counts, None

            if status in {"ERROR", "CANCELLED"}:
                return status.lower(), None, f"IBM job ended with status {status.lower()}."

            if status in {"QUEUED", "INITIALIZING", "VALIDATING"}:
                return "queued", None, None

            if status == "RUNNING":
                return "running", None, None

            return "unknown", None, None
        except Exception:
            logger.exception("IBM job lookup failed")
            return "unknown", None, None