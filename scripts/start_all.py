import subprocess
import sys
import time
import os
import platform


class ServiceManager:
    def __init__(self):
        self.procs = []
        self.targets = ["celery", "celery-beat", "flower"]
        self.is_windows = platform.system() == "Windows"

    def free_ports(self, ports):
        print("[ServiceManager] Verificando e limpando portas presas...")
        for port in ports:
            if self.is_windows:
                try:
                    output = subprocess.check_output(
                        "netstat -ano", shell=True, text=True
                    )
                    for line in output.splitlines():
                        if "LISTENING" in line and f":{port}" in line:
                            local_address = line.split()[1]
                            if local_address.endswith(f":{port}"):
                                pid = line.split()[-1]
                                if pid != "0":
                                    print(
                                        f"[ServiceManager] Porta {port} ocupada (PID {pid}). Forcando liberacao..."
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

    def start_background_services(self):
        print("[ServiceManager] Iniciando servicos em background...")
        for target in self.targets:
            flags = subprocess.CREATE_NEW_PROCESS_GROUP if self.is_windows else 0
            p = subprocess.Popen(["make", target], creationflags=flags)
            self.procs.append((target, p))
            print(f" -> '{target}' iniciado com PID {p.pid}")
            time.sleep(1)

    def run_main_server(self):
        print(
            "\n[ServiceManager] Iniciando servidor principal (FastAPI) no terminal ativo...\n"
        )
        try:
            subprocess.run(["make", "server"])
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
                os.killpg(os.getpgid(pid), 9)
            except Exception:
                pass

    def stop_all(self):
        print(
            "\n[ServiceManager] Finalizando todos os servicos dependentes e limpando processos órfãos..."
        )
        for name, p in self.procs:
            print(f" -> Encerrando árvore de processos do '{name}' (PID {p.pid})...")
            try:
                if self.is_windows:
                    self.kill_process_tree(p.pid)
                else:
                    p.terminate()
            except Exception as e:
                print(f" -> Erro ao finalizar '{name}': {e}")

        for name, p in self.procs:
            p.wait()

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
