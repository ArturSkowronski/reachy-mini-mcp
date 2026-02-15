from __future__ import annotations

import asyncio
import os
import socket
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

import cv2
import httpx
from reachy_mini import ReachyMini
from reachy_mini.utils import create_head_pose

from reachy_elevenlabs import (
    DEFAULT_ELEVENLABS_VOICE_ID,
    ElevenLabsConfig,
    elevenlabs_tts_to_temp_audio_file,
    load_elevenlabs_config,
)


SCRIPT_DIR = Path(__file__).resolve().parent
RESULTS_ROOT = SCRIPT_DIR / "results"

_HORIZONTAL_FOV = 65.0  # degrees
_VERTICAL_FOV = 40.0  # degrees

BANNER = r"""
██████╗ ███████╗ █████╗  ██████╗██╗  ██╗██╗   ██╗    ███╗   ███╗██╗███╗   ██╗██╗
██╔══██╗██╔════╝██╔══██╗██╔════╝██║  ██║╚██╗ ██╔╝    ████╗ ████║██║████╗  ██║██║
██████╔╝█████╗  ███████║██║     ███████║ ╚████╔╝     ██╔████╔██║██║██╔██╗ ██║██║
██╔══██╗██╔══╝  ██╔══██║██║     ██╔══██║  ╚██╔╝      ██║╚██╔╝██║██║██║╚██╗██║██║
██║  ██║███████╗██║  ██║╚██████╗██║  ██║   ██║       ██║ ╚═╝ ██║██║██║ ╚████║██║
╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝ ╚═════╝╚═╝  ╚═╝   ╚═╝       ╚═╝     ╚═╝╚═╝╚═╝  ╚═══╝╚═╝

███╗   ███╗ ██████╗██████╗
████╗ ████║██╔════╝██╔══██╗
██╔████╔██║██║     ██████╔╝
██║╚██╔╝██║██║     ██╔═══╝
██║ ╚═╝ ██║╚██████╗██║
╚═╝     ╚═╝ ╚═════╝╚═╝
"""

REACHY_ASCII = r"""
                 .-.
                /___\
                [o o]
               /|_=_|\
              //|   |\\
             /_/|___|\_\
               /_/ \_\
"""

_tts_disabled_reason_logged = False
_tts_runtime_disabled = False

ANNOUNCE_PAUSE_S = float(os.getenv("REACHY_DEBUG_ANNOUNCE_PAUSE_S", "0.6"))
TTS_SPEED = float(os.getenv("REACHY_DEBUG_TTS_SPEED", "0.8"))


class _Color:
    RESET = "\x1b[0m"
    DIM = "\x1b[2m"
    BOLD = "\x1b[1m"

    RED = "\x1b[31m"
    GREEN = "\x1b[32m"
    YELLOW = "\x1b[33m"
    BLUE = "\x1b[34m"
    MAGENTA = "\x1b[35m"
    CYAN = "\x1b[36m"


def _use_color() -> bool:
    if os.getenv("NO_COLOR"):
        return False
    term = os.getenv("TERM", "").lower()
    if term in ("dumb", ""):
        return False
    return True


def _c(text: str, color: str) -> str:
    if not _use_color():
        return text
    return f"{color}{text}{_Color.RESET}"


def _status_badge(status: str) -> str:
    s = status.upper()
    if s == "OK" or s == "PASS":
        return _c(s, _Color.GREEN + _Color.BOLD)
    if s == "WARN":
        return _c(s, _Color.YELLOW + _Color.BOLD)
    if s == "FAIL" or s == "FATAL":
        return _c(s, _Color.RED + _Color.BOLD)
    return _c(s, _Color.BLUE + _Color.BOLD)


@dataclass
class StepResult:
    name: str
    status: str
    details: str
    started_at: str
    finished_at: str


@dataclass
class PreflightCheck:
    name: str
    status: str  # OK, WARN, FAIL
    details: str


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _create_run_dir() -> Path:
    run_id = datetime.now().strftime("run-%Y%m%d-%H%M%S")
    run_dir = RESULTS_ROOT / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    return run_dir


def _announce(mini: ReachyMini, message: str) -> None:
    global _tts_disabled_reason_logged
    global _tts_runtime_disabled

    print(f"{_c('[ANNOUNCE]', _Color.CYAN + _Color.BOLD)} {message}")
    if _tts_runtime_disabled:
        return

    try:
        config = load_elevenlabs_config()
    except ValueError as exc:
        # Fallback when ElevenLabs is not configured.
        if not _tts_disabled_reason_logged:
            print(f"{_c('[TTS][DISABLED]', _Color.YELLOW + _Color.BOLD)} {exc}")
            _tts_disabled_reason_logged = True
        return

    audio_path: str | None = None
    try:
        print(
            f"{_c('[TTS][INFO]', _Color.BLUE)} Generating announcement audio via ElevenLabs..."
        )
        audio_path = asyncio.run(
            elevenlabs_tts_to_temp_audio_file(
                text=message,
                config=config,
                voice_settings={"use_speaker_boost": True, "speed": TTS_SPEED},
            )
        )
        print(
            f"{_c('[TTS][INFO]', _Color.BLUE)} Playing announcement audio on Reachy Mini."
        )
        mini.media.play_sound(audio_path)
    except Exception as exc:  # pragma: no cover - best effort voice announcement
        err = str(exc)
        if "403" in err:
            print(
                f"{_c('[TTS][ERROR]', _Color.RED + _Color.BOLD)} "
                "ElevenLabs returned 403 Forbidden. Check API key permissions/plan or output format."
            )
            print(
                f"{_c('[TTS][INFO]', _Color.BLUE)} Disabling TTS for the rest of this run."
            )
        else:
            print(
                f"{_c('[TTS][ERROR]', _Color.RED + _Color.BOLD)} Announcement failed: {exc}"
            )
        _tts_runtime_disabled = True
    finally:
        if audio_path:
            try:
                os.remove(audio_path)
            except FileNotFoundError:
                pass


def _shout_debug_run(mini: ReachyMini, cfg: ElevenLabsConfig) -> None:
    audio_path: str | None = None
    try:
        print(f"{_c('[TTS][INFO]', _Color.BLUE)} Speaking intro: Debug Run")
        audio_path = asyncio.run(
            elevenlabs_tts_to_temp_audio_file(
                text="Debug Run.",
                config=cfg,
                voice_settings={
                    "use_speaker_boost": True,
                    "style": 0.6,
                    "stability": 0.4,
                    "speed": TTS_SPEED,
                },
            )
        )
        mini.media.play_sound(audio_path)
    except Exception as exc:  # pragma: no cover
        print(
            f"{_c('[TTS][WARN]', _Color.YELLOW + _Color.BOLD)} Intro speech failed: {exc}"
        )
    finally:
        if audio_path:
            try:
                os.remove(audio_path)
            except FileNotFoundError:
                pass


def _print_banner(run_dir: Path) -> None:
    print(BANNER.strip("\n"))
    print(_c("Debug Run", _Color.MAGENTA + _Color.BOLD))
    print(REACHY_ASCII.strip("\n"))
    print(f"{_c('Mode:', _Color.DIM)} full sequential demo")
    print(f"Results folder: {run_dir}")
    print("-" * 61)


def _print_preflight_report(checks: list[PreflightCheck]) -> bool:
    print(
        f"{_c('[PRECHECK]', _Color.MAGENTA + _Color.BOLD)} Configuration and readiness checks"
    )
    print("-" * 61)
    for item in checks:
        badge = _status_badge(item.status)
        print(f"[{badge:<4}] {item.name}: {item.details}")
    print("-" * 61)

    fail_count = sum(1 for c in checks if c.status == "FAIL")
    warn_count = sum(1 for c in checks if c.status == "WARN")
    summary = f"{len(checks)} checks, {warn_count} warning(s), {fail_count} failure(s)"
    print(
        f"{_c('[PRECHECK] Summary:', _Color.MAGENTA + _Color.BOLD)} {_c(summary, (_Color.GREEN if fail_count == 0 else _Color.RED) + _Color.BOLD)}"
    )
    print("-" * 61)
    return fail_count == 0


def _run_preflight_checks(mini: ReachyMini, run_dir: Path) -> bool:
    checks: list[PreflightCheck] = []

    # Local filesystem checks
    try:
        run_dir.mkdir(parents=True, exist_ok=True)
        probe = run_dir / ".precheck_write_probe"
        probe.write_text("ok", encoding="utf-8")
        probe.unlink(missing_ok=True)
        checks.append(
            PreflightCheck(
                name="results_directory_write_access",
                status="OK",
                details=f"Writable: {run_dir}",
            )
        )
    except Exception as exc:
        checks.append(
            PreflightCheck(
                name="results_directory_write_access",
                status="FAIL",
                details=str(exc),
            )
        )

    # ElevenLabs config checks
    api_key = os.getenv("REACHY_ELEVENLABS_API_KEY") or os.getenv("ELEVENLABS_API_KEY")
    voice_id = os.getenv("REACHY_ELEVENLABS_VOICE_ID") or os.getenv(
        "ELEVENLABS_VOICE_ID"
    )
    checks.append(
        PreflightCheck(
            name="elevenlabs_api_key",
            status="OK" if api_key else "WARN",
            details=(
                f"Set (...{api_key[-4:]})"
                if api_key
                else "Missing (TTS announcements disabled)"
            ),
        )
    )
    checks.append(
        PreflightCheck(
            name="elevenlabs_voice_id",
            status="OK",
            details=(
                f"Set ({voice_id})"
                if voice_id
                else (f"Not set in env, using default ({DEFAULT_ELEVENLABS_VOICE_ID})")
            ),
        )
    )

    resolved_cfg: ElevenLabsConfig | None = None
    if api_key:
        try:
            resolved_cfg = load_elevenlabs_config(api_key=api_key, voice_id=voice_id)
            checks.append(
                PreflightCheck(
                    name="elevenlabs_configuration",
                    status="OK",
                    details=(
                        f"Loaded (voice_id={resolved_cfg.voice_id}, model={resolved_cfg.model_id}, "
                        f"output={resolved_cfg.output_format})"
                    ),
                )
            )
        except Exception as exc:
            checks.append(
                PreflightCheck(
                    name="elevenlabs_configuration",
                    status="WARN",
                    details=f"Invalid config ({exc})",
                )
            )

    # Optional network DNS check for ElevenLabs endpoint
    try:
        socket.gethostbyname("api.elevenlabs.io")
        checks.append(
            PreflightCheck(
                name="elevenlabs_dns_resolution",
                status="OK",
                details="api.elevenlabs.io resolves",
            )
        )
    except Exception as exc:
        checks.append(
            PreflightCheck(
                name="elevenlabs_dns_resolution",
                status="WARN",
                details=f"Could not resolve host ({exc})",
            )
        )

    def _http_json(url: str) -> tuple[int, dict]:
        assert api_key
        with httpx.Client(timeout=10.0) as client:
            resp = client.get(url, headers={"xi-api-key": api_key})
        try:
            return resp.status_code, resp.json()
        except Exception:
            return resp.status_code, {"raw": resp.text[:500]}

    def _tts_probe(cfg: ElevenLabsConfig) -> tuple[int, dict]:
        assert api_key
        url = f"https://api.elevenlabs.io/v1/text-to-speech/{cfg.voice_id}"
        accept = (
            "audio/wav" if cfg.output_format.lower().startswith("wav") else "audio/mpeg"
        )
        headers = {
            "xi-api-key": api_key,
            "Content-Type": "application/json",
            "Accept": accept,
        }
        payload = {"text": "Debug run.", "model_id": cfg.model_id}
        with httpx.Client(timeout=15.0) as client:
            resp = client.post(
                url,
                params={"output_format": cfg.output_format},
                headers=headers,
                json=payload,
            )
        if resp.status_code == 200:
            return 200, {"ok": True, "bytes": len(resp.content)}
        try:
            return resp.status_code, resp.json()
        except Exception:
            return resp.status_code, {"raw": resp.text[:500]}

    # Permission / capability checks (only if key is set and config resolved)
    if api_key and resolved_cfg:
        status, body = _http_json(
            f"https://api.elevenlabs.io/v1/voices/{resolved_cfg.voice_id}"
        )
        if status == 200:
            checks.append(
                PreflightCheck(
                    "elevenlabs_voice_access",
                    "OK",
                    f"voice={body.get('name', 'unknown')}",
                )
            )
        else:
            checks.append(
                PreflightCheck(
                    "elevenlabs_voice_access",
                    "WARN",
                    f"HTTP {status}: {body.get('detail', body)}",
                )
            )

        status, body = _tts_probe(resolved_cfg)
        if status == 200:
            checks.append(
                PreflightCheck(
                    "elevenlabs_tts_probe", "OK", f"ok (bytes={body.get('bytes')})"
                )
            )
        else:
            detail = body.get("detail", body)
            checks.append(
                PreflightCheck(
                    "elevenlabs_tts_probe", "WARN", f"HTTP {status}: {detail}"
                )
            )

    # OpenCV face detector readiness
    cascade_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
    cascade = cv2.CascadeClassifier(cascade_path)
    if cascade.empty():
        checks.append(
            PreflightCheck(
                name="opencv_face_cascade",
                status="FAIL",
                details=f"Could not load {cascade_path}",
            )
        )
    else:
        checks.append(
            PreflightCheck(
                name="opencv_face_cascade",
                status="OK",
                details=f"Loaded {cascade_path}",
            )
        )

    # Reachy sensor/runtime checks
    frame = mini.media.get_frame()
    if frame is None:
        checks.append(
            PreflightCheck(
                name="reachy_camera_frame",
                status="FAIL",
                details="No frame returned from camera",
            )
        )
    else:
        h, w = frame.shape[:2]
        checks.append(
            PreflightCheck(
                name="reachy_camera_frame",
                status="OK",
                details=f"Frame received ({w}x{h})",
            )
        )

    try:
        doa = mini.media.audio.get_DoA()
        if doa is None:
            checks.append(
                PreflightCheck(
                    name="reachy_audio_doa",
                    status="WARN",
                    details="Not available on this audio hardware/backend",
                )
            )
        else:
            angle, speech = doa
            checks.append(
                PreflightCheck(
                    name="reachy_audio_doa",
                    status="OK",
                    details=f"angle={angle:.2f} rad, speech={speech}",
                )
            )
    except Exception as exc:
        checks.append(
            PreflightCheck(
                name="reachy_audio_doa",
                status="FAIL",
                details=str(exc),
            )
        )

    if hasattr(mini.media, "play_sound"):
        checks.append(
            PreflightCheck(
                name="reachy_audio_playback_api",
                status="OK",
                details="play_sound API available",
            )
        )
    else:
        checks.append(
            PreflightCheck(
                name="reachy_audio_playback_api",
                status="FAIL",
                details="play_sound API missing",
            )
        )

    ok = _print_preflight_report(checks)

    # If ElevenLabs is usable, have the robot say "Debug Run" once.
    if api_key and resolved_cfg:
        probe_ok = any(
            c.name == "elevenlabs_tts_probe" and c.status == "OK" for c in checks
        )
        if probe_ok:
            _shout_debug_run(mini, resolved_cfg)
        else:
            print(
                f"{_c('[TTS][INFO]', _Color.BLUE)} TTS not ready; continuing without spoken intro. See PRECHECK warnings above."
            )

    return ok


def _save_frame(frame, path: Path) -> str:
    ok = cv2.imwrite(str(path), frame)
    if not ok:
        raise RuntimeError(f"Failed to save image to {path}")
    return path.name


def _build_single_frame_strip(frames: list, labels: list[str]):
    if not frames:
        raise ValueError("No frames to combine")

    target_height = min(frame.shape[0] for frame in frames)
    resized = []
    for frame, label in zip(frames, labels):
        h, w = frame.shape[:2]
        new_w = int(w * (target_height / h))
        img = cv2.resize(frame, (new_w, target_height))
        cv2.putText(
            img,
            label,
            (12, 28),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (255, 255, 255),
            2,
            cv2.LINE_AA,
        )
        resized.append(img)

    return cv2.hconcat(resized)


def _frame_sharpness(frame) -> float:
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    return float(cv2.Laplacian(gray, cv2.CV_64F).var())


def _capture_best_frame(
    mini: ReachyMini, *, warmup_frames: int = 2, candidates: int = 4
):
    best_frame = None
    best_score = -1.0

    # Warm-up frames right after movement often contain motion blur.
    for _ in range(warmup_frames):
        mini.media.get_frame()

    for _ in range(candidates):
        frame = mini.media.get_frame()
        if frame is None:
            continue
        score = _frame_sharpness(frame)
        if score > best_score:
            best_score = score
            best_frame = frame

    return best_frame


def _step_capture_image(mini: ReachyMini, run_dir: Path) -> str:
    frame = _capture_best_frame(mini)
    if frame is None:
        raise RuntimeError("Camera not available")
    name = _save_frame(frame, run_dir / "capture_image.jpg")
    return f"Saved image: {name}"


def _step_scan_surroundings(mini: ReachyMini, run_dir: Path) -> str:
    steps = 5
    yaw_range = 120.0
    quality = 95
    half = yaw_range / 2
    yaw_positions = [-half + i * yaw_range / (steps - 1) for i in range(steps)]

    saved = []
    frames_for_strip = []
    labels_for_strip = []
    for idx, yaw in enumerate(yaw_positions, start=1):
        mini.goto_target(
            head=create_head_pose(yaw=yaw, mm=True, degrees=True),
            duration=0.6,
        )
        time.sleep(0.2)
        frame = _capture_best_frame(mini)
        if frame is None:
            continue
        ok, jpeg_bytes = cv2.imencode(
            ".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, quality]
        )
        if not ok:
            continue
        out_path = run_dir / f"scan_{idx:02d}_yaw_{yaw:+.0f}.jpg"
        out_path.write_bytes(jpeg_bytes.tobytes())
        saved.append(out_path.name)
        frames_for_strip.append(frame)
        labels_for_strip.append(f"yaw {yaw:+.0f}°")

    mini.goto_target(head=create_head_pose(mm=True, degrees=True), duration=0.6)
    if not saved:
        raise RuntimeError("No scan frames captured")

    strip = _build_single_frame_strip(frames_for_strip, labels_for_strip)
    strip_name = _save_frame(strip, run_dir / "scan_surroundings_single_frame.jpg")
    return (
        f"Saved {len(saved)} panoramic images: {', '.join(saved)}; "
        f"combined frame: {strip_name}"
    )


def _step_track_face(mini: ReachyMini) -> str:
    cascade_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
    face_cascade = cv2.CascadeClassifier(cascade_path)
    if face_cascade.empty():
        raise RuntimeError(f"Failed to load face cascade: {cascade_path}")

    frame = mini.media.get_frame()
    if frame is None:
        raise RuntimeError("Camera not available")

    img_h, img_w = frame.shape[:2]
    scale = 0.25
    small = cv2.resize(frame, None, fx=scale, fy=scale)
    gray = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(
        gray, scaleFactor=1.1, minNeighbors=5, minSize=(15, 15)
    )
    if len(faces) == 0:
        return "No face detected (step completed without movement)"

    largest = max(faces, key=lambda f: f[2] * f[3])
    x, y, w, h = [v / scale for v in largest]
    face_center_x = x + w / 2
    face_center_y = y + h / 2
    offset_x = face_center_x - img_w / 2
    offset_y = face_center_y - img_h / 2
    yaw = -(offset_x / img_w) * _HORIZONTAL_FOV
    pitch = (offset_y / img_h) * _VERTICAL_FOV

    mini.goto_target(
        head=create_head_pose(yaw=yaw, pitch=pitch, mm=True, degrees=True),
        duration=0.5,
    )
    return f"Face tracked: moved to yaw={yaw:+.1f}°, pitch={pitch:+.1f}°"


def _step_move_antennas(mini: ReachyMini) -> str:
    mini.goto_target(antennas=[0.8, -0.8], duration=0.4)
    mini.goto_target(antennas=[-0.8, 0.8], duration=0.4)
    mini.goto_target(antennas=[0, 0], duration=0.4)
    return "Antenna sequence executed"


def _step_look_at_point(mini: ReachyMini) -> str:
    mini.look_at_world(0.5, 0.0, 0.1, duration=1.0)
    return "Look-at executed"


def _step_nod(mini: ReachyMini) -> str:
    mini.goto_target(
        head=create_head_pose(pitch=15, mm=True, degrees=True), duration=0.3
    )
    mini.goto_target(
        head=create_head_pose(pitch=-10, mm=True, degrees=True), duration=0.3
    )
    mini.goto_target(head=create_head_pose(mm=True, degrees=True), duration=0.3)
    return "Nod gesture executed"


def _step_shake_head(mini: ReachyMini) -> str:
    mini.goto_target(
        head=create_head_pose(yaw=-20, mm=True, degrees=True), duration=0.3
    )
    mini.goto_target(head=create_head_pose(yaw=20, mm=True, degrees=True), duration=0.3)
    mini.goto_target(head=create_head_pose(mm=True, degrees=True), duration=0.3)
    return "Shake-head gesture executed"


def _step_detect_sound_direction(mini: ReachyMini) -> str:
    doa = mini.media.audio.get_DoA()
    if doa is None:
        return "Sound direction (DoA) not available on this audio hardware/backend"
    angle, speech = doa
    return f"Detected angle={angle:.2f} rad, speech={speech}"


def _step_barrel_roll(mini: ReachyMini) -> str:
    mini.goto_target(
        head=create_head_pose(z=20, roll=10, mm=True, degrees=True), duration=1.0
    )
    mini.goto_target(antennas=[0.6, -0.6], duration=0.3)
    mini.goto_target(antennas=[-0.6, 0.6], duration=0.3)
    mini.goto_target(head=create_head_pose(), antennas=[0, 0], duration=1.0)
    return "Barrel roll sequence executed"


def _execute_step(
    mini: ReachyMini,
    name: str,
    announce_text: str,
    run_fn: Callable[[], str],
    results: list[StepResult],
    step_no: int,
    total_steps: int,
) -> None:
    print(
        f"{_c(f'[STEP {step_no:02d}/{total_steps:02d}]', _Color.MAGENTA + _Color.BOLD)} {name}"
    )
    _announce(mini, announce_text)
    time.sleep(ANNOUNCE_PAUSE_S)
    started = _utc_now_iso()
    try:
        details = run_fn()
        status = "PASS"
    except Exception as exc:
        details = str(exc)
        status = "FAIL"
    finished = _utc_now_iso()
    results.append(
        StepResult(
            name=name,
            status=status,
            details=details,
            started_at=started,
            finished_at=finished,
        )
    )
    print(f"[{_status_badge(status)}] {name}: {details}")
    print("-" * 61)


def _build_markdown_report(run_dir: Path, results: list[StepResult]) -> None:
    report_path = run_dir / "run_report.md"
    lines = [
        "# Reachy Debug Run Report",
        "",
        f"- Run directory: `{run_dir}`",
        f"- Generated at (UTC): {_utc_now_iso()}",
        "",
        "## Step Status Checks",
        "",
        "| Step | Status | Started (UTC) | Finished (UTC) | Details |",
        "|------|--------|---------------|----------------|---------|",
    ]
    for row in results:
        details = row.details.replace("|", "\\|")
        lines.append(
            f"| `{row.name}` | **{row.status}** | `{row.started_at}` | "
            f"`{row.finished_at}` | {details} |"
        )

    images = sorted(p.name for p in run_dir.glob("*.jpg"))
    lines.extend(["", "## Captured Images", ""])
    if images:
        for name in images:
            lines.append(f"- `{name}`")
    else:
        lines.append("- No images captured.")

    lines.extend(["", "## Summary", ""])
    failed = [r for r in results if r.status != "PASS"]
    if failed:
        lines.append(f"- Result: FAILED ({len(failed)} step(s) failed)")
    else:
        lines.append(f"- Result: PASS ({len(results)} step(s) passed)")

    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"[INFO] Report saved: {report_path}")


def run_demo_suite() -> int:
    run_dir = _create_run_dir()
    results: list[StepResult] = []
    total_steps = 13
    step_no = 0

    with ReachyMini() as mini:
        _print_banner(run_dir)
        print(f"{_c('[INFO]', _Color.BLUE)} Connected to Reachy Mini / simulator")
        precheck_ok = _run_preflight_checks(mini, run_dir)
        if not precheck_ok:
            print(
                f"{_c('[FATAL]', _Color.RED + _Color.BOLD)} Precheck failed. Aborting debug run before demo steps."
            )
            return 1

        def run_step(name: str, announce_text: str, run_fn: Callable[[], str]) -> None:
            nonlocal step_no
            step_no += 1
            _execute_step(
                mini=mini,
                name=name,
                announce_text=announce_text,
                run_fn=run_fn,
                results=results,
                step_no=step_no,
                total_steps=total_steps,
            )

        run_step(
            name="wake_up",
            announce_text="Now testing robot wake-up behavior.",
            run_fn=lambda: (mini.wake_up() or "Wake-up animation executed"),
        )
        run_step(
            name="move_head",
            announce_text="Now testing 6-DoF head movement.",
            run_fn=lambda: (
                mini.goto_target(
                    head=create_head_pose(
                        x=10,
                        y=0,
                        z=15,
                        roll=8,
                        pitch=-10,
                        yaw=20,
                        mm=True,
                        degrees=True,
                    ),
                    duration=1.0,
                )
                or "Head pose executed"
            ),
        )
        run_step(
            name="move_antennas",
            announce_text="Now testing antenna movement.",
            run_fn=lambda: _step_move_antennas(mini),
        )
        run_step(
            name="look_at_point",
            announce_text="Now testing look-at-point behavior in 3D space.",
            run_fn=lambda: _step_look_at_point(mini),
        )
        run_step(
            name="gesture_nod",
            announce_text="Now testing nod gesture.",
            run_fn=lambda: _step_nod(mini),
        )
        run_step(
            name="gesture_shake_head",
            announce_text="Now testing shake-head gesture.",
            run_fn=lambda: _step_shake_head(mini),
        )
        run_step(
            name="play_sound",
            announce_text="Now testing onboard audio playback.",
            run_fn=lambda: (
                mini.media.play_sound("count.wav") or "Sound played: count.wav"
            ),
        )
        run_step(
            name="detect_sound_direction",
            announce_text="Now testing sound direction detection.",
            run_fn=lambda: _step_detect_sound_direction(mini),
        )
        run_step(
            name="capture_image",
            announce_text="Now testing single camera capture.",
            run_fn=lambda: _step_capture_image(mini, run_dir),
        )
        run_step(
            name="scan_surroundings",
            announce_text="Now testing panoramic surroundings scan.",
            run_fn=lambda: _step_scan_surroundings(mini, run_dir),
        )
        run_step(
            name="track_face",
            announce_text="Now testing face tracking.",
            run_fn=lambda: _step_track_face(mini),
        )
        run_step(
            name="do_barrel_roll",
            announce_text="Now testing barrel-roll sequence.",
            run_fn=lambda: _step_barrel_roll(mini),
        )
        run_step(
            name="go_to_sleep",
            announce_text="Finally, testing sleep mode transition.",
            run_fn=lambda: (mini.goto_sleep() or "Sleep-mode animation executed"),
        )

    _build_markdown_report(run_dir, results)
    return 0 if all(r.status == "PASS" for r in results) else 1


def main() -> None:
    raise SystemExit(run_demo_suite())


if __name__ == "__main__":
    main()
