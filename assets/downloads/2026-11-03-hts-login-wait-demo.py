"""Reproduce login-wait policies without opening an HTS or clicking the desktop.

Python 3.10+; standard library only. The demo uses scripted observations and
virtual time. See the accompanying article before connecting a real UI adapter.
"""
import argparse
from dataclasses import asdict, dataclass
import json
import logging
import math
from pathlib import Path
import sys
import time

LOG = logging.getLogger("login_wait")


@dataclass(frozen=True)
class Observation:
    login: bool = False
    loading: bool = False
    ready: bool = False
    popup: str | None = None


class UnhandledPopup(RuntimeError):
    pass


class PopupNotClosed(RuntimeError):
    pass


class PopupLimitExceeded(RuntimeError):
    pass


def wait_for_login(observe, dismiss_notice, *, timeout=12.0,
                   interval=1.0, popup_timeout=2.0, max_popup_actions=2,
                   ready_samples=2, clock=time.monotonic, pause=time.sleep):
    for value in (timeout, interval, popup_timeout):
        if not math.isfinite(value) or value <= 0:
            raise ValueError("time limits and interval must be finite and positive")
    if type(max_popup_actions) is not int or max_popup_actions < 0:
        raise ValueError("max_popup_actions must be a nonnegative integer")
    if type(ready_samples) is not int or ready_samples < 2:
        raise ValueError("ready_samples must be an integer >= 2")

    started = clock()
    deadline = started + timeout
    pending_popup = None
    popup_requested_at = 0.0
    actions = 0
    ready_count = 0
    last_state = "START"
    polls = 0

    while True:
        if clock() >= deadline:
            raise TimeoutError(f"state={last_state} elapsed={clock() - started:.1f}s")
        view = observe()
        polls += 1
        now = clock()
        if now >= deadline:
            raise TimeoutError(f"observation exceeded deadline elapsed={now - started:.1f}s")
        if not isinstance(view, Observation):
            raise TypeError("observe() must return Observation")

        if view.popup is not None:
            state = "POPUP:" + view.popup
        elif view.login:
            state = "LOGIN"
        elif view.loading:
            state = "LOADING"
        elif view.ready:
            state = "READY"
        else:
            state = "UNKNOWN"
        if state != last_state:
            LOG.info("state=%s elapsed=%.1fs", state, now - started)
            last_state = state

        if view.popup is not None:
            ready_count = 0
            if view.popup != "login_notice":
                raise UnhandledPopup(f"popup={view.popup}")
            if pending_popup is None:
                if actions >= max_popup_actions:
                    raise PopupLimitExceeded(f"actions={actions}")
                actions += 1
                LOG.info("action=dismiss_notice attempt=%d", actions)
                dismiss_notice(view.popup)
                pending_popup = view.popup
                popup_requested_at = clock()
            elif clock() - popup_requested_at >= popup_timeout:
                raise PopupNotClosed(f"popup={pending_popup}")
        else:
            if pending_popup is not None:
                LOG.info("popup_gone=%s", pending_popup)
                pending_popup = None
            ready_count = ready_count + 1 if state == "READY" else 0
            if ready_count >= ready_samples:
                LOG.info("result=READY elapsed=%.1fs polls=%d actions=%d",
                         clock() - started, polls, actions)
                return view

        remaining = deadline - clock()
        if remaining <= 0:
            raise TimeoutError(f"state={last_state} elapsed={clock() - started:.1f}s")
        pause(min(interval, remaining))


class VirtualClock:
    def __init__(self):
        self.now = 0.0

    def monotonic(self):
        return self.now

    def sleep(self, seconds):
        self.now += seconds


LOGIN = Observation(login=True)
LOADING = Observation(loading=True)
READY = Observation(ready=True)
NOTICE = Observation(ready=True, popup="login_notice")
SCENARIOS = {
    "normal": [LOGIN, LOADING, READY, READY],
    "slow": [LOGIN] + [LOADING] * 7 + [READY, READY],
    "notice": [LOGIN, LOADING, NOTICE, READY, READY],
    "stuck-popup": [LOGIN, LOADING, NOTICE],
    "repeated-popup": [LOGIN, NOTICE, LOADING, NOTICE, LOADING, NOTICE],
    "unknown-popup": [LOGIN, LOADING, Observation(popup="password_error")],
    "timeout": [LOGIN, LOADING],
    "ready-with-popup": [Observation(ready=True, popup="password_error")],
    "brief-ready": [LOGIN, READY, LOADING, READY, READY],
    "deadline-with-popup": [LOGIN] + [LOADING] * 9 + [NOTICE, LOADING],
}


class DemoScreen:
    def __init__(self, frames, clock):
        self.frames = frames
        self.clock = clock
        self.last = Observation()
        self.actions = []

    def observe(self):
        index = min(int(self.clock.now), len(self.frames) - 1)
        self.last = self.frames[index]
        return self.last

    def dismiss_notice(self, popup):
        # Record a requested action. No real popup is clicked or closed.
        self.actions.append({"popup": popup, "at": self.clock.now})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scenario", choices=SCENARIOS, default="notice")
    parser.add_argument("--output-dir", type=Path)
    args = parser.parse_args()
    handlers = [logging.StreamHandler(sys.stdout)]
    if args.output_dir is not None:
        args.output_dir.mkdir(parents=True, exist_ok=True)
        handlers.append(logging.FileHandler(args.output_dir / "login-wait.log", encoding="utf-8"))
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s",
                        handlers=handlers, force=True)
    LOG.info("scenario=%s mode=virtual", args.scenario)
    timer = VirtualClock()
    screen = DemoScreen(SCENARIOS[args.scenario], timer)
    try:
        wait_for_login(screen.observe, screen.dismiss_notice,
                       clock=timer.monotonic, pause=timer.sleep)
    except (TimeoutError, UnhandledPopup, PopupNotClosed, PopupLimitExceeded) as error:
        LOG.exception("result=STOP reason=%s elapsed=%.1fs", type(error).__name__, timer.now)
        if args.output_dir is not None:
            details = {"scenario": args.scenario, "reason": type(error).__name__,
                       "elapsed": timer.now, "last_observation": asdict(screen.last),
                       "actions": screen.actions}
            (args.output_dir / "failure.json").write_text(
                json.dumps(details, ensure_ascii=False, indent=2), encoding="utf-8")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
