"""SSH command executor using Paramiko."""

import logging

import paramiko

logger = logging.getLogger(__name__)


class SSHExecutor:
    """Execute commands on remote hosts via SSH."""

    def __init__(self, host: str, port: int = 22, username: str = "root",
                 password: str | None = None, key_path: str | None = None):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.key_path = key_path
        self._client: paramiko.SSHClient | None = None

    def connect(self) -> None:
        self._client = paramiko.SSHClient()
        self._client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        kwargs = {
            "hostname": self.host,
            "port": self.port,
            "username": self.username,
        }
        if self.key_path:
            kwargs["key_filename"] = self.key_path
        elif self.password:
            kwargs["password"] = self.password

        self._client.connect(**kwargs, timeout=10)

    def execute(self, command: str, timeout: int = 30) -> tuple[int, str, str]:
        """Execute a command. Returns (exit_code, stdout, stderr)."""
        if not self._client:
            self.connect()

        stdin, stdout, stderr = self._client.exec_command(command, timeout=timeout)
        exit_code = stdout.channel.recv_exit_status()
        return exit_code, stdout.read().decode(), stderr.read().decode()

    def close(self) -> None:
        if self._client:
            self._client.close()
            self._client = None

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, *args):
        self.close()


def test_connection(config: dict) -> tuple[bool, str]:
    """Test SSH connection from connection config dict."""
    try:
        ssh = SSHExecutor(
            host=config.get("host", ""),
            port=config.get("port", 22),
            username=config.get("username", "root"),
            password=config.get("password"),
            key_path=config.get("key_path"),
        )
        ssh.connect()
        code, out, _ = ssh.execute("echo ok")
        ssh.close()
        if code == 0 and "ok" in out:
            return True, "连接成功"
        return False, f"命令执行异常: exit_code={code}"
    except Exception as e:
        return False, f"连接失败: {str(e)}"
