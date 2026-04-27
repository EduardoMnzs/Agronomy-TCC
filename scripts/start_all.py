import subprocess
import sys
import time
import os
import platform
import signal


class ServiceManager:
    def __init__(self):
        self.procs = []
        self.is_windows = platform.system() == "Windows"
        script_dir = os.path.dirname(os.path.abspath(__file__))
        self.backend = os.path.normpath(os.path.join(script_dir, "..", "backend"))
        self.venv_bin = os.path.join(self.backend, "venv", "Scripts" if self.is_windows else "bin")
        self.python = os.path.join(self.venv_bin, "python")
        self.celery_bin = os.path.join(self.venv_bin, "celery")

        print(f"[ServiceManager] Backend: {self.backend}")
        print(f"[ServiceManager] Venv bin: {self.venv_bin}")

    def free_ports(self, ports):
        print("[ServiceManager] Verificando e limpando portas presas...")
        for port in ports:
            if self.is_windows:
                try:
                    output = subprocess.check_output(
                        "netstat -ano", shell=True, text=True
                    )
                    seen_pids = set()
                    for line in output.splitlines():
                        if f":{port}" not in line:
                            continue
                        parts = line.split()
                        if len(parts) < 5:
                            continue
                        local_address = parts[1]
                        state = parts[3]
                        pid = parts[4]
                        if (local_address.endswith(f":{port}") and
                                state in ("LISTENING", "ESTABLISHED", "CLOSE_WAIT") and
                                pid != "0" and pid not in seen_pids):
                            seen_pids.add(pid)
                            print(
                                f"[ServiceManager] Porta {port} ocupada (PID {pid}, {state}). Forcando liberacao..."
                            )
                            self.kill_process_tree(pid)
                            time.sleep(1)
                except Exception:
                    pass
            else:
                try:
                    output = subprocess.check_output(
                        f"lsof -t -i:{port}", shell=True, text=True
                    )
                    for pid in output.splitlines():
                        if pid.strip():
                            print(
                                f"[ServiceManager] Porta {port} ocupada (PID {pid}). Forcando liberacao..."
                            )
                            self.kill_process_tree(pid.strip())
                            time.sleep(1)
                except Exception:
                    pass

    def _popen(self, name, cmd):
        flags = subprocess.CREATE_NEW_PROCESS_GROUP if self.is_windows else 0
        p = subprocess.Popen(
            cmd,
            cwd=self.backend,
            creationflags=flags,
        )
        self.procs.append((name, p))
        print(f" -> '{name}' iniciado com PID {p.pid}")
        return p

    def start_background_services(self):
        print("[ServiceManager] Iniciando servicos em background...")
        self._popen("celery", [
            self.celery_bin, "-A", "workers.celery_app",
            "worker", "--loglevel=info", "-Q", "ingestion", "--pool=solo"
        ])
        time.sleep(2)
        self._popen("celery-beat", [
            self.celery_bin, "-A", "workers.celery_app",
            "beat", "--loglevel=info"
        ])
        time.sleep(2)
        self._popen("flower", [
            self.python, "workers/run_flower.py"
        ])
        time.sleep(3)

        print("[ServiceManager] Todos os servicos de background foram iniciados.")
        print("[ServiceManager] Flower disponivel em: http://localhost:5555")

    def run_main_server(self):
        uvicorn_bin = os.path.join(self.venv_bin, "uvicorn")
        print(
            "\n[ServiceManager] Iniciando servidor principal (FastAPI) no terminal ativo...\n"
        )
        try:
            subprocess.run(
                [uvicorn_bin, "main:app", "--reload", "--host", "0.0.0.0", "--port", "8000"],
                cwd=self.backend,
            )
        except KeyboardInterrupt:
            print("\n[Ctrl+C] Interrupcao recebida pelo usuario.")

    def kill_process_tree(self, pid):
        if self.is_windows:
            subprocess.run(
                ["taskkill", "/F", "/T", "/PID", str(pid)],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        else:
            try:
                os.killpg(os.getpgid(int(pid)), signal.SIGKILL)
            except Exception:
                pass

    def stop_all(self):
        print(
            "\n[ServiceManager] Finalizando todos os servicos dependentes e limpando processos orfaos..."
        )
        for name, p in self.procs:
            print(f" -> Encerrando arvore de processos do '{name}' (PID {p.pid})...")
            try:
                self.kill_process_tree(p.pid)
            except Exception as e:
                print(f" -> Erro ao finalizar '{name}': {e}")

        for name, p in self.procs:
            try:
                p.wait(timeout=5)
            except Exception:
                pass

        print(
            "[ServiceManager] Todos os servicos foram limpos e finalizados com sucesso."
        )


def main():
    manager = ServiceManager()

    manager.free_ports([8000, 5555])

    manager.start_background_services()
    manager.run_main_server()
    manager.stop_all()


if __name__ == "__main__":
    main()
