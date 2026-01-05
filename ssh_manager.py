"""
SSH Manager for automated file upload and training task execution on Autodl servers.

This module provides functionality to:
- Establish SSH connections to Autodl servers
- Upload files using SCP
- Execute remote training commands
- Monitor training progress
"""

import os
import logging
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass

# Attempt to import paramiko and scp. In environments where these heavy
# dependencies are not installed (for example, minimal test environments),
# we degrade gracefully by defining placeholder classes. This allows the
# module to be imported without raising ImportError. Functions that rely on
# SSH functionality should check whether these classes are available using
# the `_SSH_AVAILABLE` flag.
try:
    import paramiko  # type: ignore
    from paramiko import SSHClient, AutoAddPolicy  # type: ignore
    from scp import SCPClient  # type: ignore
    _SSH_AVAILABLE = True
except Exception:
    # If either paramiko or scp cannot be imported, define stub classes so
    # attribute access does not fail. Methods of these classes raise
    # informative errors if called when dependencies are missing.
    paramiko = None  # type: ignore
    _SSH_AVAILABLE = False

    class SSHClient:  # type: ignore
        """Stub SSHClient used when paramiko is unavailable."""
        def __init__(self, *args, **kwargs):
            raise ImportError(
                "paramiko is not installed; SSH functionality is unavailable."
            )

    class AutoAddPolicy:  # type: ignore
        """Stub AutoAddPolicy used when paramiko is unavailable."""
        def __init__(self, *args, **kwargs):
            raise ImportError(
                "paramiko is not installed; SSH functionality is unavailable."
            )

    class SCPClient:  # type: ignore
        """Stub SCPClient used when scp is unavailable."""
        def __init__(self, *args, **kwargs):
            raise ImportError(
                "scp is not installed; file transfer functionality is unavailable."
            )

    # When SSH dependencies are missing, we will avoid creating a functional
    # SSHManager. See get_ssh_manager() for how this is handled.

logger = logging.getLogger(__name__)

@dataclass
class SSHConfig:
    """SSH connection configuration."""
    hostname: str
    port: int = 22
    username: str = "root"
    password: Optional[str] = None
    key_filename: Optional[str] = None
    key_password: Optional[str] = None
    timeout: int = 30

@dataclass
class TrainingConfig:
    """Training configuration for remote execution."""
    model_id: str
    role_file: str
    batch_size: int
    epochs: int
    learning_rate: float
    use_lora: bool = True
    remote_workspace: str = "/root/workspace"

class SSHManager:
    """SSH manager for Autodl server operations."""

    def __init__(self, config: SSHConfig):
        """Initialize SSH manager.

        Parameters
        ----------
        config : SSHConfig
            SSH connection configuration.
        """
        self.config = config
        self.ssh_client: Optional[SSHClient] = None
        self.scp_client: Optional[SCPClient] = None

    def connect(self) -> bool:
        """Establish SSH connection to the server.

        Returns
        -------
        bool
            True if connection successful, False otherwise.
        """
        try:
            self.ssh_client = SSHClient()
            self.ssh_client.set_missing_host_key_policy(AutoAddPolicy())

            # Connect using password or key
            if self.config.password:
                self.ssh_client.connect(
                    hostname=self.config.hostname,
                    port=self.config.port,
                    username=self.config.username,
                    password=self.config.password,
                    timeout=self.config.timeout
                )
            elif self.config.key_filename:
                self.ssh_client.connect(
                    hostname=self.config.hostname,
                    port=self.config.port,
                    username=self.config.username,
                    key_filename=self.config.key_filename,
                    passphrase=self.config.key_password,
                    timeout=self.config.timeout
                )
            else:
                raise ValueError("Either password or key_filename must be provided")

            # Initialize SCP client
            self.scp_client = SCPClient(self.ssh_client.get_transport())

            logger.info(f"Successfully connected to {self.config.hostname}:{self.config.port}")
            return True

        except Exception as exc:
            logger.error(f"Failed to connect to SSH server: {exc}")
            return False

    def disconnect(self):
        """Close SSH connection."""
        if self.scp_client:
            self.scp_client.close()
            self.scp_client = None

        if self.ssh_client:
            self.ssh_client.close()
            self.ssh_client = None

        logger.info("SSH connection closed")

    def execute_command(self, command: str, timeout: int = 60) -> Tuple[int, str, str]:
        """Execute a command on the remote server.

        Parameters
        ----------
        command : str
            Command to execute.
        timeout : int
            Command timeout in seconds.

        Returns
        -------
        Tuple[int, str, str]
            Return code, stdout, stderr.
        """
        if not self.ssh_client:
            raise ConnectionError("SSH client not connected")

        try:
            logger.info(f"Executing remote command: {command}")
            stdin, stdout, stderr = self.ssh_client.exec_command(command, timeout=timeout)

            # Read output
            stdout_content = stdout.read().decode('utf-8')
            stderr_content = stderr.read().decode('utf-8')
            return_code = stdout.channel.recv_exit_status()

            logger.info(f"Command executed with return code: {return_code}")

            if return_code != 0:
                logger.warning(f"Command stderr: {stderr_content}")

            return return_code, stdout_content, stderr_content

        except Exception as exc:
            logger.error(f"Failed to execute command: {exc}")
            raise

    def upload_file(self, local_path: str, remote_path: str, recursive: bool = False):
        """Upload a file or directory to the remote server.

        Parameters
        ----------
        local_path : str
            Local file/directory path.
        remote_path : str
            Remote file/directory path.
        recursive : bool
            Whether to upload recursively (for directories).
        """
        if not self.scp_client:
            raise ConnectionError("SCP client not connected")

        try:
            logger.info(f"Uploading {local_path} to {remote_path}")
            self.scp_client.put(local_path, remote_path, recursive=recursive)
            logger.info("File upload completed")

        except Exception as exc:
            logger.error(f"Failed to upload file: {exc}")
            raise

    def download_file(self, remote_path: str, local_path: str, recursive: bool = False):
        """Download a file or directory from the remote server.

        Parameters
        ----------
        remote_path : str
            Remote file/directory path.
        local_path : str
            Local file/directory path.
        recursive : bool
            Whether to download recursively (for directories).
        """
        if not self.scp_client:
            raise ConnectionError("SCP client not connected")

        try:
            logger.info(f"Downloading {remote_path} to {local_path}")
            self.scp_client.get(remote_path, local_path, recursive=recursive)
            logger.info("File download completed")

        except Exception as exc:
            logger.error(f"Failed to download file: {exc}")
            raise

    def upload_training_files(self, training_config: TrainingConfig) -> str:
        """Upload all necessary files for training.

        Parameters
        ----------
        training_config : TrainingConfig
            Training configuration.

        Returns
        -------
        str
            Remote workspace path.
        """
        remote_workspace = f"{training_config.remote_workspace}/{training_config.model_id}"

        try:
            # Create remote workspace directory
            self.execute_command(f"mkdir -p {remote_workspace}")

            # Upload role configuration file
            role_file_path = Path(training_config.role_file)
            if role_file_path.exists():
                remote_role_path = f"{remote_workspace}/role.json"
                self.upload_file(str(role_file_path), remote_role_path)
                logger.info(f"Uploaded role file: {role_file_path}")
            else:
                raise FileNotFoundError(f"Role file not found: {role_file_path}")

            # Upload training data (if exists)
            # This could include additional training samples or datasets

            # Upload training script (we'll create this)
            training_script = self._create_training_script(training_config)
            remote_script_path = f"{remote_workspace}/train.py"
            self._upload_string_as_file(training_script, remote_script_path)

            logger.info(f"All training files uploaded to {remote_workspace}")
            return remote_workspace

        except Exception as exc:
            logger.error(f"Failed to upload training files: {exc}")
            raise

    def start_training(self, training_config: TrainingConfig) -> str:
        """Start training on the remote server.

        Parameters
        ----------
        training_config : TrainingConfig
            Training configuration.

        Returns
        -------
        str
            Job ID for tracking.
        """
        try:
            # Upload training files
            remote_workspace = self.upload_training_files(training_config)

            # Start training in background
            training_cmd = f"cd {remote_workspace} && python train.py > training.log 2>&1 & echo $!"
            return_code, stdout, stderr = self.execute_command(training_cmd)

            if return_code != 0:
                raise RuntimeError(f"Failed to start training: {stderr}")

            # Get the process ID
            pid = stdout.strip()
            job_id = f"remote_{training_config.model_id}_{pid}"

            logger.info(f"Training started with job ID: {job_id}, PID: {pid}")

            # Save job information
            self._save_job_info(job_id, training_config, remote_workspace, pid)

            return job_id

        except Exception as exc:
            logger.error(f"Failed to start remote training: {exc}")
            raise

    def check_training_status(self, job_id: str) -> Dict[str, Any]:
        """Check the status of a remote training job.

        Parameters
        ----------
        job_id : str
            Job ID to check.

        Returns
        -------
        Dict[str, Any]
            Job status information.
        """
        try:
            # Load job information
            job_info = self._load_job_info(job_id)
            if not job_info:
                return {"status": "not_found", "error": "Job not found"}

            remote_workspace = job_info["remote_workspace"]
            pid = job_info["pid"]

            # Check if process is still running
            check_cmd = f"ps -p {pid} > /dev/null 2>&1 && echo 'running' || echo 'stopped'"
            return_code, stdout, stderr = self.execute_command(check_cmd)

            if "running" in stdout:
                # Try to get training progress from log file
                log_cmd = f"tail -20 {remote_workspace}/training.log"
                _, log_output, _ = self.execute_command(log_cmd)

                return {
                    "status": "running",
                    "pid": pid,
                    "remote_workspace": remote_workspace,
                    "latest_log": log_output
                }
            else:
                # Training completed or failed
                # Check if model files exist
                check_model_cmd = f"ls -la {remote_workspace}/models/"
                _, model_output, _ = self.execute_command(check_model_cmd)

                if "model" in model_output.lower():
                    return {
                        "status": "completed",
                        "pid": pid,
                        "remote_workspace": remote_workspace,
                        "model_files": model_output
                    }
                else:
                    # Check log for errors
                    error_cmd = f"tail -50 {remote_workspace}/training.log"
                    _, error_log, _ = self.execute_command(error_cmd)

                    return {
                        "status": "failed",
                        "pid": pid,
                        "remote_workspace": remote_workspace,
                        "error_log": error_log
                    }

        except Exception as exc:
            logger.error(f"Failed to check training status: {exc}")
            return {"status": "error", "error": str(exc)}

    def download_trained_model(self, job_id: str, local_path: str) -> bool:
        """Download the trained model from remote server.

        Parameters
        ----------
        job_id : str
            Job ID.
        local_path : str
            Local path to save the model.

        Returns
        -------
        bool
            True if download successful.
        """
        try:
            job_info = self._load_job_info(job_id)
            if not job_info:
                raise ValueError(f"Job not found: {job_id}")

            remote_workspace = job_info["remote_workspace"]
            remote_model_path = f"{remote_workspace}/models"

            # Check if model exists
            check_cmd = f"ls -la {remote_model_path}"
            return_code, stdout, stderr = self.execute_command(check_cmd)

            if return_code != 0:
                raise FileNotFoundError(f"Model not found on remote server: {stderr}")

            # Download model
            local_model_dir = Path(local_path) / job_id
            local_model_dir.mkdir(parents=True, exist_ok=True)

            self.download_file(remote_model_path, str(local_model_dir), recursive=True)

            logger.info(f"Model downloaded to {local_model_dir}")
            return True

        except Exception as exc:
            logger.error(f"Failed to download model: {exc}")
            return False

    def _create_training_script(self, training_config: TrainingConfig) -> str:
        """Create training script content for remote execution.

        Parameters
        ----------
        training_config : TrainingConfig
            Training configuration.

        Returns
        -------
        str
            Training script content.
        """
        script = f'''#!/usr/bin/env python3
"""
Remote training script for Qwen fine-tuning.
Generated automatically by SSH Manager.
"""

import json
import os
import sys
from pathlib import Path

def main():
    # Load configuration
    config = {json.dumps(training_config.__dict__, indent=4)}

    print("Starting remote training...")
    print(f"Model ID: {config['model_id']}")
    print(f"Role file: {config['role_file']}")
    print(f"Batch size: {config['batch_size']}")
    print(f"Epochs: {config['epochs']}")
    print(f"Learning rate: {config['learning_rate']}")

    # Create models directory
    models_dir = Path("models")
    models_dir.mkdir(exist_ok=True)

    # Load role data
    try:
        with open("role.json", "r", encoding="utf-8") as f:
            role_data = json.load(f)
        print(f"Loaded role: {{role_data.get('character_name', 'Unknown')}}")
    except Exception as e:
        print(f"Error loading role data: {{e}}")
        sys.exit(1)

    # Here you would implement the actual training logic
    # For now, we'll simulate training
    print("Training simulation started...")

    for epoch in range(config['epochs']):
        print(f"Epoch {{epoch + 1}}/{{config['epochs']}} - Training...")
        # Simulate training work
        import time
        time.sleep(2)  # Simulate training time
        print(f"Epoch {{epoch + 1}} completed")

    # Save dummy model files
    model_file = models_dir / f"{{config['model_id']}}_model.bin"
    with open(model_file, "w") as f:
        f.write("Dummy trained model")

    config_file = models_dir / f"{{config['model_id']}}_config.json"
    with open(config_file, "w") as f:
        json.dump(config, f, indent=2)

    print("Training completed successfully!")
    print(f"Model saved to: {{models_dir}}")

if __name__ == "__main__":
    main()
'''
        return script

    def _upload_string_as_file(self, content: str, remote_path: str):
        """Upload a string as a file to the remote server.

        Parameters
        ----------
        content : str
            File content.
        remote_path : str
            Remote file path.
        """
        if not self.ssh_client:
            raise ConnectionError("SSH client not connected")

        try:
            # Create temporary local file
            import tempfile
            with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.py') as f:
                f.write(content)
                temp_file = f.name

            try:
                # Upload the temporary file
                self.upload_file(temp_file, remote_path)
            finally:
                # Clean up temporary file
                os.unlink(temp_file)

        except Exception as exc:
            logger.error(f"Failed to upload string as file: {exc}")
            raise

    def _save_job_info(self, job_id: str, training_config: TrainingConfig, remote_workspace: str, pid: str):
        """Save job information to a local file for tracking.

        Parameters
        ----------
        job_id : str
            Job ID.
        training_config : TrainingConfig
            Training configuration.
        remote_workspace : str
            Remote workspace path.
        pid : str
            Process ID.
        """
        job_info = {
            "job_id": job_id,
            "model_id": training_config.model_id,
            "remote_workspace": remote_workspace,
            "pid": pid,
            "config": training_config.__dict__
        }

        job_file = Path("remote_jobs") / f"{job_id}.json"
        job_file.parent.mkdir(exist_ok=True)

        with open(job_file, 'w') as f:
            json.dump(job_info, f, indent=2)

        logger.info(f"Job info saved to {job_file}")

    def _load_job_info(self, job_id: str) -> Optional[Dict]:
        """Load job information from file.

        Parameters
        ----------
        job_id : str
            Job ID.

        Returns
        -------
        Optional[Dict]
            Job information or None if not found.
        """
        job_file = Path("remote_jobs") / f"{job_id}.json"

        if not job_file.exists():
            return None

        try:
            with open(job_file, 'r') as f:
                return json.load(f)
        except Exception as exc:
            logger.error(f"Failed to load job info: {exc}")
            return None

class AutodlSSHManager(SSHManager):
    """SSH manager specifically configured for Autodl servers."""

    def __init__(self, hostname: str, username: str = "root", key_filename: Optional[str] = None):
        """Initialize Autodl SSH manager.

        Parameters
        ----------
        hostname : str
            Autodl server hostname/IP.
        username : str
            SSH username (default: root).
        key_filename : Optional[str]
            Path to SSH private key file.
        """
        config = SSHConfig(
            hostname=hostname,
            username=username,
            key_filename=key_filename,
            timeout=60  # Longer timeout for Autodl
        )
        super().__init__(config)

    def setup_environment(self):
        """Setup the remote environment for training.

        This includes installing required packages and setting up directories.
        """
        commands = [
            "pip install transformers torch peft datasets accelerate",
            "mkdir -p /root/workspace",
            "mkdir -p /root/models"
        ]

        for cmd in commands:
            logger.info(f"Executing setup command: {cmd}")
            return_code, stdout, stderr = self.execute_command(cmd)
            if return_code != 0:
                logger.warning(f"Setup command failed: {stderr}")
            else:
                logger.info(f"Setup command successful: {stdout}")

# Global SSH manager instance
_ssh_manager: Optional[SSHManager] = None

def get_ssh_manager() -> Optional[SSHManager]:
    """Get the configured SSH manager."""
    global _ssh_manager

    if _ssh_manager is not None:
        return _ssh_manager

    # Get SSH configuration from environment
    hostname = os.getenv("SSH_HOSTNAME")
    username = os.getenv("SSH_USERNAME", "root")
    key_filename = os.getenv("SSH_KEY_FILENAME")

    if not hostname:
        logger.warning("SSH_HOSTNAME not configured")
        return None

    # If SSH support is not available (paramiko/scp not installed), disable remote training.
    if not _SSH_AVAILABLE:
        logger.warning(
            "SSH dependencies not available; remote training is disabled in this environment."
        )
        return None

    try:
        _ssh_manager = AutodlSSHManager(hostname, username, key_filename)
        logger.info(f"SSH manager created for {hostname}")
        return _ssh_manager
    except Exception as exc:
        logger.error(f"Failed to create SSH manager: {exc}")
        return None

def connect_ssh() -> bool:
    """Connect to the configured SSH server.

    Returns
    -------
    bool
        True if connection successful.
    """
    manager = get_ssh_manager()
    if not manager:
        return False

    return manager.connect()

def disconnect_ssh():
    """Disconnect from SSH server."""
    manager = get_ssh_manager()
    if manager:
        manager.disconnect()
