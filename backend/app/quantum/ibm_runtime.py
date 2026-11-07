import json
import logging

from qiskit.transpiler.preset_passmanagers import generate_preset_pass_manager

from app.config import get_settings
from app.errors import HardwareUnavailableError

logger = logging.getLogger(__name__)


def circuit_metrics(circuit) -> dict:
    """Depth and two-qubit gate count of the device-ready (transpiled) circuit."""
    return {
        "transpiled_depth": int(circuit.depth()),
        "two_qubit_gate_count": sum(
            1
            for instruction in circuit.data
            if instruction.operation.num_qubits == 2 and instruction.operation.name != "barrier"
        ),
    }


class IBMRuntimeClient:
    _services: dict[str, object] = {}

    @classmethod
    def accounts(cls) -> list[dict[str, str]]:
        settings = get_settings()
        accounts = []
        if settings.ibm_quantum_accounts.strip():
            try:
                configured = json.loads(settings.ibm_quantum_accounts)
                if not isinstance(configured, list):
                    raise ValueError("IBM_QUANTUM_ACCOUNTS must be a JSON array")
                for index, account in enumerate(configured):
                    if not isinstance(account, dict) or not account.get("api_key"):
                        raise ValueError("Each IBM account requires an api_key")
                    accounts.append(
                        {
                            "name": str(account.get("name") or f"account-{index + 1}"),
                            "api_key": str(account["api_key"]),
                            "instance": str(account.get("instance") or ""),
                        }
                    )
                if len({item["name"] for item in accounts}) != len(accounts):
                    raise ValueError("IBM account names must be unique")
            except (TypeError, ValueError, json.JSONDecodeError) as exc:
                raise HardwareUnavailableError(
                    "IBM account pool configuration is invalid."
                ) from exc
        elif settings.ibm_quantum_api_key:
            accounts.append(
                {
                    "name": "default",
                    "api_key": settings.ibm_quantum_api_key,
                    "instance": settings.ibm_quantum_instance,
                }
            )
        if not accounts:
            raise HardwareUnavailableError("IBM Quantum API key is not configured.")
        return accounts

    @classmethod
    def configured_account_count(cls) -> int:
        try:
            return len(cls.accounts())
        except HardwareUnavailableError:
            return 0

    @classmethod
    def service(cls, account_name: str | None = None):
        accounts = cls.accounts()
        account = (
            next((item for item in accounts if item["name"] == account_name), None)
            if account_name
            else accounts[0]
        )
        if account is None:
            raise HardwareUnavailableError(
                "The IBM account used for this job is no longer configured."
            )
        if account["name"] not in cls._services:
            from qiskit_ibm_runtime import QiskitRuntimeService

            cls._services[account["name"]] = QiskitRuntimeService(
                channel="ibm_quantum_platform",
                token=account["api_key"],
                instance=account["instance"] or None,
            )
        return cls._services[account["name"]]

    @classmethod
    def select_backend(cls, required_qubits: int):
        candidates = []
        for account in cls.accounts():
            try:
                service = cls.service(account["name"])
                backends = service.backends(operational=True, simulator=False)
                for backend in backends:
                    if backend.num_qubits >= required_qubits:
                        pending_jobs = backend.status().pending_jobs or 0
                        candidates.append((pending_jobs, account["name"], backend))
            except Exception as exc:
                logger.warning("IBM account %s could not be queried", account["name"], exc_info=exc)
        if not candidates:
            raise HardwareUnavailableError(
                "No configured IBM account has an available backend with enough qubits."
            )
        _, account_name, backend = min(candidates, key=lambda item: item[0])
        return account_name, backend

    @classmethod
    def submit_job(
        cls, experiment_id: str, shots: int, job_tag: str
    ) -> tuple[str, str, str, str, dict]:
        from qiskit_ibm_runtime import SamplerV2 as Sampler

        from app.quantum.circuits import build_circuit

        try:
            circuit = build_circuit(experiment_id)
            account_name, backend = cls.select_backend(circuit.num_qubits)
            pass_manager = generate_preset_pass_manager(backend=backend, optimization_level=1)
            isa_circuit = pass_manager.run(circuit)
            sampler = Sampler(mode=backend, options={"environment": {"job_tags": [job_tag]}})
        except HardwareUnavailableError:
            raise
        except Exception as exc:
            raise HardwareUnavailableError(
                "Hardware could not be prepared for this experiment."
            ) from exc

        job = sampler.run([isa_circuit], shots=shots)
        logger.info("Submitted IBM job %s on backend %s", job.job_id(), backend.name)
        return (
            job.job_id(),
            backend.name,
            isa_circuit.name,
            account_name,
            circuit_metrics(isa_circuit),
        )

    @classmethod
    def find_submission(cls, job_tag: str) -> tuple[str, str, str] | None:
        for account in cls.accounts():
            try:
                jobs = cls.service(account["name"]).jobs(job_tags=[job_tag], limit=1)
                if jobs:
                    job = jobs[0]
                    return job.job_id(), job.backend().name, account["name"]
            except Exception:
                logger.exception(
                    "Unable to search IBM account %s for a tagged submission", account["name"]
                )
        return None

    @classmethod
    def get_status_and_counts(
        cls, provider_job_id: str, account_name: str | None = None
    ) -> tuple[str, dict[str, int] | None, str | None]:
        try:
            job = cls.service(account_name).job(provider_job_id)
            status = str(job.status()).upper()
            if status == "DONE":
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
