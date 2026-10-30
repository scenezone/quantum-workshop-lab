import logging

from qiskit.transpiler.preset_passmanagers import generate_preset_pass_manager

from app.config import get_settings
from app.errors import HardwareUnavailableError

logger = logging.getLogger(__name__)


class IBMRuntimeClient:
    _service = None

    @classmethod
    def service(cls):
        settings = get_settings()
        # Disabling new submissions must not prevent existing jobs finishing.
        if not settings.ibm_quantum_api_key:
            raise HardwareUnavailableError("IBM Quantum API key is not configured.")
        if cls._service is None:
            from qiskit_ibm_runtime import QiskitRuntimeService

            cls._service = QiskitRuntimeService(
                channel="ibm_quantum_platform",
                token=settings.ibm_quantum_api_key,
                instance=settings.ibm_quantum_instance or None,
            )
        return cls._service

    @classmethod
    def select_backend(cls, required_qubits: int):
        backends = cls.service().backends(operational=True, simulator=False)
        candidates = [backend for backend in backends if backend.num_qubits >= required_qubits]
        if not candidates:
            raise HardwareUnavailableError(
                f"No available IBM backend with at least {required_qubits} qubits."
            )
        return min(candidates, key=lambda backend: backend.status().pending_jobs)

    @classmethod
    def submit_job(cls, experiment_id: str, shots: int, job_tag: str) -> tuple[str, str, str]:
        from qiskit_ibm_runtime import SamplerV2 as Sampler

        from app.quantum.circuits import build_circuit

        try:
            circuit = build_circuit(experiment_id)
            backend = cls.select_backend(circuit.num_qubits)
            pass_manager = generate_preset_pass_manager(backend=backend, optimization_level=1)
            isa_circuit = pass_manager.run(circuit)
            sampler = Sampler(mode=backend, options={"environment": {"job_tags": [job_tag]}})
        except Exception as exc:
            # No sampler submission has happened, so the reservation can be released.
            raise HardwareUnavailableError(
                "Hardware could not be prepared for this experiment."
            ) from exc

        job = sampler.run([isa_circuit], shots=shots)
        logger.info("Submitted IBM job %s", job.job_id())
        return job.job_id(), backend.name, isa_circuit.name

    @classmethod
    def find_submission(cls, job_tag: str) -> tuple[str, str] | None:
        jobs = cls.service().jobs(job_tags=[job_tag], limit=1)
        if not jobs:
            return None
        job = jobs[0]
        return job.job_id(), job.backend().name

    @classmethod
    def get_status_and_counts(
        cls, provider_job_id: str
    ) -> tuple[str, dict[str, int] | None, str | None]:
        try:
            job = cls.service().job(provider_job_id)
            status = str(job.status()).upper()
            if status == "DONE":
                # All approved circuits use the single classical register c.
                counts = dict(job.result()[0].data.c.get_counts())
                return "completed", counts, None
            if status in {"ERROR", "CANCELLED"}:
                mapped = "failed" if status == "ERROR" else "cancelled"
                return mapped, None, f"IBM job ended with status {mapped}."
            if status in {"QUEUED", "INITIALIZING", "VALIDATING"}:
                return "queued", None, None
            if status == "RUNNING":
                return "running", None, None
            return "unknown", None, "Waiting for an updated hardware job status."
        except Exception:
            logger.exception("IBM job lookup failed")
            return "unknown", None, "Hardware status is temporarily unavailable; checking again."
