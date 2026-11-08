from typing import Optional, List
import subprocess


class Signal:
	def __init__(self, account):
		self.account = account
		self.rcpt = None

	def _cmd(self) -> List[str]:
		return ["signal-cli", "-a", self.account]

	def default_rcpt(self, rcpt: str) -> None:
		self.rcpt = rcpt

	def send(self, msg: str, rcpt: Optional[str] = None) -> bool:
		if rcpt is None:
			rcpt = self.rcpt
		if rcpt is None:
			raise ValueError("Have no recipient")
		cmd = self._cmd() + ['send', '-m', msg, rcpt]
		result = subprocess.run(cmd)
		return result.returncode == 0

	def sendGroup(self, msg: str, gid: str) -> bool:
		if id is None:
			raise ValueError("Have no recipient")
		cmd = self._cmd() + ['send', '-m', msg, '-g', gid]
		result = subprocess.run(cmd)
		return result.returncode == 0


if __name__ == "__main__":
	from settings import SETTINGS
	s = SETTINGS()
	account = s.get("Signal", "Account")
	rcpt = s.get("Signal", "Target")
	sig = Signal(account)
	sig.default_rcpt(rcpt)
	sig.send("Hallo Welt")

