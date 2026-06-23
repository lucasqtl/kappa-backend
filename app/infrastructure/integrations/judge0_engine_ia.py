import time
from uuid import UUID

import httpx

from app.application.ports.engine_ia import ResultadoValidacao

_PYTHON3_LANGUAGE_ID = 71
_STATUS_IN_QUEUE = 1
_STATUS_PROCESSING = 2
_STATUS_ACCEPTED = 3
_STATUS_COMPILATION_ERROR = 6


class Judge0EngineIA:
    """Execução de código via API Judge0 (judge0.com ou instância self-hosted)."""

    def __init__(
        self,
        base_url: str,
        api_key: str = "",
        language_id: int = _PYTHON3_LANGUAGE_ID,
        max_polls: int = 15,
        poll_interval: float = 1.0,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._api_key = api_key
        self._language_id = language_id
        self._max_polls = max_polls
        self._poll_interval = poll_interval

    def validar_codigo(self, missao_id: UUID, conteudo_codigo: str) -> ResultadoValidacao:
        token = self._submit(conteudo_codigo)
        return self._aguardar_resultado(token)

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _submit(self, conteudo_codigo: str) -> str:
        with httpx.Client(timeout=15.0) as client:
            response = client.post(
                f"{self._base_url}/submissions",
                json={
                    "source_code": conteudo_codigo,
                    "language_id": self._language_id,
                },
                headers=self._headers(),
                params={"base64_encoded": "false", "wait": "false"},
            )
            response.raise_for_status()
            return response.json()["token"]

    def _aguardar_resultado(self, token: str) -> ResultadoValidacao:
        with httpx.Client(timeout=15.0) as client:
            for _ in range(self._max_polls):
                response = client.get(
                    f"{self._base_url}/submissions/{token}",
                    headers=self._headers(),
                    params={
                        "base64_encoded": "false",
                        "fields": "status,stdout,stderr,compile_output",
                    },
                )
                response.raise_for_status()
                data = response.json()
                status_id = data["status"]["id"]

                if status_id in (_STATUS_IN_QUEUE, _STATUS_PROCESSING):
                    time.sleep(self._poll_interval)
                    continue

                return self._mapear_resultado(data)

        return ResultadoValidacao(
            aprovado=False,
            falha_teste=True,
            mensagem="Tempo limite de validação excedido.",
        )

    def _mapear_resultado(self, data: dict) -> ResultadoValidacao:
        status_id = data["status"]["id"]
        status_desc = data["status"]["description"]

        if status_id == _STATUS_COMPILATION_ERROR:
            msg = (data.get("compile_output") or "").strip() or "Erro de compilação."
            return ResultadoValidacao(
                aprovado=False,
                falha_compilacao=True,
                mensagem=msg,
            )

        if status_id == _STATUS_ACCEPTED:
            return ResultadoValidacao(
                aprovado=True,
                mensagem="Todos os testes passaram.",
                testes_passados=1,
                testes_total=1,
            )

        # Wrong Answer, TLE, RTE (SIGSEGV, SIGFPE, NZEC, etc.)
        msg = (
            (data.get("stderr") or "").strip()
            or (data.get("compile_output") or "").strip()
            or f"Falha na execução: {status_desc}."
        )
        return ResultadoValidacao(
            aprovado=False,
            falha_teste=True,
            mensagem=msg,
            testes_passados=0,
            testes_total=1,
        )

    def _headers(self) -> dict[str, str]:
        headers: dict[str, str] = {"Content-Type": "application/json"}
        if self._api_key:
            headers["X-Auth-Token"] = self._api_key
        return headers
