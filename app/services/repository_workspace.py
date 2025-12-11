import os
import shutil
import subprocess
from pathlib import Path

from app.core.settings import settings
from app.utils.logger_config import logger


class RepositoryWorkspace:
    """
    Manages local workspace directory for repository.
    Combines work with Git, file system, and build tools (npm/linter).
    """

    def __init__(self, repo_url: str, local_path: str, git_ssh_key_path: str | None = None):
        self.repo_url = repo_url
        self.local_path = Path(local_path).resolve()

        # Git environment configuration
        self.git_env = os.environ.copy()

        if git_ssh_key_path:
            logger.info(f"Workspace: Using custom SSH key: {git_ssh_key_path}")
            self.git_env["GIT_SSH_COMMAND"] = f"ssh -o StrictHostKeyChecking=no -i {git_ssh_key_path}"
        else:
            logger.warning("Workspace: SSH key path NOT provided. Using default SSH behavior.")
            self.git_env["GIT_SSH_COMMAND"] = "ssh -o StrictHostKeyChecking=no"

    # =========================================================================
    # INTERNAL HELPERS
    # =========================================================================

    def _run_cmd(self, cmd: list, cwd=None) -> str:
        """Runs a system command in the workspace context."""
        try:
            result = subprocess.run(cmd, cwd=cwd or self.local_path, check=True, capture_output=True, text=True, env=self.git_env)
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            logger.error(f"Command failed: {' '.join(cmd)}\nSTDERR: {e.stderr}\nSTDOUT: {e.stdout}")
            raise e

    # =========================================================================
    # WORKSPACE SETUP (Git Clone + Dependencies)
    # =========================================================================

    def prepare_repo(self, branch_name: str):
        """Initializes workspace: clones repo, installs dependencies, creates branch."""
        # --------------------------------------------------------------
        # Check for corrupted repo TEMPORARY FIX
        # --------------------------------------------------------------
        git_dir = self.local_path / ".git"

        # Перевіряємо, чи є сміття (файли є, а .git папки немає)
        has_files = any(self.local_path.iterdir()) if self.local_path.exists() else False
        is_corrupted = self.local_path.exists() and has_files and not git_dir.exists()

        if is_corrupted:
            logger.warning(f"Found corrupted repo dir at {self.local_path}. Cleaning contents...")

            # 👇 ВАЖЛИВО: Видаляємо вміст, а не саму папку!
            for item in self.local_path.iterdir():
                try:
                    if item.is_dir():
                        shutil.rmtree(item)
                    else:
                        item.unlink()
                except Exception as e:
                    logger.warning(f"Failed to delete {item}: {e}")
        # --------------------------------------------------------------

        # 1. Clone & Bootstrap (if directory doesn't exist)
        if not (self.local_path / ".git").exists():
            logger.info(f"Cloning {self.repo_url} into {self.local_path}...")
            self.local_path.mkdir(parents=True, exist_ok=True)
            self._run_cmd(["git", "clone", self.repo_url, "."], cwd=self.local_path)

            # Config git user TODO: fix this
            self._run_cmd(["git", "config", "user.email", "slava@patrianna.com"])
            self._run_cmd(["git", "config", "user.name", "AI Agent"])

            # Bootstrap dependencies
            logger.info("Installing dependencies...")
            self._run_cmd(["npm", "run", "install-deps"], cwd=self.local_path)

        # 2. Reset state (git fetch & clean)
        self._run_cmd(["git", "fetch", "origin"])
        self._run_cmd(["git", "reset", "--hard", "origin/main"])
        self._run_cmd(["git", "clean", "-fd"])

        # 3. Switch branch (-B forces create or reset)
        self._run_cmd(["git", "checkout", "-B", branch_name])

    # =========================================================================
    # FILE SYSTEM OPERATIONS
    # =========================================================================

    def inject_code(self, file_path: str, code: str):
        """Writes or overwrites a file in the workspace."""
        full_path = self.local_path / file_path
        full_path.parent.mkdir(parents=True, exist_ok=True)

        with open(full_path, "w", encoding="utf-8") as f:
            f.write(code)

    def read_file(self, file_path: str) -> str:
        """Reads file contents."""
        with open(self.local_path / file_path, encoding="utf-8") as f:
            return f.read()

    # =========================================================================
    # TOOLING (Linter / Build)
    # =========================================================================

    def run_linter_fix(self) -> tuple[bool, str]:
        """
        Runs eslint from the repository with code. The project must have `npm run lint` command with --fix flag

        Returns: (success: bool, logs: str)
        """
        logger.info(f"Running linter in repository: '{self.local_path}'...")
        try:
            # --silent: so npm doesn't write extra output, only eslint output
            self._run_cmd(["npm", "run", "lint"])
            return True, "Linter passed"
        except subprocess.CalledProcessError as e:
            # Return error text for LLM
            error_msg = e.stdout if e.stdout else e.stderr
            return False, error_msg

    # =========================================================================
    # GIT OPERATIONS (Commit & Push)
    # =========================================================================

    def commit_and_push(self, message: str, branch_name: str):
        """Commits changes and pushes to server."""
        self._run_cmd(["git", "add", "."])

        status = self._run_cmd(["git", "status", "--porcelain"])
        if not status:
            logger.info("No changes to commit.")
            return

        # here we add the author to the commit to trigger the rebuild in Vercel
        self._run_cmd(["git", "commit", "-m", message, "--author", f"Slava <{settings.EMAIL_WITH_VERCEL_ACCESS}>"])
        self._run_cmd(["git", "push", "origin", branch_name, "--force"])
        logger.info(f"Pushed to {branch_name}")
